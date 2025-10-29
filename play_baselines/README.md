# Play Quality Score History

This directory tracks historical play quality scores for the Bridge Bidding App.

## Baseline Files

### Current Baselines

- **Level 8 (Advanced - Minimax)**: `../play_baseline_level8.json`
  - AI: MinimaxPlayAI with depth 2
  - Expected: 80-85% composite, 70-80% success rate
  - Use for: Development testing, pre-commit checks

- **Level 10 (Expert - DDS)**: `../play_baseline_level10_dds.json` *(Production Linux only)*
  - AI: DDSPlayAI (Double Dummy Solver)
  - Expected: 90-95% composite, 85-95% success rate
  - Use for: Production validation, regression testing on Linux servers

## Score History

### 2025-10-29
- **Baseline Establishment**: Initial play quality baselines being established
  - Level 8: TBD (running 500-hand test)
  - Level 10: TBD (requires Linux production server)

## File Naming Convention

Historical score files follow this format:
```
YYYY-MM-DD_levelN_description.json
```

Examples:
- `2025-10-29_level8_baseline.json` - Initial Level 8 baseline
- `2025-10-30_level8_after_minimax_fix.json` - After minimax improvements
- `2025-11-01_level8_after_trick_fix.json` - After trick evaluation fix

## Scoring System

### Dimensions (Total = 100%)

1. **Legality (30%)** - Must be 100%
   - All card plays must follow bridge rules
   - Correct suit following
   - Proper trump usage

2. **Success Rate (25%)** - Contracts made
   - Percentage of contracts that make exactly or with overtricks
   - Key metric for AI competency

3. **Efficiency (20%)** - Optimal play
   - Maximizing overtricks when making
   - Minimizing undertricks when going down

4. **Tactical (15%)** - Advanced concepts
   - Finessing
   - Trump management
   - Entry preservation
   - Card counting

5. **Timing (10%)** - Performance
   - Average time per hand
   - Average time per card play

### Grade Scale

- **A (90-100%)**: Expert level - production ready ✅
- **B (80-89%)**: Advanced level - good quality ✅
- **C (70-79%)**: Intermediate level - acceptable ⚠️
- **D (60-69%)**: Beginner level - needs improvement ⚠️
- **F (<60%)**: Poor play - major issues ❌

## Target Scores by AI Level

| Level | Description | Expected Composite | Expected Success Rate |
|-------|-------------|-------------------|----------------------|
| 1-2 | Beginner | 50-60% (F-D) | 40-50% |
| 3-4 | Intermediate | 60-70% (D-C) | 50-60% |
| 5-6 | Advanced- | 70-80% (C-B) | 60-70% |
| 7-8 | Advanced | 80-85% (B) | 70-80% |
| 9-10 | Expert/DDS | 90-95% (A) | 85-95% |

## Regression Criteria

**BLOCK commits if:**
- Legality < 100% (any illegal plays)
- Composite drops >2% from baseline
- Success rate drops >5% from baseline
- Timing increases >50% from baseline

## Usage Examples

### Establish New Baseline
```bash
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_baseline_level8.json
cp play_baseline_level8.json play_baselines/2025-10-29_level8_baseline.json
```

### Compare Before/After
```bash
python3 compare_play_scores.py play_baselines/2025-10-29_level8_baseline.json play_baseline_after_fix.json
```

### Quick Development Test
```bash
python3 backend/test_play_quality_integrated.py --hands 100 --level 8
```

## Notes

- **DDS Testing**: Level 9-10 (DDS) crashes on macOS M1/M2 - only test on Linux production servers
- **Development AI**: Use Level 8 (Minimax) for local development and testing
- **Production AI**: Level 10 (DDS) provides expert-level play for production users
- **Test Duration**:
  - 100 hands ≈ 10 minutes (Level 8), 60-90 minutes (Level 10)
  - 500 hands ≈ 30 minutes (Level 8), 4-6 hours (Level 10)

## Related Documentation

- [Play Quality Score Protocol](../.claude/CODING_GUIDELINES.md#play-logic-quality-assurance-protocol)
- [Bidding Quality Score Protocol](../.claude/CODING_GUIDELINES.md#bidding-logic-quality-assurance-protocol)
- [Test Script](../backend/test_play_quality_integrated.py)
- [Comparison Script](../compare_play_scores.py)
