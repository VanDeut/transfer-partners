#!/bin/bash
# Validation script for point-valuations.json
# Ensures schema compliance and data quality

set -e

FILE="point-valuations.json"
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
MISSING_ROOT=$(jq 'select(.schema_version == null or .last_generated == null or .default_cents_per_point == null or .valuations == null)' "$FILE")
if [ -n "$MISSING_ROOT" ]; then
  echo "❌ Error: Missing required root fields"
  ((ERRORS++))
else
  echo "✓ Root object has required fields"
fi

# Check valuations array
VALUATION_COUNT=$(jq '.valuations | length' "$FILE")
echo "✓ Found $VALUATION_COUNT valuation records"

# Validate each valuation object
echo ""
echo "Validating valuation records..."
INVALID_VALUATIONS=$(jq -r '.valuations[] | select(.program == null or .category == null or .cents_per_point == null or .aliases == null or .last_updated == null) | .program // "UNKNOWN"' "$FILE")

if [ -n "$INVALID_VALUATIONS" ]; then
  echo "❌ Error: Valuations with missing required fields:"
  echo "$INVALID_VALUATIONS"
  ((ERRORS++))
else
  echo "✓ All valuations have required fields"
fi

# Validate categories
echo ""
echo "Checking category values..."
INVALID_CATEGORIES=$(jq -r '.valuations[] | select(.category != "airline" and .category != "hotel" and .category != "car" and .category != "flexible") | .program' "$FILE")

if [ -n "$INVALID_CATEGORIES" ]; then
  echo "❌ Error: Invalid category values (must be airline, hotel, car, or flexible):"
  echo "$INVALID_CATEGORIES"
  ((ERRORS++))
else
  echo "✓ All categories are valid"
fi

# Validate valuation values
echo ""
echo "Checking valuation values..."
ZERO_OR_NEGATIVE=$(jq -r '.valuations[] | select(.cents_per_point <= 0) | .program' "$FILE")

if [ -n "$ZERO_OR_NEGATIVE" ]; then
  echo "⚠ Warning: Valuations should be > 0:"
  echo "$ZERO_OR_NEGATIVE"
  ((WARNINGS++))
fi

UNREALISTIC=$(jq -r '.valuations[] | select(.cents_per_point > 10) | .program' "$FILE")

if [ -n "$UNREALISTIC" ]; then
  echo "⚠ Warning: Unusually high valuations (>10¢):"
  echo "$UNREALISTIC"
  ((WARNINGS++))
else
  echo "✓ Valuation values are reasonable"
fi

# Check for duplicate programs
echo ""
echo "Checking for duplicates..."
DUPLICATES=$(jq -r '.valuations[] | .program' "$FILE" | sort | uniq -d)

if [ -n "$DUPLICATES" ]; then
  echo "⚠ Warning: Duplicate programs found:"
  echo "$DUPLICATES"
  ((WARNINGS++))
else
  echo "✓ No duplicate programs"
fi

# Summary statistics
echo ""
echo "📊 Summary Statistics:"
AIRLINE_COUNT=$(jq '[.valuations[] | select(.category == "airline")] | length' "$FILE")
HOTEL_COUNT=$(jq '[.valuations[] | select(.category == "hotel")] | length' "$FILE")
CAR_COUNT=$(jq '[.valuations[] | select(.category == "car")] | length' "$FILE")
FLEXIBLE_COUNT=$(jq '[.valuations[] | select(.category == "flexible")] | length' "$FILE")

echo "  • Airlines: $AIRLINE_COUNT"
echo "  • Hotels: $HOTEL_COUNT"
echo "  • Cars: $CAR_COUNT"
echo "  • Flexible rewards: $FLEXIBLE_COUNT"

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
