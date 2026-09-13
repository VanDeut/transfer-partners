#!/bin/bash
# Test script to debug the scraper

echo "🔍 Testing Roame scraper..."

python3 << 'PYTHON'
import requests
from bs4 import BeautifulSoup

# Fetch the page
print("1️⃣  Fetching page...")
response = requests.get(
    'https://roame.travel/transfer-partners-cheat-sheet',
    headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
    timeout=15
)
print(f"   Status: {response.status_code}")

# Parse HTML
print("2️⃣  Parsing HTML...")
soup = BeautifulSoup(response.text, 'html.parser')

# Find tables
tables = soup.find_all('table')
print(f"   Found {len(tables)} tables")

if tables:
    table = tables[0]
    
    # Check thead
    thead = table.find('thead')
    print(f"   Thead found: {thead is not None}")
    
    if thead:
        ths = thead.find_all('th')
        print(f"   Header cells: {len(ths)}")
        if ths:
            print(f"   First 5 headers: {[th.get_text(strip=True)[:30] for th in ths[:5]]}")
    
    # Check tbody
    tbody = table.find('tbody')
    print(f"   Tbody found: {tbody is not None}")
    
    if tbody:
        trs = tbody.find_all('tr')
        print(f"   Data rows: {len(trs)}")
        
        if trs:
            first_row = trs[0]
            cells = first_row.find_all('td')
            print(f"   Cells in first row: {len(cells)}")
            if cells:
                print(f"   First cell text: {cells[0].get_text(strip=True)[:50]}")

print("3️⃣  Checking for ratio patterns in page text...")
page_text = soup.get_text()
import re
ratios = re.findall(r'\d+:\d+', page_text)
print(f"   Found {len(ratios)} ratio patterns")
if ratios:
    print(f"   Sample ratios: {ratios[:10]}")

PYTHON
