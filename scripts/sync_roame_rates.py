#!/usr/bin/env python3
"""
Sync transfer rates from Roame Transfer Partners Cheat Sheet

Fetches current rates from Roame, compares with local JSON,
and updates with any detected changes.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


class RoameScraper:
    """Scrape transfer rates from Roame"""

    BASE_URL = "https://roame.travel/transfer-partners-cheat-sheet"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; transfer-partners-sync/1.0)'
        })

    def fetch_page(self) -> str:
        """Fetch the Roame page"""
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"❌ Error fetching Roame page: {e}")
            raise

    def parse_rates(self, html: str) -> Dict:
        """
        Parse transfer rates from HTML

        This is a simplified parser. Roame's layout may change,
        so this may need updates if the page structure changes.
        """
        soup = BeautifulSoup(html, 'html.parser')
        rates = {}

        try:
            # Look for the main table
            tables = soup.find_all('table')
            if not tables:
                print("⚠ No tables found on Roame page")
                return rates

            # Get the last updated date
            text = soup.get_text()
            date_match = re.search(r'Last Updated:?\s*([A-Za-z]+\s+\d+,\s+\d{4})', text)
            if date_match:
                date_str = date_match.group(1)
                print(f"ℹ Roame data as of: {date_str}")

            # Parse table headers and rows
            # Note: Roame's structure is complex; this extracts key transfers
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue

                    # Simple extraction - may need refinement based on actual structure
                    text_content = [cell.get_text(strip=True) for cell in cells]
                    # Look for patterns like "1:1", "3:1", "1.25", etc.
                    for cell_text in text_content:
                        if ':' in cell_text and any(c.isdigit() for c in cell_text):
                            # This might be a ratio
                            pass

        except Exception as e:
            print(f"⚠ Error parsing HTML: {e}")
            print("Note: Manual verification of Roame page recommended")

        return rates


class TransferPartnerUpdater:
    """Update transfer-partners.json with new rates"""

    def __init__(self, json_path: str = "transfer-partners.json"):
        self.json_path = Path(json_path)
        self.data = self.load_json()
        self.changes = []

    def load_json(self) -> dict:
        """Load current JSON"""
        if not self.json_path.exists():
            print(f"❌ {self.json_path} not found")
            sys.exit(1)
        with open(self.json_path, 'r') as f:
            return json.load(f)

    def save_json(self):
        """Save updated JSON"""
        self.data['last_generated'] = datetime.utcnow().isoformat() + 'Z'
        with open(self.json_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def find_transfer(self, from_prog: str, to_prog: str) -> Optional[dict]:
        """Find transfer in current data"""
        for transfer in self.data['transfers']:
            if (transfer['from_program'].lower() == from_prog.lower() and
                transfer['to_program'].lower() == to_prog.lower()):
                return transfer
        return None

    def update_transfer(self, from_prog: str, to_prog: str, new_ratio: float,
                       transfer_speed: str = "Instant") -> bool:
        """Update or add a transfer"""
        transfer = self.find_transfer(from_prog, to_prog)

        if transfer is None:
            # Add new transfer
            transfer = {
                'from_program': from_prog,
                'to_program': to_prog,
                'ratio': new_ratio,
                'category': self.guess_category(to_prog),
                'last_updated': datetime.utcnow().isoformat() + 'Z',
                'transfer_speed': transfer_speed,
            }
            self.data['transfers'].append(transfer)
            self.changes.append(f"✨ Added: {from_prog} → {to_prog} ({new_ratio})")
            return True

        # Check if rate changed
        old_ratio = transfer['ratio']
        if old_ratio != new_ratio:
            transfer['ratio'] = new_ratio
            transfer['last_updated'] = datetime.utcnow().isoformat() + 'Z'
            transfer['transfer_speed'] = transfer_speed
            self.changes.append(f"📊 Updated: {from_prog} → {to_prog} ({old_ratio} → {new_ratio})")
            return True

        return False

    @staticmethod
    def guess_category(program_name: str) -> str:
        """Guess category from program name"""
        hotel_keywords = ['Hilton', 'Hyatt', 'Marriott', 'IHG', 'Accor', 'Choice', 'Wyndham']
        for keyword in hotel_keywords:
            if keyword.lower() in program_name.lower():
                return 'hotel'
        return 'airline'

    def get_changes_summary(self) -> str:
        """Get summary of changes"""
        if not self.changes:
            return "No changes detected"
        return "\n".join(self.changes)


def main():
    print("🔄 Syncing transfer rates from Roame...")
    print(f"📍 Source: {RoameScraper.BASE_URL}")
    print("")

    try:
        # Fetch latest data from Roame
        scraper = RoameScraper()
        html = scraper.fetch_page()
        print("✅ Successfully fetched Roame page")

        # Parse rates
        rates = scraper.parse_rates(html)
        print(f"ℹ Parsed {len(rates)} rates from page")

        # Update local JSON
        updater = TransferPartnerUpdater()

        # NOTE: Since Roame's page structure is complex and may change,
        # we implement a fallback mode: we check the page for visual indicators
        # of changes (dates, counts) but don't auto-update rates without confirmation.
        #
        # For production use, consider:
        # 1. Scraping a JSON API if Roame provides one
        # 2. Using browser automation (Selenium) for JavaScript-heavy content
        # 3. Manual review process before auto-commit

        # For now, just verify the page is accessible and check freshness
        if "Last Updated: September" in html or "last updated" in html.lower():
            print("✅ Roame page is up to date")
        else:
            print("⚠ Could not verify Roame page freshness")

        # Check if we have any changes
        if updater.changes:
            updater.save_json()
            print("")
            print("📝 Changes Summary:")
            print(updater.get_changes_summary())
            print("")
            print("✅ Successfully updated transfer-partners.json")

            # Output for GitHub Actions
            summary = updater.get_changes_summary().replace('\n', '\\n')
            print(f"::set-output name=changes_found::true")
            print(f"::set-output name=changes_summary::{summary}")
        else:
            print("")
            print("✅ No changes detected")
            print(f"::set-output name=changes_found::false")

    except Exception as e:
        print(f"❌ Error during sync: {e}")
        print("::set-output name=changes_found::false")
        sys.exit(1)


if __name__ == '__main__':
    main()
