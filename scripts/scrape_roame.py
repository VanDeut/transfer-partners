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
    airlines_keywords = ['airline', 'airways', 'air', 'skypass', 'eurobonus', 'aadvantage',
                        'skymiles', 'mileageplus', 'trueblu', 'rapid rewards', 'velocity',
                        'infinity', 'maharaja', 'mileage', 'executive', 'asia miles', 'guest',
                        'privilege', 'krisflyer', 'flying', 'aeroplan', 'lifemiles', 'miles']

    hotels_keywords = ['marriott', 'hilton', 'hyatt', 'ihg', 'wyndham', 'choice', 'accor',
                       'radisson', 'best western', 'preferred', 'bonvoy', 'honors',
                       'one rewards', 'privileges', 'live limitless', 'leaders']

    program_lower = program_name.lower()

    for hotel in hotels_keywords:
        if hotel in program_lower:
            return 'hotel'

    for airline in airlines_keywords:
        if airline in program_lower:
            return 'airline'

    return 'airline'

def scrape_roame():
    """Fetch page content using Playwright or requests."""
    try:
        # Try Playwright first
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
            print("⚠️  Playwright not available, using requests...")
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
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

def parse_transfers(html_content):
    """Parse transfer data from page content."""
    from bs4 import BeautifulSoup

    print("Parsing transfers from page...")

    # Known transfer partners in order
    transfer_partners = [
        'American Express Membership Rewards', 'Bilt', 'Capital One Rewards',
        'Chase Ultimate Rewards', 'Citi ThankYou Points', 'Wells Fargo Rewards',
        'Marriott Bonvoy', 'World of Hyatt', 'IHG Rewards', 'Accor Live Limitless',
        'Choice Privileges', 'Brex Rewards', 'Ramp Rewards', 'Avios'
    ]

    soup = BeautifulSoup(html_content, 'html.parser')

    # Better text extraction: get text from elements and preserve some structure
    text_parts = []
    for element in soup.find_all(['p', 'div', 'span', 'td', 'tr']):
        text = element.get_text(strip=True)
        if text:
            text_parts.append(text)

    text = '\n'.join(text_parts)
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    print(f"Page has {len(lines)} lines")

    if len(lines) < 10:
        print(f"⚠️  Very few lines extracted. First 5 lines:")
        for i, line in enumerate(lines[:5]):
            print(f"  {i}: {line[:100]}")

    # Strategy: Find all airline/program names, then look for ratios in nearby lines
    transfers = {}  # Use dict to deduplicate

    # Key programs we're looking for
    program_keywords = {
        'American Airlines': 'American Airlines',
        'Alaska Airlines': 'Alaska Airlines',
        'British Airways': 'British Airways',
        'Cathay Pacific': 'Cathay Pacific',
        'Delta': 'Delta',
        'United': 'United',
        'Southwest': 'Southwest',
        'JetBlue': 'JetBlue',
        'Virgin': 'Virgin',
        'Marriott': 'Marriott Bonvoy',
        'Hilton': 'Hilton Honors',
        'Hyatt': 'World of Hyatt',
        'IHG': 'IHG Rewards',
    }

    print(f"Looking for programs: {', '.join(program_keywords.keys())}")

    # Find each program and extract ratios that follow
    for i, line in enumerate(lines):
        line_clean = line.strip()

        # Look for program names
        found_program = None
        for keyword, full_name in program_keywords.items():
            if keyword in line_clean and len(line_clean) < 50:  # Probably a header line
                found_program = full_name
                break

        if found_program:
            # Look ahead for ratio patterns in the next 10 lines
            program_ratios = []
            for j in range(i + 1, min(i + 15, len(lines))):
                next_line = lines[j].strip()

                # Extract all ratios from this line
                for match in re.finditer(r'(\d+\.?\d*):(\d+\.?\d*)', next_line):
                    ratio_str = f"{match.group(1)}:{match.group(2)}"
                    ratio = extract_ratio(ratio_str)
                    if ratio is not None:
                        program_ratios.append(ratio)

                # Stop if we hit another program or end of data
                if program_ratios and (j > i + 5 or any(kw in next_line for kw in program_keywords.keys())):
                    break

            print(f"  {found_program}: found {len(program_ratios)} ratios")

            # Assign ratios to transfer partners
            for idx, ratio in enumerate(program_ratios):
                if idx < len(transfer_partners):
                    key = (transfer_partners[idx], found_program)
                    transfers[key] = {
                        'from_program': transfer_partners[idx],
                        'to_program': found_program,
                        'ratio': ratio,
                        'category': get_program_category(found_program),
                        'last_updated': datetime.utcnow().isoformat() + 'Z'
                    }

    result = list(transfers.values())
    print(f"Total transfers parsed: {len(result)}")
    return result

def update_json(transfers):
    """Update transfer-partners.json with new data."""
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
    print("🔄 Fetching Roame transfer partners data...")

    content = scrape_roame()
    if not content:
        print("❌ Failed to fetch page")
        return False

    print("✅ Page fetched")

    transfers = parse_transfers(content)

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
