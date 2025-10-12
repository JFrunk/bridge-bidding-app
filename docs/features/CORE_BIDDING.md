# Core Bidding System

**Status**: Complete
**Last Updated**: 2025-10-12

## Overview

This document consolidates all core bidding functionality including opening bids, responses, and rebids following Standard American Yellow Card (SAYC) conventions.

## Opening Bids

### Notrump Openings

#### 1NT Opening
- **Requirements**: 15-17 HCP, balanced distribution
- **Distribution**: 4-3-3-3, 4-4-3-2, or 5-3-3-2 (5-card minor only)
- **Implementation**: `opening_bids.py` - `can_open_1nt()`

#### 2NT Opening
- **Requirements**: 20-21 HCP, balanced distribution
- **Distribution**: Same as 1NT
- **Implementation**: `opening_bids.py` - `can_open_2nt()`

#### 3NT Opening
- **Requirements**: 25-27 HCP, balanced distribution
- **Rare in practice but supported

### Strong Artificial Opening

#### 2♣ Opening
- **Requirements**: 22+ total points (HCP + distribution)
- **Forcing**: Game-forcing, partner must respond
- **Responses**:
  - 2♦ = negative (<8 HCP)
  - Any other bid = 8+ HCP (positive)
- **Implementation**: `opening_bids.py` - `can_open_2_clubs()`

### Suit Openings

#### 1-Level Suit Openings (1♣, 1♦, 1♥, 1♠)
- **Requirements**: 13+ HCP
- **Distribution**:
  - Major: 5+ cards
  - Minor: 3+ cards (may open better 3-card minor)
- **Priority**: Longest suit, with majors preferred
- **Implementation**: `opening_bids.py` - `get_opening_bid()`

#### Weak Two Bids (2♦, 2♥, 2♠)
- **Requirements**: 5-11 HCP, 6-card suit
- **Purpose**: Preemptive
- **Implementation**: `opening_bids.py` via PreemptConvention

#### Preemptive Openings
- **3-level**: 6-10 HCP, 7-card suit
- **4-level**: 6-10 HCP, 8-card suit
- **Purpose**: Disrupt opponent bidding

## Responses to Partner's Opening

### Responses to 1NT Opening

#### Stayman Convention (2♣)
- **Purpose**: Ask opener for 4-card major
- **Requirements**: 8+ HCP, interest in major suit game
- **Responses**:
  - 2♦ = no 4-card major
  - 2♥ = 4+ hearts (may have spades too)
  - 2♠ = 4 spades, denies 4 hearts
- **Implementation**: `conventions/stayman.py`
- **Related File**: [conventions/STAYMAN.md](STAYMAN.md)

#### Jacoby Transfers (2♦, 2♥)
- **Purpose**: Transfer to major suit
- **Mechanism**:
  - 2♦ → requests 2♥ (shows 5+ hearts)
  - 2♥ → requests 2♠ (shows 5+ spades)
- **Super-accepts**: Opener jumps with 4-card fit and maximum
- **Implementation**: `conventions/jacoby.py`
- **Related File**: [conventions/JACOBY_TRANSFERS.md](JACOBY_TRANSFERS.md)

#### Direct Responses
- **Pass**: < 8 HCP
- **2♦/2♥/2♠**: Transfer bids (see above)
- **2NT**: 8-9 HCP, invitational, balanced
- **3NT**: 10+ HCP, game bid, balanced
- **3♣/3♦**: 10+ HCP, 6+ card minor, slam interest
- **4♥/4♠**: 6+ card suit, 10-15 HCP, to play

### Responses to Suit Openings

#### Simple Raises
- **Requirements**: 6-10 support points, 3+ card support
- **Bidding**: Raise to 2-level (e.g., 1♥ - 2♥)
- **Implementation**: `responses.py`

#### Limit Raises
- **Requirements**: 10-12 support points, 3+ card support
- **Bidding**: Jump raise to 3-level (e.g., 1♥ - 3♥)
- **Nature**: Invitational

#### Game Raises
- **Requirements**: 13+ support points, 4+ card support
- **Bidding**: Jump to game (e.g., 1♥ - 4♥)

#### New Suit Responses
- **1-level**: 6+ HCP, 4+ card suit, forcing one round
- **2-level**: 10+ HCP, 5+ card suit, forcing one round
- **Jump shift**: 17+ HCP, 5+ card suit, game-forcing

#### Notrump Responses
- **1NT**: 6-10 HCP, balanced, no fit, forcing one round
- **2NT**: 11-12 HCP, balanced, no fit, invitational
- **3NT**: 13-15 HCP, balanced, no fit, to play

### Responses to 2♣ Opening

#### 2♦ Negative
- **Requirements**: <8 HCP
- **Artificial**: Waiting bid, may have diamonds

#### Positive Responses
- **2♥, 2♠, 3♣, 3♦**: 8+ HCP, 5+ card suit
- **2NT**: 8+ HCP, balanced

## Opener's Rebids

### After 1-Level Opening

#### Minimum Rebids (13-15 points)
- **Same suit**: 6+ card suit
- **Support partner**: 3+ card support
- **New suit at 1-level**: 4+ cards, economical
- **1NT**: 12-14 HCP (too weak to open 1NT), balanced
- **New suit at 2-level**: 13+ HCP, unbalanced

#### Medium Rebids (16-18 points)
- **Jump in same suit**: 6+ card suit, invitational
- **Jump raise partner**: 4-card support, invitational
- **2NT**: 18-19 HCP, balanced, stoppers
- **Reverse**: 17+ HCP, 5+ in first suit, 4+ in second, forcing

#### Strong Rebids (19+ points)
- **Jump to game**: Self-sufficient hand
- **3NT**: 19-20 HCP, balanced
- **Jump shift**: 19+ HCP, forcing to game

### After 1NT Opening

#### After Stayman (2♣)
See Stayman convention documentation

#### After Jacoby Transfer
- **Basic acceptance**: Bid requested suit
- **Super-accept**: Jump with 4-card fit and maximum
- **After transfer completes**: Responder's rebids show strength

### After 2♣ Opening

#### After 2♦ Negative
- **2NT**: 22-24 HCP, balanced
- **Suit bid**: 5+ card suit, game-forcing

#### After Positive Response
- **Support**: 3+ card support
- **New suit**: Additional suit
- **NT**: Balanced hand

## Key Points for Implementation

### Point Counting
- **HCP**: A=4, K=3, Q=2, J=1
- **Distribution points** (in support of partner):
  - Void = 5 points
  - Singleton = 3 points
  - Doubleton = 1 point
- **Support points** = HCP + distribution points

### Forcing Bids
- New suit by responder at 1 or 2 level = forcing one round
- Jump shifts = forcing to game
- 2♣ opening = forcing to game
- Reverse bids = forcing one round

### Non-Forcing Bids
- 1NT response to major = semi-forcing (opener should bid again unless minimum with balanced hand)
- Raises of partner's suit = not forcing
- Rebids of own suit = not forcing

## Testing

Core bidding tests located in:
- `backend/tests/unit/test_opening_bids.py`
- `backend/tests/unit/test_responses.py`
- `backend/tests/unit/test_stayman.py`
- `backend/tests/unit/test_jacoby_transfers.py`

## Related Documentation

- [Competitive Bidding](COMPETITIVE_BIDDING.md)
- [Conventions](CONVENTIONS.md)
- [Card Play](CARD_PLAY.md)
- [Architecture Overview](../architecture/OVERVIEW.md)

## Implementation Files

- `backend/engine/opening_bids.py` - All opening bid logic
- `backend/engine/responses.py` - Response logic
- `backend/engine/rebids.py` - Opener's rebid logic
- `backend/engine/conventions/stayman.py` - Stayman convention
- `backend/engine/conventions/jacoby.py` - Jacoby transfers

---

**Note**: This consolidated document replaces multiple smaller feature documents. See `.archive/` for historical documentation.
