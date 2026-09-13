#!/usr/bin/env python3
"""Scrape Upgraded Points valuations and update JSON."""

import json
import re
from datetime import datetime
import sys

def extract_valuation(value_str):
    """Extract cents-per-point value from string like '1.5¢', '1.5', etc."""
    if not value_str:
        return None

    # Remove common characters
    value_str = value_str.replace('¢', '').replace('cents', '').replace('%', '').strip()

    try:
        return float(value_str)
    except ValueError:
        return None

def get_program_category(program_name):
    """Determine if a program is airline or hotel."""
    airlines_keywords = ['airline', 'airways', 'air', 'delta', 'united', 'american',
                        'alaska', 'southwest', 'jetblue', 'frontier', 'spirit',
                        'skypass', 'eurobonus', 'aadvantage', 'skymiles', 'mileageplus']

    hotels_keywords = ['marriott', 'hilton', 'hyatt', 'ihg', 'wyndham', 'choice',
                       'accor', 'radisson', 'best western', 'preferred', 'bonvoy',
                       'honors', 'one rewards', 'privileges', 'live limitless']

    flexible_keywords = ['chase', 'amex', 'citi', 'capital one', 'wells fargo',
                        'bofa', 'bank of america', 'brex', 'ramp', 'bilt']

    program_lower = program_name.lower()

    for flexible in flexible_keywords:
        if flexible in program_lower:
            return 'flexible'

    for hotel in hotels_keywords:
        if hotel in program_lower:
            return 'hotel'

    for airline in airlines_keywords:
        if airline in program_lower:
            return 'airline'

    return 'flexible'  # Default for credit card programs

def scrape_upgraded_points():
    """Fetch Upgraded Points page with retries."""
    max_retries = 3

    # Try requests first (faster, no browser overhead)
    print("Trying requests method first...")
    import requests
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    for attempt in range(max_retries):
        try:
            response = requests.get(
                'https://upgradedpoints.com/travel/points-and-miles-valuations/',
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            if 'point' in response.text.lower() and len(response.text) > 1000:
                print("✅ Page fetched via requests")
                return response.text
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: requests failed - {e}")

    # Fall back to Playwright if requests doesn't work
    print("Trying Playwright method...")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://upgradedpoints.com/travel/points-and-miles-valuations/', timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            content = page.content()
            browser.close()
            print("✅ Page fetched via Playwright")
            return content
    except ImportError:
        print("⚠️  Playwright not installed")
    except Exception as e:
        print(f"❌ Playwright failed: {e}")

    print("❌ Failed to fetch page via all methods")
    return None

def parse_valuations(html_content):
    """Parse valuation data from page."""
    from bs4 import BeautifulSoup

    print("Parsing valuations from page...")

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract text from elements with better structure preservation
    text_parts = []
    for element in soup.find_all(['p', 'div', 'span', 'td', 'li', 'h2', 'h3', 'h4']):
        text = element.get_text(strip=True)
        if text and len(text) > 2 and len(text) < 300:
            text_parts.append(text)

    text = '\n'.join(text_parts)
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    print(f"Page has {len(lines)} lines")

    valuations = {}

    # Known programs to look for (short keywords for better matching)
    programs = [
        ('Delta', 'Delta'),
        ('American Airlines', 'American Airlines'),
        ('United', 'United'),
        ('Alaska', 'Alaska'),
        ('Southwest', 'Southwest'),
        ('JetBlue', 'JetBlue'),
        ('Frontier', 'Frontier'),
        ('Spirit', 'Spirit'),
        ('Allegiant', 'Allegiant'),
        ('Hawaiian', 'Hawaiian'),
        ('Marriott', 'Marriott'),
        ('Hilton', 'Hilton'),
        ('Hyatt', 'Hyatt'),
        ('IHG', 'IHG'),
        ('Wyndham', 'Wyndham'),
        ('Choice', 'Choice'),
        ('Accor', 'Accor'),
        ('Chase', 'Chase Ultimate Rewards'),
        ('Amex', 'American Express Membership Rewards'),
        ('Citi', 'Citi ThankYou Points'),
        ('Capital One', 'Capital One Rewards'),
        ('Wells Fargo', 'Wells Fargo Rewards'),
    ]

    # Extract all text to search
    full_text = '\n'.join(lines)

    # Find programs and extract valuations
    for keyword, full_name in programs:
        # Search case-insensitive
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        matches = list(pattern.finditer(full_text))

        if matches:
            # Get context around the match
            for match in matches:
                start = max(0, match.start() - 200)
                end = min(len(full_text), match.end() + 200)
                context = full_text[start:end]

                # Look for valuation in context
                valuation_patterns = re.findall(r'(\d+\.?\d*)\s*(?:¢|cents|%)?', context)

                for val_str in valuation_patterns:
                    try:
                        val = float(val_str)
                        if 0.1 <= val <= 5.0:  # Sanity check for cents per point
                            valuations[full_name] = {
                                'program': full_name,
                                'cents_per_point': val,
                                'category': get_program_category(full_name),
                                'aliases': [],
                                'last_updated': datetime.utcnow().isoformat() + 'Z'
                            }
                            print(f"  {full_name}: {val}¢")
                            break
                    except (ValueError, TypeError):
                        pass

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
    print("🔄 Fetching Upgraded Points valuations...")

    content = scrape_upgraded_points()
    if not content:
        print("❌ Failed to fetch page")
        return False

    print("✅ Page fetched")

    valuations = parse_valuations(content)

    if valuations:
        update_json(valuations)
        return True
    else:
        print("⚠️  No valuations parsed")
        update_json([])
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
