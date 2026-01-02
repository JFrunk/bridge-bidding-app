# ACBL SAYC Test Suite

**Created:** 2026-01-01
**Status:** Active
**Purpose:** Canonical test cases for validating SAYC bidding accuracy

## Overview

The ACBL SAYC Test Suite contains test cases derived from the official ACBL Standard American Yellow Card (SAYC) booklet. These tests serve as the authoritative reference for correct bidding behavior according to SAYC conventions.

## Location

```
backend/tests/acbl_sayc/
├── __init__.py              # Package documentation
├── run_acbl_tests.py        # Test runner script
├── test_opening_bids.py     # Opening bid tests
├── test_responses.py        # Response tests
├── test_rebids.py           # Rebid tests
├── test_notrump.py          # Notrump bidding and conventions
├── test_slam_bidding.py     # Slam conventions (Blackwood, etc.)
└── test_competitive.py      # Competitive bidding situations
```

## Running the Tests

### Run All ACBL Tests

```bash
cd backend
pytest tests/acbl_sayc/ -v
```

### Run Specific Category

```bash
# Opening bids only
pytest tests/acbl_sayc/test_opening_bids.py -v

# Notrump conventions only
pytest tests/acbl_sayc/test_notrump.py -v

# Competitive bidding only
pytest tests/acbl_sayc/test_competitive.py -v
```

### Using the Test Runner

```bash
cd backend/tests/acbl_sayc
python run_acbl_tests.py                    # Run all tests
python run_acbl_tests.py --category opening # Run opening bid tests
python run_acbl_tests.py --summary          # Show test coverage summary
```

## Test Categories

### 1. Opening Bids (`test_opening_bids.py`)

Tests for all opening bid situations per SAYC:

| Opening Bid | Requirements |
|-------------|--------------|
| 1NT | 15-17 HCP, balanced |
| 2NT | 20-21 HCP, balanced |
| 2♣ | 22+ HCP or 9+ tricks (artificial, forcing) |
| 2♦/2♥/2♠ | 5-11 HCP, good 6-card suit (weak) |
| 1♠/1♥ | 13+ points, 5+ card suit |
| 1♦/1♣ | 13+ points, 3+ card suit |
| 3-level | Preemptive, 7+ card suit, < opening values |

### 2. Responses (`test_responses.py`)

Tests for responding to partner's opening:

| Response | Requirements |
|----------|--------------|
| Raise (1♥→2♥) | 6-10 points, 3+ support |
| Limit Raise (1♥→3♥) | 10-12 points, 4+ support |
| 1-level new suit | 6+ points, 4+ cards |
| 2-level new suit | 10+ points, 4+ cards |
| 1NT response | 6-10 points, no fit, no major to bid |
| 2NT response | 13-15 points, balanced, forcing |

### 3. Rebids (`test_rebids.py`)

Tests for opener's and responder's second bid:

| Opener's Rebid | Requirements |
|----------------|--------------|
| Simple rebid | 13-16 points (minimum) |
| Jump rebid | 17-18 points (medium) |
| Jump to game | 19+ points (maximum) |
| 1NT rebid | 13-14 balanced |
| 2NT rebid | 18-19 balanced |

### 4. Notrump Bidding (`test_notrump.py`)

Tests for notrump-related conventions:

| Convention | Meaning |
|------------|---------|
| 2♣ Stayman | Asks for 4-card major |
| 2♦ Jacoby | Transfers to hearts |
| 2♥ Jacoby | Transfers to spades |
| 2NT | Invitational (8-9 HCP) |
| 3NT | To play (10-15 HCP) |
| 4NT | Quantitative slam invite |

### 5. Slam Bidding (`test_slam_bidding.py`)

Tests for slam conventions:

| Convention | Meaning |
|------------|---------|
| 4NT Blackwood | Asks for aces (5♣=0/4, 5♦=1, 5♥=2, 5♠=3) |
| 5NT | Asks for kings |
| 4♣ Gerber | Asks for aces over NT |
| Control bids | Shows first/second round control |

### 6. Competitive Bidding (`test_competitive.py`)

Tests for competitive situations:

| Action | Requirements |
|--------|--------------|
| Simple overcall | 8-16 points, good 5+ card suit |
| 1NT overcall | 15-18 HCP, balanced, stopper |
| Takeout double | Opening values, support for unbid suits |
| Negative double | Shows unbid major(s) |
| Michaels cuebid | 5-5 two-suiter |
| Unusual 2NT | 5-5 in lowest unbid suits |

## Test Structure

Each test includes:

1. **SAYC Reference**: Which section of the booklet the test is based on
2. **Hand Description**: Clear description of the hand being tested
3. **HCP Verification**: Assert statement confirming hand evaluation
4. **Expected Bid**: The canonical correct bid
5. **Alternative Bids**: Where applicable, other acceptable bids

### Example Test

```python
def test_1nt_minimum_15_hcp_4333(self):
    """SAYC Example: 15 HCP, 4-3-3-3 shape opens 1NT."""
    # ♠ AQ32 ♥ KJ5 ♦ Q43 ♣ K32
    # HCP: A(4)+Q(2)+K(3)+J(1)+Q(2)+K(3) = 15
    hand = make_hand("AQ32", "KJ5", "Q43", "K32")
    assert hand.hcp == 15
    assert hand.is_balanced
    bid, _ = get_opening_bid(hand)
    assert bid == "1NT", f"15 HCP balanced should open 1NT, got {bid}"
```

## Using Tests for Quality Assurance

### Before Making Bidding Changes

```bash
# Run ACBL tests as baseline
pytest tests/acbl_sayc/ -v > acbl_baseline.txt

# Make your changes

# Re-run and compare
pytest tests/acbl_sayc/ -v > acbl_after.txt
diff acbl_baseline.txt acbl_after.txt
```

### Regression Testing

Any failure in this test suite indicates a potential regression in SAYC compliance and should be investigated immediately.

### Adding New Tests

When adding tests to this suite:

1. Reference the specific SAYC booklet section
2. Use the `make_hand()` helper for clarity
3. Assert HCP/shape requirements before testing the bid
4. Include comments showing the exact hand
5. Explain why the bid is correct

## Test Count by Category

| Category | Approximate Test Count |
|----------|----------------------|
| Opening Bids | 20+ |
| Responses | 25+ |
| Rebids | 20+ |
| Notrump | 25+ |
| Slam Bidding | 15+ |
| Competitive | 30+ |
| **Total** | **~135+ test cases** |

## Relationship to Other Tests

| Test Suite | Purpose |
|------------|---------|
| `tests/acbl_sayc/` | Canonical SAYC validation (this suite) |
| `tests/unit/` | Internal module unit tests |
| `tests/integration/` | Cross-module integration |
| `tests/regression/` | Bug fix verification |
| `tests/scenarios/` | Specific bidding situations |

## Future Enhancements

- [ ] Add parametrized tests for hand variations
- [ ] Include vulnerability-dependent tests
- [ ] Add competitive interference variations
- [ ] Expert review and validation of edge cases
- [ ] Cross-reference with Bridge Baron/GIB for validation

## References

- [ACBL SAYC Booklet](https://www.acbl.org/learn_page/how-to-play-bridge/)
- [SAYC System Card (PDF)](https://web2.acbl.org/documentLibrary/play/SP3%20(for%20web).pdf)
- Project bidding engine: `backend/engine/bidding_engine.py`
