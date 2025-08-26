#!/usr/bin/env python3
"""
Historical stocking data importer for Uinta Mountains fishing database.
This script fetches and imports historical data for a specific year into the database.
"""
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

def fetch_stocking_data(county, year):
    """Fetch stocking data for a given county and year."""
    url = f"https://dwrapps.utah.gov/fishstocking/FishAjax?y={year}&sort=watername&sortorder=ASC&sortspecific={county}&whichSpecific=county"
    try:
        response = requests.get(url)
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
    ambiguous_entries = []
    new_csv_records = []
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 6:
            water_name = cols[0].text.strip()
            county_name = cols[1].text.strip()
            raw_species = cols[2].text.strip()
            species = standardize_stocking_species(raw_species)
            quantity = int(cols[3].text.strip())
            length = float(cols[4].text.strip())
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
                log_file.write(f"  UNMATCHED: {water_name} - {species} x{quantity}\n")
                continue

            # Check for potential issues
            if match_type in ['fuzzy', 'partial']:
                ambiguous_entries.append({
                    'water_name': water_name,
                    'match_details': match_details,
                    'match_type': match_type,
                    'species': species,
                    'quantity': quantity,
                    'date': stock_date
                })

            # Check if record already exists
            if not stocking_record_exists(cursor, lake_id, species, quantity, stock_date):
                insert_stocking_record(cursor, lake_id, species, quantity, length, stock_date, source_year, county_name)
                new_records += 1
                
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
                log_file.write(f"  NEW: {water_name} ({lake_id}) - {species} x{quantity} on {stock_date}\n")

    # Write new records to CSV
    for record in new_csv_records:
        csv_writer.writerow(record)

    conn.commit()
    return new_records, unmatched_lakes, ambiguous_entries

def import_year(year):
    """Import stocking data for a specific year."""
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    csv_path = os.path.join(project_dir, 'data', 'utah_dwr_stocking_data.csv')
    log_path = os.path.join(project_dir, 'logs', f'import_{year}.log')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Start logging
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"=== IMPORTING {year} STOCKING DATA ===")
    print(f"Starting import at {timestamp}")
    
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"=== IMPORTING {year} STOCKING DATA ===\n")
        log_file.write(f"Started at: {timestamp}\n\n")
        
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
            all_ambiguous = []
            
            for county in ["Summit", "Duchesne"]:
                log_file.write(f"\n=== PROCESSING {county.upper()} COUNTY ===\n")
                print(f"Processing {county} county...")
                
                html_content = fetch_stocking_data(county, year)
                if html_content:
                    new_records, unmatched, ambiguous = parse_and_insert_data(
                        html_content, conn, cursor, county, year, csv_writer, log_file
                    )
                    total_new_records += new_records
                    all_unmatched.update(unmatched)
                    all_ambiguous.extend(ambiguous)
                    
                    log_file.write(f"\n{county} Summary: {new_records} new records, {len(unmatched)} unmatched\n")
                else:
                    log_file.write(f"ERROR: Failed to fetch data for {county}\n")
            
            conn.close()
            
            # Final summary
            log_file.write(f"\n=== {year} IMPORT SUMMARY ===\n")
            log_file.write(f"Total new records: {total_new_records}\n")
            log_file.write(f"Total unmatched lakes: {len(all_unmatched)}\n")
            log_file.write(f"Ambiguous matches: {len(all_ambiguous)}\n")
            log_file.write(f"CSV file updated: {csv_path}\n")
            log_file.write(f"Run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            if all_ambiguous:
                log_file.write(f"\nAMBIGUOUS ENTRIES:\n")
                for entry in all_ambiguous:
                    log_file.write(f"  {entry['water_name']} -> {entry['match_details']} ({entry['match_type']})\n")
            
            print(f"\n=== {year} IMPORT COMPLETE ===")
            print(f"New records added: {total_new_records}")
            print(f"Unmatched lakes: {len(all_unmatched)}")
            print(f"Ambiguous matches: {len(all_ambiguous)}")
            if all_unmatched:
                print("Unmatched lakes:", ", ".join(sorted(list(all_unmatched))))
            if all_ambiguous:
                print("Ambiguous entries found - check log for details")
            print(f"Log: {log_path}")
            
            return total_new_records, len(all_unmatched), len(all_ambiguous)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
    else:
        year = 2017
    
    import_year(year)