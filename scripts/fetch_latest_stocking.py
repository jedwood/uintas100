#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import sqlite3
from database_utils import create_database, extract_letter_number, stocking_record_exists, find_matching_lake
from datetime import datetime

def insert_stocking_record(cursor, lake_id, species, quantity, length, stock_date, source_year, county):
    """Insert a new stocking record."""
    cursor.execute("""
        INSERT INTO stocking_records (lake_id, species, quantity, length, stock_date, source_year, county)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lake_id, species, quantity, length, stock_date, source_year, county))

def fetch_stocking_data(county):
    """Fetch stocking data for a given county."""
    url = f"https://dwrapps.utah.gov/fishstocking/FishAjax?y=2025&sort=watername&sortorder=ASC&sortspecific={county}&whichSpecific=county"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {county}: {e}")
        return None

def parse_and_insert_data(html_content, conn, cursor):
    """Parse HTML and insert new stocking records."""
    if not html_content:
        return

    soup = BeautifulSoup(html_content, 'lxml')
    rows = soup.find_all('tr')
    
    new_records = 0
    unmatched_lakes = set()
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 6:
            water_name = cols[0].text.strip()
            county = cols[1].text.strip()
            species = cols[2].text.strip()
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

    conn.commit()
    print(f"Inserted {new_records} new stocking records for {county} county.")
    if unmatched_lakes:
        print("\nUnmatched lakes:")
        for lake in sorted(list(unmatched_lakes)):
            print(f"- {lake}")

def main():
    """Main function to fetch and update stocking data."""
    conn = create_database()
    cursor = conn.cursor()

    for county in ["Summit", "Duchesne"]:
        print(f"Fetching data for {county} county...")
        html_content = fetch_stocking_data(county)
        parse_and_insert_data(html_content, conn, cursor)

    conn.close()

if __name__ == "__main__":
    main()