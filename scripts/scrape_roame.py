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

        # Find all table cells with data
        # The structure has airlines/programs in rows and transfer partners in columns

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

        # Map known transfer partners to clean names
        partner_map = {
            'amexmembershipawards': 'American Express Membership Rewards',
            'bilt': 'Bilt',
            'capitalone': 'Capital One Rewards',
            'chaseultimaterewards': 'Chase Ultimate Rewards',
            'citi': 'Citi ThankYou Points',
            'wellsfargo': 'Wells Fargo Rewards',
            'marriottbonvoy': 'Marriott Bonvoy',
            'worldofhyatt': 'World of Hyatt',
            'ihgrewards': 'IHG Rewards',
            'accor': 'Accor Live Limitless',
            'choiceprivileges': 'Choice Privileges',
            'brex': 'Brex Rewards',
            'ramp': 'Ramp Rewards'
        }

        # Extract data rows
        tbody = table.find('tbody')
        if tbody:
            for tr in tbody.find_all('tr'):
                cells = tr.find_all('td')
                if len(cells) > 0:
                    # First cell is airline/program name
                    airline_name = cells[0].get_text(strip=True)

                    if not airline_name or airline_name == 'Airline/Program':
                        continue

                    # Extract ratios from remaining cells
                    # Cells after Award Release (skip first 5 columns typically)
                    for col_idx, cell in enumerate(cells[5:]):  # Skip first 5 metadata columns
                        cell_text = cell.get_text(strip=True)

                        # Look for ratio patterns
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

    except Exception as e:
        print(f"⚠️  Error parsing HTML table: {e}")
        print("Attempting to parse from text content...")
        return parse_from_text(html_content)

def parse_from_text(text_content):
    """Parse data from plain text extraction of page."""
    transfers = []

    # Split by airline/program blocks
    # Pattern: look for program names followed by code and then ratio data

    lines = text_content.split('\n')

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

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for program identifiers (usually have airline codes or specific keywords)
        if any(keyword in line for keyword in ['Airlines', 'Airways', 'Club', 'Rewards', 'Plus', 'Miles']) and len(line) > 2:
            program_name = line

            # Collect ratios from next lines
            ratios = []
            j = i + 1
            ratio_found = False

            while j < min(i + 15, len(lines)):
                next_line = lines[j].strip()

                # Find all ratio patterns
                for match in re.finditer(r'(\d+\.?\d*):(\d+\.?\d*)', next_line):
                    ratio_str = f"{match.group(1)}:{match.group(2)}"
                    ratio = extract_ratio(ratio_str)
                    if ratio is not None:
                        ratios.append(ratio)
                        ratio_found = True

                # Stop if we hit another program or empty section
                if ratio_found and (
                    any(kw in next_line for kw in ['Airlines', 'Airways', 'Club']) or
                    (next_line == '' and j > i + 5)
                ):
                    break

                j += 1

            # Create transfer entries
            for idx, ratio in enumerate(ratios):
                if idx < len(transfer_partners):
                    transfer = {
                        'from_program': transfer_partners[idx],
                        'to_program': program_name,
                        'ratio': ratio,
                        'category': get_program_category(program_name),
                        'last_updated': datetime.utcnow().isoformat() + 'Z'
                    }
                    transfers.append(transfer)

        i += 1

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
