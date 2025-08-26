#!/usr/bin/env python3
"""
Historical stocking data fetcher for Uinta Mountains fishing database.
This script fetches historical data for a specific year without inserting into the database.
Used for testing format and data availability before doing bulk historical imports.
"""
import requests
from bs4 import BeautifulSoup
import sqlite3
import csv
import os
from database_utils import create_database, extract_letter_number, find_matching_lake
from species_utils import standardize_stocking_species
from datetime import datetime

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

def parse_and_analyze_data(html_content, conn, cursor, county, year, log_file):
    """Parse HTML and analyze historical stocking records without inserting."""
    if not html_content:
        return 0, set(), []

    soup = BeautifulSoup(html_content, 'lxml')
    rows = soup.find_all('tr')
    
    found_records = 0
    unmatched_lakes = set()
    matched_lakes = set()
    all_records = []
    
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
                print(f"Could not parse date: {stock_date_str}")
                continue

            lake_id, match_type, match_details = find_matching_lake(cursor, water_name)

            record = {
                'water_name': water_name,
                'county': county_name,
                'raw_species': raw_species,
                'standardized_species': species,
                'quantity': quantity,
                'length': length,
                'stock_date': stock_date,
                'source_year': source_year,
                'lake_id': lake_id,
                'match_type': match_type,
                'match_details': match_details
            }
            all_records.append(record)

            if lake_id:
                matched_lakes.add(water_name)
                log_file.write(f"  MATCH: {water_name} -> Lake ID {lake_id} ({match_type})\n")
                log_file.write(f"    {species} x{quantity} ({length}\") on {stock_date}\n")
            else:
                unmatched_lakes.add(water_name)
                log_file.write(f"  NO MATCH: {water_name}\n")
                log_file.write(f"    {species} x{quantity} ({length}\") on {stock_date}\n")
            
            found_records += 1

    return found_records, unmatched_lakes, all_records

def main():
    """Main function to fetch and analyze historical stocking data."""
    year = 2017
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    log_path = os.path.join(project_dir, 'logs', f'historical_stocking_{year}.log')
    csv_path = os.path.join(project_dir, 'logs', f'historical_stocking_{year}.csv')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Start logging
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"=== HISTORICAL STOCKING DATA TEST: {year} ===")
    print(f"Starting historical fetch at {timestamp}")
    print(f"NOTE: This is a TEST RUN - no data will be inserted into the database")
    print()
    
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"=== HISTORICAL STOCKING DATA TEST: {year} ===\n")
        log_file.write(f"Started at: {timestamp}\n")
        log_file.write(f"NOTE: Test run - no database insertions\n\n")
        
        # Connect to database (read-only for matching)
        conn = create_database()
        cursor = conn.cursor()
        
        total_records = 0
        all_unmatched = set()
        all_matched = set()
        all_data = []
        
        for county in ["Summit", "Duchesne"]:
            log_file.write(f"=== PROCESSING {county.upper()} COUNTY ===\n")
            print(f"Fetching {year} data for {county} county...")
            
            html_content = fetch_stocking_data(county, year)
            if html_content:
                records, unmatched, data = parse_and_analyze_data(
                    html_content, conn, cursor, county, year, log_file
                )
                total_records += records
                all_unmatched.update(unmatched)
                all_matched.update([r['water_name'] for r in data if r['lake_id']])
                all_data.extend(data)
                
                log_file.write(f"\n{county} Summary:\n")
                log_file.write(f"  Records found: {records}\n")
                log_file.write(f"  Matched lakes: {len([r for r in data if r['lake_id']])}\n")
                log_file.write(f"  Unmatched lakes: {len(unmatched)}\n\n")
            else:
                log_file.write(f"ERROR: Failed to fetch data for {county}\n\n")
        
        conn.close()
        
        # Save detailed CSV for analysis
        if all_data:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
                fieldnames = ['water_name', 'county', 'raw_species', 'standardized_species', 
                            'quantity', 'length', 'stock_date', 'source_year', 'lake_id', 
                            'match_type', 'match_details']
                csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                csv_writer.writeheader()
                csv_writer.writerows(all_data)
        
        # Final summary
        log_file.write(f"=== FINAL SUMMARY ===\n")
        log_file.write(f"Year: {year}\n")
        log_file.write(f"Total records found: {total_records}\n")
        log_file.write(f"Total matched lakes: {len(all_matched)}\n")
        log_file.write(f"Total unmatched lakes: {len(all_unmatched)}\n")
        log_file.write(f"Match rate: {len(all_matched)/(len(all_matched)+len(all_unmatched))*100:.1f}%\n")
        log_file.write(f"Detailed CSV saved: {csv_path}\n")
        log_file.write(f"Run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"\n=== ANALYSIS COMPLETE ===")
        print(f"Year: {year}")
        print(f"Total records found: {total_records}")
        print(f"Matched lakes: {len(all_matched)}")
        print(f"Unmatched lakes: {len(all_unmatched)}")
        if total_records > 0:
            print(f"Match rate: {len(all_matched)/(len(all_matched)+len(all_unmatched))*100:.1f}%")
        print(f"Log saved to: {log_path}")
        print(f"CSV saved to: {csv_path}")
        print(f"\nReview the log and CSV files before proceeding with actual data import.")

if __name__ == "__main__":
    main()