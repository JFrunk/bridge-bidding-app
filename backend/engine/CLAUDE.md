# Bidding AI Engine

**Specialist Area:** SAYC bidding logic, convention implementation, bid evaluation

## Scope

This area covers the AI bidding system that implements Standard American Yellow Card (SAYC) bidding. You are responsible for:

- **Bidding modules:** Opening bids, responses, rebids, overcalls, advancer bids
- **Conventions:** All 12 implemented conventions (Stayman, Jacoby, Blackwood, etc.)
- **Decision routing:** How auctions route to the correct specialist module
- **Validation:** Bid legality and appropriateness checking
- **Explanations:** Human-readable bid explanations

## Key Files

```
engine/
├── bidding_engine.py          # Main orchestrator - START HERE
├── opening_bids.py            # 1-level openings, 1NT, 2♣
├── responses.py               # Responding to partner's opening
├── rebids.py                  # Opener's second bid
├── responder_rebids.py        # Responder's subsequent bids
├── overcalls.py               # Bidding after opponent opens
├── advancer_bids.py           # After partner overcalls
└── ai/
    ├── decision_engine.py     # Routes auction → module
    ├── feature_extractor.py   # Extracts auction context
    ├── validation_pipeline.py # Appropriateness validation
    ├── sanity_checker.py      # Final safety net
    ├── module_registry.py     # Module management
    └── conventions/           # Convention implementations
```

## Architecture

### Bid Flow
```
Request → BiddingEngine.get_next_bid()
       → extract_features() (auction context)
       → select_bidding_module() (decision routing)
       → specialist.evaluate(hand, features)
       → ValidationPipeline.validate()
       → SanityChecker.check()
       → Return (bid, explanation)
```

### Module Interface
All bidding modules extend `ConventionModule` and implement:
```python
def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
    # Returns (bid, explanation) or None if module doesn't apply
```

### Decision Priority
1. **Opening:** Preempts → 2♣ → 1-level suits → 1NT
2. **Competitive:** Michaels → Unusual 2NT → Overcalls → Takeout Doubles
3. **Partnership:** Blackwood → Splinter → FSF → Negative Doubles → Conventions → Natural

## SAYC Reference

**Opening Requirements:**
- 1-level suit: 12-21 HCP, 5+ card major or 3+ card minor
- 1NT: 15-17 HCP, balanced
- 2♣: 22+ HCP or 9+ tricks
- Preempts: 6-10 HCP, 6+ card suit (2-level) or 7+ card suit (3-level)

**Response Logic:**
- 6-9 HCP: Single raise or 1NT
- 10-12 HCP: Jump raise or new suit
- 13+ HCP: Game forcing response

## Quality Requirements

**MANDATORY before committing bidding changes:**

```bash
# Establish baseline BEFORE changes
python3 test_bidding_quality_score.py --hands 500 --output baseline_before.json

# After changes
python3 test_bidding_quality_score.py --hands 500 --output baseline_after.json

# Compare - MUST NOT regress
python3 compare_scores.py baseline_before.json baseline_after.json
```

**Blocking Thresholds:**
- Legality: **100%** (no illegal bids ever)
- Appropriateness: **≥ baseline** (no regression)
- Composite: **≥ baseline - 2%** (small tolerance)

## Common Tasks

### Fix Incorrect Bid
1. Reproduce with specific hand + auction
2. Trace through `decision_engine.py` to find routing
3. Check `feature_extractor.py` output
4. Fix in appropriate specialist module
5. Add regression test in `tests/regression/`
6. Run quality score to verify no regression

### Add New Convention
1. Create `conventions/new_convention.py` extending `ConventionModule`
2. Add `@ModuleRegistry.register('name')` decorator
3. Import in `bidding_engine.py` (triggers registration)
4. Add routing logic in `decision_engine.py`
5. Add hand generator in `hand_constructor.py` (optional)
6. Create test file `tests/unit/test_new_convention.py`
7. Run full quality score

### Debug Routing Issues
```python
# Enable verbose logging in decision_engine.py
print(f"🎯 DECISION ENGINE for {my_pos_str}:")
print(f"   Opener: {auction.get('opener')}")
print(f"   Opener relationship: {auction.get('opener_relationship')}")
```

## Testing

```bash
# Quick unit tests
pytest tests/unit/test_opening_bids.py -v
pytest tests/unit/test_stayman.py -v

# Convention-specific
pytest tests/scenarios/ -v

# Integration
pytest tests/integration/test_bidding_*.py -v

# Full quality assessment
python3 test_bidding_quality_score.py --hands 100  # Quick
python3 test_bidding_quality_score.py --hands 500  # Comprehensive
```

## Dependencies

- **Uses:** `Hand` class from `engine/hand.py`
- **Used by:** `server.py` API endpoints, `feedback/bidding_feedback.py`

## Gotchas

- Feature extraction must happen BEFORE module selection
- Modules return `None` to indicate "doesn't apply" (not "Pass")
- ValidationPipeline can be bypassed with metadata for artificial bids
- SanityChecker is the FINAL safety net - fixes obviously wrong bids
- Convention modules can return 3-tuple with metadata: `(bid, explanation, metadata)`
- Auction indexing: position = `index % 4` (0=North, 1=East, 2=South, 3=West)
- Hand generation in scenarios consumes cards from deck - order matters
- Always run quality score before/after bidding changes to catch regressions

## Reference Documents

- **SAYC Rules:** `.claude/SAYC_REFERENCE.md` - Official SAYC bidding system
- **Play Rules:** `.claude/BRIDGE_PLAY_RULES.md` - Card play mechanics (online + offline)
