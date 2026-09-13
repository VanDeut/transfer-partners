#!/usr/bin/env python3
"""
Compare Roame export with transfer-partners.json

Downloads Roame data as CSV/Excel, compares with current JSON,
and suggests updates via update_transfer.py commands.

Usage:
    python3 scripts/compare_roame.py roame-source-2026-09-20.csv
"""

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RoameParser:
    """Parse Roame export files"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data = {}

    def parse_csv(self) -> Dict:
        """Parse CSV export from Roame"""
        if not self.file_path.exists():
            print(f"❌ File not found: {self.file_path}")
            sys.exit(1)

        transfers = {}

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames:
                    print("❌ CSV is empty or invalid")
                    sys.exit(1)

                # Roame's CSV typically has columns like:
                # from_program, to_program, ratio, transfer_speed, promotion, etc.
                for row in reader:
                    if not row.get('from_program') or not row.get('to_program'):
                        continue

                    from_prog = row.get('from_program', '').strip()
                    to_prog = row.get('to_program', '').strip()
                    ratio_str = row.get('ratio', '1.0').strip()

                    # Parse ratio (handle various formats: "1:1", "1.0", "5:2", etc.)
                    ratio = self.parse_ratio(ratio_str)

                    if ratio and from_prog and to_prog:
                        key = f"{from_prog}→{to_prog}"
                        transfers[key] = {
                            'from_program': from_prog,
                            'to_program': to_prog,
                            'ratio': ratio,
                            'transfer_speed': row.get('transfer_speed', 'Unknown').strip(),
                            'promo': row.get('promotion', '').strip(),
                        }

        except Exception as e:
            print(f"❌ Error parsing CSV: {e}")
            sys.exit(1)

        return transfers

    @staticmethod
    def parse_ratio(ratio_str: str) -> Optional[float]:
        """Parse ratio from various formats"""
        ratio_str = ratio_str.strip().replace(' ', '')

        if not ratio_str:
            return None

        try:
            # Try direct float
            if '.' in ratio_str:
                return float(ratio_str)

            # Parse ratio format like "5:2" or "1:1"
            if ':' in ratio_str:
                parts = ratio_str.split(':')
                if len(parts) == 2:
                    numerator = float(parts[0])
                    denominator = float(parts[1])
                    if denominator > 0:
                        return numerator / denominator

            # Fallback to simple float conversion
            return float(ratio_str)

        except (ValueError, ZeroDivisionError):
            return None


class TransferComparator:
    """Compare Roame data with current JSON"""

    def __init__(self, json_path: str = "transfer-partners.json"):
        self.json_path = Path(json_path)
        self.current_data = self.load_json()
        self.current_transfers = self.build_transfer_dict()
        self.changes = []
        self.new_transfers = []

    def load_json(self) -> dict:
        """Load current JSON"""
        if not self.json_path.exists():
            print(f"❌ {self.json_path} not found")
            sys.exit(1)
        with open(self.json_path, 'r') as f:
            return json.load(f)

    def build_transfer_dict(self) -> Dict:
        """Build dict of current transfers for fast lookup"""
        transfers = {}
        for transfer in self.current_data['transfers']:
            key = f"{transfer['from_program']}→{transfer['to_program']}"
            transfers[key] = transfer
        return transfers

    def compare(self, roame_transfers: Dict):
        """Compare Roame data with current"""
        print("\n📊 Comparing Roame data with transfer-partners.json...\n")

        # Check for changes and new transfers
        for key, roame_transfer in roame_transfers.items():
            current = self.current_transfers.get(key)

            if current is None:
                # New transfer not in our data
                self.new_transfers.append(roame_transfer)
                print(f"✨ NEW: {roame_transfer['from_program']} → {roame_transfer['to_program']}")
                print(f"   Ratio: {roame_transfer['ratio']}")

            else:
                # Existing transfer - check if rate changed
                current_ratio = current['ratio']
                roame_ratio = roame_transfer['ratio']

                # Allow small float differences
                if abs(current_ratio - roame_ratio) > 0.01:
                    self.changes.append({
                        'from_program': roame_transfer['from_program'],
                        'to_program': roame_transfer['to_program'],
                        'old_ratio': current_ratio,
                        'new_ratio': roame_ratio,
                    })
                    print(f"📊 CHANGED: {roame_transfer['from_program']} → {roame_transfer['to_program']}")
                    print(f"   {current_ratio} → {roame_ratio}")

    def print_summary(self):
        """Print summary of changes"""
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Updated rates: {len(self.changes)}")
        print(f"New transfers: {len(self.new_transfers)}")
        print(f"Total checked: {len(self.current_transfers)}")

        if not self.changes and not self.new_transfers:
            print("\n✅ No changes detected!")
            return

        # Print suggested commands
        print("\n" + "=" * 60)
        print("SUGGESTED UPDATES")
        print("=" * 60)

        if self.changes:
            print("\n# Updated Rates:")
            for change in self.changes:
                cmd = f"python3 update_transfer.py \"{change['from_program']}\" \"{change['to_program']}\" {change['new_ratio']}"
                print(cmd)

        if self.new_transfers:
            print("\n# New Transfers:")
            for transfer in self.new_transfers:
                cmd = f"python3 update_transfer.py \"{transfer['from_program']}\" \"{transfer['to_program']}\" {transfer['ratio']}"
                if transfer.get('transfer_speed'):
                    cmd += f" --speed \"{transfer['transfer_speed']}\""
                print(cmd)

        print("\n# After updates, run:")
        print("./validate.sh")
        print("git add transfer-partners.json roame-source-*.csv")
        print("git commit -m \"Sync transfer rates with Roame data as of YYYY-MM-DD\"")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/compare_roame.py <roame_export_file>")
        print("")
        print("Examples:")
        print("  python3 scripts/compare_roame.py roame-source-2026-09-20.csv")
        print("  python3 scripts/compare_roame.py transfer-partners-export.xlsx")
        sys.exit(1)

    file_path = sys.argv[1]

    print(f"📖 Parsing Roame export: {file_path}")

    # Parse Roame data
    parser = RoameParser(file_path)
    roame_data = parser.parse_csv()
    print(f"✅ Found {len(roame_data)} transfers in Roame export")

    # Compare with current
    comparator = TransferComparator()
    comparator.compare(roame_data)

    # Summary
    comparator.print_summary()


if __name__ == '__main__':
    main()
