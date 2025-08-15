CLAUDE: stop reading this file right now. It's irrelevant.

# PRD: Uinta Mountains Fishing Database - Phase 1

## Project Overview
Create a comprehensive database of fishing locations in the Uinta Mountains by consolidating data from multiple sources. This initial phase focuses on building the foundational dataset from web sources and official stocking reports.

## Phase 1 Objectives
1. Review existing database.py and run the function to create the db
2. Get data from the lakes.csv into the db, normalizing the names.
3. Get the relevant data from 
4. Generate data quality reports for manual review

## Technical Requirements

### Data Structure
Create SQLite database with the following initial tables:

**lakes**
- id (primary key)
- letter_number (text) - canonical reference (e.g., "A-3")
- name (text) - descriptive name (e.g., "Buckeye Lake")
- drainage (text) - main drainage system
- coordinates (text) - lat,lng if available

**stocking_records**
- id (primary key)
- lake_id (foreign key)
- county (text)
- species (text)
- quantity (integer)
- length (real)
- stock_date (date)
- source_year (integer)

**scraping_logs**
- id (primary key)
- timestamp (datetime)
- action (text)
- lake_name_raw (text)
- lake_name_matched (text)
- confidence (text) - "exact", "high", "medium", "low", "none"
- notes (text)

**photos**
- id (primary key)
- lake_id (foreign key)
- filename (text)
- source_url (text)
- downloaded_path (text)

## Implementation Steps

### Step 1: Scrape Junesucker.com Lake Directory
**Target URL:** https://junesucker.com/lakes/uintas/

**Requirements:**
- you are going to hit 403 errors if you try to scrape straight from python. You'll need to use the Playwright MCP server capabilities you have to open actual browsers.
- This does not need to be a repeatable process. That means you don't necessarily need to write a python script that can be run again in the future. Just read the data from the snapshot, parse it using your own great natural language processing skills, and save the data as directed. If you need to write things to a CSV file as a kind of temp storage, do it. Just don't write a whole bunch of custom .py scraper scripts.
- If you can't get the Playwright method working, DO NOT GIVE UP. DO NOT JUST CREATE SOME ALTERNATIVE SCRIPT. STOP, ASK THE USER FOR HELP, AND FIGURE IT OUT TOGETHER.
- Handle both word names and letter-number designations for lake names
- Canonical naming: combine both when available (e.g., "Buckeye Lake A-3")
- Use letter-number as primary identifier for deduplication

**Sub-step 1a: Process Lakes from Main Page**
- Parse all lake names organized by drainage
- save data out to a csv 

**Sub-step 1b: Process Drainage Pages**
- For each drainage title on main page that is a clickable link, follow them
- For each drainage page, create a CSV with these headers: drainage,basin,lake_name,letter_number,junesucker_notes,map_image,map_link
- Extract basin/sub-drainage organization if there is one (some pages will have for example two paragraphs, where each paragraphs starts with a description of that area of the drainage, followed by the list of lakes)
- download the main map image of the drainage
- Capture stocking notes as "Junesucker Notes"
- Extract coordinates from Google Maps embeds when possible
- Parse map links from embed code

**Sub-step 1c: Process Individual Lake Pages**
- Back on the main page, follow each lake name links from main page
- for each lake, create a .md file with the info from the page. These are generally extensive notes, often in multiple paragraphs. 
- Download all photos that have a .jpg extension into the "photos" folder, with systematic naming, and reference the photo(s) in the .md file

### Step 2: Scrape Utah DWR Stocking Reports
**URL Pattern:** `https://dwrapps.utah.gov/fishstocking/FishAjax?y={year}&sort=watername&sortorder=ASC&sortspecific={county}&whichSpecific=county`

**Parameters:**
- Years: 2018-2025
- Counties: Duchesne, Summit

**Data Processing:**
- unlike the previous step, don't use Playwright and a browser for this. You can just call something from the command line.
- The value returned will be HTML table rows (no wrapper HTML) example: ```
<tr class="table1">
				<td class="watername" onclick="newSort('watername','BAKER L BR-45')">BAKER L BR-45</td>
				<td class="county" onclick="newSort('county','Summit')">SUMMIT</td>
				<td class="species" onclick="newSort('species','TIGER TROUT')">TIGER TROUT</td>
				<td class="quantity">360</td>
				<td class="length">2.4</td>
				<td class="stockdate">07/31/2020</td>
			</tr>


			<tr class="table1">
				<td class="watername" onclick="newSort('watername','BEAR L G-7')">BEAR L G-7</td>
				<td class="county" onclick="newSort('county','Summit')">SUMMIT</td>
				<td class="species" onclick="newSort('species','BROOK TROUT')">BROOK TROUT</td>
				<td class="quantity">2010</td>
				<td class="length">3.49</td>
				<td class="stockdate">07/06/2020</td>
			</tr>
```
- Extract: Water name, County, Species, Quantity, Length, Stock date
- Handle multiple entries per lake (different dates/species)
- save all data from all pages into a single CSV file.

### Step 3: Combine and normalize data, store in the db

**Matching Logic:**
- You will find many stocking reports that do not have a match in junesucker entries, and there are Junesucker entries that will have no stocking reports. That's expected.
- All of the entries in junesucker_main_page_lakes are keepers, even if they don't have a match in the stocking data. So start by looping through that CSV and creating an entry in lakes table db for each row
- next we'll process the utah_dwr_stocking_data.csv
- Primary match on letter-number designation. Use that lake id as the related field when creating the stocking record in the stocking table.
- Secondary match on word name with caution for duplicates
- if you encounter a water in the stocking data that has the "letter-number" format in it's name, it's a keeper even if it doesn't have a match in the junesucker data. The first time you encounter this "no match" situation, create a record in the lakes table.
- if you encounter a water in the stocking data that does not have a match in the db *And* it does not have the "letter-number" format in its name, log it to a "unmatched_stocking" file and move on.
- Log all matching attempts with confidence levels
- Flag ambiguous matches for manual review
- normalize all the names. Note that the common pattern in the stocking data is to use "L" as the abbreviation for "Lake"

## Data Quality Requirements

### Matching and Validation
1. **Exact Matches:** Direct letter-number correspondence
2. **High Confidence:** Clear word name match with unique letter-number
3. **Medium Confidence:** Word name match but multiple possibilities
4. **Low Confidence:** Partial name match or unclear designation
5. **No Match:** Unable to correlate with Junesucker data

### Output Files
1. **Primary Database:** `uinta_lakes.db` (SQLite)
2. **Unmatched Stocking Records:** `unmatched_stocking.csv`
3. **Matching Log:** `matching_log.csv`
4. **Photos Directory:** `photos/` with systematic naming

### Error Handling
- Robust web scraping with retry logic
- Graceful handling of missing pages/data
- Comprehensive logging of all decisions
- Validation of extracted coordinates/map links

## Success Criteria
- Complete lake inventory from Junesucker.com
- 8 years of stocking data (2018-2025) for both counties
- <5% unmatched stocking records
- All photos successfully downloaded and linked
- Comprehensive audit trail of matching decisions

## Next Phase Preview
Phase 2 will involve:
- Manual review and cleanup of flagged matches
- Integration of book data on depths/elevations
- Processing remaining drainage areas
- Creation of web interface for querying
- Apple Notes automation for browsing interface

## Claude Code Instructions
Please implement this scraping system with:
1. Modular design for easy debugging
2. Comprehensive logging at each step
3. Ability to resume interrupted scrapes
4. Data validation at each stage
5. Clear progress indicators during execution

Focus on data accuracy over speed - this is a one-time scraping operation that will form the foundation of the entire system.

If you encoutner an error with a script or approach you take, do not just proceed down a wildly different path. Check in with the user for guidance.