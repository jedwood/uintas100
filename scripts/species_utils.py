#!/usr/bin/env python3

import re

def normalize_species_name(species_text):
    """
    Normalize species names to standardized display format.
    
    Rules:
    - Brook trout → Brookies
    - Arctic grayling → Grayling  
    - Other trouts (Rainbow, Tiger, Golden, Cutthroat) → pluralized with 's'
    - Other species → as-is with proper capitalization
    """
    if not species_text:
        return None
    
    # Clean and normalize the text
    text = species_text.strip().lower()
    
    # Handle special cases first
    if re.search(r'brook', text):
        return 'Brookies'
    
    if re.search(r'(arctic\s+)?grayling', text):
        return 'Grayling'
    
    # Handle other trouts - pluralize
    if re.search(r'rainbow', text):
        return 'Rainbows'
    
    if re.search(r'tiger', text):
        return 'Tigers'
    
    if re.search(r'golden', text):
        return 'Goldens'
    
    if re.search(r'cut.*throat|cutthroat|cuthroat', text):
        return 'Cutthroats'
    
    # Handle other species
    if re.search(r'splake', text):
        return 'Splake'
    
    if re.search(r'tiger.*muskie|muskie.*tiger', text):
        return 'Tiger muskie'
    
    if re.search(r'channel.*catfish|catfish.*channel', text):
        return 'Channel catfish'
    
    # Fallback - title case the original
    return species_text.title()

def normalize_species_list(species_text):
    """
    Parse a species string and return a sorted list of normalized species names.
    
    Examples:
    - "Brook trout, cutthroat trout" → ["Brookies", "Cutthroats"]
    - "Arctic grayling" → ["Grayling"]
    """
    if not species_text:
        return []
    
    # Remove asterisks and parenthetical info
    cleaned = re.sub(r'\*', '', species_text)
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)
    
    # Split on common delimiters
    parts = re.split(r'[,;&]|\sand\s', cleaned)
    
    # Normalize each part
    normalized_species = set()
    for part in parts:
        part = part.strip()
        if part:
            normalized = normalize_species_name(part)
            if normalized:
                normalized_species.add(normalized)
    
    return sorted(list(normalized_species))

def format_species_display(species_list, asterisk_species=None):
    """
    Format a list of species for display, adding asterisks where needed.
    
    Args:
        species_list: List of normalized species names
        asterisk_species: Set of species that should have asterisks
    
    Returns:
        Formatted string like "Brookies, Cutthroats*"
    """
    if not species_list:
        return None
    
    asterisk_species = asterisk_species or set()
    
    display_list = []
    for species in species_list:
        if species in asterisk_species:
            display_list.append(f"{species}*")
        else:
            display_list.append(species)
    
    return ", ".join(display_list)

def standardize_stocking_species(raw_species):
    """Convert raw stocking species from DWR data to normalized names"""
    mapping = {
        'BROOK TROUT': 'Brookies',
        'CUTTHROAT': 'Cutthroats', 
        'TIGER TROUT': 'Tigers',
        'RAINBOW': 'Rainbows',
        'GRAYLING ARCTIC': 'Grayling',
        'SPLAKE': 'Splake',
        'MUSKIE TIGER': 'Tiger muskie',
        'CHANNEL CATFISH': 'Channel catfish'
    }
    return mapping.get(raw_species, normalize_species_name(raw_species))

# Test the functions
if __name__ == "__main__":
    test_cases = [
        "Brook trout",
        "Brook trout, cutthroat trout",
        "Rainbow trout (stocked)",
        "Arctic grayling",
        "Tiger trout",
        "Brook and cutthroat trout (naturally reproducing)",
        "BROOK TROUT",
        "GRAYLING ARCTIC"
    ]
    
    print("=== Testing Species Normalization ===\n")
    
    for case in test_cases:
        normalized_list = normalize_species_list(case)
        display = format_species_display(normalized_list)
        print(f"'{case}' → {normalized_list} → '{display}'")
    
    print("\n=== Testing Stocking Species Mapping ===\n")
    
    stocking_cases = ['BROOK TROUT', 'CUTTHROAT', 'GRAYLING ARCTIC', 'TIGER TROUT']
    for case in stocking_cases:
        normalized = standardize_stocking_species(case)
        print(f"'{case}' → '{normalized}'")