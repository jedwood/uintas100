#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import sqlite3
import csv
import os
import subprocess
from database_utils import (
    create_database, extract_letter_number, stocking_record_exists, find_matching_lake,
    find_fringe_water, upsert_other_water, other_stocking_exists,
)
from species_utils import standardize_stocking_species, update_lake_fish_species, refresh_all_fish_species
from writer_guard import pull_and_exit_if_readonly
from datetime import datetime

def insert_stocking_record(cursor, lake_id, species, quantity, length, stock_date, source_year, county):
    """Insert a new stocking record."""
    cursor.execute("""
        INSERT INTO stocking_records (lake_id, species, quantity, length, stock_date, source_year, county)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lake_id, species, quantity, length, stock_date, source_year, county))

def fetch_stocking_data(county, year=None):
    """Fetch stocking data for a given county and year."""
    if year is None:
        year = datetime.now().year
    url = f"https://dwrapps.utah.gov/fishstocking/FishAjax?y={year}&sort=watername&sortorder=ASC&sortspecific={county}&whichSpecific=county"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {county} ({year}): {e}")
        return None

def parse_and_insert_data(html_content, conn, cursor, county, csv_writer, log_file):
    """Parse HTML and insert new stocking records."""
    if not html_content:
        return 0, set()

    soup = BeautifulSoup(html_content, 'lxml')
    rows = soup.find_all('tr')
    
    new_records = 0
    new_fringe_records = 0
    unmatched_lakes = set()
    new_csv_records = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 6:
            water_name = cols[0].text.strip()
            county = cols[1].text.strip()
            raw_species = cols[2].text.strip()
            species = standardize_stocking_species(raw_species)
            quantity = int(cols[3].text.strip())
            length = float(cols[4].text.strip())
            stock_date_str = cols[5].text.strip()

            try:
                stock_date = datetime.strptime(stock_date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
                source_year = datetime.strptime(stock_date_str, '%m/%d/%Y').year
            except ValueError:
                print(f"Could not parse date: {stock_date_str}")
                continue

            lake_id, match_type, match_details = find_matching_lake(cursor, water_name)

            if not lake_id:
                # Not one of our lakes. If it shares a name root with a lake (e.g.
                # "Beaver Cr" ~ BR-10 Beaver), file it as a fringe water with a
                # guessed drainage; otherwise it's a lowland water we ignore.
                fringe = find_fringe_water(cursor, water_name)
                if fringe:
                    water_id = upsert_other_water(cursor, water_name, fringe, county=county.title())
                    if not other_stocking_exists(cursor, water_id, species, quantity, stock_date):
                        cursor.execute(
                            """INSERT INTO other_stocking_records
                               (water_id, county, species, quantity, length, stock_date, source_year)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (water_id, county, species, quantity, length, stock_date, source_year),
                        )
                        new_fringe_records += 1
                        # keep the CSV a complete log of everything DWR stocked
                        new_csv_records.append({
                            'water_name': water_name, 'county': county,
                            'species': raw_species, 'quantity': quantity, 'length': length,
                            'stock_date': stock_date_str, 'source_year': source_year,
                        })
                        log_file.write(
                            f"  FRINGE: {water_name} [{fringe['water_type']}] "
                            f"~{fringe['likely_drainage']} - {species} x {quantity} on {stock_date}\n"
                        )
                else:
                    unmatched_lakes.add(water_name)
                continue

            if not stocking_record_exists(cursor, lake_id, species, quantity, stock_date):
                insert_stocking_record(cursor, lake_id, species, quantity, length, stock_date, source_year, county)
                new_records += 1
                
                # Update fish_species field with new stocking data
                update_lake_fish_species(cursor, lake_id)
                
                # Flag lake for Apple Notes update when new stocking record added
                cursor.execute("UPDATE lakes SET notes_needs_update = TRUE WHERE id = ?", (lake_id,))
                
                # Add to CSV records list
                new_csv_records.append({
                    'water_name': water_name,
                    'county': county,
                    'species': raw_species,  # Use original for CSV
                    'quantity': quantity,
                    'length': length,
                    'stock_date': stock_date_str,  # Use original format for CSV
                    'source_year': source_year
                })
                
                # Log the new record
                # Show the lake's designation (e.g. WR-33), not the meaningless internal id
                designation = conn.execute(
                    "SELECT letter_number FROM lakes WHERE id = ?", (lake_id,)
                ).fetchone()[0] or lake_id
                log_file.write(f"  NEW: {water_name} ({designation}) - {species} x {quantity} on {stock_date}\n")

    # Write new records to CSV
    for record in new_csv_records:
        csv_writer.writerow(record)

    conn.commit()
    
    # Log summary
    log_file.write(f"  → {new_records} new records added for {county} county\n")
    if new_fringe_records:
        log_file.write(f"  → {new_fringe_records} new fringe (creek/pond) records in {county}\n")
    if unmatched_lakes:
        log_file.write(f"  → {len(unmatched_lakes)} unmatched lakes in {county}\n")
        for lake in sorted(list(unmatched_lakes)):
            log_file.write(f"    - {lake}\n")

    print(f"Inserted {new_records} new stocking records ({new_fringe_records} fringe) for {county} county.")
    return new_records, new_fringe_records, unmatched_lakes

def commit_and_push_changes(log_file, new_records_count, refreshed_count=0):
    """Commit database changes and push to remote if new records were added."""
    try:
        # Get the project root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        
        # Change to project directory for git commands
        original_cwd = os.getcwd()
        os.chdir(project_dir)
        
        # Check git status to see what files changed
        result = subprocess.run(['git', 'status', '--porcelain'], 
                               capture_output=True, text=True, check=True)
        
        if not result.stdout.strip():
            log_file.write("No git changes detected, skipping commit\n")
            return
        
        log_file.write(f"Git changes detected:\n{result.stdout}")

        # Keep the committed CSV seeds in lockstep with the DB. The pre-commit
        # hook also does this when enabled (git config core.hooksPath .githooks),
        # but regenerate here too so an unattended cron run can't push a DB whose
        # seeds have drifted, regardless of how the machine's hooks are set up.
        try:
            import export_seeds
            export_seeds.export()
            log_file.write("Regenerated data/seeds/ from DB\n")
        except Exception as e:
            log_file.write(f"WARNING: seed export failed ({e}); committing without seed refresh\n")

        # Add changed files
        subprocess.run(['git', 'add', 'uinta_lakes.db',
                        'data/utah_dwr_stocking_data.csv', 'data/seeds'],
                       check=True)
        log_file.write("Added database, CSV, and seed files to git\n")
        
        # Commit with descriptive message
        if new_records_count > 0:
            commit_msg = f"Auto-update: {new_records_count} new DWR stocking records"
        else:
            commit_msg = f"Auto-update: refresh fish_species for {refreshed_count} lakes"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        log_file.write(f"Committed changes: {commit_msg}\n")
        
        # Push to remote
        subprocess.run(['git', 'push'], check=True)
        log_file.write("Pushed changes to remote repository\n")
        
        print(f"✓ Committed and pushed {new_records_count} new stocking records")
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Git operation failed: {e}"
        log_file.write(f"ERROR: {error_msg}\n")
        print(f"⚠️  {error_msg}")
    except Exception as e:
        error_msg = f"Unexpected error during git operations: {e}"
        log_file.write(f"ERROR: {error_msg}\n")
        print(f"⚠️  {error_msg}")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def main():
    """Main function to fetch and update stocking data."""
    # Single-writer guard: on a read-only mirror (e.g. the MacBook) this becomes
    # a `git pull --ff-only` so the mirror clone — and the Tauri-served web app —
    # picks up whatever the Mini pushed, then exits.
    pull_and_exit_if_readonly("stocking fetch")

    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    csv_path = os.path.join(project_dir, 'data', 'utah_dwr_stocking_data.csv')
    log_path = os.path.join(project_dir, 'logs', 'stocking_update.log')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Start logging
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(log_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"\n=== STOCKING UPDATE RUN: {timestamp} ===\n")
        print(f"Starting stocking update at {timestamp}")
        
        # Open CSV file for appending new records
        csv_file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['water_name', 'county', 'species', 'quantity', 'length', 'stock_date', 'source_year']
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            # Write header if new file
            if not csv_file_exists:
                csv_writer.writeheader()
                log_file.write("Created new CSV file with headers\n")
            
            # Connect to database
            conn = create_database()
            cursor = conn.cursor()
            
            total_new_records = 0
            total_fringe_records = 0
            all_unmatched = set()

            # Fetch current year and prior year (catches late-season stocking added after year rolls over)
            current_year = datetime.now().year
            years_to_fetch = [current_year, current_year - 1]

            # Wasatch covers a few fringe Uinta lakes (e.g. D-33 Iron Mine, D-40
            # Broadhead). Non-Uinta waters in any county are dropped by the matcher.
            for year in years_to_fetch:
                log_file.write(f"\n--- Fetching {year} data ---\n")
                for county in ["Summit", "Duchesne", "Uintah", "Daggett", "Wasatch"]:
                    log_file.write(f"\nProcessing {county} county ({year})...\n")
                    print(f"Fetching data for {county} county ({year})...")

                    html_content = fetch_stocking_data(county, year)
                    if html_content:
                        new_records, new_fringe, unmatched = parse_and_insert_data(
                            html_content, conn, cursor, county, csv_writer, log_file
                        )
                        total_new_records += new_records
                        total_fringe_records += new_fringe
                        all_unmatched.update(unmatched)
                    else:
                        log_file.write(f"  ERROR: Failed to fetch data for {county} ({year})\n")
            
            # Sweep all lakes so the denormalized fish_species field can't drift
            # from the stocking table (e.g. species added via other import paths).
            changed = refresh_all_fish_species(cursor)
            conn.commit()
            log_file.write(f"Refreshed fish_species for {changed} lakes\n")
            if changed:
                print(f"Refreshed fish_species for {changed} lakes")

            conn.close()

            # Flush the appended CSV rows to disk BEFORE git add. commit_and_push
            # runs while this file is still open, and small appends (e.g. a couple
            # of new fringe rows) otherwise sit in the buffer past `git add`,
            # leaving the CSV committed a run behind / dirty in the working tree.
            csv_file.flush()

            # Commit and push changes if new records were added
            if total_new_records > 0 or total_fringe_records > 0 or changed > 0:
                log_file.write(f"\n=== GIT OPERATIONS ===\n")
                if total_fringe_records:
                    log_file.write(f"Plus {total_fringe_records} new fringe (creek/pond) records\n")
                print(f"\nCommitting and pushing {total_new_records} new records ({total_fringe_records} fringe)...")
                commit_and_push_changes(log_file, total_new_records, changed)
            else:
                log_file.write(f"\nNo new records added, skipping git commit\n")
                print("No new records added, skipping git operations")
                # A run with nothing to commit can still rewrite uinta_lakes.db
                # (SQLite page churn / last_modified) and leave it dirty in the
                # working tree. If left uncommitted, the scheduler's next
                # `git pull --autostash` stashes the binary DB and the pop
                # conflicts ("unmerged files") — exactly the failure this avoids.
                # Reset the DB to HEAD so each run ends with a clean tree.
                try:
                    subprocess.run(['git', 'checkout', 'HEAD', '--', 'uinta_lakes.db'],
                                   cwd=project_dir, check=True)
                    log_file.write("Reset no-op DB churn to keep the working tree clean\n")
                except subprocess.CalledProcessError as e:
                    log_file.write(f"WARNING: could not reset DB to HEAD: {e}\n")
            
            # Final summary
            log_file.write(f"\n=== SUMMARY ===\n")
            log_file.write(f"Total new records: {total_new_records}\n")
            log_file.write(f"Total unmatched lakes: {len(all_unmatched)}\n")
            log_file.write(f"CSV file updated: {csv_path}\n")
            log_file.write(f"Run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            print(f"\n=== FINAL SUMMARY ===")
            print(f"Total new records added: {total_new_records}")
            print(f"Unmatched lakes: {len(all_unmatched)}")
            print(f"Log saved to: {log_path}")
            print(f"CSV updated: {csv_path}")

if __name__ == "__main__":
    main()