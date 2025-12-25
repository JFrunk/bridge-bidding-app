# Play Engine & AI

**Specialist Area:** Card play simulation, trick-taking logic, AI difficulty levels

## Scope

This area covers the card play system that executes hands after bidding completes. You are responsible for:

- **Play engine:** Trick execution, winner determination, contract tracking
- **AI players:** Four difficulty levels (beginner → expert)
- **Scoring:** Contract calculation, doubled/redoubled, vulnerability
- **DDS integration:** Double Dummy Solver for expert play (Linux only)

## Key Files

```
engine/
├── play_engine.py             # Main play orchestrator
├── bridge_rules_engine.py     # Scoring calculations
├── contract_utils.py          # Contract analysis
├── simple_play_ai.py          # Legacy AI (backward compat)
└── play/
    └── ai/
        ├── base_ai.py         # Abstract interface
        ├── simple_ai.py       # beginner: Heuristics
        ├── minimax_ai.py      # intermediate/advanced: Lookahead
        ├── dds_ai.py          # expert: Perfect play
        └── evaluation.py      # Position evaluation
```

## Architecture

### Play Flow
```
Contract established → PlayEngine initialized
  → Loop for 13 tricks:
      1. Determine current player
      2. Get legal plays (follow suit rules)
      3. AI selects card OR user input
      4. Add card to trick
      5. When trick complete → determine winner
      6. Winner leads next trick
  → Calculate final score
  → Return result
```

### AI Difficulty System

| Difficulty | Class | Strategy | Performance |
|------------|-------|----------|-------------|
| beginner | `SimplePlayAI` | Heuristics | <1s/hand |
| intermediate | `MinimaxPlayAI(depth=2)` | Lookahead | 2-3s/hand |
| advanced | `MinimaxPlayAI(depth=3)` | Deeper lookahead | 2-3s/hand |
| expert | `DDSPlayAI` | Perfect analysis | 15-30s/hand |

### AI Interface
```python
class BasePlayAI(ABC):
    @abstractmethod
    def select_card(self, game_state: PlayState) -> Card:
        """Select the best card to play given current state."""
        pass
```

## DDS Critical Notes

**DDS ONLY works on Linux production servers.**

```python
# In server.py - platform detection
PLATFORM_ALLOWS_DDS = platform.system() == 'Linux'

# Expert fallback on macOS/Windows
'expert': DDSPlayAI() if (DDS_AVAILABLE and PLATFORM_ALLOWS_DDS)
          else MinimaxPlayAI(max_depth=4)
```

**Why:** DDS crashes on macOS M1/M2 with Error Code -14 (segmentation fault).
**Impact:** Development uses Minimax; production Linux uses DDS.

## Quality Requirements

**MANDATORY before committing play changes:**

```bash
# Establish baseline BEFORE changes
python3 test_play_quality_integrated.py --hands 500 --level 8 --output play_before.json

# After changes
python3 test_play_quality_integrated.py --hands 500 --level 8 --output play_after.json

# Compare
python3 compare_play_scores.py play_before.json play_after.json
```

**Blocking Thresholds:**
- Legality: **100%** (no illegal plays)
- Success Rate: **≥ baseline - 5%**
- Composite: **≥ baseline - 2%**
- Timing: **< baseline + 50%** (performance)

## Common Tasks

### Improve AI Play Quality
1. Identify weakness (e.g., trump management, defensive signals)
2. Add/modify heuristics in `simple_ai.py` or evaluation in `minimax_ai.py`
3. Test with quality score at target level
4. Ensure no performance regression

### Fix Illegal Play Bug
1. Check `play_engine.py` legal play determination
2. Verify follow-suit logic
3. Add regression test
4. Run quality score

### Optimize Minimax Performance
1. Profile with `cProfile`
2. Consider alpha-beta pruning improvements
3. Optimize evaluation function
4. Test timing doesn't regress

## Testing

```bash
# Unit tests
pytest tests/play/ -v

# Specific AI type
python3 test_play_quality_integrated.py --hands 100 --ai simple   # beginner
python3 test_play_quality_integrated.py --hands 100 --ai minimax  # advanced

# Performance benchmark
python3 -m cProfile -s cumtime test_play_quality_integrated.py --hands 50 --level 8
```

## Play Strategies

### SimplePlayAI (beginner)
- Second hand low, third hand high
- Lead partner's suit
- Finesse when possible
- Trump management basics

### MinimaxPlayAI (intermediate/advanced)
- Alpha-beta pruning
- Position evaluation function
- Depth-limited search (2-3 plies)

### DDSPlayAI (expert)
- Uses `endplay` library
- Perfect double-dummy analysis
- **Linux only** due to stability issues

## Dependencies

- **Uses:** `Hand`, `Card` from `engine/hand.py`
- **Used by:** `server.py` play endpoints

## Gotchas

- DDS will crash on macOS - always test with Minimax locally
- PlayState must be fully initialized before AI selection
- Trick winner determination must handle trump correctly
- Contract scoring varies by vulnerability and doubling
- AI instances are created at server startup (see `ai_instances` dict)

## Reference Documents

- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Online single-player rules + offline reference
- **SAYC Rules:** `.claude/SAYC_REFERENCE.md` - Bidding system reference
