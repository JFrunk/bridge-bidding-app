# Revoke Handling in Bridge Bidding App
**Decision Date**: January 12, 2025
**Status**: PREVENTION (not detection)
**Reference**: [BRIDGE_PLAY_AUDIT_2025-01-12.md](BRIDGE_PLAY_AUDIT_2025-01-12.md)

---

## Decision

**The application PREVENTS revokes rather than detecting and penalizing them.**

---

## What is a Revoke?

According to official bridge rules ([COMPLETE_BRIDGE_RULES.md](COMPLETE_BRIDGE_RULES.md#revoke-failure-to-follow-suit)):

> **Revoke**: Playing a different suit when able to follow suit
> **Penalty**: If established (trick completed), transfer tricks to opponents

---

## Our Approach

### Prevention (Current Implementation) ✅

The application **prevents all revokes** by validating card plays BEFORE they are accepted.

**Implementation**: [play_engine.py:207-233](../backend/engine/play_engine.py#L207-L233)

```python
def is_legal_play(card: Card, hand: Hand, current_trick: List[Tuple[Card, str]],
                  trump_suit: Optional[str] = None) -> bool:
    """
    Check if card play is legal according to bridge rules

    Rules:
    1. Must follow suit if able
    2. If void in led suit, any card is legal
    """
    if card not in hand.cards:
        return False

    if not current_trick:
        # Leading - any card is legal
        return True

    led_suit = current_trick[0][0].suit

    # Check if we have cards in led suit
    cards_in_led_suit = [c for c in hand.cards if c.suit == led_suit]

    if cards_in_led_suit:
        # Must follow suit
        return card.suit == led_suit

    # Void in led suit - any card is legal
    return True
```

**Enforcement**: [server.py:604-614](../backend/server.py#L604-L614)

```python
# Validate legal play
is_legal = play_engine.is_legal_play(
    card, hand, current_play_state.current_trick,
    current_play_state.contract.trump_suit
)

if not is_legal:
    return jsonify({
        "legal": False,
        "error": "Must follow suit if able"
    }), 400
```

---

## Rationale

### Why Prevention Over Detection?

| Factor | Prevention ✅ | Detection |
|--------|--------------|-----------|
| **User Experience** | Better - can't make mistakes | Worse - get penalized after error |
| **Learning** | Better - learn correct plays | Punishing for learners |
| **Complexity** | Simpler | More complex |
| **Development Time** | 30 minutes (documentation) | 4-6 hours (implementation) |
| **Rules Compliance** | Equivalent (no revokes occur) | Technically more realistic |
| **UI Clarity** | Card either plays or doesn't | Need revoke indicators |

### Benefits of Prevention

1. **Better UX for Learning**
   - New players can't accidentally revoke
   - Immediate feedback (card won't play)
   - No penalties to understand

2. **Simpler Implementation**
   - No need to track revokes
   - No penalty calculations
   - No correction mechanism

3. **Same Result**
   - No revokes occur in either approach
   - End result is identical (legal plays only)

4. **Mobile-Friendly**
   - Touch interfaces: hard to distinguish "misclick" from "revoke"
   - Prevention avoids accidental touches

### Disadvantages

1. **Less Realistic**
   - Real bridge allows (then penalizes) revokes
   - Advanced players expect this

2. **Can't Test Revoke Penalties**
   - Educational limitation for tournament prep

---

## User-Facing Behavior

### What Users See

**When attempting to play wrong suit**:
- Card is **not accepted**
- Error message: **"Must follow suit if able"**
- Cards in correct suit remain clickable
- Other cards are disabled (grayed out)

**No penalties** because no revokes can occur.

---

## Future Enhancements (Optional)

### v2.0: Revoke Detection Mode (Optional)

For advanced users wanting tournament-realistic experience:

**Design**:
1. Add configuration: `allow_revokes: boolean`
2. Default: `false` (prevention)
3. Advanced mode: `true` (detection + penalties)

**Implementation** (if requested):
```python
def detect_revoke(trick_history, hands_history):
    """
    Detect if a revoke occurred in previous tricks
    Must check if player had card in led suit but played different suit
    """
    # Check each trick
    for trick in trick_history:
        led_suit = trick.led_suit
        for card, player in trick.cards:
            # Get player's hand at time of play
            hand_at_time = hands_history[player][trick_number]
            # Check if had led suit but played different
            if card.suit != led_suit:
                cards_in_led_suit = [c for c in hand_at_time if c.suit == led_suit]
                if cards_in_led_suit:
                    return (player, trick_number, card)  # REVOKE!
    return None

def calculate_revoke_penalty():
    """
    Official penalty: Transfer 2 tricks to opponents
    (or 1 trick if only 1 available to transfer)
    """
    return -2  # Adjust tricks_won
```

**Effort**: 4-6 hours
**Priority**: P3 (nice-to-have)

---

## Technical Details

### Code Locations

**Validation Logic**:
- [play_engine.py:207-233](../backend/engine/play_engine.py#L207-L233) - `is_legal_play()`

**Server Enforcement**:
- [server.py:604-614](../backend/server.py#L604-L614) - User play validation
- AI play doesn't need validation (AI always plays legally)

**Frontend**:
- Cards are disabled when illegal (CSS + onClick check)
- Error message shown on invalid play attempt

### Testing

**Existing Tests**:
- `tests/unit/test_play_engine.py` - Legal play validation
- `tests/integration/test_standalone_play.py` - Follow suit enforcement

**Coverage**: ✅ **GOOD** - Prevention is well-tested

---

## Comparison to Official Rules

### Official Bridge Rules

From [COMPLETE_BRIDGE_RULES.md](COMPLETE_BRIDGE_RULES.md#irregularities-and-penalties):

> **Revoke**: Playing a different suit when able to follow suit
> **Penalty**: If established (trick completed), transfer tricks
> **Correction**: If caught immediately, card may be corrected

### Our Implementation

✅ **Compliant** - No revokes occur (prevention achieves same result)

**Deviation**: Prevents rather than detects
**Impact**: **LOW** - End result identical (no illegal plays)

---

## User Documentation

### Help Text (to add to UI)

**"Why can't I play this card?"**

> You must follow suit if you have any cards in the suit that was led. This is a fundamental rule of bridge.
>
> In this game, illegal plays are prevented automatically to help you learn. If you can't play a card, it means you have cards in the led suit that you must play first.

**"What about revokes?"**

> In tournament bridge, playing the wrong suit (a "revoke") results in penalty points. This application prevents revokes from happening, so you don't need to worry about penalties. Focus on learning the correct plays!

---

## Decision Log

| Date | Decision | Rationale | Approved By |
|------|----------|-----------|-------------|
| 2025-01-12 | Use prevention (not detection) | Better UX, simpler, same result | Audit recommendation |
| | | | |

---

## Related Documents

- [COMPLETE_BRIDGE_RULES.md](COMPLETE_BRIDGE_RULES.md) - Full bridge rules
- [BRIDGE_PLAY_AUDIT_2025-01-12.md](BRIDGE_PLAY_AUDIT_2025-01-12.md) - Audit findings
- [BRIDGE_PLAY_FIX_CHECKLIST.md](BRIDGE_PLAY_FIX_CHECKLIST.md) - Fix checklist

---

**Status**: ✅ **DOCUMENTED AND IMPLEMENTED**
**Next Review**: v2.0 planning (if revoke detection requested by users)
