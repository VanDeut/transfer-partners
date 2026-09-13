# Setup Guide

This document explains how to set up and use the transfer-partners repository.

## Overview

This repository maintains `transfer-partners.json`, the authoritative data source for loyalty program transfer rates consumed by the TravelRewards Wallet iOS app.

## Files & Purposes

### Core Data
- **`transfer-partners.json`** — The main data file with all transfer rates and promotions
  - Consumed by iOS app (24-hour cache with bundled fallback)
  - Single source of truth for transfer rates

### Documentation
- **`README.md`** — Complete schema documentation and usage guide
- **`MAINTENANCE.md`** — Step-by-step instructions for updating rates and promos
- **`SETUP.md`** — This file (setup and getting started)

### Tools
- **`validate.sh`** — Validates JSON schema and data quality
- **`update_transfer.py`** — Programmatic update tool for rates/promos
- **`.gitignore`** — Standard git ignore patterns

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/transfer-partners.git
cd transfer-partners
```

### 2. Verify Setup

```bash
# Check that all required files exist
ls -la transfer-partners.json README.md MAINTENANCE.md validate.sh update_transfer.py

# Validate the data
./validate.sh
```

Expected output:
```
🔍 Validating transfer-partners.json...
✓ Valid JSON syntax
✓ Root object has required fields
✓ Found 59 transfer records
...
✅ All checks passed!
```

### 3. Review the Data

```bash
# See all transfers
jq '.transfers[] | {from: .from_program, to: .to_program, ratio: .ratio}' transfer-partners.json

# Count by category
jq '.transfers | group_by(.category) | map({category: .[0].category, count: length})' transfer-partners.json

# Find active promotions
jq '.transfers[] | select(.promo_bonus_pct != null)' transfer-partners.json | head -20
```

## Common Tasks

### Update a Transfer Rate

```bash
# Example: Chase-to-United changes from 1:1 to 0.8:1
python3 update_transfer.py "Chase" "United MileagePlus" 0.8

# Always validate after updates
./validate.sh
```

### Add a Promotional Bonus

```bash
# Example: AMEX announces +30% to British Airways through Oct 31
python3 update_transfer.py "American Express" "British Airways Executive Club" 1.0 \
  --promo 30 \
  --expires "2026-10-31T23:59:59Z" \
  --speed "Instant"

./validate.sh
```

### Commit Changes

```bash
git add transfer-partners.json
git commit -m "Update Chase-to-United ratio from 1:1 to 0.8:1"
git push origin main
```

## iOS App Integration

### Fetching the Data

The iOS app fetches from:
```
https://api.example.com/transfer-partners.json
```

### Caching Strategy

- **Cache TTL**: 24 hours
- **Fallback**: Bundled JSON (updated with each app release)
- **Verification**: App checks `last_generated` timestamp for freshness

### Example Swift Code

```swift
struct TransferPartnersManager {
    let remoteURL = URL(string: "https://api.example.com/transfer-partners.json")!
    let cacheDuration: TimeInterval = 86400 // 24 hours

    func fetchTransfers() async throws -> [Transfer] {
        // Check cache
        if let cached = getCachedTransfers(), !isCacheExpired() {
            return cached
        }

        // Fetch remote
        let data = try await URLSession.shared.data(from: remoteURL).0
        let bundle = try JSONDecoder().decode(TransferBundle.self, from: data)
        
        // Cache the result
        cacheTransfers(bundle.transfers)
        
        return bundle.transfers
    }

    func getFallbackTransfers() -> [Transfer] {
        // Bundled fallback
        guard let url = Bundle.main.url(forResource: "transfer-partners", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let bundle = try? JSONDecoder().decode(TransferBundle.self, from: data)
        else { return [] }
        return bundle.transfers
    }
}
```

## Development Workflow

### 1. Feature Branch

```bash
git checkout -b update/chase-rate-changes
```

### 2. Make Changes

```bash
# Add or update transfers
python3 update_transfer.py "Chase" "Delta SkyMiles" 0.75

# Validate
./validate.sh

# Review changes
git diff transfer-partners.json
```

### 3. Commit

```bash
git add transfer-partners.json
git commit -m "Update Chase-to-Delta ratio to 0.75 (effective 2026-09-14)"
```

### 4. Create Pull Request

```bash
git push origin update/chase-rate-changes
# Create PR on GitHub
```

### 5. Merge

After approval:
```bash
git checkout main
git merge update/chase-rate-changes
git push origin main
```

## Deployment

### Update iOS App Bundle

1. **Copy JSON to Xcode project**
   ```bash
   cp transfer-partners.json path/to/TravelRewardsWallet/Resources/
   ```

2. **Update app version** if major data changes:
   ```
   Version: 2.1.0
   Build: 45
   ```

3. **Commit and tag**
   ```bash
   git tag -a "v2.1.0" -m "Update with latest transfer rates"
   git push --tags
   ```

### Update Remote API

1. **Deploy to API server**
   ```bash
   scp transfer-partners.json api.example.com:/var/www/api/v1/
   ```

2. **Verify availability**
   ```bash
   curl https://api.example.com/transfer-partners.json | jq .schema_version
   ```

## Monitoring

### Set Up Alerts

Monitor these conditions:
```bash
# Stale data (>30 days)
./validate.sh | grep "should re-verify"

# Expired promos still in file
./validate.sh | grep "expired promotional"

# File size anomalies
ls -lh transfer-partners.json
```

### Schedule Regular Reviews

```
Weekly: Check Roame for new promos/rate changes
Monthly: Verify data accuracy
Quarterly: Review schema for improvements
```

## Troubleshooting

### JSON Validation Fails

```bash
# Check syntax
jq . transfer-partners.json

# Find the problematic transfer
jq '.transfers[] | select(.ratio <= 0)'

# Reload from backup if needed
git checkout HEAD transfer-partners.json
```

### Python Script Errors

```bash
# Check Python version (requires 3.6+)
python3 --version

# Run with debug
python3 -u update_transfer.py "From" "To" 1.0
```

### Merge Conflicts

```bash
# If two people update simultaneously
git status
# Edit transfer-partners.json to resolve
git add transfer-partners.json
git commit -m "Resolve merge conflict in transfer rates"
```

## Next Steps

1. Read [README.md](README.md) for complete schema documentation
2. Read [MAINTENANCE.md](MAINTENANCE.md) for detailed update procedures
3. Run `./validate.sh` to verify your setup
4. Try updating a transfer: `python3 update_transfer.py "Chase" "United" 1.0`

---

**Last Updated**: 2026-09-13  
**Version**: 1.0.0
