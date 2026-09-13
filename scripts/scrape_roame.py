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
    airlines_keywords = ['airline', 'airways', 'air', 'delta', 'united', 'american',
                        'alaska', 'southwest', 'jetblue', 'frontier', 'spirit', 'allegiant',
                        'hawaiian', 'skypass', 'eurobonus', 'aadvantage', 'skymiles',
                        'mileageplus', 'trueblu', 'rapid rewards', 'velocity', 'infinity',
                        'maharaja', 'mileage', 'executive', 'asia miles', 'guest',
                        'privilege', 'krisflyer', 'flying', 'aeroplan', 'lifemiles',
                        'miles', 'club', 'plus', 'lotusmiles', 'lfb', 'honor', 'avios']

    hotels_keywords = ['marriott', 'hilton', 'hyatt', 'ihg', 'wyndham', 'choice',
                       'accor', 'radisson', 'best western', 'preferred', 'bonvoy',
                       'honors', 'one rewards', 'privileges', 'live limitless', 'leaders']

    program_lower = program_name.lower()

    for hotel in hotels_keywords:
        if hotel in program_lower:
            return 'hotel'

    for airline in airlines_keywords:
        if airline in program_lower:
            return 'airline'

    return 'airline'

def scrape_roame():
    """Fetch Roame page with retries."""
    max_retries = 3
    print("Fetching Roame transfer partners data...")

    import requests
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    for attempt in range(max_retries):
        try:
            response = requests.get(
                'https://roame.travel/transfer-partners-cheat-sheet',
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            if len(response.text) > 5000:
                print("✅ Page fetched successfully")
                return response.text
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: {e}")

    # Fall back to Playwright
    print("Trying Playwright fallback...")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://roame.travel/transfer-partners-cheat-sheet', timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            content = page.content()
            browser.close()
            print("✅ Page fetched via Playwright")
            return content
    except Exception as e:
        print(f"❌ Playwright failed: {e}")

    return None

def parse_roame_table(html_content):
    """Parse the complete Roame transfer table."""
    from bs4 import BeautifulSoup

    print("Parsing transfer matrix...")
    soup = BeautifulSoup(html_content, 'html.parser')

    transfers = []

    # Find the main table
    tables = soup.find_all('table')
    if not tables:
        print("❌ No tables found")
        return transfers

    table = tables[0]
    print(f"Found {len(tables)} table(s), parsing first one")

    # Extract header row (transfer partner programs)
    header_row = table.find('thead')
    headers = []

    if header_row:
        for th in header_row.find_all('th'):
            text = th.get_text(strip=True)
            # Skip metadata columns
            if text and text not in ['Airline/Program', 'Alliance', 'IATA', 'Also Bookable', 'Award Release', '']:
                headers.append(text)

    print(f"Found {len(headers)} transfer partner columns")

    # Extract data rows (airlines/hotels)
    tbody = table.find('tbody')
    if not tbody:
        print("⚠️  No tbody found, parsing text structure instead")
        return parse_from_page_text(html_content)

    print("Parsing table rows...")
    row_count = 0

    for tr in tbody.find_all('tr'):
        cells = tr.find_all('td')
        if len(cells) < 6:  # Must have at least metadata + some transfer columns
            continue

        # First cell is program name
        program_name = cells[0].get_text(strip=True)

        if not program_name or program_name == 'Airline/Program':
            continue

        row_count += 1

        # Extract ratios from remaining cells (skip first 5 metadata columns)
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

    print(f"Extracted {row_count} programs with {len(transfers)} total transfers")
    return transfers

def parse_from_page_text(html_content):
    """Fallback: parse from full page text if table parsing fails."""
    from bs4 import BeautifulSoup

    print("Falling back to text parsing...")
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract all text
    text_parts = []
    for element in soup.find_all(['div', 'span', 'td', 'p']):
        text = element.get_text(strip=True)
        if text and 2 < len(text) < 300:
            text_parts.append(text)

    full_text = '\n'.join(text_parts)
    lines = full_text.split('\n')

    print(f"Page has {len(lines)} text lines")

    # Look for program names followed by ratios
    transfers = []

    # Common keywords for programs
    program_patterns = [
        r'(American Airlines|Alaska Airlines|British Airways|Cathay Pacific|Finnair|Iberia|Japan Airlines|Qantas|Qatar Airways|Aeromexico|Delta|Air France|KLM|Korean Air|SAS|Vietnam Airlines|Virgin Atlantic|Air Canada|Air India|ANA|Avianca|EVA Air|Lufthansa|Singapore Airlines|TAP|Thai Airways|Turkish Airlines|United|Aer Lingus|Emirates|Etihad|Frontier|Hainan Airlines|JetBlue|Southwest|Virgin Australia|Accor|Choice|Hilton|Hyatt|IHG|LHW|Marriott|Preferred|Wyndham)',
        r'(American Express|Chase|Citi|Capital One|Wells Fargo|Brex|Ramp|AMEX|BILT)',
    ]

    # Simple approach: look for program names and collect nearby ratios
    for i, line in enumerate(lines):
        # Check if line contains a program name
        for pattern in program_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Look ahead for ratios
                for j in range(i, min(i + 10, len(lines))):
                    ratios = re.findall(r'(\d+\.?\d*):(\d+\.?\d*)', lines[j])
                    if ratios:
                        for ratio_tuple in ratios:
                            ratio = extract_ratio(f"{ratio_tuple[0]}:{ratio_tuple[1]}")
                            if ratio:
                                # This is a simplified fallback; real implementation would map to partners
                                pass
                        break

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
        print(f"✅ Parsed {len(transfers)} transfers")
    else:
        print("⚠️  No transfers found")

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
        print("⚠️  No transfers parsed")
        update_json([])
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
