#!/usr/bin/env python3

import csv
import sqlite3
import os
import re
import time
from playwright.sync_api import sync_playwright

def get_database_lakes():
    """Get all lakes from database for matching."""
    conn = sqlite3.connect('uinta_lakes.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, letter_number, name, drainage FROM lakes")
    lakes = cursor.fetchall()
    conn.close()
    return lakes

def find_matching_lake(page_title, page_content, db_lakes):
    """Find matching lake in database using letter-number or name matching."""
    
    # Extract letter-number from page content if present
    letter_number_match = re.search(r'([A-Z]{1,3}-\d{1,3})', page_content)
    if letter_number_match:
        letter_number = letter_number_match.group(1)
        for lake in db_lakes:
            if lake[1] == letter_number:  # letter_number column
                return lake
    
    # Try name matching
    page_name = page_title.replace(' Lake', '').replace(' Reservoir', '').strip().lower()
    
    for lake in db_lakes:
        if lake[2]:  # if name is not None
            lake_name = lake[2].lower()
            # Direct name match
            if lake_name == page_name:
                return lake
            # Partial name match
            if page_name in lake_name or lake_name in page_name:
                return lake
    
    return None

def extract_page_content(page):
    """Extract content from a Junesucker lake page."""
    try:
        # Wait for content to load
        page.wait_for_selector('h1', timeout=10000)
        
        # Get title
        title = page.evaluate("() => document.querySelector('h1')?.textContent?.trim() || ''")
        
        # Extract paragraph content
        content = page.evaluate("""() => {
            const contentSections = [];
            const allParagraphs = Array.from(document.querySelectorAll('p'));
            
            allParagraphs.forEach(p => {
                const text = p.textContent.trim();
                if (text && !text.includes('© 2025') && !text.includes('Search for:') && !text.includes('Utah fishing and outdoor index')) {
                    contentSections.push(text);
                }
            });
            
            return contentSections;
        }""")
        
        return title, content
    except Exception as e:
        print(f"Error extracting content: {e}")
        return None, []

def content_to_markdown(title, content_sections):
    """Convert extracted content to markdown format."""
    if not title or not content_sections:
        return ""
    
    markdown = f"# {title}\n\n"
    
    for section_text in content_sections:
        # Check if section starts with a bold header (contains ':')
        if ':' in section_text and len(section_text.split(':', 1)) == 2:
            header, content = section_text.split(':', 1)
            markdown += f"## {header.strip()}:\n{content.strip()}\n\n"
        else:
            markdown += f"{section_text}\n\n"
    
    return markdown.strip()

def save_markdown_file(filename, content):
    """Save markdown content to file."""
    os.makedirs('lake_pages', exist_ok=True)
    filepath = os.path.join('lake_pages', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath

def update_database(lake_id, markdown_content):
    """Update database with junesucker notes."""
    conn = sqlite3.connect('uinta_lakes.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE lakes SET junesucker_notes = ? WHERE id = ?", (markdown_content, lake_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected

def process_lake_links():
    """Process all lake links from CSV file."""
    
    # Read lake links
    with open('uinta_lake_links.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        lake_links = list(reader)
    
    # Get database lakes for matching
    db_lakes = get_database_lakes()
    
    # Statistics
    processed = 0
    matched = 0
    errors = 0
    
    print(f"Processing {len(lake_links)} lake links...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        for i, link in enumerate(lake_links):
            url = link['url']
            text = link['text']
            
            print(f"\n[{i+1}/{len(lake_links)}] Processing: {text}")
            print(f"URL: {url}")
            
            try:
                # Skip main uintas page and drainage pages
                if url.endswith('/uintas/') or 'drainage' in url.lower():
                    print("Skipping drainage/main page")
                    continue
                
                # Navigate to page
                page.goto(url, timeout=30000)
                time.sleep(2)  # Brief wait for content
                
                # Extract content
                title, content_sections = extract_page_content(page)
                
                if not title or not content_sections:
                    print("No content found")
                    errors += 1
                    continue
                
                # Convert to markdown
                markdown_content = content_to_markdown(title, content_sections)
                
                if not markdown_content:
                    print("No markdown content generated")
                    errors += 1
                    continue
                
                # Save markdown file
                filename = url.split('/')[-2] + '.md' if url.split('/')[-2] else f'lake_{i}.md'
                filepath = save_markdown_file(filename, markdown_content)
                print(f"Saved: {filepath}")
                
                # Find matching lake in database
                matching_lake = find_matching_lake(title, markdown_content, db_lakes)
                
                if matching_lake:
                    lake_id, letter_number, name, drainage = matching_lake
                    print(f"Matched: {letter_number} ({name}) in {drainage}")
                    
                    # Update database
                    rows_updated = update_database(lake_id, markdown_content)
                    if rows_updated:
                        print(f"Updated database for {letter_number}")
                        matched += 1
                    else:
                        print(f"Failed to update database for {letter_number}")
                        errors += 1
                else:
                    print("No matching lake found in database")
                
                processed += 1
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                errors += 1
            
            # Brief pause between requests
            time.sleep(1)
        
        browser.close()
    
    print(f"\n=== Summary ===")
    print(f"Total links: {len(lake_links)}")
    print(f"Processed: {processed}")
    print(f"Matched & Updated: {matched}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    process_lake_links()