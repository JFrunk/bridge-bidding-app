# V2 Schema-Driven Bidding Engine

**Created:** 2026-01-03
**Updated:** 2026-01-03
**Status:** Production (86.5% native coverage, V1 fallback enabled)

## Overview

The V2 Schema Engine is a new bidding engine architecture that uses JSON schema files to define bidding rules instead of Python code. This enables:

1. **Easier Rule Modifications** - Change bidding logic by editing JSON, no Python required
2. **System Toggling** - Switch between SAYC, 2/1, or custom systems via schema files
3. **Machine-Readable Rules** - Rules can be analyzed, validated, and tested programmatically
4. **Cleaner Separation** - Bidding knowledge is separate from engine logic
5. **Forcing Level Tracking** - State machine tracks forcing sequences across the auction

## Architecture

```
engine/v2/
├── __init__.py
├── bidding_engine_v2_schema.py    # Main engine class
├── features/
│   ├── __init__.py
│   └── enhanced_extractor.py      # Feature extraction with PBN support
├── interpreters/
│   ├── __init__.py
│   └── schema_interpreter.py      # JSON rule evaluation + forcing state
├── inference/
│   └── conflict_resolver.py       # Monte Carlo integration (optional)
├── schemas/
│   ├── sayc_openings.json         # Opening bids
│   ├── sayc_responses.json        # Responses to openings
│   ├── sayc_overcalls.json        # Competitive bidding (overcalls)
│   ├── sayc_advancer.json         # Advancer bids (after partner overcalls/doubles)
│   ├── sayc_doubles.json          # Takeout/negative doubles
│   ├── sayc_rebids.json           # Opener rebids (including Forcing 1NT)
│   ├── sayc_responder_rebids.json # Responder's second bid
│   └── sayc_balancing.json        # Pass-out seat actions
└── scripts/
    └── migrate_forcing_levels.py  # Migration script for forcing tags
```

## Usage

```python
from engine.v2 import BiddingEngineV2Schema

engine = BiddingEngineV2Schema()

# Reset state for a new deal (important for forcing level tracking)
engine.new_deal()

bid, explanation = engine.get_next_bid(
    hand=hand,
    auction_history=['1♦', 'Pass', 'Pass'],
    my_position='West',
    vulnerability='None'
)

# Check current forcing state
forcing_state = engine.get_forcing_state()
# Returns: {'forcing_level': 'NON_FORCING', 'is_game_forced': False, ...}
```

## Schema Format

Each JSON schema file contains bidding rules with conditions:

```json
{
  "schema_version": "1.0",
  "system": "SAYC",
  "category": "openings",
  "rules": [
    {
      "id": "open_1nt",
      "bid": "1NT",
      "priority": 90,
      "conditions": {
        "is_opening": true,
        "hcp": {"min": 15, "max": 17},
        "is_balanced": true
      },
      "forcing": "none",
      "sets_forcing_level": "NON_FORCING",
      "explanation": "1NT opening showing {hcp} HCP, balanced"
    }
  ]
}
```

### Condition Types

- **Simple equality**: `"is_opening": true`
- **Numeric ranges**: `"hcp": {"min": 15, "max": 17}`
- **Set membership**: `"opening_bid": {"in": ["1♣", "1♦", "1♥", "1♠"]}`
- **Boolean logic**: `"OR": [...]`, `"AND": [...]`, `"NOT": {...}`

### Forcing Level Tags

Each rule includes a `sets_forcing_level` tag indicating what forcing state the bid establishes:

| Value | Description |
|-------|-------------|
| `GAME_FORCE` | Forces partnership to game (sticky, cannot be unset) |
| `FORCING_1_ROUND` | Partner must bid (expires after one round) |
| `NON_FORCING` | No forcing requirements |

**Examples:**
- `2♣` opening → `GAME_FORCE`
- New suit response → `FORCING_1_ROUND`
- Raises, NT bids → `NON_FORCING`

### Available Features

The feature extractor provides these values for rule matching:

| Feature | Type | Description |
|---------|------|-------------|
| `hcp` | int | High card points |
| `is_balanced` | bool | 4-3-3-3, 4-4-3-2, or 5-3-3-2 shape |
| `is_opening` | bool | First to bid (non-pass) |
| `is_response` | bool | Partner opened, we haven't bid |
| `is_overcall` | bool | Opponent opened, we haven't bid |
| `is_balancing` | bool | In pass-out seat |
| `longest_suit_length` | int | Length of longest suit |
| `spades_length` | int | Number of spades |
| `hearts_length` | int | Number of hearts |
| `diamonds_length` | int | Number of diamonds |
| `clubs_length` | int | Number of clubs |
| `quick_tricks` | float | Quick trick count |
| `stopper_count` | int | Number of stopped suits |
| `support_for_partner` | int | Cards in partner's suit |
| `is_advancer` | bool | Partner overcalled or doubled, we haven't bid |
| `is_responder_rebid` | bool | Responder's second bid |
| `partner_last_bid` | str | Partner's most recent bid |
| `my_last_bid` | str | Our most recent bid |
| `my_suit` | str | Our bid suit (♠, ♥, ♦, ♣) |
| `second_suit` | str | Our second longest suit |
| `has_4_card_major` | bool | Has 4+ card major suit |

## Testing

Run the baseline test:

```bash
cd backend
source venv/bin/activate
python3 tests/sayc_baseline/test_schema_engine.py
```

## Forcing Level State Machine

The engine tracks forcing state across the auction using a state machine:

```
NON_FORCING ←→ FORCING_1_ROUND → GAME_FORCE (sticky)
```

**Key behaviors:**
- **Game Force is sticky**: Once established (e.g., 2♣ opening), partnership must reach game
- **One-round forcing expires**: After partner bids, reverts to NON_FORCING
- **Bid validation**: Engine prevents passing during forcing sequences

**State reset:**
- Call `engine.new_deal()` before each new hand to reset forcing state

## Current Performance

**V2 Native Coverage:** 86.5% (V1 fallback rate: 13.5%)

Based on 1000-hand test runs:

| Category | V2 Native % | Notes |
|----------|-------------|-------|
| Opening | 95%+ | Comprehensive coverage |
| Response | 90%+ | Includes invitational jumps |
| Rebid | 85%+ | Forcing 1NT rebids implemented |
| Overcall | 80%+ | Simple/jump overcalls |
| Advancer | 75%+ | Double responses, overcall raises |
| Responder Rebid | 70%+ | Invitational sequences |

### V1 Fallback

When no V2 schema rule matches, the engine automatically falls back to V1:

```python
BiddingEngineV2Schema(use_v1_fallback=True)  # Default
```

Statistics available via:
```python
engine.get_fallback_stats()
# Returns: {'total_bids': 1000, 'v1_fallbacks': 135, 'fallback_rate': 13.5}
```

## Adding New Rules

1. Identify the category (openings, responses, etc.)
2. Edit the corresponding JSON schema file
3. Add a new rule with:
   - Unique `id`
   - `bid` to make (can use templates like `{longest_suit}`)
   - `priority` (higher = checked first)
   - `conditions` that must all be true
   - `sets_forcing_level` (GAME_FORCE, FORCING_1_ROUND, or NON_FORCING)
   - `explanation` (can include `{feature}` placeholders)
4. Run the test suite to verify

### Migration Script

To add forcing level tags to existing rules, use the migration script:

```bash
cd backend/engine/v2/scripts

# Preview changes
python3 migrate_forcing_levels.py

# Apply changes
python3 migrate_forcing_levels.py --apply
```

## Relationship to V1 Engine

The V2 Schema Engine is independent of the V1 module-based engine. Both can coexist:

- **V1** (`engine/bidding_engine.py`): Python module-based, production
- **V2** (`engine/v2/`): Schema-driven, experimental

The goal is to expand V2's rule coverage until it can replace V1.

## Recent Updates (2026-01-03)

### Forcing 1NT Rebid Rules
After partner responds 1NT to our major opening:
- Rebid 6-card major (minimum)
- Show second lower suit (2♣/2♦)
- Bid 2NT with 18-19 balanced
- Pass 1NT with minimum 12-14

### Advancer Rules (New)
Added `sayc_advancer.json` for responding to partner's competitive actions:
- Responses to takeout doubles (1♠, 1♥, 2♦, 2♣)
- Jump responses showing values (2♠, 2♥)
- 1NT with stopper in opponent's suit
- Raises of partner's overcall
- Penalty pass conversions

### Responder Rebid Rules
Added rules for responder's second bid:
- 2NT invitational (11-12 HCP balanced)
- 3NT game values (13+ HCP balanced)
- Support opener's major with 3-card support
- Game bids with major fit

### Invitational Response Rules
Added direct invitational jumps:
- 2NT invitational to 1-level opening (11-12 HCP)
- 3NT to opening with game values
- Limit raises of minors

## Future Work

1. Expand competitive bidding (reopening doubles, balancing)
2. Implement 2/1 GF schema as alternative system
3. Add slam bidding rules (Blackwood, cuebids)
4. Create schema validation tooling
5. Target 95%+ native V2 coverage
