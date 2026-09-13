#!/usr/bin/env python3
"""Scrape ALL Roame transfer partners data and update JSON."""

import json
import re
from datetime import datetime
import sys

def extract_ratio(ratio_str):
    """Convert ratio string like '1:1', '5:2', '3:1' to decimal."""
    if not ratio_str or ratio_str.strip() == '':
        return None

    ratio_str = ratio_str.strip()

    if ':' in ratio_str:
        parts = ratio_str.split(':')
        try:
            numerator = float(parts[0])
            denominator = float(parts[1])
            return round(numerator / denominator, 2) if denominator != 0 else None
        except (ValueError, IndexError):
            return None

    try:
        return float(ratio_str)
    except ValueError:
        return None

def get_program_category(program_name):
    """Determine if a program is airline or hotel."""
    hotels_keywords = ['marriott', 'hilton', 'hyatt', 'ihg', 'wyndham', 'choice',
                       'accor', 'radisson', 'best western', 'preferred', 'bonvoy',
                       'honors', 'one rewards', 'privileges', 'live limitless', 'leaders', 'hotel']

    program_lower = program_name.lower()

    for hotel in hotels_keywords:
        if hotel in program_lower:
            return 'hotel'

    return 'airline'

def scrape_roame():
    """Fetch Roame page - prioritize Playwright for JS rendering."""
    print("Fetching Roame transfer partners data...")

    # Try Playwright first (handles JavaScript rendering)
    try:
        from playwright.sync_api import sync_playwright

        print("Using Playwright for JavaScript rendering...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://roame.travel/transfer-partners-cheat-sheet', timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            content = page.content()
            browser.close()
            if len(content) > 10000:
                print("✅ Page fetched successfully via Playwright")
                return content
    except Exception as e:
        print(f"⚠️  Playwright failed: {e}")

    # Fallback to requests
    print("Falling back to requests...")
    import requests
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    try:
        response = requests.get(
            'https://roame.travel/transfer-partners-cheat-sheet',
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        if len(response.text) > 5000:
            print("✅ Page fetched via requests")
            return response.text
    except Exception as e:
        print(f"❌ Requests failed: {e}")

    print("❌ Failed to fetch page with all methods")
    return None

def parse_roame_table(html_content):
    """Parse the complete Roame transfer table from HTML."""
    from bs4 import BeautifulSoup

    print("Parsing transfer matrix from HTML...")
    soup = BeautifulSoup(html_content, 'html.parser')

    transfers = []

    # Find all tables
    tables = soup.find_all('table')
    if not tables:
        print("❌ No tables found, trying text parsing")
        return parse_from_text(html_content)

    print(f"Found {len(tables)} table(s)")

    table = tables[0]

    # Try to extract headers - they could be in various places
    headers = []

    # Method 1: Look in thead
    thead = table.find('thead')
    if thead:
        for th in thead.find_all('th'):
            text = th.get_text(strip=True)
            if text and text not in ['Airline/Program', 'Alliance', 'IATA', 'Also Bookable', 'Award Release', '']:
                headers.append(text)

    # Method 2: If no headers found, look at first row cells
    if not headers:
        first_row = table.find('tr')
        if first_row:
            for cell in first_row.find_all(['td', 'th']):
                text = cell.get_text(strip=True)
                if text and len(text) > 2 and text not in ['Airline/Program', 'Alliance', 'IATA', 'Also Bookable', 'Award Release']:
                    headers.append(text)

    print(f"Extracted {len(headers)} transfer partner columns")

    if not headers:
        print("⚠️  Could not extract headers, trying text parsing")
        return parse_from_text(html_content)

    # Extract data rows
    tbody = table.find('tbody')
    rows_to_parse = []

    if tbody:
        print("Found tbody, extracting rows...")
        rows_to_parse = tbody.find_all('tr')
    else:
        print("No tbody, trying all tr elements...")
        rows_to_parse = table.find_all('tr')[1:]  # Skip header row

    print(f"Found {len(rows_to_parse)} rows to parse")

    row_count = 0
    for tr in rows_to_parse:
        cells = tr.find_all(['td', 'th'])
        if len(cells) < 6:
            continue

        # First cell is program name
        program_name = cells[0].get_text(strip=True)

        if not program_name or len(program_name) < 2 or program_name == 'Airline/Program':
            continue

        row_count += 1

        # Extract ratios from cells after the first 5 (metadata columns)
        for col_idx, cell in enumerate(cells[5:]):
            cell_text = cell.get_text(strip=True)

            # Look for ratio patterns
            ratio_match = re.search(r'(\d+\.?\d*):(\d+\.?\d*)', cell_text)

            if ratio_match and col_idx < len(headers):
                ratio_str = f"{ratio_match.group(1)}:{ratio_match.group(2)}"
                ratio = extract_ratio(ratio_str)

                if ratio is not None:
                    transfer = {
                        'from_program': headers[col_idx],
                        'to_program': program_name,
                        'ratio': ratio,
                        'category': get_program_category(program_name),
                        'last_updated': datetime.utcnow().isoformat() + 'Z'
                    }
                    transfers.append(transfer)

    print(f"Parsed {row_count} programs, extracted {len(transfers)} transfers")
    return transfers

def parse_from_text(html_content):
    """Parse transfer data from page text as fallback."""
    from bs4 import BeautifulSoup

    print("Parsing from page text...")
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for script in soup(['script', 'style']):
        script.decompose()

    # Extract text from elements with newlines preserved
    lines = []
    for element in soup.find_all(['div', 'span', 'p', 'td', 'h2', 'h3', 'h4', 'li']):
        text = element.get_text(strip=True)
        if text and len(text) > 1:
            lines.append(text)

    print(f"Extracted {len(lines)} text elements")

    # Strategy: look for patterns like "Program Name" followed by ratios
    transfers = []

    # Look for lines with program names followed by ratio patterns
    for i in range(len(lines) - 1):
        line = lines[i]

        # Check if line looks like a program name
        if any(keyword in line for keyword in ['Airlines', 'Airways', 'Club', 'Rewards', 'Plus', 'Miles', 'Mileage', 'Hilton', 'Marriott', 'Hyatt', 'Choice', 'Wyndham', 'Accor', 'IHG']):
            program_name = line

            # Look in next few lines for ratios
            for j in range(i + 1, min(i + 8, len(lines))):
                next_line = lines[j]

                # Find all ratios in this line
                ratios = re.findall(r'(\d+\.?\d*):(\d+\.?\d*)', next_line)

                if ratios:
                    # Map to known transfer partners in order
                    transfer_partners = [
                        'American Express Membership Rewards', 'Bilt', 'Capital One Rewards',
                        'Chase Ultimate Rewards', 'Citi ThankYou Points', 'Wells Fargo Rewards',
                        'Marriott Bonvoy', 'World of Hyatt', 'IHG Rewards', 'Accor Live Limitless',
                        'Choice Privileges', 'Brex Rewards', 'Ramp Rewards', 'Avios'
                    ]

                    for idx, (num, denom) in enumerate(ratios):
                        if idx < len(transfer_partners):
                            ratio = extract_ratio(f"{num}:{denom}")
                            if ratio:
                                transfer = {
                                    'from_program': transfer_partners[idx],
                                    'to_program': program_name,
                                    'ratio': ratio,
                                    'category': get_program_category(program_name),
                                    'last_updated': datetime.utcnow().isoformat() + 'Z'
                                }
                                transfers.append(transfer)

                    break  # Move to next program

    print(f"Text parsing extracted {len(transfers)} transfers")
    return transfers

def update_json(transfers):
    """Update transfer-partners.json."""
    try:
        with open('transfer-partners.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {
            'schema_version': '1.0.0',
            'last_generated': datetime.utcnow().isoformat() + 'Z',
            'last_data_source': 'https://roame.travel/transfer-partners-cheat-sheet',
            'data_as_of': datetime.utcnow().isoformat() + 'Z',
            'transfers': []
        }

    data['last_generated'] = datetime.utcnow().isoformat() + 'Z'

    if transfers:
        data['transfers'] = transfers
        data['data_as_of'] = datetime.utcnow().isoformat() + 'Z'
        print(f"✅ Updated with {len(transfers)} transfers")
    else:
        print("⚠️  No transfers found, updating timestamp only")

    with open('transfer-partners.json', 'w') as f:
        json.dump(data, f, indent=2)

    return len(transfers) > 0

def main():
    content = scrape_roame()
    if not content:
        print("❌ Failed to fetch page")
        return False

    transfers = parse_roame_table(content)

    if transfers:
        update_json(transfers)
        return True
    else:
        print("⚠️  No transfers extracted")
        update_json([])
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
