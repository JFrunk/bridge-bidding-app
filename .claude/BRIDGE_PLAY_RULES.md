# Bridge Play Rules Reference

Quick reference for card play phase mechanics.

---

## ONLINE SINGLE-PLAYER MODE (This App)

**These rules override standard 4-player rules for this application.**

### User Position
- User ALWAYS plays as South
- User's partner is North (AI)
- Opponents are East and West (AI)

### Control Rules by Declaring Side

**When North-South is declaring (N or S is declarer):**
1. User controls BOTH South AND North (declarer + dummy)
2. User plays cards from both hands
3. Unlike offline bridge, dummy is NOT passive - user actively plays dummy's cards

**When East-West is declaring (E or W is declarer):**
1. User controls only South (as defender)
2. AI controls East, West, AND North
3. User makes opening lead if South is opening leader

### Opening Lead Rules
- Before opening lead, only the opening leader can act
- If opening leader is N or S, user makes the lead
- If opening leader is E or W, wait for AI

### Key Difference from Offline Bridge
In offline 4-player bridge, dummy is passive and declarer calls cards.
In this single-player app, when user is declaring side, user actively
clicks cards from BOTH their hand and dummy's hand.

---

## STANDARD BRIDGE RULES (Offline Reference)

*The following are standard bridge rules. Some do not apply to single-player online mode.*

## Phase Transition: Bidding → Play

1. Auction ends with three consecutive passes
2. **Declarer**: Player who first bid the trump suit (or NT) for the winning side
3. **Dummy**: Declarer's partner
4. **Opening Leader**: Defender to declarer's LEFT
5. Opening lead is made, THEN dummy is exposed

## Trick-Taking Rules

### The Process (13 tricks total)
1. **Lead**: One player plays first card
2. **Follow**: Other three play clockwise
3. **Must Follow Suit**: If you have a card of the led suit, you MUST play it
4. **If void**: May discard any card OR trump (if trump suit exists)
5. **Winner**: Highest trump played, OR highest card of led suit
6. **Next Lead**: Winner leads next trick

### Trump Suit (Suit Contracts Only)
- Any trump beats any non-trump (even 2♥ beats A♠ if hearts are trump)
- **Ruffing/Trumping**: Playing trump when void in led suit
- **Overtrumping**: Playing higher trump than previous trump
- Cannot trump if you can follow suit

### Notrump Contracts
- No trump suit exists
- Highest card of led suit wins
- No ruffing possible

## Declarer & Dummy Roles

### Declarer
- Controls BOTH hands (own + dummy)
- Calls which card to play from dummy
- Makes ALL play decisions

### Dummy
- Cards laid face-up after opening lead
- Arranged by suit (♠ ♥ ♦ ♣), ranked high to low
- Does NOT make play decisions
- May warn about irregularities (revokes)

### Defenders
- Each plays own hand independently
- Cannot see partner's cards
- Left-hand defender makes opening lead

## Critical Rules

### Revoke (Failure to Follow Suit)
A **revoke** occurs when a player fails to follow suit when able.
- Must be corrected if caught before trick is turned
- Penalties apply if established (after next lead)
- Dummy may warn declarer about potential revoke

### Card Once Played
- Once a card touches the table, it is played
- Declarer: Naming a card from dummy = played
- Defender: Card faced on table = played

## Scoring Basics

### Contract Made
Declarer wins at least: 6 + bid level tricks
- 3NT needs 9 tricks (6 + 3)
- 4♥ needs 10 tricks (6 + 4)
- 6♠ needs 12 tricks (6 + 6, small slam)

### Undertricks
Each trick short of contract = penalty points to defenders

### Overtricks
Extra tricks beyond contract = bonus points to declarer

## Quick Suit Rankings

**For bidding**: ♣ < ♦ < ♥ < ♠ < NT
**Within suit**: 2 < 3 < 4 < 5 < 6 < 7 < 8 < 9 < 10 < J < Q < K < A
