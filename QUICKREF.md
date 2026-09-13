# Quick Reference

Fast lookup for common tasks.

## Update Operations

### Update transfer rate
```bash
python3 update_transfer.py "Chase" "United MileagePlus" 1.0
```

### Add promo bonus
```bash
python3 update_transfer.py "AMEX" "Qatar Airways" 1.0 --promo 25 --expires "2026-10-31"
```

### Update transfer speed
```bash
python3 update_transfer.py "Chase" "Air France" 1.0 --speed "2-3 weeks"
```

## Validation

```bash
./validate.sh                    # Full validation
```

## JSON Queries

```bash
# List all transfers
jq '.transfers[]' transfer-partners.json

# Show transfer from one program
jq '.transfers[] | select(.from_program == "Chase")' transfer-partners.json

# Find all promos
jq '.transfers[] | select(.promo_bonus_pct != null)' transfer-partners.json

# Best ratios
jq '.transfers | sort_by(-.ratio) | .[0:5]' transfer-partners.json

# Group by category
jq '.transfers | group_by(.category)' transfer-partners.json

# Find stale data
jq '.transfers[] | select(.last_updated < "2026-08-13")' transfer-partners.json
```

## Git Workflow

```bash
# Check what changed
git diff transfer-partners.json

# Stage changes
git add transfer-partners.json

# Commit
git commit -m "Update Chase-to-United from 1:1 to 0.8:1"

# Push
git push origin main
```

## Schema at a Glance

```json
{
  "schema_version": "1.0.0",
  "last_generated": "2026-09-13T00:00:00Z",
  "last_data_source": "https://roame.travel/transfer-partners-cheat-sheet",
  "data_as_of": "2026-09-11T00:00:00Z",
  "transfers": [
    {
      "from_program": "Chase Sapphire",
      "to_program": "United MileagePlus",
      "ratio": 1.0,
      "category": "airline",
      "promo_bonus_pct": null,
      "promo_expires": null,
      "last_updated": "2026-09-11T00:00:00Z",
      "transfer_speed": "Instant"
    }
  ]
}
```

## Important Notes

- **Always validate** after manual edits: `./validate.sh`
- **Ratio interpretation**: 1.0 = 1:1, 0.8 = 4:5, 1.25 = 1:1.25
- **Promos**: Must set both `promo_bonus_pct` AND `promo_expires` (or neither)
- **Categories**: Either `"airline"` or `"hotel"`
- **Dates**: Always ISO8601 format (YYYY-MM-DDTHH:MM:SSZ)

## Files

| File | Purpose |
|------|---------|
| `transfer-partners.json` | Main data file |
| `README.md` | Schema & design docs |
| `SETUP.md` | Getting started |
| `MAINTENANCE.md` | Detailed update guide |
| `QUICKREF.md` | This file |
| `validate.sh` | Validation tool |
| `update_transfer.py` | Update script |
| `.gitignore` | Git ignore rules |

## Links

- [Schema Documentation](README.md)
- [Setup Guide](SETUP.md)
- [Maintenance Guide](MAINTENANCE.md)
- [Data Source](https://roame.travel/transfer-partners-cheat-sheet)

---

Last updated: 2026-09-13
