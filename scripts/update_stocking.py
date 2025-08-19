#!/usr/bin/env python3
"""
Ongoing stocking data update script for Uinta Mountains fishing database.
Run this whenever new stocking reports are available.

This script safely adds new stocking records without duplicating existing ones.
"""

import sqlite3
import csv
import re
from datetime import datetime
from database_utils import create_database, find_matching_lake, extract_letter_number, dump_stocking_data, dump_combined_data

def process_stocking_data(conn):
    """Process stocking data and match with lakes"""
    cursor = conn.cursor()
    unmatched_records = []
    new_records_count = 0
    duplicate_count = 0
    
    with open('../data/utah_dwr_stocking_data.csv', 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            water_name = row['water_name']
            lake_id, confidence, notes = find_matching_lake(cursor, water_name)
            
            if lake_id:
                # Convert date from MM/DD/YYYY to YYYY-MM-DD for comparison and storage
                try:
                    date_obj = datetime.strptime(row['stock_date'], '%m/%d/%Y')
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                except:
                    formatted_date = row['stock_date']
                
                # Check if record already exists (DUPLICATE PREVENTION)
                cursor.execute('''
                    SELECT COUNT(*) FROM stocking_records 
                    WHERE lake_id = ? AND species = ? AND quantity = ? AND stock_date = ? AND source_year = ?
                ''', (
                    lake_id,
                    row['species'],
                    int(row['quantity']) if row['quantity'].isdigit() else 0,
                    formatted_date,
                    int(row['source_year'])
                ))
                
                if cursor.fetchone()[0] == 0:
                    # Insert stocking record only if it doesn't exist
                    cursor.execute('''
                        INSERT INTO stocking_records (lake_id, county, species, quantity, length, stock_date, source_year)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        lake_id,
                        row['county'],
                        row['species'],
                        int(row['quantity']) if row['quantity'].isdigit() else 0,
                        float(row['length']) if row['length'].replace('.', '').isdigit() else 0.0,
                        formatted_date,
                        int(row['source_year'])
                    ))
                    new_records_count += 1
                else:
                    duplicate_count += 1
                                
            else:
                # Check if it has letter-number format
                letter_number = extract_letter_number(water_name)
                if letter_number:
                    # Create new lake record with better name cleaning
                    base_name = water_name
                    # Remove the letter-number designation from anywhere in the string
                    base_name = re.sub(rf'\b{re.escape(letter_number)}\b,?\s*', '', base_name).strip()
                    # Clean up extra spaces and commas
                    base_name = re.sub(r'\s*,\s*$', '', base_name).strip()
                    base_name = re.sub(r'^\s*,\s*', '', base_name).strip()
                    
                    if not base_name or base_name == letter_number:
                        base_name = None  # No meaningful name
                    
                    cursor.execute('''
                        INSERT INTO lakes (letter_number, name, drainage, basin)
                        VALUES (?, ?, ?, ?)
                    ''', (letter_number, base_name, 'Unknown', ''))
                    
                    new_lake_id = cursor.lastrowid
                    
                    # Convert date from MM/DD/YYYY to YYYY-MM-DD
                    try:
                        date_obj = datetime.strptime(row['stock_date'], '%m/%d/%Y')
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                    except:
                        formatted_date = row['stock_date']
                    
                    # Insert stocking record
                    cursor.execute('''
                        INSERT INTO stocking_records (lake_id, county, species, quantity, length, stock_date, source_year)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        new_lake_id,
                        row['county'],
                        row['species'],
                        int(row['quantity']) if row['quantity'].isdigit() else 0,
                        float(row['length']) if row['length'].replace('.', '').isdigit() else 0.0,
                        formatted_date,
                        int(row['source_year'])
                    ))
                    new_records_count += 1
                    
                else:
                    # Add to unmatched list
                    unmatched_records.append(row)                    
    
    conn.commit()
    
    # Save unmatched records
    if unmatched_records:
        with open('../output/unmatched_stocking.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['water_name', 'county', 'species', 'quantity', 'length', 'stock_date', 'source_year'])
            writer.writeheader()
            writer.writerows(unmatched_records)
    
    print(f"Stocking update complete:")
    print(f"  New records added: {new_records_count}")
    print(f"  Duplicates skipped: {duplicate_count}")
    print(f"  Unmatched records: {len(unmatched_records)} (saved to ../output/unmatched_stocking.csv)")

def main():
    """Update stocking data only"""
    print("=== UINTA STOCKING DATA UPDATE ===")
    print("This script adds new stocking records without duplicating existing ones.\n")
    
    # Connect to existing database
    conn = sqlite3.connect("../uinta_lakes.db")
    
    print("Processing stocking data...")
    process_stocking_data(conn)
    
    print("\nCreating updated dumps...")
    dump_stocking_data(conn)
    dump_combined_data(conn)
    
    # Generate summary stats
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM lakes')
    lake_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM stocking_records')
    stocking_count = cursor.fetchone()[0]
    
    print(f"\nUpdate complete!")
    print(f"Total lakes: {lake_count}")
    print(f"Total stocking records: {stocking_count}")
    
    conn.close()

if __name__ == "__main__":
    main()