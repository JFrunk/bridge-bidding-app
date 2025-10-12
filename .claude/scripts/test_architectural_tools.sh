#!/bin/bash
# Test suite for architectural tooling
# Ensures trigger detection and compliance reporting work correctly

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "================================================================================"
echo "Testing Architectural Decision Tools"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

run_test() {
    test_count=$((test_count + 1))
    echo "Test $test_count: $1"
}

pass() {
    pass_count=$((pass_count + 1))
    echo -e "${GREEN}✓ PASS${NC}: $1"
    echo ""
}

fail() {
    fail_count=$((fail_count + 1))
    echo -e "${RED}✗ FAIL${NC}: $1"
    echo ""
}

# Test 1: Check scripts exist and are executable
run_test "Scripts exist and are executable"
if [ -x "$SCRIPT_DIR/check_architectural_triggers.py" ] && [ -x "$SCRIPT_DIR/architectural_compliance_report.py" ]; then
    pass "Both scripts are executable"
else
    fail "Scripts are not executable"
    echo "Run: chmod +x .claude/scripts/*.py"
fi

# Test 2: Trigger detection runs without errors
run_test "Trigger detection script runs"
if python3 "$SCRIPT_DIR/check_architectural_triggers.py" > /dev/null 2>&1; then
    exit_code=$?
    if [ $exit_code -eq 0 ] || [ $exit_code -eq 1 ] || [ $exit_code -eq 2 ]; then
        pass "Trigger detection returns valid exit code ($exit_code)"
    else
        fail "Trigger detection returned unexpected exit code: $exit_code"
    fi
else
    fail "Trigger detection script failed to run"
fi

# Test 3: Compliance report runs without errors
run_test "Compliance report script runs"
python3 "$SCRIPT_DIR/architectural_compliance_report.py" > /tmp/compliance_test.txt 2>&1
exit_code=$?
if [ $exit_code -eq 0 ] || [ $exit_code -eq 1 ] || [ $exit_code -eq 2 ]; then
    pass "Compliance report generated successfully (exit code: $exit_code)"
else
    fail "Compliance report returned unexpected exit code: $exit_code"
fi

# Test 4: Compliance report contains expected sections
run_test "Compliance report has expected content"
if grep -q "ARCHITECTURAL COMPLIANCE REPORT" /tmp/compliance_test.txt && \
   grep -q "SUMMARY" /tmp/compliance_test.txt && \
   grep -q "ARCHITECTURAL HEALTH SCORE" /tmp/compliance_test.txt; then
    pass "Report contains all expected sections"
else
    fail "Report is missing expected sections"
fi

# Test 5: HTML report generation
run_test "HTML report generation"
python3 "$SCRIPT_DIR/architectural_compliance_report.py" --html -o /tmp/compliance_test.html > /dev/null 2>&1
exit_code=$?
if [ $exit_code -eq 0 ] || [ $exit_code -eq 1 ] || [ $exit_code -eq 2 ]; then
    if [ -f /tmp/compliance_test.html ] && grep -q "<html>" /tmp/compliance_test.html; then
        pass "HTML report generated successfully"
    else
        fail "HTML report is invalid"
    fi
else
    fail "HTML report generation returned exit code: $exit_code"
fi

# Test 6: Baseline metrics file exists
run_test "Baseline metrics captured"
if [ -f "$SCRIPT_DIR/../baseline_metrics_2025-10-12.txt" ]; then
    pass "Baseline metrics file exists"
else
    fail "Baseline metrics file not found"
    echo "Run: python3 .claude/scripts/architectural_compliance_report.py --verbose > .claude/baseline_metrics_2025-10-12.txt"
fi

# Test 7: Framework document exists and is comprehensive
run_test "Framework document exists"
FRAMEWORK="$PROJECT_ROOT/.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md"
if [ -f "$FRAMEWORK" ]; then
    # Check for key sections
    if grep -q "Decision Authority Matrix" "$FRAMEWORK" && \
       grep -q "Worked Examples" "$FRAMEWORK" && \
       grep -q "TL;DR" "$FRAMEWORK"; then
        pass "Framework has all required sections"
    else
        fail "Framework is missing required sections"
    fi
else
    fail "Framework document not found"
fi

# Test 8: ADR directory structure
run_test "ADR directory structure"
ADR_DIR="$PROJECT_ROOT/docs/architecture/decisions"
if [ -d "$ADR_DIR" ] && \
   [ -f "$ADR_DIR/README.md" ] && \
   [ -f "$ADR_DIR/ADR-0000-use-architecture-decision-records.md" ]; then
    pass "ADR directory structure is correct"
else
    fail "ADR directory structure is incomplete"
fi

# Cleanup
rm -f /tmp/compliance_test.txt /tmp/compliance_test.html

# Summary
echo "================================================================================"
echo "Test Summary"
echo "================================================================================"
echo "Total Tests: $test_count"
echo -e "${GREEN}Passed: $pass_count${NC}"
if [ $fail_count -gt 0 ]; then
    echo -e "${RED}Failed: $fail_count${NC}"
else
    echo -e "${GREEN}Failed: 0${NC}"
fi
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    echo "Architectural decision tools are working correctly!"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please fix the failing tests before using the architectural decision system."
    exit 1
fi
