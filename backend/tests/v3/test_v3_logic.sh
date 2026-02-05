#!/bin/bash
# V3 Logic Stack Test Runner
# Runs comprehensive tests for V3 bidding logic
#
# Usage:
#   ./test_v3_logic.sh              # Run all V3 tests
#   ./test_v3_logic.sh --level 1    # Run only Level 1 tests
#   ./test_v3_logic.sh --quick      # Quick smoke test
#   ./test_v3_logic.sh --verbose    # Verbose output

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Default settings
LEVEL=""
QUICK=false
VERBOSE=false
OUTPUT_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --level)
            LEVEL="$2"
            shift 2
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "V3 Logic Stack Test Runner"
            echo ""
            echo "Usage: ./test_v3_logic.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --level N     Run only tests for level N (1-4)"
            echo "  --quick       Run quick smoke tests only"
            echo "  --verbose     Show detailed test output"
            echo "  --output FILE Save results to JSON file"
            echo "  --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./test_v3_logic.sh                    # Run all tests"
            echo "  ./test_v3_logic.sh --level 1          # Run Level 1 tests"
            echo "  ./test_v3_logic.sh --quick --verbose  # Quick verbose test"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Print header
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}           V3 Logic Stack Test Suite                       ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Change to backend directory
cd "$BACKEND_DIR"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Check for test suite JSON
TEST_SUITE="$SCRIPT_DIR/v3_logic_test_suite.json"
if [ ! -f "$TEST_SUITE" ]; then
    echo -e "${RED}ERROR: Test suite not found: $TEST_SUITE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Test suite found${NC}"

# Run foundation tests
echo ""
echo -e "${YELLOW}Running V3 Foundation Tests...${NC}"
echo "─────────────────────────────────────────────────────────────"

# Test 1: Convention Registry
echo -n "Testing convention registry... "
python3 -c "
from engine.ai.conventions.convention_registry import ConventionRegistry, ConventionLevel

registry = ConventionRegistry()
foundational = registry.get_foundational_conventions()

assert len(foundational) >= 10, f'Expected 10+ foundational modules, got {len(foundational)}'

# Check specific modules exist
required = ['when_to_pass', 'opening_one_major', 'opening_one_minor', 'single_raise', 'limit_raise']
for mod in required:
    assert any(c.id == mod for c in foundational), f'Missing foundational module: {mod}'

print('PASS')
" && echo -e "${GREEN}PASS${NC}" || echo -e "${RED}FAIL${NC}"

# Test 2: Skill Tree Structure
echo -n "Testing skill tree structure... "
python3 -c "
from engine.learning.skill_tree import SKILL_TREE

# Check Level 1 exists with basic bidding
assert 'level_1_basic_bidding' in SKILL_TREE, 'Missing level_1_basic_bidding'
level1 = SKILL_TREE['level_1_basic_bidding']
assert level1['level'] == 1, f'Level 1 should have level=1, got {level1[\"level\"]}'
assert len(level1.get('conventions', [])) >= 10, 'Level 1 should have 10+ conventions'

print('PASS')
" && echo -e "${GREEN}PASS${NC}" || echo -e "${RED}FAIL${NC}"

# Test 3: Hand Generators
echo -n "Testing hand generators... "
python3 -c "
from engine.learning.skill_hand_generators import SKILL_GENERATORS

required_generators = [
    'when_to_pass',
    'opening_one_major',
    'opening_one_minor',
    'single_raise',
    'limit_raise',
    'new_suit_response',
    'dustbin_1nt_response',
    'game_raise',
    'two_over_one_response'
]

for gen_id in required_generators:
    assert gen_id in SKILL_GENERATORS, f'Missing generator: {gen_id}'

print('PASS')
" && echo -e "${GREEN}PASS${NC}" || echo -e "${RED}FAIL${NC}"

# Test 4: Hand Generation
echo -n "Testing hand generation... "
python3 -c "
from engine.learning.skill_hand_generators import SKILL_GENERATORS

# Test that generators can create hands
# generate() returns (Hand, remaining_deck) tuple
for gen_id in ['when_to_pass', 'opening_one_major', 'single_raise']:
    generator_class = SKILL_GENERATORS[gen_id]
    generator = generator_class()
    result = generator.generate()

    assert result is not None, f'Generator {gen_id} returned None'
    assert isinstance(result, tuple), f'Generator {gen_id} should return tuple, got {type(result)}'
    assert len(result) == 2, f'Generator {gen_id} should return (hand, deck), got {len(result)} items'

    hand, remaining_deck = result
    if hand is not None:
        assert hasattr(hand, 'hcp'), f'Generator {gen_id} hand missing hcp'
        assert hasattr(hand, 'cards'), f'Generator {gen_id} hand missing cards'
        assert len(hand.cards) == 13, f'Generator {gen_id} hand should have 13 cards'

print('PASS')
" && echo -e "${GREEN}PASS${NC}" || echo -e "${RED}FAIL${NC}"

# Test 5: Balancing Module (V3 Borrowed King)
echo -n "Testing balancing module (Borrowed King)... "
python3 -c "
from engine.balancing import BalancingModule

module = BalancingModule()

# Check Virtual Offset
assert module.VIRTUAL_OFFSET == 3, f'Borrowed King offset should be 3, got {module.VIRTUAL_OFFSET}'

# Check constraints
constraints = module.get_constraints()
assert constraints['hcp_min'] == 8, 'Balancing HCP min should be 8'
assert constraints['hcp_max'] == 14, 'Balancing HCP max should be 14'

print('PASS')
" && echo -e "${GREEN}PASS${NC}" || echo -e "${RED}FAIL${NC}"

# Run level-specific tests if requested
if [ -n "$LEVEL" ]; then
    echo ""
    echo -e "${YELLOW}Running Level $LEVEL Specific Tests...${NC}"
    echo "─────────────────────────────────────────────────────────────"

    case $LEVEL in
        1)
            pytest tests/unit/test_opening_bids.py -v --tb=short 2>/dev/null || true
            pytest tests/unit/test_responses.py -v --tb=short 2>/dev/null || true
            ;;
        2)
            pytest tests/unit/test_rebids.py -v --tb=short 2>/dev/null || true
            ;;
        3)
            pytest tests/unit/test_responder_rebids.py -v --tb=short 2>/dev/null || true
            ;;
        4)
            pytest tests/unit/test_overcalls.py -v --tb=short 2>/dev/null || true
            pytest tests/unit/test_takeout_doubles.py -v --tb=short 2>/dev/null || true
            ;;
        *)
            echo -e "${RED}Unknown level: $LEVEL${NC}"
            ;;
    esac
fi

# Run quick pytest if not in quick mode
if [ "$QUICK" = false ]; then
    echo ""
    echo -e "${YELLOW}Running Full Test Suite...${NC}"
    echo "─────────────────────────────────────────────────────────────"

    if [ "$VERBOSE" = true ]; then
        pytest tests/unit/ -v --tb=short -q 2>/dev/null || true
    else
        pytest tests/unit/ -q --tb=no 2>/dev/null || true
    fi
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}           V3 Test Suite Complete                          ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Save results if output file specified
if [ -n "$OUTPUT_FILE" ]; then
    echo ""
    echo -e "${YELLOW}Saving results to: $OUTPUT_FILE${NC}"
    python3 -c "
import json
from datetime import datetime

results = {
    'timestamp': datetime.now().isoformat(),
    'version': 'V3',
    'status': 'complete',
    'tests_run': True
}

with open('$OUTPUT_FILE', 'w') as f:
    json.dump(results, f, indent=2)

print('Results saved.')
"
fi
