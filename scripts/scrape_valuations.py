#!/usr/bin/env python3
"""Scrape ALL Upgraded Points valuations dynamically and update JSON."""

import json
import re
from datetime import datetime
import sys

def extract_valuation(value_str):
    """Extract cents-per-point value from string."""
    if not value_str:
        return None

    # Remove common characters
    value_str = value_str.replace('¢', '').replace('cents', '').replace('%', '').strip()

    try:
        val = float(value_str)
        # Sanity check: valuations should be between 0.1 and 10 cents
        if 0.1 <= val <= 10.0:
            return val
    except ValueError:
        pass

    return None

def get_program_category(program_name):
    """Determine if a program is airline, hotel, or flexible."""
    airlines_keywords = ['airline', 'airways', 'air', 'delta', 'united', 'american',
                        'alaska', 'southwest', 'jetblue', 'frontier', 'spirit', 'allegiant',
                        'hawaiian', 'skypass', 'eurobonus', 'aadvantage', 'skymiles',
                        'mileageplus', 'trueblu', 'rapid rewards', 'velocity', 'infinity',
                        'maharaja', 'mileage', 'executive', 'asia miles', 'guest',
                        'privilege', 'krisflyer', 'flying', 'aeroplan', 'lifemiles', 'miles']

    hotels_keywords = ['marriott', 'hilton', 'hyatt', 'ihg', 'wyndham', 'choice',
                       'accor', 'radisson', 'best western', 'preferred', 'bonvoy',
                       'honors', 'one rewards', 'privileges', 'live limitless', 'leaders', 'hotel']

    program_lower = program_name.lower()

    for hotel in hotels_keywords:
        if hotel in program_lower:
            return 'hotel'

    for airline in airlines_keywords:
        if airline in program_lower:
            return 'airline'

    return 'flexible'  # Default for credit card programs

def scrape_upgraded_points():
    """Fetch Upgraded Points page - prioritize Playwright."""
    print("Fetching Upgraded Points valuations...")

    # Try Playwright first (handles JavaScript rendering)
    try:
        from playwright.sync_api import sync_playwright

        print("Using Playwright for JavaScript rendering...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://upgradedpoints.com/travel/points-and-miles-valuations/', timeout=60000)
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
            'https://upgradedpoints.com/travel/points-and-miles-valuations/',
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        if len(response.text) > 5000:
            print("✅ Page fetched via requests")
            return response.text
    except Exception as e:
        print(f"❌ Requests failed: {e}")

    print("❌ Failed to fetch page")
    return None

def parse_valuations(html_content):
    """Parse ALL valuations from page dynamically."""
    from bs4 import BeautifulSoup

    print("Parsing valuations from page...")
    soup = BeautifulSoup(html_content, 'html.parser')

    valuations = {}

    # Extract text from all elements to preserve structure
    text_parts = []
    for element in soup.find_all(['div', 'span', 'p', 'td', 'h2', 'h3', 'h4', 'li']):
        text = element.get_text(strip=True)
        if text and len(text) > 1:
            text_parts.append(text)

    lines = text_parts
    print(f"Extracted {len(lines)} text elements")

    # Look for program names followed by valuation numbers
    # Valid program line must:
    # - Be reasonably short (< 100 chars)
    # - Contain program-related keywords
    program_keywords = ['airline', 'airways', 'air', 'club', 'rewards', 'plus', 'miles',
                       'mileage', 'hilton', 'marriott', 'hyatt', 'choice', 'wyndham',
                       'accor', 'ihg', 'honors', 'bonvoy', 'privileges', 'lotusmiles',
                       'eurobonus', 'skypass', 'aeroplan', 'lifemiles', 'flying',
                       'skywards', 'guest', 'mileageplus', 'trueblu', 'rapid', 'velocity',
                       'infinity', 'maharaja', 'liveLimitless', 'amex', 'chase', 'citi',
                       'capital one', 'wells', 'fargo']

    for i, line in enumerate(lines):
        # Filter: reasonable length, contains keyword, no garbage
        if len(line) < 100 and any(kw in line.lower() for kw in program_keywords):
            if 'http' in line.lower() or 'columns' in line.lower() or '2027' in line:
                continue

            program_name = line

            # Look in next 3 lines for valuation (should be close)
            valuation_found = None
            for j in range(i + 1, min(i + 4, len(lines))):
                next_line = lines[j]

                # Extract all valuation numbers (including decimals)
                numbers = re.findall(r'(\d+\.?\d*)', next_line)

                for num_str in numbers:
                    val = extract_valuation(num_str)
                    if val:
                        valuation_found = val
                        break

                if valuation_found:
                    break

            # Only add if we found a valid valuation
            if valuation_found:
                key = program_name
                valuations[key] = {
                    'program': program_name,
                    'cents_per_point': valuation_found,
                    'category': get_program_category(program_name),
                    'aliases': [],
                    'last_updated': datetime.utcnow().isoformat() + 'Z'
                }
                print(f"  {program_name}: {valuation_found}¢")

    result = list(valuations.values())
    print(f"Total valuations parsed: {len(result)}")
    return result

def update_json(valuations):
    """Update point-valuations.json."""
    try:
        with open('point-valuations.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {
            'schema_version': '1.0',
            'last_generated': datetime.utcnow().isoformat() + 'Z',
            'default_cents_per_point': 1.0,
            'valuations': []
        }

    data['last_generated'] = datetime.utcnow().isoformat() + 'Z'

    if valuations:
        data['valuations'] = valuations
        print(f"✅ Updated with {len(valuations)} valuations")
    else:
        print("⚠️  No valuations found, updating timestamp only")

    with open('point-valuations.json', 'w') as f:
        json.dump(data, f, indent=2)

    return len(valuations) > 0

def main():
    content = scrape_upgraded_points()
    if not content:
        print("❌ Failed to fetch page")
        return False

    valuations = parse_valuations(content)

    if valuations:
        update_json(valuations)
        return True
    else:
        print("⚠️  No valuations extracted")
        update_json([])
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
