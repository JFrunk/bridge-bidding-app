# DDS Analysis & ACBL Integration

**Status:** Foundation Implemented (Phase 1 Complete)
**Priority:** Future Enhancement (Phase 6)
**Last Updated:** 2026-01-01

---

## Overview

This feature provides comprehensive Double Dummy Solver (DDS) analysis capabilities and lays the groundwork for importing and analyzing ACBL tournament results.

### Use Cases

1. **Post-Game Analysis:** Show "what if" scenarios after playing a hand
2. **Par Score Comparison:** Compare user's bidding/play against optimal (par) results
3. **ACBL Import:** Import tournament results and analyze your performance
4. **Training Feedback:** "You made 9 tricks, but optimal play makes 11"

---

## Implementation Status

### Phase 1: Foundation (COMPLETE)

The DDS analysis service is fully implemented and tested.

#### Files Created

| File | Purpose |
|------|---------|
| `backend/engine/play/dds_analysis.py` | Core analysis service |
| `backend/migrations/007_add_dds_analysis.sql` | Database schema |
| `backend/tests/play/test_dds_analysis.py` | Test suite (31 tests) |

#### Capabilities Implemented

- **Full DD Table:** 20-result grid (4 players × 5 strains)
- **Par Calculation:** Optimal contract with vulnerability awareness
- **PBN Parsing:** Full 4-hand deals, with 3-hand inference
- **LIN Support:** Bridge Base Online format parsing
- **Caching:** Results cached for performance
- **JSON Export:** All results serializable for API/database

#### Hand.py Enhancements

Added to `backend/engine/hand.py`:
- `Hand.from_pbn()` - Parse PBN hand strings
- `Hand.to_pbn()` - Export to PBN format
- `Hand.from_lin()` - Parse Bridge Base Online format
- `shape_string` property - e.g., "5-4-3-1"
- `sorted_shape` property - e.g., "5431"

---

## API Reference

### DDSAnalysisService

```python
from engine.play.dds_analysis import DDSAnalysisService, analyze_deal

# Create service
service = DDSAnalysisService()

# Analyze a deal
analysis = service.analyze_deal(
    hands={'N': north, 'E': east, 'S': south, 'W': west},
    dealer='N',
    vulnerability='NS'
)

# Access results
if analysis.is_valid:
    # DD Table: tricks by player/strain
    tricks = analysis.dd_table.get_tricks('S', 'NT')  # e.g., 10

    # Par result
    par_score = analysis.par_result.score  # e.g., 420
    par_contracts = analysis.par_result.contracts  # e.g., ['4HS', '4HN']

    # Display
    print(analysis.dd_table.format_display())
    print(analysis.par_result.format_display())
```

### Convenience Functions

```python
from engine.play.dds_analysis import analyze_deal, get_dd_table, get_par_score

# Quick analysis
analysis = analyze_deal(hands)

# Just DD table
dd_table = get_dd_table(hands)

# Just par score
par = get_par_score(hands, vulnerability='Both')
```

### Compare with Par

```python
result = service.compare_with_par(
    hands,
    contract_level=3,
    contract_strain='NT',
    declarer='S',
    tricks_made=10,
    vulnerability='NS'
)

# Result includes:
# - dd_tricks: Optimal tricks for this contract
# - par_score: Par score for the deal
# - optimal_play: Whether user matched/exceeded DD
# - made_contract: Whether contract was made
```

---

## Database Schema

### Session Hands Additions (Migration 007)

```sql
-- Added to session_hands table
dds_analysis TEXT      -- Full JSON analysis
par_score INTEGER      -- Par score for quick queries
par_contract TEXT      -- Par contract display
dd_tricks INTEGER      -- DD tricks for played contract
```

### Imported Hands Table (New)

```sql
CREATE TABLE imported_hands (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,

    -- Import metadata
    source TEXT DEFAULT 'pbn',  -- 'pbn', 'lin', 'acbl'
    source_file TEXT,
    event_name TEXT,
    board_number INTEGER,

    -- Deal data
    dealer TEXT,
    vulnerability TEXT,
    deal_pbn TEXT NOT NULL,
    auction TEXT,  -- JSON

    -- Contract/result (if available)
    contract_level INTEGER,
    contract_strain TEXT,
    contract_declarer TEXT,
    tricks_taken INTEGER,

    -- Scoring
    score_ns INTEGER,
    score_matchpoints REAL,
    score_imps INTEGER,

    -- DDS Analysis
    dds_analysis TEXT,
    par_score INTEGER,
    par_contract TEXT,
    dd_tricks INTEGER,
    analysis_status TEXT DEFAULT 'pending'
);
```

---

## Phase 2: ACBL Import (PLANNED)

### Planned Features

1. **PBN File Import Endpoint**
   - `POST /api/import-pbn`
   - Upload PBN files
   - Parse all hands and metadata
   - Queue for DDS analysis

2. **Batch Analysis**
   - Background job to analyze imported hands
   - Rate-limited to avoid DDS overload
   - Progress tracking

3. **Event Metadata**
   - Event name, date, location
   - Board numbers
   - Scoring method (matchpoints, IMPs)

4. **Results Comparison**
   - Your score vs. par
   - Your score vs. field average
   - Identify bidding/play errors

### API Design (Draft)

```
POST /api/import-pbn
  - Upload PBN file
  - Returns: import_id, hand_count

GET /api/imports/{import_id}
  - Get import status and hands

GET /api/imports/{import_id}/hands
  - List imported hands with analysis

GET /api/imports/{import_id}/hands/{hand_id}
  - Single hand with full DD analysis
```

---

## Platform Notes

### DDS Availability

| Platform | Status | Notes |
|----------|--------|-------|
| Linux (Production) | ✅ Works | Default on Oracle Cloud |
| macOS Intel | ✅ Works | Development supported |
| macOS M1/M2 | ⚠️ May crash | Use Minimax fallback |
| Windows | ✅ Works | Tested with endplay |

### Performance

- **Cold analysis:** ~50-100ms per deal
- **Cached analysis:** <1ms
- **Batch mode:** ~10 deals/second

---

## Testing

### Run Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/play/test_dds_analysis.py -v
```

### Test Coverage

- DDTable operations (5 tests)
- ParResult operations (3 tests)
- DDSAnalysisService (9 tests)
- PBN parsing with inference (3 tests)
- Convenience functions (4 tests)
- Edge cases (4 tests)
- Performance (2 tests)

**Total: 31 tests, all passing**

---

## Dependencies

```
endplay>=0.5.0  # Already in requirements.txt
```

The `endplay` library provides:
- DDS solver bindings
- PBN parser
- Deal representation
- Par calculation

---

## Related Documentation

- [FEATURES_SUMMARY.md](../project-overview/FEATURES_SUMMARY.md) - Phase 6 roadmap
- [Play Engine](../../backend/engine/play_engine.py) - Card play integration
- [DDS AI](../../backend/engine/play/ai/dds_ai.py) - Real-time play decisions

---

## Future Considerations

1. **LIN Import:** Bridge Base Online hand records
2. **ACBL API:** Direct integration with ACBL Live
3. **Hand Records PDF:** Parse PDF hand records from tournaments
4. **Traveler Import:** Full traveler data with all scores
5. **Club Game Support:** Local club game result import
