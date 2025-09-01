#!/usr/bin/env python3
"""
Historical stocking data importer for Uintah and Daggett counties.
This script fetches and imports historical data from 2002 to present for the two previously missing counties.
"""
import requests
from bs4 import BeautifulSoup
import sqlite3
import csv
import os
import sys
from database_utils import create_database, extract_letter_number, stocking_record_exists, find_matching_lake
from species_utils import standardize_stocking_species, update_lake_fish_species
from datetime import datetime

def insert_stocking_record(cursor, lake_id, species, quantity, length, stock_date, source_year, county):
    """Insert a new stocking record."""
    cursor.execute("""
        INSERT INTO stocking_records (lake_id, species, quantity, length, stock_date, source_year, county)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lake_id, species, quantity, length, stock_date, source_year, county))

def fetch_stocking_data(county, year):
    """Fetch stocking data for a given county and year."""
    url = f"https://dwrapps.utah.gov/fishstocking/FishAjax?y={year}&sort=watername&sortorder=ASC&sortspecific={county}&whichSpecific=county"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {county} {year}: {e}")
        return None

def parse_and_insert_data(html_content, conn, cursor, county, year, csv_writer, log_file):
    """Parse HTML and insert historical stocking records."""
    if not html_content:
        return 0, set(), []

    soup = BeautifulSoup(html_content, 'lxml')
    rows = soup.find_all('tr')
    
    new_records = 0
    unmatched_lakes = set()
    matched_lakes = set()
    new_csv_records = []
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 6:
            water_name = cols[0].text.strip()
            county_name = cols[1].text.strip()
            raw_species = cols[2].text.strip()
            species = standardize_stocking_species(raw_species)
            
            try:
                quantity = int(cols[3].text.strip())
                length = float(cols[4].text.strip())
            except ValueError as e:
                log_file.write(f"  ERROR: Could not parse quantity/length for {water_name}: {e}\n")
                continue
                
            stock_date_str = cols[5].text.strip()
            
            try:
                stock_date = datetime.strptime(stock_date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
                source_year = datetime.strptime(stock_date_str, '%m/%d/%Y').year
            except ValueError:
                log_file.write(f"  ERROR: Could not parse date: {stock_date_str} for {water_name}\n")
                continue

            lake_id, match_type, match_details = find_matching_lake(cursor, water_name)

            if not lake_id:
                unmatched_lakes.add(water_name)
                continue

            # Check if this exact record already exists
            if not stocking_record_exists(cursor, lake_id, species, quantity, stock_date):
                insert_stocking_record(cursor, lake_id, species, quantity, length, stock_date, source_year, county_name)
                new_records += 1
                matched_lakes.add(water_name)
                
                # Update fish_species field with new stocking data
                update_lake_fish_species(cursor, lake_id)
                
                # Flag lake for Apple Notes update when new stocking record added
                cursor.execute("UPDATE lakes SET notes_needs_update = TRUE WHERE id = ?", (lake_id,))
                
                # Add to CSV records list
                new_csv_records.append({
                    'water_name': water_name,
                    'county': county_name,
                    'species': raw_species,  # Use original for CSV
                    'quantity': quantity,
                    'length': length,
                    'stock_date': stock_date_str,  # Use original format for CSV
                    'source_year': source_year
                })
                
                # Log the new record
                log_file.write(f"  NEW: {water_name} ({lake_id}) - {species} x{quantity} on {stock_date} [{match_type}]\n")

    # Write new records to CSV
    for record in new_csv_records:
        csv_writer.writerow(record)

    conn.commit()
    
    # Log summary
    if matched_lakes:
        log_file.write(f"  → {new_records} new records added for {len(matched_lakes)} lakes in {county}\n")
        log_file.write(f"    Matched lakes: {', '.join(sorted(matched_lakes))}\n")
    if unmatched_lakes:
        log_file.write(f"  → {len(unmatched_lakes)} unmatched waters in {county}\n")
    
    print(f"  {county} {year}: {new_records} new records from {len(matched_lakes)} matched lakes")
    return new_records, unmatched_lakes, matched_lakes

def main():
    """Main function to fetch and import historical stocking data for Uintah and Daggett counties."""
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    csv_path = os.path.join(project_dir, 'data', 'utah_dwr_stocking_data.csv')
    log_path = os.path.join(project_dir, 'logs', 'uintah_daggett_historical_import.log')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Start logging
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"=== IMPORTING UINTAH & DAGGETT HISTORICAL DATA (2002-2025) ===")
    print(f"Starting import at {timestamp}")
    print(f"This will take several minutes...")
    print()
    
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"=== UINTAH & DAGGETT HISTORICAL STOCKING IMPORT ===\n")
        log_file.write(f"Started at: {timestamp}\n")
        log_file.write(f"Years: 2002-2025\n")
        log_file.write(f"Counties: Uintah, Daggett\n\n")
        
        # Open CSV file for appending new records
        csv_file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['water_name', 'county', 'species', 'quantity', 'length', 'stock_date', 'source_year']
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            # Write header if new file (shouldn't happen but just in case)
            if not csv_file_exists:
                csv_writer.writeheader()
                log_file.write("Created new CSV file with headers\n")
            
            # Connect to database
            conn = create_database()
            cursor = conn.cursor()
            
            total_new_records = 0
            all_unmatched = set()
            all_matched = set()
            county_summaries = {}
            
            counties = ["Uintah", "Daggett"]
            years = range(2002, 2026)  # 2002 through 2025
            
            for county in counties:
                log_file.write(f"\n=== PROCESSING {county.upper()} COUNTY ===\n")
                print(f"\nProcessing {county} county (2002-2025):")
                
                county_records = 0
                county_matched = set()
                county_unmatched = set()
                
                for year in years:
                    print(f"  Fetching {year}...", end=" ")
                    sys.stdout.flush()
                    
                    html_content = fetch_stocking_data(county, year)
                    if html_content:
                        new_records, unmatched, matched = parse_and_insert_data(
                            html_content, conn, cursor, county, year, csv_writer, log_file
                        )
                        county_records += new_records
                        county_matched.update(matched)
                        county_unmatched.update(unmatched)
                        
                        if new_records > 0:
                            print(f"✓ {new_records}")
                        else:
                            print("✓ 0")
                    else:
                        print("✗ Failed")
                        log_file.write(f"    ERROR: Failed to fetch data for {county} {year}\n")
                
                county_summaries[county] = {
                    'records': county_records,
                    'matched_lakes': len(county_matched),
                    'unmatched_waters': len(county_unmatched)
                }
                
                total_new_records += county_records
                all_matched.update(county_matched)
                all_unmatched.update(county_unmatched)
                
                log_file.write(f"\n{county} County Summary:\n")
                log_file.write(f"  Total new records: {county_records}\n")
                log_file.write(f"  Matched lakes: {len(county_matched)}\n")
                log_file.write(f"  Unmatched waters: {len(county_unmatched)}\n")
                if county_matched:
                    log_file.write(f"  Lake names matched: {', '.join(sorted(county_matched))}\n")
                log_file.write("\n")
            
            conn.close()
            
            # Final summary
            log_file.write(f"=== FINAL SUMMARY ===\n")
            log_file.write(f"Counties processed: Uintah, Daggett\n")
            log_file.write(f"Years processed: 2002-2025\n")
            log_file.write(f"Total new stocking records: {total_new_records}\n")
            log_file.write(f"Total unique lakes matched: {len(all_matched)}\n")
            log_file.write(f"Total unmatched waters: {len(all_unmatched)}\n")
            log_file.write(f"CSV file updated: {csv_path}\n")
            log_file.write(f"Run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            print(f"\n=== FINAL SUMMARY ===")
            print(f"Total new records imported: {total_new_records}")
            print(f"Unique Uinta lakes found: {len(all_matched)}")
            for county in counties:
                summary = county_summaries[county]
                print(f"  {county}: {summary['records']} records from {summary['matched_lakes']} lakes")
            print(f"Unmatched waters (ignored): {len(all_unmatched)}")
            print(f"\nLog saved to: {log_path}")
            print(f"CSV updated: {csv_path}")
            
            if all_matched:
                print(f"\n🎣 Found Uinta lakes in new counties:")
                for lake in sorted(all_matched):
                    print(f"   • {lake}")

if __name__ == "__main__":
    main()