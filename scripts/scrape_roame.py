#!/usr/bin/env python3
"""Scrape Roame transfer partners data and update JSON."""

import json
import re
from datetime import datetime
import sys

def extract_ratio(ratio_str):
    """Convert ratio string like '1:1', '5:2', '3:1' to decimal."""
    if not ratio_str or ratio_str.strip() == '':
        return None

    ratio_str = ratio_str.strip()

    # Handle ratios like "1:1", "5:2", etc.
    if ':' in ratio_str:
        parts = ratio_str.split(':')
        try:
            numerator = float(parts[0])
            denominator = float(parts[1])
            return round(numerator / denominator, 2) if denominator != 0 else None
        except (ValueError, IndexError):
            return None

    # Handle direct numbers
    try:
        return float(ratio_str)
    except ValueError:
        return None

def get_program_category(program_name):
    """Determine if a program is airline or hotel."""
    airlines_keywords = ['airline', 'airways', 'air', 'skypass', 'eurobonus', 'lotusmiles',
                         'aadvantage', 'atmos', 'skymiles', 'mileageplus', 'trueblu',
                         'rapid rewards', 'velocity', 'infinity', 'maharaja', 'mileage club',
                         'executive club', 'asia miles', 'guest', 'privilege', 'krisflyer',
                         'flying blue', 'flying club', 'aeroplan', 'lifemiles', 'miles & more',
                         'miles & go', 'royal orchid', 'miles & smiles', 'aerclub', 'skywards',
                         'frequent flyer', 'rewards']

    hotels_keywords = ['marriott', 'hilton', 'hyatt', 'ihg', 'wyndham', 'choice', 'accor',
                       'radisson', 'best western', 'preferred', 'bonvoy', 'honors',
                       'one rewards', 'privileges', 'live limitless', 'leaders club']

    program_lower = program_name.lower()

    for hotel in hotels_keywords:
        if hotel in program_lower:
            return 'hotel'

    for airline in airlines_keywords:
        if airline in program_lower:
            return 'airline'

    return 'airline'  # Default

def scrape_roame():
    """Scrape Roame data using Playwright for JavaScript rendering."""
    try:
        # Try Playwright first for proper JavaScript rendering
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto('https://roame.travel/transfer-partners-cheat-sheet', timeout=30000)
                page.wait_for_load_state('networkidle', timeout=15000)

                content = page.content()
                browser.close()

                return content
        except ImportError:
            # Fall back to requests
            print("⚠️  Playwright not available, using requests fallback...")
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(
                'https://roame.travel/transfer-partners-cheat-sheet',
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            return response.text

    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return None

def parse_roame_table(html_content):
    """Parse the Roame transfer table from HTML or text content."""
    from bs4 import BeautifulSoup

    transfers = []

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Get all table rows
        tables = soup.find_all('table')

        if not tables:
            print("⚠️  No tables found, parsing text content instead...")
            return parse_from_text(html_content)

        # Use the first table (should be the main transfer matrix)
        table = tables[0] if len(tables) > 0 else None

        if not table:
            return []

        # Extract header row to get column names (transfer partner programs)
        headers = []
        header_row = table.find('thead')
        if header_row:
            for th in header_row.find_all('th'):
                text = th.get_text(strip=True)
                if text and text not in ['Airline/Program', 'Alliance', 'IATA', 'Also Bookable', 'Award Release']:
                    headers.append(text)

        print(f"DEBUG: Extracted {len(headers)} headers from table")

        # Check if tbody exists (HTML-rendered tables) or parse from text (JS-rendered)
        tbody = table.find('tbody')
        if tbody:
            print("DEBUG: Found tbody in HTML, parsing table rows...")
            for tr in tbody.find_all('tr'):
                cells = tr.find_all('td')
                if len(cells) > 0:
                    # First cell is airline/program name
                    airline_name = cells[0].get_text(strip=True)

                    if not airline_name or airline_name == 'Airline/Program':
                        continue

                    # Extract ratios from remaining cells
                    for col_idx, cell in enumerate(cells[5:]):  # Skip first 5 metadata columns
                        cell_text = cell.get_text(strip=True)
                        ratio_match = re.search(r'(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)', cell_text)

                        if ratio_match:
                            ratio_str = f"{ratio_match.group(1)}:{ratio_match.group(2)}"
                            ratio = extract_ratio(ratio_str)

                            if ratio is not None and col_idx < len(headers):
                                transfer = {
                                    'from_program': headers[col_idx] if col_idx < len(headers) else f'Partner {col_idx}',
                                    'to_program': airline_name,
                                    'ratio': ratio,
                                    'category': get_program_category(airline_name),
                                    'last_updated': datetime.utcnow().isoformat() + 'Z'
                                }
                                transfers.append(transfer)
            return transfers
        else:
            print("DEBUG: No tbody found in HTML (JavaScript-rendered), parsing text content instead...")
            return parse_from_text(html_content)

    except Exception as e:
        print(f"⚠️  Error parsing HTML table: {e}")
        print("Attempting to parse from text content...")
        return parse_from_text(html_content)

def parse_from_text(text_content):
    """Parse data from plain text extraction of page."""
    transfers = []

    # Known transfer partners in typical column order on the Roame page
    transfer_partners = [
        'American Express Membership Rewards',
        'Bilt',
        'Capital One Rewards',
        'Chase Ultimate Rewards',
        'Citi ThankYou Points',
        'Wells Fargo Rewards',
        'Marriott Bonvoy',
        'World of Hyatt',
        'IHG Rewards',
        'Accor Live Limitless',
        'Choice Privileges',
        'Brex Rewards',
        'Ramp Rewards',
        'Avios'
    ]

    # Split text into lines
    lines = text_content.split('\n')

    # Look for program sections - they have a name followed by code, then ratios
    current_program = None
    program_buffer = []

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Detect program names (contain specific keywords and IATA codes)
        if any(kw in line for kw in ['Airlines', 'Airways', 'Club', 'Rewards', 'Plus', 'Miles', 'Mileage']) and len(line_stripped) > 3:
            # Check if previous program has data
            if current_program and program_buffer:
                # Extract ratios from the buffer
                ratios = []
                for buffer_line in program_buffer:
                    for match in re.finditer(r'(\d+\.?\d*):(\d+\.?\d*)', buffer_line):
                        ratio_str = f"{match.group(1)}:{match.group(2)}"
                        ratio = extract_ratio(ratio_str)
                        if ratio is not None and ratio not in ratios:  # Avoid duplicates
                            ratios.append(ratio)

                # Create transfers for this program
                for idx, ratio in enumerate(ratios):
                    if idx < len(transfer_partners):
                        transfer = {
                            'from_program': transfer_partners[idx],
                            'to_program': current_program,
                            'ratio': ratio,
                            'category': get_program_category(current_program),
                            'last_updated': datetime.utcnow().isoformat() + 'Z'
                        }
                        transfers.append(transfer)

            # Start new program
            current_program = line_stripped
            program_buffer = []

        # Collect lines with potential ratio data
        elif current_program and re.search(r'\d+:\d+', line):
            program_buffer.append(line_stripped)

    # Don't forget the last program
    if current_program and program_buffer:
        ratios = []
        for buffer_line in program_buffer:
            for match in re.finditer(r'(\d+\.?\d*):(\d+\.?\d*)', buffer_line):
                ratio_str = f"{match.group(1)}:{match.group(2)}"
                ratio = extract_ratio(ratio_str)
                if ratio is not None and ratio not in ratios:
                    ratios.append(ratio)

        for idx, ratio in enumerate(ratios):
            if idx < len(transfer_partners):
                transfer = {
                    'from_program': transfer_partners[idx],
                    'to_program': current_program,
                    'ratio': ratio,
                    'category': get_program_category(current_program),
                    'last_updated': datetime.utcnow().isoformat() + 'Z'
                }
                transfers.append(transfer)

    print(f"DEBUG: Parsed {len(transfers)} transfers from text")
    return transfers

def update_transfer_partners_json(transfers):
    """Update transfer-partners.json with new data."""
    try:
        with open('transfer-partners.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        # Create new file if it doesn't exist
        data = {
            'schema_version': '1.0.0',
            'last_generated': datetime.utcnow().isoformat() + 'Z',
            'last_data_source': 'https://roame.travel/transfer-partners-cheat-sheet',
            'data_as_of': datetime.utcnow().isoformat() + 'Z',
            'transfers': []
        }

    # Update metadata
    data['last_generated'] = datetime.utcnow().isoformat() + 'Z'

    # Only update if we got new data
    if transfers:
        data['transfers'] = transfers
        data['data_as_of'] = (datetime.utcnow()).isoformat() + 'Z'
        print(f"✅ Parsed {len(transfers)} transfer partnerships")
    else:
        print("⚠️  No transfer data parsed - updating timestamp only")

    with open('transfer-partners.json', 'w') as f:
        json.dump(data, f, indent=2)

    return len(transfers) > 0

def main():
    print("🔄 Fetching Roame transfer partners data...")

    content = scrape_roame()
    if not content:
        print("❌ Failed to fetch page content")
        return False

    print("✅ Page fetched successfully")

    # Parse transfers from the content
    transfers = parse_roame_table(content)

    if transfers:
        update_transfer_partners_json(transfers)
        print("✅ Updated transfer-partners.json")
        return True
    else:
        print("⚠️  No transfer data found")
        # Still update timestamp
        try:
            with open('transfer-partners.json', 'r') as f:
                data = json.load(f)
            data['last_generated'] = datetime.utcnow().isoformat() + 'Z'
            with open('transfer-partners.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("✅ Updated timestamp")
        except Exception as e:
            print(f"Error updating timestamp: {e}")

        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
