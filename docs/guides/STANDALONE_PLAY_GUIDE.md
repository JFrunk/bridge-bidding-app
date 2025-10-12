# Standalone Play Module Guide

## Overview

The card play module is now **fully modular** and can be used independently of the bidding phase. This enables:

- ✅ **Fast testing** - Test play scenarios without manual bidding
- ✅ **Isolated development** - Work on play AI without touching bidding code
- ✅ **Flexible scenarios** - Create specific hand scenarios for testing
- ✅ **Better test coverage** - Write focused unit tests for play logic

---

## Quick Start Example

```python
from tests.play_test_helpers import create_test_deal, create_play_scenario, print_hand_diagram

# 1. Create a deal
deal = create_test_deal(
    north="♠AKQ2 ♥432 ♦KQJ ♣432",
    east="♠765 ♥765 ♦765 ♣7654",
    south="♠432 ♥AKQ ♦A32 ♣AKQ8",
    west="♠JT98 ♥JT98 ♦T98 ♣J9"
)

# 2. Create play scenario (no bidding required!)
play_state = create_play_scenario("3NT by S", deal, "NS")

# 3. Show hand diagram
print_hand_diagram(deal, play_state.contract)

# 4. Start playing
ai = SimplePlayAI()
card = ai.choose_card(play_state, play_state.next_to_play)
```

**Result:** You can now test card play without completing an auction!

---

## New Components

### 1. Factory Method: `PlayEngine.create_play_session()`

**Location:** [backend/engine/play_engine.py](backend/engine/play_engine.py)

Creates a `PlayState` ready for play without going through bidding.

```python
from engine.play_engine import PlayEngine, Contract

contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
vulnerability = {'ns': False, 'ew': False}

play_state = PlayEngine.create_play_session(contract, hands, vulnerability)
```

**Features:**
- Automatically determines opening leader (LHO of declarer)
- Initializes empty current trick
- Sets up trick tracking
- Ready to begin play immediately

---

### 2. Contract Parser: `parse_contract()`

**Location:** [backend/engine/contract_utils.py](backend/engine/contract_utils.py)

Parse contract strings into Contract objects.

```python
from engine.contract_utils import parse_contract

# Various formats supported
contract1 = parse_contract("3NT by S")           # Regular contract
contract2 = parse_contract("4♠X by N")           # Doubled
contract3 = parse_contract("7♥XX by W")          # Redoubled
```

**Supported formats:**
- `"<level><strain> by <declarer>"` - e.g., `"3NT by S"`
- `"<level><strain>X by <declarer>"` - e.g., `"4♠X by N"` (doubled)
- `"<level><strain>XX by <declarer>"` - e.g., `"7♥XX by W"` (redoubled)

**Validation:**
- Level: 1-7
- Strain: ♣, ♦, ♥, ♠, or NT
- Declarer: N, E, S, W
- Raises `ValueError` for invalid formats

---

### 3. Test Helpers

**Location:** [backend/tests/play_test_helpers.py](backend/tests/play_test_helpers.py)

#### `create_hand_from_string(hand_str)`

Create hands from readable strings:

```python
from tests.play_test_helpers import create_hand_from_string

hand = create_hand_from_string("♠AKQ32 ♥J54 ♦KQ3 ♣A2")
# Returns Hand object with 13 cards

# Void in a suit (represented by omitting the suit)
hand_void = create_hand_from_string("♠AKQJ ♦98765432 ♣A")  # Void in hearts
```

**Format:**
- Suits separated by spaces
- Suit symbol (♠, ♥, ♦, ♣) followed by ranks
- Ranks: A, K, Q, J, T, 9-2
- Must total exactly 13 cards

#### `create_test_deal(north, east, south, west)`

Create a complete deal (all 4 hands):

```python
deal = create_test_deal(
    north="♠AKQ ♥432 ♦KQJ2 ♣432",
    east="♠765 ♥765 ♦7654 ♣765",
    south="♠432 ♥AKQ ♦A32 ♣AKQ8",
    west="♠JT98 ♥JT98 ♦T98 ♣JT9"
)
# Returns: {'N': Hand, 'E': Hand, 'S': Hand, 'W': Hand}
```

#### `create_play_scenario(contract_str, hands, vulnerability)`

One-stop setup for play testing:

```python
play_state = create_play_scenario(
    contract_str="3NT by S",
    hands=deal,
    vulnerability="NS"  # "None", "NS", "EW", or "Both"
)
# Returns: PlayState ready to begin play
```

#### `print_hand_diagram(hands, contract)`

Visual debugging aid:

```python
print_hand_diagram(deal, contract)
```

**Output:**
```
Contract: 3NT by S

            North
            ♠ A K Q 2
            ♥ 4 3 2
            ♦ K Q J
            ♣ 4 3 2

   West                    East
  ♠ J T 9 8            ♠ 7 6 5
  ♥ J T 9 8            ♥ 7 6 5
  ♦ T 9 8              ♦ 7 6 5
  ♣ J 9                ♣ 7 6 5 4

            South
            ♠ 4 3 2
            ♥ A K Q
            ♦ A 3 2
            ♣ A K Q 8
```

#### `assert_play_result(play_state, expected_tricks, expected_made)`

Verify play outcomes:

```python
# After playing out 13 tricks
assert_play_result(
    play_state,
    expected_declarer_tricks=9,
    expected_made=True
)
```

---

## Testing Workflow

### Before (Required Full Bidding)

```python
# ❌ Old way - tedious
def test_3nt_play():
    # 1. Create hands
    # 2. Simulate entire auction
    # 3. Check for 3 passes
    # 4. Extract contract
    # 5. Finally start playing
    pass
```

### After (Direct Play Testing)

```python
# ✅ New way - fast and focused
def test_3nt_play():
    # 1. Create scenario directly
    deal = create_test_deal(...)
    play_state = create_play_scenario("3NT by S", deal)

    # 2. Test play immediately
    assert play_state.contract.level == 3
    # ... test logic
```

---

## Complete Test Examples

### Example 1: Basic Setup Test

```python
def test_create_3nt_scenario():
    """Verify we can create a 3NT contract without bidding"""

    deal = create_test_deal(
        north="♠AKQ ♥432 ♦KQJ2 ♣432",
        east="♠765 ♥765 ♦7654 ♣765",
        south="♠432 ♥AKQ ♦A32 ♣AKQ8",
        west="♠JT98 ♥JT98 ♦T98 ♣JT9"
    )

    play_state = create_play_scenario("3NT by S", deal, "None")

    assert play_state.contract.level == 3
    assert play_state.contract.strain == 'NT'
    assert play_state.contract.declarer == 'S'
    assert play_state.next_to_play == 'W'  # Opening leader
    assert play_state.dummy == 'N'  # Partner of South
```

### Example 2: Test One Trick

```python
def test_play_one_trick():
    """Test playing one complete trick"""

    deal = create_test_deal(
        north="♠AKQ ♥432 ♦KQJ2 ♣432",
        east="♠765 ♥765 ♦7654 ♣765",
        south="♠432 ♥AKQ ♦A32 ♣AKQ8",
        west="♠JT98 ♥JT98 ♦T98 ♣JT9"
    )

    play_state = create_play_scenario("3NT by S", deal)
    ai = SimplePlayAI()

    # West leads
    assert play_state.next_to_play == 'W'
    card = ai.choose_card(play_state, 'W')
    play_state.current_trick.append((card, 'W'))
    play_state.hands['W'].cards.remove(card)

    # Continue for North, East, South...
    # Determine winner
    winner = PlayEngine.determine_trick_winner(
        play_state.current_trick,
        play_state.contract.trump_suit
    )

    assert winner in ['N', 'E', 'S', 'W']
```

### Example 3: Test Legal Play Rules

```python
def test_must_follow_suit():
    """Test that players must follow suit if able"""

    deal = create_test_deal(
        north="♠AKQ ♥432 ♦KQJ2 ♣432",
        east="♠765 ♥765 ♦7654 ♣765",
        south="♠432 ♥AKQ ♦A32 ♣AKQ8",
        west="♠JT98 ♥JT98 ♦T98 ♣JT9"
    )

    play_state = create_play_scenario("3NT by S", deal)

    # Simulate West leading a spade
    lead_card = Card('J', '♠')
    play_state.current_trick.append((lead_card, 'W'))

    # North has spades, so must follow suit
    north_hand = play_state.hands['N']
    heart_card = Card('4', '♥')
    spade_card = Card('A', '♠')

    # Can't play heart when we have spades
    assert not PlayEngine.is_legal_play(
        heart_card, north_hand, play_state.current_trick, None
    )

    # Can play spade
    assert PlayEngine.is_legal_play(
        spade_card, north_hand, play_state.current_trick, None
    )
```

### Example 4: Test Scoring

```python
def test_3nt_scoring():
    """Test scoring without playing full hand"""

    contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
    vulnerability = {'ns': False, 'ew': False}

    # Making exactly 9 tricks
    score_result = PlayEngine.calculate_score(contract, 9, vulnerability)

    assert score_result['made'] is True
    assert score_result['overtricks'] == 0
    assert score_result['score'] == 400

    # Making 10 tricks (+1)
    score_result = PlayEngine.calculate_score(contract, 10, vulnerability)

    assert score_result['made'] is True
    assert score_result['overtricks'] == 1
    assert score_result['score'] == 430
```

---

## Running Tests

### Run the example script:

```bash
cd backend
PYTHONPATH=. python3 tests/test_standalone_play.py
```

**Output:**
```
============================================================
COMPLETE STANDALONE PLAY TEST EXAMPLE
============================================================

1. Creating test deal...
✓ Deal created

2. Creating play scenario: 3NT by South...
✓ Contract: 3NT by S
✓ Opening leader: W
✓ Dummy: N

3. Hand diagram:
[Shows visual diagram]

4. Verifying setup...
✓ All assertions passed

SUCCESS: Standalone play test completed!
```

### Run with pytest (if installed):

```bash
cd backend
pytest tests/test_standalone_play.py -v
```

---

## API Usage in Backend

The standalone play module can also be used via API endpoints.

### Start play with direct contract (new capability):

```python
POST /api/play/start
{
    "contract": "3NT by S",
    "hands": {
        "N": [...],
        "E": [...],
        "S": [...],
        "W": [...]
    },
    "vulnerability": "NS"
}
```

**Response:**
```json
{
    "session_id": "uuid",
    "contract": "3NT by S",
    "opening_leader": "W",
    "dummy": "N"
}
```

### Continue using existing endpoints:

- `POST /api/play-card` - User plays a card
- `POST /api/get-ai-play` - AI plays a card
- `GET /api/get-play-state` - Get current state
- `GET /api/complete-play` - Get final results

---

## File Organization

```
backend/
├── engine/
│   ├── play_engine.py           ✅ NEW: Factory method added
│   ├── contract_utils.py         ✅ NEW: Contract parsing utilities
│   ├── simple_play_ai.py         (existing)
│   └── hand.py                   (existing, shared)
│
├── tests/
│   ├── play_test_helpers.py      ✅ NEW: Test utilities
│   ├── test_standalone_play.py   ✅ NEW: Standalone tests
│   ├── test_play_endpoints.py    (existing)
│   └── test_opening_bids.py      (existing bidding tests)
│
└── server.py                     (existing endpoints)
```

---

## Benefits of Modular Design

### 1. **Faster Testing**
- No need to simulate bidding for every play test
- Focus on specific play scenarios
- Faster test execution

### 2. **Better Test Coverage**
- Test edge cases easily (specific hands)
- Test legal play rules in isolation
- Test scoring calculations independently

### 3. **Easier Development**
- Work on play AI without touching bidding code
- Develop Phase 2/3 AI improvements independently
- Clear separation of concerns

### 4. **Future Features Enabled**
- **Practice mode**: Let users practice playing specific contracts
- **Hand analysis**: Analyze specific deals after play
- **Training scenarios**: Create educational scenarios
- **Replay functionality**: Replay specific hands

---

## Migrating Existing Tests

If you have existing tests that create full auctions, you can simplify them:

### Before:
```python
def test_something():
    # Create hands
    # Simulate auction: "1NT", "Pass", "3NT", "Pass", "Pass", "Pass"
    # Extract contract
    # Start play
    # Test logic
```

### After:
```python
def test_something():
    deal = create_test_deal(...)
    play_state = create_play_scenario("3NT by S", deal)
    # Test logic immediately!
```

---

## Next Steps

### Immediate Use Cases

1. **Write more unit tests** for play logic
2. **Test AI strategies** with specific scenarios
3. **Verify scoring edge cases** (doubled contracts, slams, etc.)
4. **Test illegal play detection** with tricky hands

### Future Enhancements (Phase 2+)

1. **Session-based play** - Support multiple concurrent games
2. **Save/load scenarios** - JSON scenario files
3. **Minimax AI testing** - Compare AI strategies on same hands
4. **DDS integration** - Compare actual play to optimal play

---

## Examples Repository

See [tests/test_standalone_play.py](backend/tests/test_standalone_play.py) for comprehensive examples including:

- ✅ Creating contracts directly
- ✅ Testing one trick
- ✅ Testing legal play validation
- ✅ Testing scoring calculations
- ✅ Complete hand diagrams

---

## Questions?

**Q: Can I still use the bidding-to-play workflow?**
A: Yes! The original workflow still works. This is an *additional* capability.

**Q: Do I need to change existing code?**
A: No. All changes are backward compatible.

**Q: How do I test my own play scenarios?**
A: Use `create_test_deal()` and `create_play_scenario()` as shown above.

**Q: Can I use this for frontend development?**
A: Yes! You can start play sessions directly via API without bidding.

---

## Summary

The play module is now **fully modular** thanks to:

1. ✅ **Factory method** - `PlayEngine.create_play_session()`
2. ✅ **Contract parser** - `parse_contract()`
3. ✅ **Test helpers** - `create_hand_from_string()`, `create_test_deal()`, etc.
4. ✅ **Standalone tests** - Complete test examples

**Result:** You can now develop, test, and use card play functionality completely independently of the bidding phase!
