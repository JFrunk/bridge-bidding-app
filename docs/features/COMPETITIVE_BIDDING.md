# Competitive Bidding

**Status**: Complete
**Last Updated**: 2025-10-12

## Overview

This document covers all competitive bidding situations: overcalls, doubles (takeout and negative), and advancer bids. These occur when opponents have opened or bid.

## Takeout Doubles

### Requirements
- **HCP**: 12+ HCP (opening hand strength)
- **Distribution**: Support for all unbid suits
  - Typically shortness (0-2 cards) in opponent's suit
  - 3+ cards in each unbid suit
- **Context**: After opponent opens at 1-level

### Purpose
- Ask partner to bid their best suit
- Shows opening strength with flexible distribution
- Alternative to overcalling when no clear suit

### Responses to Takeout Double (Advancer)
- **Bid your longest unbid suit** (forced if minimal hand)
- **Jump with 9-11 points** (invitational)
- **Cuebid opponent's suit** with 12+ points (game-forcing)
- **Pass rarely** (only with very long/strong trump stack for penalty)

### Implementation
- **File**: `backend/engine/competitive/doubles.py`
- **Tests**: `backend/tests/unit/test_negative_doubles.py`
- **Bug Fixes**: See `docs/.archive/bug-fixes/TAKEOUT_DOUBLE_FIX.md`

### Known Issues & Fixes
- **Fixed**: Takeout double now properly checks support for unbid suits
- **Fixed**: Negative double point requirements adjusted by level

## Negative Doubles

### Requirements
- **Purpose**: Show unbid major(s) after partner opens and RHO overcalls
- **HCP Requirements** (level-dependent):
  - At 1-level: 6+ HCP
  - At 2-level: 8+ HCP
  - At 3-level: 12+ HCP
- **Distribution**: Shows 4+ cards in unbid major(s)

### When to Use
```
Partner  RHO   You
1♣       1♥    X (negative double - shows spades, 6+ HCP)
1♦       1♠    X (negative double - shows hearts, 6+ HCP)
1♥       2♣    X (negative double - shows spades, 8+ HCP at 2-level)
```

### Opener's Rebids After Negative Double
- **Bid unbid major**: With 4+ cards in major shown by double
- **Raise doubler's implied suit**: With good support
- **Rebid own suit**: With 6+ cards and minimum
- **Bid notrump**: With stopper and balanced hand

### Implementation
- **File**: `backend/engine/competitive/doubles.py`
- **Tests**: `backend/tests/unit/test_negative_doubles.py`
- **Regression**: `backend/tests/regression/test_negative_double_rebid.py`

## Overcalls

### 1-Level Overcalls

#### Requirements
- **HCP**: 8-16 HCP
- **Suit**: 5+ card suit
- **Quality**: Good suit quality (2 of top 3 honors preferred)
- **Context**: After opponent opens

#### Purpose
- Show a good suit
- Compete for the contract
- Suggest a lead to partner

#### Example
```
Opponent  You
1♣        1♥ (shows 8-16 HCP, 5+ hearts, good suit)
```

### 2-Level Overcalls

#### Requirements
- **HCP**: 11-16 HCP (more than 1-level overcall)
- **Suit**: 5+ card suit
- **Quality**: Very good suit quality
- **Reason**: Higher level requires more strength

### Jump Overcalls (Weak)

#### Requirements
- **HCP**: 6-10 HCP
- **Suit**: 6+ card suit
- **Purpose**: Preemptive, take up bidding space
- **Example**: `1♣ - 2♠` (weak jump overcall)

### 1NT Overcall

#### Requirements
- **HCP**: 15-18 HCP
- **Distribution**: Balanced
- **Stopper**: Must have stopper in opponent's suit
- **Note**: Slightly stronger than 1NT opening (due to unfavorable position)

### 2NT Overcall

#### Requirements
- **HCP**: 19-20 HCP
- **Distribution**: Balanced
- **Stopper**: Must have stopper in opponent's suit

### Implementation
- **File**: `backend/engine/overcalls.py`
- **Tests**: `backend/tests/unit/test_overcalls.py`

## Advancer Bids (Partner of Overcaller)

Advancer is the partner of the player who overcalled or doubled.

### After Partner's Suit Overcall

#### Simple Raise
- **Requirements**: 8-10 support points, 3+ card support
- **Bidding**: Raise to 2-level (e.g., `1♣-(1♥)-P-2♥`)
- **Nature**: Constructive, somewhat invitational

#### Jump Raise (Two Types)

**Invitational Jump Raise**:
- **Requirements**: 11-12 support points, 3+ card support
- **Bidding**: Raise to 3-level (e.g., `1♣-(1♥)-P-3♥`)
- **Nature**: Invitational to game

**Preemptive Jump Raise**:
- **Requirements**: 5-8 support points, 4+ card support
- **Bidding**: Also to 3-level but with weaker hand
- **Purpose**: Obstruct opponents
- **Context-dependent**: Based on vulnerability and hand type

#### Cuebid
- **Requirements**: 12+ points, interest in game
- **Bidding**: Bid opponent's suit (e.g., `1♣-(1♥)-P-2♣`)
- **Forcing**: Yes, asks overcaller to describe hand

#### New Suit
- **Requirements**: 8+ points, 5+ card suit
- **Nature**: Constructive, non-forcing
- **Purpose**: Suggest alternative strain

#### Notrump Bids
- **1NT**: 8-10 HCP, balanced, stopper in opponent's suit
- **2NT**: 11-12 HCP, balanced, stopper, invitational
- **3NT**: 13+ HCP, balanced, stopper, to play

### After Partner's Takeout Double

#### Minimum Response
- **Requirements**: 0-8 HCP
- **Bidding**: Bid longest suit at cheapest level (forced)
- **Not forcing**: Shows weak hand

#### Jump Response
- **Requirements**: 9-11 HCP
- **Bidding**: Jump in longest suit
- **Nature**: Invitational

#### Cuebid
- **Requirements**: 12+ HCP
- **Bidding**: Bid opponent's suit
- **Forcing**: Game-forcing, asks for doubler's best suit

#### Pass (for Penalty)
- **Requirements**: Length and strength in opponent's suit
- **Rare**: Only with 5+ card trump stack with honors
- **Purpose**: Convert takeout double to penalty double

### After Partner's 1NT Overcall

Treat similarly to responses to 1NT opening:
- Can use Stayman (2♣)
- Can use Jacoby transfers
- Can pass, invite, or bid game

### Implementation
- **File**: `backend/engine/advancer_bids.py`
- **Tests**: Multiple scenario tests

## Strategy Guidelines

### When to Compete
- **Favorable vulnerability**: More aggressive
- **Unfavorable vulnerability**: More conservative
- **Part-score situations**: Compete more actively
- **Game situations**: Be more cautious

### Balancing
- **4th seat**: Can compete with slightly less (law of total tricks)
- **Direct seat**: Full requirements needed

### Preemptive Philosophy
- **"Rule of 2 and 3"**:
  - Vulnerable: Within 2 tricks of contract
  - Non-vulnerable: Within 3 tricks of contract

## Common Mistakes to Avoid

1. **Overcalling light**: Overcalls promise values and suit quality
2. **Takeout double without support**: Must have support for unbid suits
3. **Forgetting point requirements**: Negative doubles need more HCP at higher levels
4. **Wrong cuebid meaning**: As advancer, cuebid is game-forcing
5. **Penalty passing takeout doubles**: Rare, only with very strong trump holding

## Related Topics

### Forcing vs. Non-Forcing
- **Cuebid by advancer**: Always forcing
- **New suit by advancer**: Non-forcing (constructive)
- **Simple raises**: Non-forcing
- **Response to takeout double**: Not forcing (unless cuebid)

### Defensive Bidding Philosophy
- Compete actively for part-scores
- Be cautious at 3-level
- When in doubt, defend

## Bug Fixes & Improvements

### Major Fixes Applied
1. **Takeout Double Suit Detection** (Fixed 2025-10-10)
   - Now correctly identifies unbid suits
   - Properly checks support requirements
   - See: `docs/.archive/bug-fixes/TAKEOUT_DOUBLE_FIX.md`

2. **Negative Double Point Requirements** (Fixed 2025-10-11)
   - Level-adjusted point requirements implemented
   - 6+ at 1-level, 8+ at 2-level, 12+ at 3-level
   - See: `tests/regression/test_negative_double_rebid.py`

3. **Opener's Rebid After Negative Double** (Fixed 2025-10-11)
   - Opener now properly continues bidding
   - Correctly identifies partner's implied suit
   - Forcing to game logic fixed

## Testing

Competitive bidding tests located in:
- `backend/tests/unit/test_negative_doubles.py`
- `backend/tests/regression/test_takeout_double_fix.py`
- `backend/tests/regression/test_takeout_double_integration.py`
- `backend/tests/regression/test_negative_double_rebid.py`
- `backend/tests/scenarios/test_convention_scenarios.py`

## Related Documentation

- [Core Bidding](CORE_BIDDING.md)
- [Conventions](CONVENTIONS.md)
- [Architecture Overview](../architecture/OVERVIEW.md)

## Implementation Files

- `backend/engine/overcalls.py` - Overcall logic
- `backend/engine/competitive/doubles.py` - Double logic
- `backend/engine/advancer_bids.py` - Advancer bid logic
- `backend/engine/rebids.py` - Opener's rebids after competition

---

**Note**: This consolidated document replaces multiple smaller competitive bidding documents. Historical details in `.archive/`.
