# Bridge Bidding System - Complete Technical Documentation

**Last Updated:** October 29, 2025
**System:** Standard American Yellow Card (SAYC) Bidding System
**Target Audience:** Non-technical Bridge Experts

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Specialist Bidding Modules](#specialist-bidding-modules)
3. [Implemented Conventions](#implemented-conventions)
4. [Decision Routing Logic](#decision-routing-logic)
5. [Hand Evaluation Metrics](#hand-evaluation-metrics)
6. [HCP and Shape Requirements](#hcp-and-shape-requirements)
7. [Configuration Files](#configuration-files)

---

## System Overview

The Bridge Bidding System is a modular AI engine that makes bidding decisions using SAYC conventions. It processes auction history, hand features, and position information to recommend the appropriate bid.

### Architecture Overview

```
┌─────────────────────────────────────┐
│   API Request (Hand + Auction)      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Feature Extractor                 │
│   - Extracts HCP, Shape, Points     │
│   - Detects interference            │
│   - Identifies partnerships/roles   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Decision Engine                   │
│   - Routes to appropriate module    │
│   - Checks state (opening/comp/part)│
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Specialist Module                 │
│   - Evaluates bid appropriateness   │
│   - Returns bid + explanation       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Validation Pipeline               │
│   - Legality check                  │
│   - Shape/HCP requirement check     │
│   - Sanity checks                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Return: (Bid, Explanation)        │
└─────────────────────────────────────┘
```

---

## Specialist Bidding Modules

All specialist modules inherit from `ConventionModule` base class and implement the `evaluate()` method.

### 1. Opening Bids Module
**File:** `backend/engine/opening_bids.py`
**Responsibility:** Generate opening bids for hands that haven't been opened yet

**Handled Bids:**

| Bid Type | Requirements | Priority |
|----------|--------------|----------|
| 1NT | 15-17 HCP, balanced | High (checked first) |
| 2NT | 22-24 HCP, balanced | High |
| 3NT | 25-27 HCP, balanced | High |
| 3NT (Gambling) | 10-16 HCP, solid minor (7+ cards) | Special case |
| 2♣ (Strong) | 22+ total points or game-forcing | Medium |
| 1-level suit | 13+ points, 5+ card suit (or 3+ in minors) | Default |

**Logic Flow:**
1. Check for Gambling 3NT (solid minor)
2. Check for balanced NT openings (15-17, 22-24, 25-27 HCP ranges)
3. Check for Strong 2♣ (22+ points, non-balanced)
4. Fall back to 1-level suit openings
5. For 1-level: Prioritize majors, then diamonds, then clubs

**Suit Opening Priority:**
- 1♥: Hearts 5+ cards (preferred if both majors)
- 1♠: Spades 5+ cards
- 1♦: Diamonds (natural opening, 4+ cards minimum)
- 1♣: Clubs (better minor principle - open 1♣ with 4-4 minors)

---

### 2. Responses Module
**File:** `backend/engine/responses.py`
**Responsibility:** Generate responder's first bid after partner's opening

**Handled Situations:**

**Response to 1NT:**
- Stayman/Jacoby managed by convention modules (see below)
- Non-convention responses:
  - Pass: < 6 points
  - 2NT: 8-9 HCP invitational
  - 3NT: 10+ HCP to play
  - 2-level suit: 5+ card suit, 8-9 HCP
  - 3-level suit: 6+ card suit, 10+ HCP

**Response to Strong 2♣:**
- 2NT: Positive response (8+ HCP, balanced)
- 2♦: Artificial waiting response

**Response to Suit Openings:**
- Supports with 3+ cards:
  - Simple raise: 6-9 support points
  - Jump raise: 10-12 support points (invitational)
  - Game raise: 13+ support points
- New suit response (lower or higher):
  - First priority: Unbid majors with 4+ cards, 6+ HCP
  - Minimum level to suggest values
- 1NT response: 6-9 HCP, balanced, no support, no lower unbid suit

**Bid Adjustment Logic:**
- If suggested bid is illegal (too low), adjusts to next legal level
- Sanity check: Won't adjust more than 2 levels (prevents escalation)
- Falls back to Pass if no legal bid possible

---

### 3. Responder Rebid Module
**File:** `backend/engine/responder_rebids.py`
**Responsibility:** Responder's second and subsequent bids

**Key Logic:**
- Evaluates strength (minimum, invitational, game-forcing)
- Decides between supporting, bidding new suits, or NT
- Handles competitive auctions (interference from opponents)

---

### 4. Rebid Module (Opener's Second Bid)
**File:** `backend/engine/rebids.py`
**Responsibility:** Opener's rebids after receiving responder's first response

**Rebid Categories by Strength:**

| HCP Range | Bid Type | Examples |
|-----------|----------|----------|
| 13-15 | Minimum | Rebid suit, raise responder (simple), 1NT |
| 16-18 | Invitational | Jump raise, jump rebid, 2NT |
| 19+ | Game-forcing | Jump shift (new suit), jump to game |

**Reverse Bid Detection:**
- If opener bids a new suit that ranks HIGHER than opening suit at 2-level = REVERSE (forcing, shows 17+ HCP)
- Example: 1♦ - 1♠ - 2♥ is a reverse (hearts > diamonds)

**Rebid Priority:**
1. Support responder's major with 4+ cards (especially with fit-showing bids)
2. Rebid own suit (6+ cards) at appropriate level
3. Bid new suit (forcing if reverse)
4. Bid NT (balanced hands without fits)

---

### 5. Overcalls Module
**File:** `backend/engine/overcalls.py`
**Responsibility:** Generate overcalls when opponents have opened and partner hasn't bid

**Overcall Types:**

| Overcall Type | Requirements | Strength |
|---------------|--------------|----------|
| 1NT Direct | 15-18 HCP, balanced, stopper | Direct seat |
| 1NT Balancing | 12-15 HCP, balanced, stopper | Balancing seat |
| 2NT Direct | 19-20 HCP, balanced, stopper | Over 1-level openings |
| 3NT | 21-24 HCP, balanced, stopper | Direct; 18-21 HCP balancing |
| 1-level Suit | 8-16 HCP direct, 7+ balancing | Good suit quality required |
| 2-level Suit | 11-16 HCP direct, 10+ balancing | Very good suit quality |

**Stopper Requirement:**
- Stop opponent's suit: Ace, K-x, K-x-x, etc. (not singleton K)

**Suit Quality (SAYC):**
- 1-level: Some high cards in suit (A, K, Q, J, T)
- 2-level: Even stronger (typically 2 of top 3 honors)

**Balancing Seat Detection:**
- True if last 2 bids in auction were Pass (your pass would end auction)
- Allows lighter overcalls (7-10 HCP vs. 8-16 HCP)

---

### 6. Advancer Bids Module
**File:** `backend/engine/advancer_bids.py`
**Responsibility:** Bid as partner of overcaller (advancer role)

**Advancer Responses to Suit Overcall:**

| Response | Requirements | Points |
|----------|--------------|--------|
| Simple Raise | 3+ card support | 8-10 points |
| Jump Raise | 3+ card support | 11-12 points (invitational) OR 4+ support + weak hand (preemptive) |
| Cuebid | 12+ points, fit, game-forcing | Game-forcing |
| New Suit | 5+ card suit | 8+ points |
| NT Bid | Balanced, stopper | Based on NT requirements |
| Pass | Nothing else available | |

**Advancer Responses to NT Overcall:**
- Different logic based on NT level (1NT vs 2NT vs 3NT)

**Subsequent Bids:**
- After initial advance, adjust for competitive pressure
- Can re-advance in competitive auctions

---

## Implemented Conventions

### Convention Architecture

All conventions inherit from `ConventionModule` and implement:
- `evaluate(hand, features)` - Main evaluation method
- `get_constraints()` - Hand generation requirements (optional)

### 1. Stayman Convention (2♣)
**File:** `backend/engine/ai/conventions/stayman.py`

**When to Use:**
- Partner opens 1NT (15-17 HCP)
- You have 4+ card major (hearts or spades)
- Minimum: 8 HCP (or 7 HCP with both 4-card majors)

**How It Works:**
```
Responder: 1NT - 2♣ (Stayman - asking for 4-card major)

Opener responses:
- 2♦ = No 4-card major
- 2♥ = 4+ hearts
- 2♠ = 4+ spades
```

**Requirements:**
- HCP Range: 7-40
- Suit Length: 4+ card major
- Cannot have 5+ card major (use Jacoby instead)

**Responder Rebid After Opener's Response:**
- If fit found: Raise to appropriate level
- If no fit (2♦): Bid 2NT, 3NT, or own 5-card major

---

### 2. Jacoby Transfer Convention (2♦/2♥)
**File:** `backend/engine/ai/conventions/jacoby_transfers.py`

**When to Use:**
- Partner opens 1NT (15-17 HCP)
- You have 5+ card major (hearts or spades)
- Any point range (0-40 HCP)

**How It Works:**
```
2♦ = Transfer to hearts (shows 5+ hearts)
     Opener must bid 2♥
2♥ = Transfer to spades (shows 5+ spades)
     Opener must bid 2♠

After transfer:
- Pass: Invitational (0-7 HCP)
- Invite (raise, 2NT): 8-9 HCP
- Game bid: 10+ HCP
```

**Super-Accept:**
- If opener has maximum 1NT (17 HCP) + 4-card support
- Jump to 3-level of major instead of 2-level
- Shows maximum + fit

**Requirements:**
- Suit Length: 5+ in target major

---

### 3. Blackwood Convention (4NT / 5NT)
**File:** `backend/engine/ai/conventions/blackwood.py`

**When to Use:**
- Partnership has agreed on trump suit
- Slam interest (33+ combined points typical)
- Want to check for aces and kings

**How It Works:**
```
4NT = Ace-asking (Blackwood)

Responses (SAYC):
- 5♣ = 0 or 4 aces
- 5♦ = 1 ace
- 5♥ = 2 aces
- 5♠ = 3 aces

5NT = King-asking (after all aces shown)
- Same responses for kings
```

**Asker's Signoff:**
- 5-level of trump: Sign off (missing 2 aces)
- 6-level of trump: Small slam (missing 1 ace or none)
- 7-level of trump: Grand slam (all aces)

**Requirements:**
- HCP Range: 18+ (sufficient strength to ask)

**Blackwood Triggers:**
- Partner shows strong raise (3-level or higher)
- Clear trump suit agreement
- Not using 4NT as quantitative 1NT invite

---

### 4. Preempts Convention (Weak Twos, 3-level)
**File:** `backend/engine/ai/conventions/preempts.py`

**When to Use:**
- First to bid (opening position)
- Have a long suit (6, 7, or 8 cards)
- Limited strength (6-10 HCP)

**Preempt Levels:**

| Bid | Suit Length | HCP | Suit Quality | Notes |
|-----|-------------|-----|--------------|-------|
| 2♦/♥/♠ | 6 cards | 6-10 HCP | 2 of top 3 honors (A/K/Q) | Weak Two |
| 3♣/♦/♥/♠ | 7 cards | 6-10 HCP | 2+ honors | 3-level preempt |
| 4♣/♦/♥/♠ | 8 cards | 6-10 HCP | 2+ honors | 4-level preempt |

**SAYC Restrictions for Weak Twos:**
- NO void (too shapely)
- NO singleton ace (too strong)
- NO 4-card side major (might belong in that major)
- Typically 2 of top 3 honors in preempt suit

**Responder Options:**
- Pass: No interest
- Raise: With fit and invitational/game values
- 2NT: Feature ask (asks for highest side card)
- Bid game: With enough for game

---

### 5. Takeout Doubles (X)
**File:** `backend/engine/ai/conventions/takeout_doubles.py`

**When to Use:**
- Opponent has opened (any suit except NT usually)
- You have opening strength (12+ HCP)
- You have support for unbid suits (3+ cards each)
- You're short in opponent's suit (0-2 cards)

**Requirements:**

| Strength | Min HCP | Shortness | Support |
|----------|---------|-----------|---------|
| Minimum | 12 HCP | 0-2 cards in opponent suit | 3+ each unbid suit |
| Medium | 16 HCP | Can be 3 cards (unbalanced) | 3+ each unbid suit |
| Strong | 19+ HCP | 3+ in opponent suit (balanced hand) | Balanced preferred |

**Support Double (Special Case):**
- Opener showing support for responder's first suit
- After interference (opponent bid between opening and response)
- Shows 3-card support + opening strength

**Advancer's Responses (must bid):**
- 0-8 HCP: Minimum bid in best suit
- 9-11 HCP: Jump one level (invitational)
- 12+ HCP: Jump to game or cuebid (game-forcing)

---

### 6. Negative Doubles (X)
**File:** `backend/engine/ai/conventions/negative_doubles.py`

**When to Use:**
- Partner opened 1 of a suit
- Opponent interfered with an overcall
- You can't make a natural bid
- You have length in unbid suits (especially unbid majors)

**HCP Requirements by Level:**

| Overcall Level | Min HCP | Meaning |
|----------------|---------|---------|
| Through 2♠ | 6+ HCP | Responding values |
| 3-level | 8-10 HCP | Invitational values |
| 4-level+ | 12+ HCP | Game-forcing values |

**What Double Shows:**
- Length in unbid majors (at least 4 cards)
- Some values
- Competitive interest

**Responsive Double (Partner Doubled, RHO Raised):**
- Shows competitive values with no clear suit
- Asks partner to pick best action

**Example Sequences:**
```
1♦ - (1♠) - Dbl = Shows hearts (unbid major) + some values
1♦ - (1♠) - Pass - (Pass) - Dbl = Balancing negative double
```

---

### 7. Michaels Cuebid (2 of Opponent's Suit)
**File:** `backend/engine/ai/conventions/michaels_cuebid.py`

**When to Use:**
- Opponent has opened
- You have 5-5 or better in two specific suits
- Strength: 8-16 HCP

**What Shows What:**

| Opponent Opens | You Bid | Shows |
|----------------|---------|-------|
| 1♣ | 2♣ | 5+ hearts AND 5+ spades |
| 1♦ | 2♦ | 5+ hearts AND 5+ spades |
| 1♥ | 2♥ | 5+ spades AND 5+ minor (C or D) |
| 1♠ | 2♠ | 5+ hearts AND 5+ minor (C or D) |

**Partner's Responses:**
- Bid their best fit at appropriate level
- Bid 2NT to ask "which minor?" (when major shown with a minor)
- Cuebid with game values

**Strength Considerations:**
- Weak: 8-11 HCP (preemptive)
- Intermediate: 12-16 HCP (constructive)
- NOT 12-16 HCP (use Michaels or simple overcall)

---

### 8. Unusual 2NT
**File:** `backend/engine/ai/conventions/unusual_2nt.py`

**When to Use:**
- Opponent has opened
- You have 5-5 or better in both minors (clubs and diamonds)
- Strength: 6-11 HCP (weak) or 17+ HCP (strong)
- NOT 12-16 HCP (middle range)

**How It Works:**
```
1♥ (opponent) - 2NT (you)
Shows: 5+ clubs AND 5+ diamonds (any point range typically)
```

**Strength Patterns:**
- Weak: 6-11 HCP, preemptive
- Strong: 17+ HCP, too strong for simple bid
- Avoid: 12-16 HCP (use simple overcall or Michaels instead)

**Partner's Responses:**
- Bid their better minor (at minimum level with weak hand)
- Jump in minor with invitational values (10+ HCP)
- Bid 3NT with stoppers and strength
- Cuebid with game values and slam interest

---

### 9. Splinter Bids (Unusual Jump)
**File:** `backend/engine/ai/conventions/splinter_bids.py`

**When to Use:**
- Partner has opened 1 of a major
- You have 4+ card support for partner's major
- You have game-forcing values (12-15 support points)
- You have a singleton or void in a side suit

**How It Works:**
```
1♠ (partner) - 4♣ (you)
Shows:
- 4+ spade support
- Singleton/void in clubs
- Game-forcing values
- Slam interest
```

**Support Points Calculation:**
- HCP + distribution points for shortness
- Singleton: +2 points
- Void: +3 points (but be conservative)

**Requirements:**
- Support points: 12-15 (game-forcing minimum)
- HCP: Maximum 15 HCP (16+ suggests other methods)
- Support: 4+ cards in partner's major

**Opener's Evaluation After Splinter:**
- Good news: Working honors in side suits (encourages slam)
- Bad news: Wasted honors in splinter suit (discourages slam)
- With working values: Cuebid for slam exploration
- With wasted values: Sign off in game

---

### 10. Fourth Suit Forcing (FSF)
**File:** `backend/engine/ai/conventions/fourth_suit_forcing.py`

**When to Use:**
- Three suits already bid naturally
- You (responder) have game-forcing values (12+ HCP)
- You have no clear natural bid
- You need opener to further describe

**How It Works:**
```
1♦ - 1♥ - 1♠ - 2♣ (FSF)
2♣ is artificial and game-forcing, not showing clubs
```

**What FSF Asks Opener:**
- Show 3-card support for responder's suit
- Show stopper in fourth suit for NT
- Show extra length
- Show minimum vs. extra values

**Opener's Priority Responses:**
1. 3-card support for responder's major
2. Stopper in fourth suit for NT
3. Extra length in a previously bid suit
4. Raise fourth suit (rare)

**Requirements:**
- Game-forcing (12+ HCP)
- Three suits already bid by partnership

---

### 11. Negative Double (Balancing / Responsive)
**File:** `backend/engine/ai/conventions/negative_doubles.py`

**Responsive Double:**
- Partner made takeout double
- RHO raised opponent's suit
- You double to show competitive values
- Asks partner to pick action

---

## Decision Routing Logic

**File:** `backend/engine/ai/decision_engine.py`

The Decision Engine is a state-based router that determines which specialist module to use.

### Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│                   START: New auction state                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │  Has opener? (Anyone bid?) │
         └──┬─────────────────┬───────┘
            │                 │
            NO               YES
            │                 │
            ▼                 ▼
    ┌──────────────┐  ┌──────────────────────┐
    │ OPENING      │  │ Who is opener?       │
    │ SITUATION    │  └──┬─────────┬────┬───┘
    │              │     │         │    │
    │ 1. Check     │   ME    PARTNER OPP
    │    Preempts  │     │         │    │
    │    first     │     │         │    │
    │              │     │         │    │
    │ 2. Open      │     │         │    │
    │    normally  │     │         │    │
    └──────────────┘     │         │    │
                         ▼         ▼    ▼
                    ┌──────────────┐┌────┐
                    │ OPENER'S     ││COMP│
                    │ REBID        ││ ││ ││
                    │              ││││││
                    │ 1. Slam conv.││││││
                    │ 2. Rebid     ││││││
                    └──────────────┘└────┘

COMPETITIVE SITUATION (Opponent opened):
├─ My first bid: Check Michaels/Unusual 2NT → Overcall/Takeout Double
├─ Subsequent: Check balancing seat → Re-compete
└─ I'm advancer: Simple raise, cuebid, new suit

UNCONTESTED PARTNERSHIP AUCTION (Partner opened):
├─ My first response:
│  ├─ Check conventions (Stayman, Jacoby, Blackwood, Negative Double, etc.)
│  └─ Fall back to natural responses
└─ My second+ bid:
   ├─ Check conventions (Blackwood for slam, etc.)
   └─ Fall back to responder rebid
```

### State Transitions

**STATE 1: OPENING SITUATION**
- No one has bid yet (opening_bid = None)
- Check Preempts first (intercepts weak hands with long suits)
- Fall back to Opening Bids module

**STATE 2: COMPETITIVE SITUATION** 
- Opponent has opened (opener_relationship = 'Opponent')
- Check my previous bids:
  - First bid: Try Michaels → Unusual 2NT → Overcall → Takeout Double
  - Subsequent: Re-compete with overcall/double (balancing seat logic)
- Check advancer status (if partner overcalled/doubled)

**STATE 3: UNCONTESTED PARTNERSHIP AUCTION**
- Partner opened (opener_relationship = 'Partner')
- Check if I'm opener (opener_relationship = 'Me')
- Route based on auction progress:
  - First response: Conventions (Stayman/Jacoby) → Natural responses
  - Second+ response: Responder rebid
  - Slam conventions: Blackwood, Splinter, FSF (checked by priority)

### Convention Priority Checks

**When Partner Opens (Responder's First Bid):**
1. Check if we're in responder rebid position (second bid)
2. Check Slam conventions (Blackwood, Splinter, Fourth Suit Forcing)
3. Check Negative Double (if interference)
4. Check 1NT-specific conventions:
   - Jacoby Transfer (5+ major)
   - Stayman (4-card major, 8+ HCP)
5. Fall back to natural responses

**When Opponent Opens (Competitive):**
1. Michaels Cuebid (5-5 in two suits)
2. Unusual 2NT (5-5 in minors)
3. Takeout Double (12+ HCP, support for unbid)
4. Simple Overcall (good suit)

---

## Hand Evaluation Metrics

**File:** `backend/engine/hand.py` and `backend/engine/ai/feature_extractor.py`

### High Card Points (HCP)

Standard point count:
- Ace: 4 points
- King: 3 points
- Queen: 2 points
- Jack: 1 point
- Other cards: 0 points

### Distribution Points

Added to HCP for evaluative strength:
- 5-card suit: +1 point
- 6-card suit: +2 points
- 7+ card suit: +3 points

### Support Points (with fit)

When you have support for partner's suit:
- Singleton in side suit: +2 points
- Void in side suit: +3 points
- (Added on top of HCP)

### Total Points = HCP + Distribution Points

### Shape Classification

**Balanced Distribution:**
- No singleton or void
- At most one doubleton
- Typical shapes: 4-3-3-3, 4-4-3-2, 5-3-3-2 (depends on context)

**Unbalanced Distribution:**
- One or more singletons/voids
- Longer suits

### Feature Extraction

The feature extractor analyzes the auction and identifies:

1. **Auction Features:**
   - `opening_bid`: First bid made (e.g., "1♦")
   - `opener`: Position of opening bidder
   - `opener_relationship`: Me, Partner, or Opponent
   - `partner_last_bid`: Partner's most recent non-pass bid
   - `opener_last_bid`: Opener's most recent non-pass bid
   - `is_contested`: Both N-S and E-W have made bids (competition)
   - `interference`: Info about opponent bids between opening and my response

2. **Hand Features:**
   - `hcp`: High card points
   - `dist_points`: Distribution points
   - `total_points`: HCP + dist_points
   - `suit_lengths`: Cards in each suit
   - `is_balanced`: Whether hand is balanced

3. **Positional Features:**
   - `my_index`: My position (0-3 mapping to N/E/S/W)
   - `opener_index`: Opener's position
   - `positions`: List of position names

---

## HCP and Shape Requirements

### By Bid Type

#### No Trump Bids

| Bid | HCP | Shape | Notes |
|-----|-----|-------|-------|
| 1NT | 15-17 | Balanced | Responses: Stayman (4-card major), Jacoby (5-card major) |
| 2NT | 22-24 | Balanced | Game-forcing, rebid to 3NT or use conventions |
| 3NT | 25-27 | Balanced | To play, very strong |
| 1NT Overcall (direct) | 15-18 | Balanced + stopper | In opponent's suit |
| 1NT Overcall (balancing) | 12-15 | Balanced + stopper | More lenient |
| 2NT Overcall | 19-20 | Balanced + stopper | Over 1-level openings |
| 3NT Overcall | 21-24 | Balanced + stopper | Direct (or 18-21 balancing) |

#### Suit Openings

| Bid | Min HCP | Min Suit Length | Notes |
|-----|---------|-----------------|-------|
| 1♠/♥ | 13 | 5 cards | Natural opening |
| 1♦/♣ | 13 | 4 cards (minors can be 3 with 4-4) | Natural opening |
| 2♣ | 22 | Variable | Artificial, game-forcing |

#### Suit Overcalls

| Level | Min HCP (direct) | Min HCP (balancing) | Notes |
|-------|------------------|-------------------|-------|
| 1 | 8-16 | 7+ | Good suit required |
| 2 | 11-16 | 10+ | Very good suit required |

#### Preempts

| Bid | Min HCP | Suit Length | Quality |
|-----|---------|-------------|---------|
| 2 (weak) | 6-10 | 6 cards | 2 of top 3 honors |
| 3-level | 6-10 | 7 cards | 2+ honors |
| 4-level | 6-10 | 8 cards | 2+ honors |

#### Slam Conventions

| Convention | Min HCP | Requirements |
|------------|---------|--------------|
| Blackwood (4NT) | 18+ | Trump agreed, slam interest |
| Splinter | 12-15 support pts | 4+ support, singleton/void |
| Stayman/Jacoby | 7-8+ | Partner opened 1NT |

#### Takeout Double

| Position | HCP | Support | Shortness |
|----------|-----|---------|-----------|
| Direct | 12+ | 3+ each unbid suit | 0-2 in opponent suit |
| Balancing | 11+ | 3+ each unbid suit | 0-2 in opponent suit |

---

## Configuration Files

### convention_descriptions.json

**Location:** `backend/convention_descriptions.json`

This JSON file contains detailed descriptions of each convention for user education:

**Structure:**
```json
{
  "Convention Name": {
    "name": "Human-readable name",
    "background": "Historical context",
    "when_used": "Situations when to use",
    "how_it_works": "Mechanics of the convention",
    "responder_actions": "What responder does",
    "opener_actions": "What opener does"
  }
}
```

**Included Conventions:**
- Jacoby Transfer
- Stayman
- Opener Rebid
- Preemptive Bid (Weak Two)
- Blackwood
- Takeout Double
- Negative Double
- Michaels Cuebid
- Unusual 2NT
- Splinter Bid
- Fourth Suit Forcing

**Usage:** Provides educational content in the UI

---

### bidding_scenarios.json

**Location:** `backend/scenarios/bidding_scenarios.json`

Defines training scenarios with hand generation rules.

**Structure:**
```json
[
  {
    "name": "Scenario name",
    "level": "Essential/Intermediate/Advanced",
    "description": "What to practice",
    "setup": [
      {
        "position": "North/East/South/West",
        "constraints": { "hcp_range": [15, 17], "is_balanced": true },
        // OR
        "generate_for_convention": "Convention name"
      }
    ]
  }
]
```

**Parameters:**
- `hcp_range`: [min, max] HCP values
- `is_balanced`: true/false
- `suit_length_req`: Requires specific suit lengths
- `generate_for_convention`: Uses convention's hand generator

---

### sayc_rules.py

**Location:** `backend/engine/ai/sayc_rules.py`

Defines SAYC rule references with documentation links.

**Structure:**
```python
SAYC_RULES = {
    "rule_id": SAYCRule(
        id="rule_id",
        name="Rule name",
        description="What the rule says",
        url="Link to official documentation",
        category="Category"
    )
}
```

**Categories:**
- Opening Bids
- Responses
- Rebids
- Overcalls
- Conventions

---

## Summary

This bidding system implements SAYC conventions through:

1. **Modular Architecture:** Each bidding situation handled by dedicated module
2. **State-Based Routing:** Decision engine routes to appropriate specialist
3. **Feature Extraction:** Hand and auction analyzed for decision-making
4. **Convention Priority:** Checks conventions before natural bids
5. **Validation:** Every bid validated for legality before returning
6. **Educational Content:** Detailed explanations and convention descriptions

The system handles:
- Opening bids (natural and preempts)
- Responses to various openings
- Competitive bidding (overcalls, takeout doubles)
- Partnership bidding (conventions like Stayman, Jacoby, Blackwood)
- Slam exploration
- NT bidding and conventions
- Hand evaluation using HCP + distribution + support points

All logic is grounded in SAYC conventions with explicit HCP ranges, suit length requirements, and specific trigger conditions documented throughout the code.

