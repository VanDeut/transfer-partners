#!/usr/bin/env python3
"""
Update or add transfer rates in transfer-partners.json

Usage:
    python3 update_transfer.py "Chase" "United MileagePlus" 1.0
    python3 update_transfer.py "American Express" "Qatar Airways Privilege Club" 1.0 --promo 25 --expires "2026-10-31"
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def load_transfers():
    """Load the transfer-partners.json file"""
    with open('transfer-partners.json', 'r') as f:
        return json.load(f)


def save_transfers(data):
    """Save the transfer-partners.json file"""
    data['last_generated'] = datetime.utcnow().isoformat() + 'Z'
    with open('transfer-partners.json', 'w') as f:
        json.dump(data, f, indent=2)


def find_transfer(transfers: list, from_prog: str, to_prog: str) -> Optional[dict]:
    """Find a transfer in the transfers array"""
    for transfer in transfers:
        if transfer['from_program'] == from_prog and transfer['to_program'] == to_prog:
            return transfer
    return None


def get_category(to_program: str) -> str:
    """Guess the category based on program name"""
    hotel_keywords = ['Hilton', 'Hyatt', 'Marriott', 'IHG', 'Accor', 'Choice', 'Wyndham', 'Preferred']
    for keyword in hotel_keywords:
        if keyword.lower() in to_program.lower():
            return 'hotel'
    return 'airline'


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 update_transfer.py FROM_PROGRAM TO_PROGRAM RATIO [OPTIONS]")
        print("")
        print("Options:")
        print("  --promo PCT      Promotional bonus percentage")
        print("  --expires DATE   Promo expiration date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)")
        print("  --speed SPEED    Transfer speed (e.g., 'Instant', '~1 day', '2-3 weeks')")
        print("")
        print("Examples:")
        print("  python3 update_transfer.py 'Chase' 'United MileagePlus' 1.0")
        print("  python3 update_transfer.py 'AMEX' 'Qatar Airways' 1.0 --promo 25 --expires 2026-10-31 --speed Instant")
        sys.exit(1)

    from_program = sys.argv[1]
    to_program = sys.argv[2]
    ratio = float(sys.argv[3])

    # Parse optional arguments
    promo_bonus_pct = None
    promo_expires = None
    transfer_speed = "Instant"

    i = 4
    while i < len(sys.argv):
        if sys.argv[i] == '--promo' and i + 1 < len(sys.argv):
            promo_bonus_pct = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--expires' and i + 1 < len(sys.argv):
            date_str = sys.argv[i + 1]
            # Parse and format the date
            try:
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                promo_expires = dt.isoformat() + 'Z' if 'T' not in date_str else date_str
            except ValueError:
                print(f"Error: Invalid date format: {date_str}")
                sys.exit(1)
            i += 2
        elif sys.argv[i] == '--speed' and i + 1 < len(sys.argv):
            transfer_speed = sys.argv[i + 1]
            i += 2
        else:
            print(f"Unknown option: {sys.argv[i]}")
            sys.exit(1)

    # Validate inputs
    if ratio <= 0:
        print("Error: Ratio must be positive")
        sys.exit(1)

    if promo_bonus_pct is not None and promo_expires is None:
        print("Error: If --promo is set, --expires must also be set")
        sys.exit(1)

    if promo_bonus_pct is None and promo_expires is not None:
        print("Error: If --expires is set, --promo must also be set")
        sys.exit(1)

    # Load current data
    data = load_transfers()
    transfers = data['transfers']

    # Find or create transfer record
    transfer = find_transfer(transfers, from_program, to_program)

    if transfer is None:
        # Create new transfer
        transfer = {
            'from_program': from_program,
            'to_program': to_program,
            'ratio': ratio,
            'category': get_category(to_program),
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'transfer_speed': transfer_speed,
        }
        if promo_bonus_pct is not None:
            transfer['promo_bonus_pct'] = promo_bonus_pct
            transfer['promo_expires'] = promo_expires

        transfers.append(transfer)
        print(f"✓ Added transfer: {from_program} → {to_program}")
    else:
        # Update existing transfer
        old_ratio = transfer.get('ratio')
        transfer['ratio'] = ratio
        transfer['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        transfer['transfer_speed'] = transfer_speed

        if promo_bonus_pct is not None:
            transfer['promo_bonus_pct'] = promo_bonus_pct
            transfer['promo_expires'] = promo_expires
        else:
            # Remove promo if not specified
            transfer.pop('promo_bonus_pct', None)
            transfer.pop('promo_expires', None)

        print(f"✓ Updated transfer: {from_program} → {to_program}")
        if old_ratio != ratio:
            print(f"  Ratio changed: {old_ratio} → {ratio}")

    # Save updated data
    save_transfers(data)
    print(f"✓ Saved to transfer-partners.json")
    print(f"✓ Generated at: {data['last_generated']}")


if __name__ == '__main__':
    main()
