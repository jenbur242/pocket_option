#!/usr/bin/env python3
"""
Extract asset names from HTML content in date.txt file.
Looks for <span class="alist__label"> elements and extracts the text content.
"""

import re
from pathlib import Path

def extract_asset_names(html_content):
    """Extract asset names from HTML content using regex."""
    # Pattern to match <span class="alist__label">ASSET_NAME</span>
    pattern = r'<span class="alist__label">([^<]+)</span>'
    
    # Find all matches
    matches = re.findall(pattern, html_content)
    
    return matches

def main():
    # Read the HTML content from date.txt
    try:
        with open('date.txt', 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print("Error: date.txt file not found!")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Extract asset names
    asset_names = extract_asset_names(html_content)
    
    if not asset_names:
        print("No asset names found in the HTML content.")
        return
    
    # Display results
    print(f"Found {len(asset_names)} assets:")
    print("-" * 40)
    
    for i, asset in enumerate(asset_names, 1):
        print(f"{i:2d}. {asset}")
    
    # Save to a text file
    output_file = 'extracted_assets.txt'
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write("Extracted Asset Names\n")
            file.write("=" * 20 + "\n\n")
            for asset in asset_names:
                file.write(f"{asset}\n")
        
        print(f"\nAsset names saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving to file: {e}")
    
    # Also save as CSV format
    csv_file = 'extracted_assets.csv'
    try:
        with open(csv_file, 'w', encoding='utf-8') as file:
            file.write("Asset Name\n")
            for asset in asset_names:
                file.write(f'"{asset}"\n')
        
        print(f"Asset names also saved as CSV: {csv_file}")
        
    except Exception as e:
        print(f"Error saving CSV file: {e}")

if __name__ == "__main__":
    main()