# Data Sources & Update Workflow

This document explains how transfer rate data flows into the repository.

## Data Sources

### Primary Source: Roame Transfer Partners
- **URL**: https://roame.travel/transfer-partners-cheat-sheet
- **Download**: Click the "Download" button on their page
- **Format**: CSV, Excel, or screenshot
- **Frequency**: Check weekly/monthly for updates

### Secondary Source: Official Credit Card Issuers
- Chase: https://www.chase.com/personal/sapphire/transfers
- American Express: https://www.americanexpress.com/us/credit-cards/rewards/
- Citi: https://www.citi.com/thank-you/
- Capital One: https://www.capitalone.com/credit-cards/

## Workflow: Updating Transfer Rates

### Step 1: Download Fresh Data from Roame

1. Visit https://roame.travel/transfer-partners-cheat-sheet
2. Click the **Download** button
3. Save as `roame-source-YYYY-MM-DD.csv` (or .xlsx)
4. Commit to repo:
   ```bash
   git add roame-source-*.csv
   git commit -m "Add Roame source data as of 2026-09-20"
   ```

### Step 2: Compare with Current transfer-partners.json

```bash
# View current rates by category
jq '.transfers | group_by(.category) | map({category: .[0].category, count: length})' transfer-partners.json

# Find specific transfers
jq '.transfers[] | select(.from_program == "Chase")' transfer-partners.json
```

### Step 3: Update Changed Rates

For each change found in Roame data:

```bash
# Update a rate
python3 update_transfer.py "Chase" "United MileagePlus" 1.0

# Add a promotional offer
python3 update_transfer.py "AMEX" "Qatar Airways" 1.0 --promo 25 --expires "2026-10-31"

# Verify
./validate.sh
```

### Step 4: Commit Changes

```bash
git add transfer-partners.json
git commit -m "Sync transfer rates with Roame data as of 2026-09-20

Changes:
- Updated Chase-to-United: 1.0 → 0.8
- Added AMEX-to-Qatar: 1.0 with +25% bonus

Source: roame-source-2026-09-20.csv"
```

## File Organization

```
transfer-partners/
├── transfer-partners.json          # CURRENT DATA (single source of truth)
├── roame-source-2026-09-20.csv    # REFERENCE: Latest Roame download
├── roame-source-2026-09-13.csv    # ARCHIVE: Previous downloads
├── scripts/
│   └── compare_roame.py            # Tool to compare Roame data
└── docs/
    └── roame-export-example.csv    # Example format
```

## Automated Comparison Script

Use this to detect changes between Roame data and transfer-partners.json:

```bash
python3 scripts/compare_roame.py roame-source-2026-09-20.csv
```

This script will:
- Parse Roame CSV/Excel file
- Compare with current JSON
- Show what changed
- Suggest update commands

## Update Frequency

Recommended schedule:
- **Weekly**: Quick visual check on Roame
- **Monthly**: Full download and compare
- **On-demand**: When you hear about rate changes

Create a reminder:
```bash
# Add to your calendar or cron job
0 9 * * MON python3 scripts/compare_roame.py  # Every Monday 9 AM
```

## Data Quality Checklist

Before committing updates:

- [ ] Source data downloaded from Roame (not scraped)
- [ ] All changes documented in commit message
- [ ] `./validate.sh` passes all checks
- [ ] No stale data (>30 days old)
- [ ] Promotional dates are in the future
- [ ] Ratios are reasonable (0 < ratio < 5)

## Archive Strategy

Keep historical Roame exports for:
- **Audit trail**: Who changed what and when
- **Dispute resolution**: Verify what Roame said on a date
- **Trend analysis**: See how rates have changed over time

```bash
# Keep Roame exports for 1 year
roame-source-2026-*.csv   # Current year
roame-source-2025-*.csv   # Previous year
```

## Licensing & Attribution

When redistributing Roame data:

1. **Credit Roame** in your docs/code
2. **Include timestamp** of when data was current
3. **Check their ToS** for redistribution rights
4. **Fair use**: You're using publicly available data for personal project

Current attribution in README.md:
```markdown
Data sourced from:
- [Roame Transfer Partners Cheat Sheet](https://roame.travel/transfer-partners-cheat-sheet)
```

## Future: Roame API Integration

If Roame offers an API, we can:
1. Query their API instead of downloading manually
2. Auto-detect changes
3. Auto-commit with their data

Until then, manual downloads + local comparison is the best approach.

## Troubleshooting

**Q: Roame changed their download format**  
A: Check `scripts/compare_roame.py` and update parser as needed

**Q: I can't find the download button**  
A: It may be on a specific page section. Look for CSV/Excel export options.

**Q: Should I keep old Roame exports?**  
A: Yes, for 6-12 months as audit trail and for trend analysis

**Q: Can I share the Roame CSV publicly?**  
A: Check their ToS. Generally, publicly available data is sharable with attribution.

---

Last Updated: 2026-09-13
