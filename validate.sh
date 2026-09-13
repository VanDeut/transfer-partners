#!/bin/bash
# Validation script for transfer-partners.json
# Ensures schema compliance and data quality

set -e

FILE="transfer-partners.json"
ERRORS=0
WARNINGS=0

echo "🔍 Validating $FILE..."
echo ""

# Check file exists
if [ ! -f "$FILE" ]; then
  echo "❌ Error: $FILE not found"
  exit 1
fi

# Check valid JSON
if ! jq . "$FILE" > /dev/null 2>&1; then
  echo "❌ Error: Invalid JSON syntax"
  exit 1
fi
echo "✓ Valid JSON syntax"

# Check required root fields
echo "Checking root schema..."
MISSING_ROOT=$(jq 'select(.schema_version == null or .last_generated == null or .transfers == null)' "$FILE")
if [ -n "$MISSING_ROOT" ]; then
  echo "❌ Error: Missing required root fields (schema_version, last_generated, transfers)"
  ((ERRORS++))
else
  echo "✓ Root object has required fields"
fi

# Check transfers array
TRANSFER_COUNT=$(jq '.transfers | length' "$FILE")
echo "✓ Found $TRANSFER_COUNT transfer records"

# Validate each transfer object
echo ""
echo "Validating transfer records..."
INVALID_TRANSFERS=$(jq -r '.transfers[] | select(.from_program == null or .to_program == null or .ratio == null or .category == null or .last_updated == null) | "\(.from_program) → \(.to_program)"' "$FILE")

if [ -n "$INVALID_TRANSFERS" ]; then
  echo "❌ Error: Transfers with missing required fields:"
  echo "$INVALID_TRANSFERS"
  ((ERRORS++))
else
  echo "✓ All transfers have required fields"
fi

# Validate categories
echo ""
echo "Checking category values..."
INVALID_CATEGORIES=$(jq -r '.transfers[] | select(.category != "airline" and .category != "hotel") | "\(.from_program) → \(.to_program): \(.category)"' "$FILE")

if [ -n "$INVALID_CATEGORIES" ]; then
  echo "❌ Error: Invalid category values (must be 'airline' or 'hotel'):"
  echo "$INVALID_CATEGORIES"
  ((ERRORS++))
else
  echo "✓ All categories are valid"
fi

# Validate ratio values
echo ""
echo "Checking ratio values..."
ZERO_RATIOS=$(jq -r '.transfers[] | select(.ratio <= 0) | "\(.from_program) → \(.to_program): \(.ratio)"' "$FILE")

if [ -n "$ZERO_RATIOS" ]; then
  echo "⚠ Warning: Ratios should be > 0:"
  echo "$ZERO_RATIOS"
  ((WARNINGS++))
fi

HIGH_RATIOS=$(jq -r '.transfers[] | select(.ratio > 5) | "\(.from_program) → \(.to_program): \(.ratio)"' "$FILE")

if [ -n "$HIGH_RATIOS" ]; then
  echo "⚠ Warning: Unusually high ratios (>5):"
  echo "$HIGH_RATIOS"
  ((WARNINGS++))
else
  echo "✓ Ratio values are reasonable"
fi

# Check for orphaned promo dates
echo ""
echo "Checking promotional offers..."
ORPHANED_PROMOS=$(jq -r '.transfers[] | select((.promo_bonus_pct != null and .promo_expires == null) or (.promo_bonus_pct == null and .promo_expires != null)) | "\(.from_program) → \(.to_program)"' "$FILE")

if [ -n "$ORPHANED_PROMOS" ]; then
  echo "⚠ Warning: Promo bonus % and expiry should both be set or both be null:"
  echo "$ORPHANED_PROMOS"
  ((WARNINGS++))
else
  echo "✓ Promotional offers are complete"
fi

# Check for expired promos
echo ""
echo "Checking for expired promos..."
CURRENT_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
EXPIRED_PROMOS=$(jq -r ".transfers[] | select(.promo_expires != null and .promo_expires < \"$CURRENT_DATE\") | \"\(.from_program) → \(.to_program) (expired: \(.promo_expires))\"" "$FILE")

if [ -n "$EXPIRED_PROMOS" ]; then
  echo "⚠ Warning: Found expired promotional offers (should be removed):"
  echo "$EXPIRED_PROMOS"
  ((WARNINGS++))
else
  echo "✓ No expired promotional offers found"
fi

# Check last_updated dates
echo ""
echo "Checking data freshness..."
THIRTY_DAYS_AGO=$(date -u -v-30d +'%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -d '30 days ago' +'%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo "")

if [ -n "$THIRTY_DAYS_AGO" ]; then
  STALE_COUNT=$(jq --arg cutoff "$THIRTY_DAYS_AGO" '[.transfers[] | select(.last_updated < $cutoff)] | length' "$FILE")

  if [ "$STALE_COUNT" -gt 0 ]; then
    echo "⚠ Warning: $STALE_COUNT transfers not updated in >30 days (should re-verify)"
    ((WARNINGS++))
  else
    echo "✓ All transfers recently verified"
  fi
else
  echo "⊘ Skipped (date calculation unavailable on this system)"
fi

# Summary statistics
echo ""
echo "📊 Summary Statistics:"
AIRLINE_COUNT=$(jq '[.transfers[] | select(.category == "airline")] | length' "$FILE")
HOTEL_COUNT=$(jq '[.transfers[] | select(.category == "hotel")] | length' "$FILE")
PROMO_COUNT=$(jq '[.transfers[] | select(.promo_bonus_pct != null)] | length' "$FILE")

echo "  • Airline transfers: $AIRLINE_COUNT"
echo "  • Hotel transfers: $HOTEL_COUNT"
echo "  • Active promotions: $PROMO_COUNT"

# Final summary
echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo "✅ All checks passed!"
  exit 0
elif [ $ERRORS -eq 0 ]; then
  echo "⚠ Validation passed with $WARNINGS warning(s)"
  exit 0
else
  echo "❌ Validation failed with $ERRORS error(s)"
  exit 1
fi
