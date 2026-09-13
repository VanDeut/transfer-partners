# Setup Guide

This document explains how to set up and maintain the transfer-partners repository.

## Overview

This repository maintains two data files consumed by the TravelRewards iOS app:
- **`transfer-partners.json`** — Transfer rates between credit card programs and airlines/hotels
- **`point-valuations.json`** — Point valuations (cents-per-point) for loyalty programs

Data is maintained manually with quarterly updates. No automated scraping.

## Files & Purposes

### Core Data
- **`transfer-partners.json`** — 54 transfer routes from Chase, Amex, Capital One, Citi
- **`point-valuations.json`** — 32 loyalty programs with valuations

### Documentation
- **`README.md`** — Schema documentation and data guide
- **`SETUP.md`** — This file (setup and updates)

### Tools
- **`validate.sh`** — Validates transfer-partners.json schema
- **`validate-valuations.sh`** — Validates point-valuations.json schema
- **`.gitignore`** — Standard git ignore patterns

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/VanDeut/transfer-partners.git
cd transfer-partners
```

### 2. Verify Setup

```bash
# Validate both data files
./validate.sh
./validate-valuations.sh
```

Expected output:
```
✅ All checks passed!
```

## Quarterly Update Process

Updates are manual, typically done every 3 months. Takes ~5-10 minutes.

### 1. Gather New Data

Visit the source websites and copy the data:

- **Transfer Partners**: https://roame.travel/transfer-partners-cheat-sheet
- **Point Valuations**: https://upgradedpoints.com/travel/points-and-miles-valuations/

### 2. Update the JSON Files

Replace the old data with new rates. You can:

**Option A: Direct JSON editing** (if comfortable with JSON)
- Open the files in your editor
- Update ratios and valuations
- Ensure proper formatting

**Option B: Copy-paste and regenerate** (recommended)
- Paste the data you copied into a message
- I'll regenerate the JSON files with proper schema

### 3. Validate Before Committing

```bash
# Always run validation after any changes
./validate.sh
./validate-valuations.sh
```

Both scripts must show `✅ All checks passed!`

### 4. Commit and Push

```bash
git add transfer-partners.json point-valuations.json
git commit -m "Quarterly update: transfer rates and valuations (Sept 2026)"
git push origin main
```

### Data Quality Checks

The validation scripts check:
- ✅ Valid JSON syntax
- ✅ Required fields present
- ✅ Reasonable ratio values
- ✅ No duplicate programs
- ✅ Category values correct

## Schema Documentation

Both files use consistent schemas:

### transfer-partners.json
```json
{
  "schema_version": "1.0.0",
  "last_generated": "2026-09-13T21:35:00.000000Z",
  "transfers": [
    {
      "from_program": "Chase Ultimate Rewards",
      "to_program": "Southwest Rapid Rewards",
      "ratio": 1.0,
      "category": "airline"
    }
  ]
}
```

### point-valuations.json
```json
{
  "schema_version": "1.0",
  "last_generated": "2026-09-13T21:30:00.000000Z",
  "valuations": [
    {
      "program": "Delta SkyMiles",
      "cents_per_point": 1.2,
      "category": "airline",
      "aliases": ["Delta"]
    }
  ]
}
```

See [README.md](README.md) for complete schema details.

## Troubleshooting

### JSON Validation Fails

```bash
# Check syntax
jq . transfer-partners.json

# If there are syntax errors, fix them and validate again
./validate.sh
```

### File Size Changed Unexpectedly

```bash
# Check what changed
git diff transfer-partners.json

# Revert if needed
git checkout transfer-partners.json
```

## Next Steps

1. Read [README.md](README.md) for complete schema documentation
2. Set a calendar reminder for quarterly updates (every 3 months)
3. Run validation before any commits

---

**Last Updated**: 2026-09-13  
**Maintenance**: Manual quarterly updates  
**Update Cycle**: Every 3 months
