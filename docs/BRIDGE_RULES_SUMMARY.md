# Bridge Rules - Quick Reference Summary

**For complete details, see [COMPLETE_BRIDGE_RULES.md](COMPLETE_BRIDGE_RULES.md)**

---

## Game Structure

### Players and Partnerships
- **4 Players**: North, East, South, West
- **2 Partnerships**: North-South vs East-West
- **Partners**: Sit opposite each other

### Objective
Win points by bidding and making contracts through trick-taking.

---

## Game Phases

### 1. DEALING
- Dealer shuffles and deals all 52 cards (13 per player)
- Players organize hands by suit

### 2. BIDDING (The Auction)
- **Goal**: Determine contract (tricks to win, trump suit)
- **Order**: Dealer starts, proceeds clockwise
- **Calls**: Bid, Pass, Double, Redouble
- **End**: Three consecutive passes
- **Result**: Final bid becomes contract; identifies declarer & dummy

### 3. PLAY
- **Opening Lead**: Defender left of declarer plays first card
- **Dummy Exposed**: After opening lead, dummy's cards laid face-up
- **Declarer Control**: Plays both own hand and dummy
- **Trick-Taking**: 13 tricks played, highest card or trump wins
- **Must Follow Suit**: Players must follow suit if able

### 4. SCORING
- **Contract Made**: Declarer scores points
- **Contract Defeated**: Defenders score penalty points
- **Bonuses**: Game, slam, overtricks
- **Penalties**: Undertricks (going down)

---

## Critical Phase Transitions

### Bidding → Play
1. ✅ Three passes end auction
2. ✅ Identify declarer (first to bid contract strain)
3. ✅ Identify dummy (declarer's partner)
4. ✅ Opening leader (left of declarer) leads
5. ✅ **THEN dummy exposes hand** (AFTER opening lead)

### During Play - Declarer/Dummy Rules
**DECLARER**:
- Controls BOTH hands (own and dummy's)
- Makes all play decisions
- When dummy is their turn: Declarer selects card from dummy

**DUMMY**:
- Lays cards face-up after opening lead
- Makes NO decisions
- Cannot comment or suggest plays
- Just a card holder controlled by declarer

### Play → Scoring
1. ✅ 13 tricks completed
2. ✅ Count tricks won
3. ✅ Compare to contract
4. ✅ Calculate score

---

## Hand Evaluation (SAYC)

### High Card Points (HCP)
- Ace = 4, King = 3, Queen = 2, Jack = 1
- Total deck = 40 HCP
- Average hand = 10 HCP

### Opening Strength
- **13+ HCP**: Opening hand
- **15-17 HCP**: 1NT opening (balanced)
- **22+ HCP**: 2♣ opening (strong conventional)

---

## Common Opening Bids (SAYC)

| Bid | Requirements |
|-----|--------------|
| 1♣ | 13+ HCP, 3+ clubs |
| 1♦ | 13+ HCP, 3+ diamonds |
| 1♥ | 13+ HCP, 5+ hearts |
| 1♠ | 13+ HCP, 5+ spades |
| 1NT | 15-17 HCP, balanced |
| 2♣ | 22+ HCP (strong, forcing) |
| 2♦/♥/♠ | 5-11 HCP, 6-card suit (weak) |

---

## Game Contracts

### What Makes Game (100+ points)
- **3NT** = 9 tricks (100 points)
- **4♥ or 4♠** = 10 tricks (120 points)
- **5♣ or 5♦** = 11 tricks (100 points)

### Slams
- **Small Slam (6-level)**: 12 tricks
- **Grand Slam (7-level)**: All 13 tricks

---

## Scoring Basics

### Contract Points

| Denomination | Points per Trick |
|--------------|------------------|
| ♣ (Clubs) | 20 |
| ♦ (Diamonds) | 20 |
| ♥ (Hearts) | 30 |
| ♠ (Spades) | 30 |
| NT (first/subsequent) | 40/30 |

### Bonuses (Duplicate)

| Type | Not Vulnerable | Vulnerable |
|------|----------------|------------|
| Part-score | +50 | +50 |
| Game | +300 | +500 |
| Small Slam | +500 | +750 |
| Grand Slam | +1000 | +1500 |

### Undertricks (Failed Contract)

**Undoubled**:
- Not Vulnerable: -50 per trick
- Vulnerable: -100 per trick

**Doubled** (first undertrick):
- Not Vulnerable: -100
- Vulnerable: -200

---

## Play Rules

### Must Follow Suit
- **MUST** play same suit as led if able
- If unable: May discard or trump

### Trump Power
- Any trump beats any non-trump
- Highest trump wins if multiple played
- Cannot trump if able to follow suit

### Winning Tricks
Trick won by:
1. **Highest trump** (if any trump played)
2. **Highest card in led suit** (if no trump)

### Next Lead
- Winner of trick leads next trick
- Continues until 13 tricks played

---

## Common Conventions (SAYC)

### Stayman (2♣ after 1NT)
- Asks opener for 4-card major
- Responses: 2♦ (no), 2♥ (hearts), 2♠ (spades)

### Jacoby Transfers
- 2♦ = Transfer to hearts (opener bids 2♥)
- 2♥ = Transfer to spades (opener bids 2♠)

### Blackwood (4NT)
- Asks for aces when exploring slam
- 5♣=0/4, 5♦=1, 5♥=2, 5♠=3 aces

---

## Quick Decision Guide

### As Dealer/Opener (13+ HCP)
1. Balanced 15-17? → 1NT
2. 5+ card major? → 1♥ or 1♠
3. 4+ diamonds? → 1♦
4. Otherwise → 1♣

### As Responder to 1NT
- 0-7 HCP → Pass
- 8+ HCP, want major → 2♣ (Stayman)
- 6+ HCP, 5+ hearts → 2♦ (Transfer)
- 6+ HCP, 5+ spades → 2♥ (Transfer)
- 10-15 HCP, balanced → 3NT

### As Declarer
- Plan: Count sure tricks and potential tricks
- Dummy first: After opening lead, see dummy
- Follow suit: Must follow suit if able
- Control both: Make decisions for both hands

---

## Implementation Checklist

### State Machine States
1. `DEALING` - Cards distributed
2. `BIDDING` - Auction in progress
3. `BIDDING_COMPLETE` - Contract set
4. `PLAY_STARTING` - Opening lead made
5. `PLAY_IN_PROGRESS` - Tricks being played
6. `PLAY_COMPLETE` - 13 tricks done
7. `SCORING` - Calculate score
8. `ROUND_COMPLETE` - Ready for next

### Key Validations
- ✅ Bid must be higher than previous
- ✅ Must follow suit if able
- ✅ Dummy revealed AFTER opening lead
- ✅ Only declarer controls dummy
- ✅ Correct score calculation based on vulnerability

---

**Full Rules**: [COMPLETE_BRIDGE_RULES.md](COMPLETE_BRIDGE_RULES.md)
**SAYC Details**: See COMPLETE_BRIDGE_RULES.md Section 6
**Scoring Tables**: See COMPLETE_BRIDGE_RULES.md Section 5
