# Comprehensive Analysis System

**Status:** Phase 3 Complete (Backend)
**Created:** 2025-01-04
**Last Updated:** 2026-01-04

## Overview

The Comprehensive Analysis System provides deep insights into bridge bidding and play performance by analyzing hands after completion. It calculates quadrant classification, bidding efficiency, and points left on table.

## Architecture

### Components

1. **BridgeAnalysisEngine** (`backend/engine/analysis/analysis_engine.py`)
   - Core analysis logic
   - Quadrant classification (Q1-Q4)
   - Bidding efficiency calculation
   - Points left on table estimation

2. **Database Migration 011** (`backend/migrations/011_add_comprehensive_analysis.sql`)
   - Adds analysis columns to `session_hands`
   - Creates aggregate views for dashboard

3. **Post-Game Hook** (`backend/server.py`)
   - Triggers async analysis after each hand
   - Runs in background thread

4. **API Endpoints** (`backend/engine/learning/analytics_api.py`)
   - Dashboard integration
   - Dedicated bidding analysis endpoint

## Key Concepts

### Quadrant Classification

Hands are classified into four quadrants based on bidding and play quality:

| Quadrant | Bidding | Play | Color | Description |
|----------|---------|------|-------|-------------|
| Q1 | Good | Good | Green | Optimal performance |
| Q2 | Good | Bad | Yellow | Bid well, played poorly |
| Q3 | Bad | Bad | Red | Needs improvement in both |
| Q4 | Bad | Good | Yellow | Overbid but recovered |

### "Good Bidding" Definition

**Corrected Logic:** A bid is "good" if either:
1. `reached_optimal_bonus_level` - Contract achieves maximum available bonus (game/slam)
2. `no_higher_bonus_available` - No higher makeable bonus exists

This differs from simply checking if "contract was makeable" (which would miss underbids).

### Bid Efficiency

| Classification | Meaning |
|---------------|---------|
| `optimal` | Contract achieves maximum available bonus |
| `underbid` | Higher bonus was available but not bid |
| `overbid` | Contract is unmakeable (DD analysis) |

### Points Left on Table

Calculated as the difference between:
- Optimal contract bonus (based on DD analysis)
- Achieved contract bonus

Uses tier-based comparison:
- Tier 0: Partscore (50 points)
- Tier 1: Game (300 NV / 500 V)
- Tier 2: Small Slam (+500 NV / +750 V)
- Tier 3: Grand Slam (+1000 NV / +1500 V)

## Database Schema

### New Columns (session_hands)

```sql
-- Decay curve (Phase 3)
decay_curve TEXT DEFAULT NULL;

-- Major errors during play
major_errors TEXT DEFAULT NULL;

-- Quadrant: Q1/Q2/Q3/Q4
quadrant TEXT DEFAULT NULL;

-- Bid efficiency: optimal/underbid/overbid
bid_efficiency TEXT DEFAULT NULL;

-- Points lost from underbidding
points_left_on_table INTEGER DEFAULT 0;

-- Opening lead analysis
opening_lead_card TEXT DEFAULT NULL;
opening_lead_quality TEXT DEFAULT NULL;  -- optimal/neutral/leaking
opening_lead_cost INTEGER DEFAULT 0;

-- Full DD matrix for "what if" analysis
dd_matrix TEXT DEFAULT NULL;
```

### Views

1. **v_user_analysis_stats** - Aggregate statistics per user
2. **v_user_strain_accuracy** - Per-strain bidding accuracy
3. **v_recent_boards_for_quadrant** - Pre-formatted data for quadrant chart

## API Endpoints

### GET /api/analytics/dashboard

Includes new fields:
- `bidding_analysis` - Quadrant/efficiency aggregates
- `recent_analyzed_hands` - Last 20 hands for quadrant chart
- `strain_accuracy` - Per-strain accuracy for heatmap

### GET /api/analytics/bidding-analysis

Dedicated endpoint for bidding analysis visualization.

**Query Parameters:**
- `user_id` (required)

**Response:**
```json
{
  "user_id": 1,
  "bidding_analysis": {
    "total_analyzed_hands": 50,
    "quadrant_distribution": {"Q1": 25, "Q2": 10, "Q3": 5, "Q4": 10},
    "quadrant_percentages": {"Q1": 50, "Q2": 20, "Q3": 10, "Q4": 20},
    "bidding_efficiency": {"optimal": 30, "underbid": 15, "overbid": 5},
    "efficiency_percentages": {"optimal": 60, "underbid": 30, "overbid": 10},
    "total_points_left": 1200,
    "avg_points_left_when_underbid": 80
  },
  "recent_analyzed_hands": [...],
  "strain_accuracy": {"NT": {...}, "S": {...}, ...}
}
```

## Implementation Phases

### Phase 1 (Complete)
- [x] Database migration 011
- [x] AnalysisEngine with corrected bidding logic
- [x] Post-game analysis hook
- [x] API endpoints and dashboard integration
- [x] Unit tests (25 tests)

### Phase 2 (Pending)
- [ ] Frontend quadrant chart (SVG)
- [ ] Bidding efficiency card visualization

### Phase 3 (Complete - Backend)
- [x] Decay curve generation (DecayCurveGenerator)
- [x] State reconstruction for trick-by-trick analysis (StateReconstructor)
- [x] Major error detection from curve drops
- [x] Integration with post-game analysis hook
- [x] Unit tests (32 tests)
- [ ] Sparkline visualization (frontend pending)

## Testing

```bash
# Run all analysis tests (57 tests)
cd backend
python3 -m pytest tests/analysis/ -v

# Run analysis engine tests only (25 tests)
python3 -m pytest tests/analysis/test_analysis_engine.py -v

# Run decay curve tests only (32 tests)
python3 -m pytest tests/analysis/test_decay_curve.py -v

# Test API functions
python3 -c "
from engine.learning.analytics_api import get_bidding_analysis_stats_for_user
stats = get_bidding_analysis_stats_for_user(1)
print(stats)
"
```

## Related Files

- `backend/engine/analysis/__init__.py`
- `backend/engine/analysis/analysis_engine.py`
- `backend/engine/analysis/decay_curve.py` (Phase 3)
- `backend/tests/analysis/test_analysis_engine.py`
- `backend/tests/analysis/test_decay_curve.py` (Phase 3)
- `backend/migrations/011_add_comprehensive_analysis.sql`
- `backend/engine/learning/analytics_api.py`
- `backend/server.py`

## Decay Curve Details (Phase 3)

### How It Works

The decay curve tracks declarer's **trick potential** at each card played:
- **Serial Mutation**: Cards are consumed in play order
- **Normalization**: All values from declarer's perspective
- **Monotonicity**: Potential should stay flat or decrease with optimal play

### Error Detection

- **Declarer Error**: Curve drops = tricks lost by declarer
- **Defensive Gift**: Curve increases = tricks given by defense

### Performance

- DDS called once per card (52 calls per hand)
- Runs async in post-game hook (won't block gameplay)
- Only runs on production (Linux with DDS available)
