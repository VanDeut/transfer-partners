# Transfer Partners Maintenance Guide

This guide explains how to keep transfer-partners.json up-to-date with current rates and promotions.

## Quick Update

### Via Command Line

Update an existing transfer rate:
```bash
python3 update_transfer.py "Chase" "United MileagePlus" 1.0 --speed Instant
```

Add a transfer with promotional bonus:
```bash
python3 update_transfer.py "American Express" "Qatar Airways Privilege Club" 1.0 \
  --promo 25 \
  --expires "2026-10-31" \
  --speed Instant
```

### Manual Edit

Edit `transfer-partners.json` directly:
1. Find the transfer object (or add new one to `transfers` array)
2. Update `ratio`, `promo_bonus_pct`, `promo_expires`
3. Set `last_updated` to today's date in ISO8601 format
4. Update `last_generated` in the root object
5. Validate: `./validate.sh`

## Validation Checklist

After any update, run:
```bash
./validate.sh
```

This checks:
- ✓ Valid JSON syntax
- ✓ Required fields present
- ✓ Valid category values
- ✓ Reasonable ratio values (>0, <5)
- ✓ Promotional consistency (both pct and expiry or neither)
- ✓ No expired promotional offers
- ✓ Data freshness (not stale >30 days)

## Common Update Scenarios

### Scenario 1: Transfer Rate Changes

Example: Chase-to-United changes from 1:1 to 0.8:1

```bash
python3 update_transfer.py "Chase" "United MileagePlus" 0.8 --speed Instant
```

Or manually edit the existing transfer record:
```json
{
  "from_program": "Chase",
  "to_program": "United MileagePlus",
  "ratio": 0.8,
  "last_updated": "2026-09-14T00:00:00Z",
  "transfer_speed": "Instant"
}
```

### Scenario 2: Add Promotional Bonus

Example: AMEX announces +30% bonus to British Airways through 10/31

```bash
python3 update_transfer.py "American Express" "British Airways Executive Club" 1.0 \
  --promo 30 \
  --expires "2026-10-31T23:59:59Z" \
  --speed Instant
```

### Scenario 3: Remove Expired Promotion

The validation script will warn about expired promos. Remove them by:

1. Edit the transfer record
2. Delete `promo_bonus_pct` and `promo_expires` fields
3. Run `validate.sh`

```json
{
  "from_program": "Citi ThankYou",
  "to_program": "Emirates Skywards",
  "ratio": 1.0,
  "category": "airline",
  "last_updated": "2026-09-14T00:00:00Z",
  "transfer_speed": "Instant"
}
```

### Scenario 4: Add New Transfer Route

Example: A new airline joins Citi's transfer partners

```bash
python3 update_transfer.py "Citi ThankYou" "Lufthansa Miles & More" 1.0
```

The script will auto-detect the category (airline/hotel) based on program name.

### Scenario 5: Update Transfer Speed

Example: Transfer to a specific program now takes 2-3 weeks instead of instant

```bash
python3 update_transfer.py "Chase" "Air France Flying Blue" 1.0 --speed "2-3 weeks"
```

## Data Quality Standards

### Source Truth

Always verify rates against:
1. **Primary**: https://roame.travel/transfer-partners-cheat-sheet
2. **Secondary**: Official credit card issuer website
3. **Tertiary**: Community reporting (with confirmation)

### Ratio Accuracy

- **Airline transfers**: Verified to ±0.05 ratio
- **Hotel transfers**: Verified to ±0.05 ratio
- **Promotional rates**: Confirmed via official announcement

### Timeliness

| Event | Response Time |
|-------|---|
| New promotional offer | Within 24 hours |
| Rate change | Within 24 hours |
| Promotion expiration | On expiry date |
| Program discontinuation | Within 1 week |
| Routine verification | Monthly |

## Workflow: Updating from Roame

1. **Fetch latest data**
   - Visit https://roame.travel/transfer-partners-cheat-sheet
   - Screenshot or note any rate changes/new promos

2. **Compare with current JSON**
   ```bash
   # List all current transfers
   jq -r '.transfers[] | "\(.from_program) → \(.to_program): \(.ratio)"' transfer-partners.json
   ```

3. **Update changed rates**
   ```bash
   # For each change:
   python3 update_transfer.py "FROM" "TO" RATIO
   ```

4. **Add promotional offers**
   ```bash
   # For new promos:
   python3 update_transfer.py "FROM" "TO" RATIO --promo PCT --expires DATE
   ```

5. **Validate**
   ```bash
   ./validate.sh
   ```

6. **Commit**
   ```bash
   git add transfer-partners.json
   git commit -m "Update transfer rates from Roame as of YYYY-MM-DD"
   ```

## Automated Updates (Future)

Setup scheduled update job:

```bash
# Check Roame daily and auto-update if changes detected
# (Example cron configuration)

0 09 * * * cd /path/to/transfer-partners && python3 fetch_and_update.py
```

## Monitoring & Alerts

### Stale Data Detection

```bash
# Find transfers not updated in 30+ days
jq -r '.transfers[] | select(.last_updated < (now - (30 * 86400)) | todate) | "\(.from_program) → \(.to_program)"' transfer-partners.json
```

### Expired Promotions

```bash
# List active promotions
jq -r '.transfers[] | select(.promo_expires != null) | {from: .from_program, to: .to_program, expires: .promo_expires}' transfer-partners.json
```

### Missing Transfers

```bash
# Identify gaps (transfers in Roame but not in our JSON)
# Manually compare against https://roame.travel/transfer-partners-cheat-sheet
```

## Backup & Recovery

### Before Major Updates

```bash
git stash  # Save any uncommitted changes
git pull   # Ensure latest version
cp transfer-partners.json transfer-partners.json.backup.$(date +%Y%m%d)
```

### Rollback a Bad Update

```bash
git checkout HEAD transfer-partners.json
# or
cp transfer-partners.json.backup.YYYYMMDD transfer-partners.json
./validate.sh
```

## Git Commit Messages

Use clear, descriptive commit messages:

```
# New transfers
Add Citi transfers to Lufthansa (1:1 rate)

# Rate changes
Update Chase-to-United ratio from 1:1 to 0.8:1

# Promotions
Add AMEX +30% bonus to British Airways through 10/31

# Bulk updates
Sync transfer rates with Roame as of 2026-09-14

# Maintenance
Remove expired promotional offers (as of 2026-09-14)
```

## FAQ

**Q: Should I update the schema_version field?**  
A: Only if you change the field structure. Minor updates (adding/removing data) don't require version bump.

**Q: What if Roame and official sources disagree?**  
A: Use the official credit card issuer website. Roame may lag by a day or two.

**Q: How do I handle transfer programs that discontinue?**  
A: Remove the transfer completely. Update commit message: "Remove [Program] transfer (discontinued as of [DATE])".

**Q: Can I add transfer speeds beyond "Instant" and "~1 day"?**  
A: Yes. Use descriptive values: "~2-3 hours", "~2-3 days", "1-2 weeks", "Up to 6 weeks", etc.

**Q: What's the difference between updating ratio vs. setting a promo?**  
A: **Ratio**: Permanent exchange rate. **Promo**: Temporary bonus (temporary ratio). Use promo if the bonus expires.

## Support

For issues or questions:
1. Check this guide's FAQ
2. Review recent commits: `git log --oneline -20 transfer-partners.json`
3. Run validation: `./validate.sh` (look for warnings)
4. Consult the main README.md for schema details

---

**Last Updated**: 2026-09-13  
**Maintainer**: TravelRewards Team
