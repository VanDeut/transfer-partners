# Transfer Partners JSON

A comprehensive, single-source-of-truth database of loyalty program transfer rates and promotional bonuses. This file is consumed by the TravelRewards Wallet iOS app (with 24-hour caching and bundled fallback).

## Overview

`transfer-partners.json` maintains current exchange rates for transferring points between:
- **Source Programs**: Flexible rewards credit card programs (Chase Sapphire, American Express, Citi ThankYou, Capital One, etc.)
- **Destination Programs**: Airline and hotel loyalty programs

The data is updated regularly as transfer rates change and promotional bonuses are announced.

## JSON Schema

### Root Object

```json
{
  "schema_version": "1.0.0",
  "last_generated": "2026-09-13T00:00:00Z",
  "last_data_source": "https://roame.travel/transfer-partners-cheat-sheet",
  "data_as_of": "2026-09-11T00:00:00Z",
  "transfers": [...]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Semantic version of the schema. Update when field structure changes. |
| `last_generated` | ISO8601 date | When the file was last generated/updated |
| `last_data_source` | string | URL of the authoritative data source |
| `data_as_of` | ISO8601 date | Effective date of the transfer rate data |
| `transfers` | array | Array of transfer rate objects |

### Transfer Object

```json
{
  "from_program": "American Express",
  "to_program": "British Airways Executive Club",
  "ratio": 1.0,
  "category": "airline",
  "promo_bonus_pct": 30,
  "promo_expires": "2026-09-11T23:59:59Z",
  "last_updated": "2026-09-11T00:00:00Z",
  "transfer_speed": "Instant"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from_program` | string | ✓ | Source flexible rewards program (Chase Sapphire, American Express, Citi ThankYou, Capital One, etc.) |
| `to_program` | string | ✓ | Destination loyalty program (airline or hotel) |
| `ratio` | number | ✓ | Exchange rate. `1.0` = 1:1, `1.25` = 1:1.25 bonus ratio, `0.8` = 4:5 ratio |
| `category` | string | ✓ | Program category: `"airline"` or `"hotel"` |
| `promo_bonus_pct` | number | ✗ | Percentage bonus if promotional rate active (e.g., 30 = +30% bonus) |
| `promo_expires` | ISO8601 date | ✗ | Expiration date/time of promotional bonus |
| `last_updated` | ISO8601 date | ✓ | When this transfer rate was last verified |
| `transfer_speed` | string | ✓ | Expected transfer time (e.g., "Instant", "~1 day", "2-3 weeks") |

## Ratio Interpretation

The `ratio` field represents how many destination points you receive per source point transferred:

- `1.0` = 1:1 (1 source point → 1 destination point)
- `1.25` = 1:1.25 bonus (1 source point → 1.25 destination points)
- `0.8` = 4:5 ratio (5 source points → 4 destination points)
- `0.5` = 1:2 (1 source point → 0.5 destination points)

## Categories

- **airline**: Transfer to airline loyalty programs
- **hotel**: Transfer to hotel loyalty programs

## Data Maintenance

### When to Update

Update `transfer-partners.json` when:
1. Transfer rates change (e.g., Chase to United changes from 1:1 to 0.75:1)
2. New transfer partners are added
3. Promotional bonuses are announced or expire
4. Transfer speeds change
5. Programs are discontinued

### Update Process

1. **Verify the source**: Check https://roame.travel/transfer-partners-cheat-sheet or the official credit card issuer website
2. **Locate the transfer**: Search for the `from_program` + `to_program` combination
3. **Update or add**:
   - If exists: Update `ratio`, `promo_bonus_pct`, `promo_expires`, and `last_updated`
   - If new: Add complete transfer object to the `transfers` array
4. **Update timestamps**:
   - Set `last_updated` to today's date in ISO8601 format
   - Set `last_generated` in root object to today
   - Set `data_as_of` to the effective date of the rates
5. **Validate**: Run validation checks (see below)
6. **Commit**: Include rationale in commit message

### Validation

Before committing, validate the JSON:

```bash
# Basic JSON syntax check
jq . transfer-partners.json > /dev/null && echo "✓ Valid JSON"

# Verify schema compliance
jq '.transfers[] | select(.from_program == null or .to_program == null or .ratio == null or .category == null or .last_updated == null)' transfer-partners.json

# Count transfers by category
jq '.transfers | group_by(.category) | map({category: .[0].category, count: length})' transfer-partners.json

# Find promotional offers
jq '.transfers[] | select(.promo_bonus_pct != null) | {from: .from_program, to: .to_program, bonus: .promo_bonus_pct, expires: .promo_expires}' transfer-partners.json
```

## Sync Frequency

- **Automated checks**: Weekly against Roame transfer-partners-cheat-sheet
- **Manual verification**: Monthly review of active promotions
- **Crisis updates**: Immediately if major transfer rate changes are detected
- **Cache refresh**: iOS app refreshes every 24 hours with bundled fallback

## Data Quality Standards

1. **Accuracy**: All rates must be verified against authoritative source
2. **Completeness**: Include all major transfer corridors (>0.1% user traffic)
3. **Timeliness**: Promotional changes reflected within 24 hours of announcement
4. **Consistency**: Bidirectional transfers use identical rates (when applicable)
5. **No stale data**: Rates older than 30 days should be re-verified

## Example Usage

### iOS App Integration

```swift
// Fetch from remote with 24-hour cache
let transfers = try await fetchTransferPartners(
  url: "https://api.example.com/transfer-partners.json",
  cacheExpiry: 86400 // 24 hours
)

// Fallback to bundled JSON if network unavailable
let fallbackTransfers = try loadBundledTransfers()
```

### Filtering Examples

Find all American Express transfers:
```bash
jq '.transfers[] | select(.from_program == "American Express")' transfer-partners.json
```

Get best airline rates:
```bash
jq '.transfers[] | select(.category == "airline") | sort_by(-.ratio) | .[0:5]' transfer-partners.json
```

Find active promotions:
```bash
jq '.transfers[] | select(.promo_expires > now | todate)' transfer-partners.json
```

## Version History

### 1.0.0 (2026-09-13)
- Initial schema and transfer data
- Support for promotional bonuses
- Transfer speed tracking
- 50+ verified transfer corridors

## Credits

Data sourced from:
- [Roame Transfer Partners Cheat Sheet](https://roame.travel/transfer-partners-cheat-sheet)
- Official credit card issuer websites
- Community reporting (verified)

---

**Last Updated**: 2026-09-13  
**Last Data Source**: Roame Transfer Partners (2026-09-11)
