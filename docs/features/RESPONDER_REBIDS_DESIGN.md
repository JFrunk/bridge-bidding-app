# Responder's Rebids - Complete Design Document

**Status:** Design Phase
**Priority:** HIGH - Critical for complete auction sequences
**Date:** 2025-10-12

---

## Overview

This document defines complete logic for responder's second (and subsequent) bids after:
1. Opener makes their opening bid
2. Responder makes initial response
3. Opener rebids
4. **Responder must now make intelligent rebid**

---

## Current State Analysis

### What Exists (responses.py:282-352)
- ✅ 2♣ auction continuations (game-forcing)
- ✅ Basic point-based rebids (very generic)
- ⚠️ No auction context awareness
- ⚠️ No suit preference logic
- ⚠️ No forcing vs non-forcing intelligence

### Critical Gaps
1. ❌ Preference bids (choosing between opener's suits)
2. ❌ New suit rebids (forcing vs non-forcing)
3. ❌ Jump rebids to show extras
4. ❌ Support for opener's rebid suit
5. ❌ NT rebids with stoppers
6. ❌ Competitive rebids after interference
7. ❌ Checkback sequences (New Minor Forcing, XYZ)

---

## SAYC Responder Rebid Rules

### Rule 1: Minimum Rebids (6-9 points)
**Philosophy:** Sign off, don't encourage game

| Auction Example | Rebid | Meaning |
|----------------|-------|---------|
| 1♣-1♥-1♠-? | Pass | No fit, minimum |
| 1♣-1♥-1♠-? | 2♣ | Preference to clubs, 3+ clubs |
| 1♣-1♥-2♣-? | Pass | Minimum, 5+ clubs accepted |
| 1♣-1♥-1NT-? | Pass | Minimum, balanced acceptable |
| 1♣-1♥-2♦-? | 2♣ | Preference, probably longer clubs |

**Key Points:**
- Pass when comfortable with opener's rebid
- Give simple preference with 2-card support
- Rebid own 6+ card suit at 2-level
- Do NOT bid new suits (would be forcing)

### Rule 2: Invitational Rebids (10-12 points)
**Philosophy:** Invite game, but let opener decide

| Auction Example | Rebid | Meaning |
|----------------|-------|---------|
| 1♣-1♥-1♠-? | 2NT | 10-12 HCP, balanced, stoppers |
| 1♣-1♥-1♠-? | 3♠ | 10-12 pts, 3+ spades, invitational |
| 1♣-1♥-2♣-? | 3♣ | 10-12 pts, 3+ clubs, invitational |
| 1♣-1♥-1NT-? | 2NT | 10-12 HCP, balanced, invitational |
| 1♣-1♥-1♠-? | 3♥ | 10-12 pts, 6+ hearts, invitational |

**Key Points:**
- Jump to 3-level to invite
- 2NT shows balanced with stoppers
- Jump in own suit shows 6+ cards
- Jump raise of opener's suit shows 3+ support

### Rule 3: Game-Forcing Rebids (13+ points)
**Philosophy:** Ensure game is reached

| Auction Example | Rebid | Meaning |
|----------------|-------|---------|
| 1♣-1♥-1♠-? | 3NT | 13-15 HCP, balanced, stoppers |
| 1♣-1♥-1♠-? | 4♠ | 13+ pts, 3+ spades, game |
| 1♣-1♥-1♠-? | 4♥ | 13+ pts, 6+ hearts, game |
| 1♣-1♥-1♠-? | 3♣ | 13+ pts, 5+ clubs, forcing |
| 1♣-1♥-2♦-? | 2♠ | Fourth Suit Forcing (artificial) |

**Key Points:**
- Bid game directly when hand is clear
- New suit at 3-level is forcing
- Fourth suit is artificial game force
- 3NT with balanced 13-15 HCP

### Rule 4: Preference Bids
**When:** Opener shows two suits

**Logic:**
```
1♣ - 1♥ - 1♠ - ?

If 2+ spades AND 2+ clubs:
  - Choose based on LENGTH (prefer longer suit)
  - If equal, prefer FIRST suit (clubs)

Strength determines LEVEL:
  - 6-9 pts: Simple preference (2♣ or pass)
  - 10-12 pts: Jump preference (3♣ or 3♠)
  - 13+ pts: Game (4♠, 3NT, or 5♣)
```

**Examples:**
- 1♦-1♠-2♣-2♦ = Preference to diamonds, 6-9 pts, 3+ diamonds
- 1♦-1♠-2♣-3♦ = Invitational, 10-12 pts, 3+ diamonds
- 1♥-1♠-2♣-2♥ = Preference to hearts, 6-9 pts, 2+ hearts

### Rule 5: Fourth Suit Forcing (FSF)
**When:** Responder bids the only unbid suit

**Requirements:**
- 12+ HCP (game-forcing)
- No natural bid available
- Asking opener to describe hand further

**Examples:**
- 1♣-1♥-1♠-**2♦** = FSF (artificial, diamonds may not exist)
- 1♦-1♠-2♣-**2♥** = FSF (artificial)

**Responses to FSF:**
- Bid 3-card support for responder's first suit
- Bid NT with stopper in FSF suit
- Rebid 6+ card suit
- Raise FSF suit with 4+ cards (rare, but natural)

### Rule 6: Rebidding Own Suit
**Shows:** 6+ card suit (sometimes 5 good cards)

| Strength | Bid | Example |
|----------|-----|---------|
| 6-9 pts | Simple rebid (2-level) | 1♦-1♥-1NT-**2♥** |
| 10-12 pts | Jump rebid (3-level) | 1♦-1♥-1NT-**3♥** |
| 13+ pts | Game rebid (4-level) | 1♦-1♥-1NT-**4♥** |

**Special Case:** After 1NT rebid, responder's 2-level rebid is to play

### Rule 7: Notrump Rebids
**Requirements:**
- Balanced hand
- Stoppers in unbid suits
- Appropriate point range

| Auction | Rebid | Meaning |
|---------|-------|---------|
| 1♣-1♥-1♠-**1NT** | Illegal (already at 1NT level) |
| 1♣-1♥-1♠-**2NT** | 10-12 HCP, balanced, stoppers |
| 1♣-1♥-1♠-**3NT** | 13-15 HCP, balanced, stoppers |
| 1♣-1♥-2♣-**2NT** | 10-12 HCP, balanced |

---

## Implementation Strategy

### Phase 1: Core Responder Rebid Module

**File:** `backend/engine/responder_rebids.py`

**Structure:**
```python
class ResponderRebidModule(ConventionModule):
    """
    Handles responder's second bid after:
    1. Partner opened
    2. We responded
    3. Partner rebid
    4. Our turn again
    """

    def evaluate(self, hand, features):
        # Detect we are responder on our second+ bid
        # Get auction context
        # Route to appropriate handler
        pass

    def _classify_opener_rebid(self, opening_bid, opener_rebid):
        """
        Determine what opener showed:
        - Same suit (1♥-1♠-2♥)
        - Second suit (1♣-1♥-1♠)
        - Notrump (1♦-1♥-1NT)
        - Reverse (1♦-1♠-2♥)
        - Jump (1♣-1♥-3♣)
        """
        pass

    def _get_preference_bid(self, hand, opener_suit1, opener_suit2):
        """Choose between opener's two suits"""
        pass

    def _get_support_bid(self, hand, opener_rebid_suit):
        """Raise opener's rebid suit"""
        pass

    def _get_own_suit_rebid(self, hand, my_first_suit):
        """Rebid own suit with 6+ cards"""
        pass

    def _get_nt_rebid(self, hand):
        """Bid notrump with balanced hand"""
        pass

    def _get_new_suit_bid(self, hand, auction_context):
        """Bid new suit (may be FSF)"""
        pass
```

### Phase 2: Auction Context Detection

**Key Information Needed:**
1. What did I bid first? (my_first_response)
2. What did opener rebid? (opener_rebid)
3. Was it same suit, new suit, or NT?
4. What's my point range?
5. What suits do I have length in?

**Helper Functions:**
```python
def _count_suits_bid(self, auction_history):
    """Count how many different suits shown"""

def _identify_unbid_suit(self, suits_bid):
    """Find the fourth suit (for FSF)"""

def _is_forcing_situation(self, auction_context):
    """Determine if we're in a forcing auction"""
```

### Phase 3: Point-Range Based Actions

**Framework:**
```python
# Minimum (6-9 points)
if 6 <= hand.total_points <= 9:
    return self._minimum_rebid(hand, auction_context)

# Invitational (10-12 points)
elif 10 <= hand.total_points <= 12:
    return self._invitational_rebid(hand, auction_context)

# Game Forcing (13+ points)
elif hand.total_points >= 13:
    return self._game_forcing_rebid(hand, auction_context)
```

### Phase 4: Integration Points

**Where to Hook In:**
1. ✅ `responses.py:_get_responder_rebid()` - Already exists but needs rewrite
2. 🆕 `responder_rebids.py` - New comprehensive module
3. 🔄 `bidding_engine.py` - Register new module with correct priority

**Priority Order:**
```python
# In decision_engine.py or bidding_engine.py
modules = [
    # ... opening bids, responses ...

    # Responder's second bid (before general response catch-all)
    ResponderRebidModule(),  # NEW - priority 40

    # Conventions that apply to responder rebids
    FourthSuitForcingConvention(),  # priority 35 (higher priority)

    # ... other conventions ...
]
```

---

## Test Scenarios

### Test Suite 1: Minimum Rebids (6-9 points)
```python
# Test 1: Simple preference
hand = "♠AJ5 ♥Q874 ♦K32 ♣852"  # 9 HCP
auction = "1♣ - 1♥ - 1♠ - ?"
expected = "2♣"  # Preference to clubs (3 cards vs 3 spades)

# Test 2: Pass with fit
hand = "♠K74 ♥QJ862 ♦952 ♣83"  # 7 HCP
auction = "1♦ - 1♥ - 2♥ - ?"
expected = "Pass"  # Minimum, happy with fit

# Test 3: Rebid own suit
hand = "♠AJ9874 ♥K5 ♦863 ♣72"  # 9 HCP
auction = "1♣ - 1♠ - 2♣ - ?"
expected = "2♠"  # 6-card suit, show length
```

### Test Suite 2: Invitational Rebids (10-12 points)
```python
# Test 4: Jump preference
hand = "♠KQ5 ♥AJ84 ♦K32 ♣852"  # 12 HCP
auction = "1♣ - 1♥ - 1♠ - ?"
expected = "3♠"  # Invitational raise with 3 spades

# Test 5: 2NT invitational
hand = "♠KJ5 ♥AQ84 ♦Q32 ♣J52"  # 11 HCP
auction = "1♣ - 1♥ - 1♠ - ?"
expected = "2NT"  # Balanced, stoppers, invitational

# Test 6: Jump in own suit
hand = "♠AQJ874 ♥K5 ♦Q63 ♣72"  # 12 HCP
auction = "1♦ - 1♠ - 2♦ - ?"
expected = "3♠"  # Invitational with 6-card suit
```

### Test Suite 3: Game-Forcing Rebids (13+ points)
```python
# Test 7: Direct game
hand = "♠KQ85 ♥AJ84 ♦K32 ♣A5"  # 15 HCP
auction = "1♣ - 1♥ - 1♠ - ?"
expected = "4♠"  # Game with 4 spades

# Test 8: 3NT
hand = "♠KJ5 ♥AQ84 ♦AQ3 ♣J52"  # 14 HCP
auction = "1♣ - 1♥ - 1♠ - ?"
expected = "3NT"  # Balanced, game values

# Test 9: Fourth Suit Forcing
hand = "♠AQJ5 ♥KQ84 ♦A32 ♣75"  # 14 HCP
auction = "1♣ - 1♥ - 1♠ - ?"
expected = "2♦"  # FSF - need more info from partner
```

### Test Suite 4: Complex Sequences
```python
# Test 10: After opener's reverse
hand = "♠K74 ♥QJ862 ♦K52 ♣83"  # 9 HCP
auction = "1♦ - 1♥ - 2♠ - ?"  # Reverse (forcing)
expected = "2NT" or "3♥"  # Must bid (forced), show weakness

# Test 11: After 1NT rebid
hand = "♠K74 ♥AQJ862 ♦52 ♣83"  # 10 HCP
auction = "1♦ - 1♥ - 1NT - ?"
expected = "3♥"  # Invitational with 6-card suit

# Test 12: After jump rebid
hand = "♠K74 ♥QJ86 ♦K52 ♣983"  # 9 HCP
auction = "1♦ - 1♥ - 3♦ - ?"  # Invitational jump
expected = "4♦" or "3NT"  # Accept invitation with maximum
```

---

## Success Criteria

### Functional Requirements
- ✅ All common auction patterns handled
- ✅ Correct forcing vs non-forcing logic
- ✅ Preference bids work correctly
- ✅ Fourth Suit Forcing integrated
- ✅ Point ranges respected

### Test Coverage
- ✅ 20+ test cases covering all scenarios
- ✅ Minimum/invitational/game-forcing paths
- ✅ All opener rebid types (same suit, new suit, NT, reverse, jump)
- ✅ Edge cases (forcing situations, competitive auctions)

### Integration
- ✅ No regression in existing tests (48/48 bidding tests still pass)
- ✅ Proper priority in convention registry
- ✅ Clean separation from initial response logic
- ✅ Works with existing conventions (Stayman, Jacoby, etc.)

---

## Implementation Plan

### Step 1: Create responder_rebids.py (Day 1)
- Basic module structure
- Auction context detection
- Opener rebid classification

### Step 2: Implement minimum rebids (Day 1-2)
- Pass logic
- Preference bids
- Own suit rebids

### Step 3: Implement invitational rebids (Day 2)
- Jump raises
- 2NT invitational
- Jump in own suit

### Step 4: Implement game-forcing rebids (Day 2-3)
- Direct games
- 3NT
- Fourth Suit Forcing integration
- New suit forcing logic

### Step 5: Write tests (Day 3)
- Create test_responder_rebids.py
- 20+ comprehensive test cases
- Edge case coverage

### Step 6: Integration (Day 3-4)
- Register module in decision engine
- Test with existing conventions
- Verify no regressions
- Run full test suite

### Step 7: Documentation (Day 4)
- Update CORE_BIDDING.md
- Add examples to CLAUDE.md
- Update PROJECT_STATUS.md

---

## Risk Mitigation

### Risk 1: Breaking Existing Tests
**Mitigation:**
- Run test suite after each step
- Use feature branch for development
- Backward compatibility checks

### Risk 2: Priority Conflicts with Other Modules
**Mitigation:**
- Careful priority assignment
- Test with all conventions enabled
- Clear detection of when module applies

### Risk 3: Complex Auction Logic
**Mitigation:**
- Start with simple cases
- Incremental complexity
- Extensive testing at each step

---

## References

**SAYC Documentation:**
- Bridge World Standard (BWS)
- ACBL SAYC booklet
- Standard bidding guides

**Existing Code:**
- `responses.py:282-352` - Current responder rebid logic
- `rebids.py` - Opener's rebid logic (parallel structure)
- `ai/conventions/fourth_suit_forcing.py` - FSF convention

---

**Status:** Design Complete ✅
**Next:** Begin Implementation (Step 1)
**Estimated Time:** 3-4 days
