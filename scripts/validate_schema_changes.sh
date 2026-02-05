#!/bin/bash
#
# Schema Change Validation Script
#
# This script validates bidding schema changes by running targeted tests.
# It should be run:
# 1. Before committing changes to backend/engine/v2/schemas/*.json
# 2. As part of CI/CD pipeline
#
# Usage:
#   ./scripts/validate_schema_changes.sh
#   ./scripts/validate_schema_changes.sh --quick  # Skip generated hand tests
#
# Exit codes:
#   0 - All tests passed
#   1 - Tests failed
#   2 - No schema changes detected (skipped)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Schema Change Validation"
echo "========================================"

# Check if we're in a git repo and if schemas were modified
if git rev-parse --git-dir > /dev/null 2>&1; then
    SCHEMA_CHANGES=$(git diff --cached --name-only -- 'backend/engine/v2/schemas/*.json' 2>/dev/null || echo "")
    if [ -z "$SCHEMA_CHANGES" ]; then
        SCHEMA_CHANGES=$(git diff --name-only -- 'backend/engine/v2/schemas/*.json' 2>/dev/null || echo "")
    fi

    if [ -z "$SCHEMA_CHANGES" ]; then
        echo -e "${YELLOW}No schema changes detected, skipping validation${NC}"
        exit 0
    fi

    echo "Schema files changed:"
    echo "$SCHEMA_CHANGES" | sed 's/^/  /'
    echo ""
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Set V2 schema engine
export USE_V2_SCHEMA_ENGINE=true

echo "Running schema validation tests..."
echo ""

# Track failures
FAILURES=0

# 1. Schema Integrity Tests
echo "1/4: Schema Integrity Tests"
echo "----------------------------"
if python -m pytest tests/acbl_sayc/test_schema_conformance.py::TestSchemaIntegrity -v --tb=short 2>&1; then
    echo -e "${GREEN}✓ Schema integrity tests passed${NC}"
else
    echo -e "${RED}✗ Schema integrity tests FAILED${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 2. Opening Bid Edge Cases (most likely to catch bugs)
echo "2/4: Opening Bid Edge Case Tests"
echo "---------------------------------"
if python -m pytest tests/acbl_sayc/test_opening_bids_edge_cases.py -v --tb=short 2>&1; then
    echo -e "${GREEN}✓ Opening bid edge cases passed${NC}"
else
    echo -e "${RED}✗ Opening bid edge cases FAILED${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 3. User Feedback Regression Tests
echo "3/4: User Feedback Regression Tests"
echo "------------------------------------"
if python -m pytest tests/regression/test_user_feedback_regressions.py -v --tb=short 2>&1; then
    echo -e "${GREEN}✓ User feedback regressions passed${NC}"
else
    echo -e "${RED}✗ User feedback regressions FAILED${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 4. Opening Bid Conformance Tests (unless --quick)
if [ "$1" != "--quick" ]; then
    echo "4/4: Opening Bid Conformance Tests"
    echo "-----------------------------------"
    if python -m pytest tests/acbl_sayc/test_schema_conformance.py::TestOpeningBidConformance -v --tb=short 2>&1; then
        echo -e "${GREEN}✓ Opening bid conformance passed${NC}"
    else
        echo -e "${RED}✗ Opening bid conformance FAILED${NC}"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo "4/4: Skipped (--quick mode)"
fi
echo ""

# Summary
echo "========================================"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All schema validation tests PASSED${NC}"
    exit 0
else
    echo -e "${RED}$FAILURES test suite(s) FAILED${NC}"
    echo ""
    echo "Please fix the failing tests before committing."
    echo "Run individual test files for detailed output:"
    echo "  pytest tests/acbl_sayc/test_opening_bids_edge_cases.py -v"
    exit 1
fi
