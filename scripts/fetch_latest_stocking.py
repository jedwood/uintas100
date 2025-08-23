#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import sqlite3
import csv
import os
from database_utils import create_database, extract_letter_number, stocking_record_exists, find_matching_lake
from species_utils import standardize_stocking_species
from datetime import datetime

def insert_stocking_record(cursor, lake_id, species, quantity, length, stock_date, source_year, county):
    """Insert a new stocking record."""
    cursor.execute("""
        INSERT INTO stocking_records (lake_id, species, quantity, length, stock_date, source_year, county)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lake_id, species, quantity, length, stock_date, source_year, county))

def fetch_stocking_data(county):
    """Fetch stocking data for a given county."""
    current_year = datetime.now().year
    url = f"https://dwrapps.utah.gov/fishstocking/FishAjax?y={current_year}&sort=watername&sortorder=ASC&sortspecific={county}&whichSpecific=county"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {county}: {e}")
        return None

def parse_and_insert_data(html_content, conn, cursor, county, csv_writer, log_file):
    """Parse HTML and insert new stocking records."""
    if not html_content:
        return 0, set()

    soup = BeautifulSoup(html_content, 'lxml')
    rows = soup.find_all('tr')
    
    new_records = 0
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
                unmatched_lakes.add(water_name)
                continue

            if not stocking_record_exists(cursor, lake_id, species, quantity, stock_date):
                insert_stocking_record(cursor, lake_id, species, quantity, length, stock_date, source_year, county)
                new_records += 1
                
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
                log_file.write(f"  NEW: {water_name} ({lake_id}) - {species} x{quantity} on {stock_date}\n")

    # Write new records to CSV
    for record in new_csv_records:
        csv_writer.writerow(record)

    conn.commit()
    
    # Log summary
    log_file.write(f"  → {new_records} new records added for {county} county\n")
    if unmatched_lakes:
        log_file.write(f"  → {len(unmatched_lakes)} unmatched lakes in {county}\n")
        for lake in sorted(list(unmatched_lakes)):
            log_file.write(f"    - {lake}\n")
    
    print(f"Inserted {new_records} new stocking records for {county} county.")
    return new_records, unmatched_lakes

def main():
    """Main function to fetch and update stocking data."""
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    csv_path = os.path.join(project_dir, 'data', 'utah_dwr_stocking_data.csv')
    log_path = os.path.join(project_dir, 'output', 'stocking_update.log')
    
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
            all_unmatched = set()
            
            for county in ["Summit", "Duchesne"]:
                log_file.write(f"\nProcessing {county} county...\n")
                print(f"Fetching data for {county} county...")
                
                html_content = fetch_stocking_data(county)
                if html_content:
                    new_records, unmatched = parse_and_insert_data(
                        html_content, conn, cursor, county, csv_writer, log_file
                    )
                    total_new_records += new_records
                    all_unmatched.update(unmatched)
                else:
                    log_file.write(f"  ERROR: Failed to fetch data for {county}\n")
            
            conn.close()
            
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