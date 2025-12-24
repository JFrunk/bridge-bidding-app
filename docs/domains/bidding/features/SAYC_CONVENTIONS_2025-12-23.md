# SAYC Convention Implementation - December 2025

## Overview

This update implements several missing SAYC (Standard American Yellow Card) conventions identified through a comprehensive review of the ACBL SAYC System Booklet.

## Conventions Implemented

### 1. Gerber Convention (4♣ over NT)

**File:** `backend/engine/ai/conventions/gerber.py`

Ace-asking convention used over notrump openings (alternative to Blackwood).

**Responses to 4♣:**
- 4♦ = 0 or 4 aces
- 4♥ = 1 ace
- 4♠ = 2 aces
- 4NT = 3 aces

**5♣ asks for kings** with the same step responses.

### 2. Grand Slam Force (5NT)

**File:** `backend/engine/ai/conventions/grand_slam_force.py`

Asks partner about top trump honors when considering a grand slam.

**Requirements:**
- Clear trump suit agreement
- Strong hand (16+ HCP)
- At least one top honor (A/K/Q) in trump suit

**Responses:**
- 7 of trump suit = 2 of top 3 honors (A/K/Q)
- 6 of trump suit = fewer than 2 top honors

### 3. Minor Suit Bust (2♠ Relay)

**File:** `backend/engine/ai/conventions/minor_suit_bust.py`

Weak hand escape mechanism over 1NT opening.

**Requirements:**
- Partner opened 1NT
- Weak hand (0-7 HCP)
- 6+ card minor suit
- No 4-card major

**Sequence:**
1. Responder bids 2♠ (artificial)
2. Opener bids 3♣ (forced)
3. Responder passes with clubs OR bids 3♦ with diamonds

### 4. 3NT Response to Major Opening

**File:** `backend/engine/responses.py`

Shows balanced game values without a major fit.

**Requirements:**
- Partner opened 1♥ or 1♠
- 15-17 HCP
- Balanced hand
- Exactly 2-card support (with 3+ would raise the major)

### 5. Feature-Showing (Weak Two 2NT Response)

**File:** `backend/engine/ai/conventions/preempts.py`

Changed from Ogust to SAYC Feature-showing system.

**Opener's responses to 2NT inquiry:**
- Rebid suit at 3-level = Minimum (5-8 HCP)
- Bid new suit = Maximum (9-11 HCP) with feature (A or K)
- Bid 3NT = Maximum without outside feature

### 6. 2NT Opening Range Correction

**File:** `backend/engine/opening_bids.py`

Fixed 2NT opening range from 22-24 to 20-21 HCP per SAYC standard.

## Quality Assurance

All changes tested with quality score baseline:
- **Legality:** 100%
- **Composite Score:** 94-96% (Grade A/B)
- **No regressions** in existing convention handling

## Files Modified

- `backend/engine/ai/conventions/gerber.py` (NEW)
- `backend/engine/ai/conventions/grand_slam_force.py` (NEW)
- `backend/engine/ai/conventions/minor_suit_bust.py` (NEW)
- `backend/engine/ai/conventions/preempts.py` (Modified)
- `backend/engine/ai/decision_engine.py` (Modified - routing)
- `backend/engine/bidding_engine.py` (Modified - imports)
- `backend/engine/opening_bids.py` (Modified - 2NT range)
- `backend/engine/responses.py` (Modified - 3NT response)
