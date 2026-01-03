# V2 Priority Tier Architecture

**Last Updated:** 2026-01-03

## Overview

The V2 Schema Engine uses a 4-tier priority hierarchy based on bidding "physics" - the fundamental principle that certain bid types always take precedence over others. This ensures consistent, predictable bid selection across all auction contexts.

## The 4-Tier Model

### TIER I (800-999): Artificial & Systemic - "Code Words"

Bids that alter the meaning of the auction or convey artificial agreements.

| Priority Range | Convention Type | Examples |
|----------------|-----------------|----------|
| 950-959 | RKCB/Blackwood | 4NT, responses (5♣/5♦/etc.) |
| 940-949 | Queen Ask | 5NT queen ask responses |
| 920-929 | Jacoby Rebid - Void | Showing void after Jacoby 2NT |
| 910-919 | Jacoby Rebid - Singleton | Showing singleton after Jacoby 2NT |
| 885-889 | Jacoby Rebid - Strong (18+) | Strong hand, slam interest |
| 880-884 | Jacoby Rebid - Extra (15-17) | Extra values, mild slam interest |
| 860-869 | Splinter | Jump to new suit showing shortness |
| 850-859 | Jacoby 2NT | Game-forcing major raise |
| 840-849 | Jacoby Rebid - Minimum | Fast Arrival (denies slam interest) |
| 830-839 | Texas Transfer | Jump transfers to major at 4-level |
| 820-829 | Jacoby Transfer | Transfers over 1NT |
| 810-819 | Stayman/Smolen | Major suit inquiries |
| 800-809 | Fourth Suit Forcing | FSF in constructive auctions |
| 795-805 | Negative Double | Takeout-style doubles of overcalls |
| 790-794 | Redouble | Strength-showing redoubles |

### TIER II (500-799): Constructive & Forcing - "Dialogue"

Natural bids that force the auction to continue.

| Priority Range | Bid Type | Examples |
|----------------|----------|----------|
| 750-759 | Reverses | Opener showing extra values |
| 700-720 | Jump Shift | Strong new suit response |
| 650-659 | Game Force | Forcing to game bids |
| 600-609 | 2/1 Response | New suit at 2-level (game forcing) |
| 580-589 | Cuebids | Michaels, competitive cuebids |
| 550-559 | Limit Raise | 10-12 HCP support |
| 520-529 | Free Bid | New suit after interference |

### TIER III (200-499): Invitational & Limit - "Proposals"

Bids that define hand limit and invite conclusion.

| Priority Range | Bid Type | Examples |
|----------------|----------|----------|
| 450-459 | Invitational | 2NT invitational, jump preference |
| 350-380 | Raise to 3NT | Direct game raises |
| 320-329 | Game Raise | 4M over 1M with support |
| 280-289 | Single Raise | 2M over 1M |
| 250-259 | Opener Rebid | NT rebids, suit rebids |
| 220-230 | Support Double | Double showing 3-card support |

### TIER IV (0-199): Terminal & Competitive - "Sign-offs"

Sign-offs and competitive bids.

| Priority Range | Bid Type | Examples |
|----------------|----------|----------|
| 170-179 | Minimum | Minimum rebids, preferences |
| 160-169 | Sign-off | Auction-ending bids |
| 140-149 | Simple Overcall | 1-level natural overcalls |
| 110-119 | Takeout Double | Standard takeout doubles |
| 100-109 | Balancing | Reopening bids in passout seat |
| 80-89 | Preempt | Weak 2s, 3-level preempts |
| 70-79 | Weak | Weak openings and responses |
| 20-29 | Pass | All pass actions |

## Fast Arrival Principle

The priority architecture enforces the Fast Arrival principle for Jacoby 2NT rebids:

**Higher-priority bids preserve bidding space for slam exploration:**
- Void showing (920+) - highest priority, shows best hand feature
- Singleton showing (910+) - next best feature
- Strong 18+ HCP (885+) - slam interest without shortness
- Extra 15-17 HCP (880+) - mild slam interest

**Lower-priority bids deny slam interest:**
- Minimum/Fast Arrival (840+) - jumps to game, denies extras

This ensures that when opener has a void, the void-showing bid will always be selected over the minimum rebid, even though both are legal responses.

## Implementation

### Auto-Refactoring Tool

The `tools/apply_priority_tiers.py` script normalizes priorities across all schema files:

```bash
# Dry run to see proposed changes
python3 tools/apply_priority_tiers.py --dry-run --verbose

# Apply changes
python3 tools/apply_priority_tiers.py --verbose
```

### Keyword Matching

The script uses an ordered list of keyword patterns for priority assignment:

```python
TIER_KEYWORDS = [
    ("rkcb", 950),
    ("blackwood", 950),
    ("jacoby_rebid_void", 920),      # Most specific first
    ("jacoby_rebid_singleton", 910),
    ("jacoby_rebid_strong", 885),
    ("jacoby_rebid_extra", 880),
    ("splinter", 860),
    ("jacoby_2nt", 850),
    ("jacoby_rebid_minimum", 840),   # Least specific last
    # ...
]
```

Keywords are checked in order, so more specific patterns match before general ones.

## Verification

After applying priority tiers, verify the ordering:

```python
# Test Jacoby rebid hierarchy
# Input: 1♥-2NT with various opener hands
# Expected outputs:
#   Void in clubs  → 3♣ (priority 920+)
#   Singleton      → 3♣ (priority 910+)
#   Strong 18+ HCP → 3♥ (priority 885+)
#   Minimum        → 4♥ (priority 840+, Fast Arrival)
```

## Files Modified

Priority normalization was applied to:
- `sayc_balancing.json` - 13/14 rules
- `sayc_doubles.json` - 10/13 rules
- `sayc_gf_raises.json` - 30/30 rules
- `sayc_interference.json` - 19/20 rules
- `sayc_openings.json` - 7/17 rules
- `sayc_overcalls.json` - 11/12 rules
- `sayc_penalty.json` - 4/8 rules
- `sayc_rebids.json` - 32/39 rules
- `sayc_responses.json` - 19/22 rules
- `sayc_rkcb.json` - 10/14 rules

**Total: 155 rules updated across 10 files**

## Related Documentation

- [V2_SCHEMA_EXPERT_BIDDING.md](V2_SCHEMA_EXPERT_BIDDING.md) - Expert bidding implementation
