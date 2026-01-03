# V2 Schema-Driven Bidding Engine

**Created:** 2026-01-03
**Status:** Experimental

## Overview

The V2 Schema Engine is a new bidding engine architecture that uses JSON schema files to define bidding rules instead of Python code. This enables:

1. **Easier Rule Modifications** - Change bidding logic by editing JSON, no Python required
2. **System Toggling** - Switch between SAYC, 2/1, or custom systems via schema files
3. **Machine-Readable Rules** - Rules can be analyzed, validated, and tested programmatically
4. **Cleaner Separation** - Bidding knowledge is separate from engine logic

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
│   └── schema_interpreter.py      # JSON rule evaluation
└── schemas/
    ├── sayc_openings.json         # Opening bids
    ├── sayc_responses.json        # Responses to openings
    ├── sayc_overcalls.json        # Competitive bidding
    ├── sayc_doubles.json          # Takeout/negative doubles
    ├── sayc_rebids.json           # Opener/responder rebids
    └── sayc_balancing.json        # Pass-out seat actions
```

## Usage

```python
from engine.v2 import BiddingEngineV2Schema

engine = BiddingEngineV2Schema()
bid, explanation = engine.get_next_bid(
    hand=hand,
    auction_history=['1♦', 'Pass', 'Pass'],
    my_position='West',
    vulnerability='None'
)
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

## Testing

Run the baseline test:

```bash
cd backend
source venv/bin/activate
python3 tests/sayc_baseline/test_schema_engine.py
```

## Current Performance

Against the saycbridge baseline (218 test cases):

| Metric | Value |
|--------|-------|
| Match Rate | 12.8% |
| No Rule Found | 71.1% |

### Category Breakdown

| Category | Match Rate |
|----------|------------|
| Balancing | 36.4% |
| Reopening Double | 45.5% |
| Overcalls | 16.7% |
| Doubles | 11.8% |

## Adding New Rules

1. Identify the category (openings, responses, etc.)
2. Edit the corresponding JSON schema file
3. Add a new rule with:
   - Unique `id`
   - `bid` to make (can use templates like `{longest_suit}`)
   - `priority` (higher = checked first)
   - `conditions` that must all be true
   - `explanation` (can include `{feature}` placeholders)
4. Run the test suite to verify

## Relationship to V1 Engine

The V2 Schema Engine is independent of the V1 module-based engine. Both can coexist:

- **V1** (`engine/bidding_engine.py`): Python module-based, production
- **V2** (`engine/v2/`): Schema-driven, experimental

The goal is to expand V2's rule coverage until it can replace V1.

## Future Work

1. Add more schema rules for missing categories
2. Implement 2/1 GF schema as alternative system
3. Add schema validation tooling
4. Create schema editor UI
