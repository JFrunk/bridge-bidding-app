# V2 Schema Engine - Issue Tracking

**Analysis Date:** 2026-01-05
**Data Source:** 200 hands with production DDS analysis

## Summary Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Accuracy Rate | 9.1% | 25%+ |
| Overbid Rate | 80.3% | <50% |
| Mean Gap | +2.80 | <+1.5 |
| Critical Failures | 109 | <40 |

---

## Issue Files (Parallel Investigation)

| File | Priority | Failures | Avg Gap | Agent Assignment |
|------|----------|----------|---------|------------------|
| [ISSUE_v1_fallback.md](ISSUE_v1_fallback.md) | 1 | 78 | +4.2 | Agent 1 |
| [ISSUE_rkcb_slam.md](ISSUE_rkcb_slam.md) | 2 | 13 | +4.5 | Agent 2 |
| [ISSUE_responder_rebids.md](ISSUE_responder_rebids.md) | 3 | 25 | +3.5 | Agent 3 |
| [ISSUE_preempt_raises.md](ISSUE_preempt_raises.md) | 4 | 4 | +5.4 | Agent 4 |
| [ISSUE_opener_rebids.md](ISSUE_opener_rebids.md) | 5 | 5 | +4.6 | Agent 4 |

---

## Quick Start for Each Agent

### Agent 1: V1 Fallback (78 failures)
```bash
# Investigate
cat ISSUE_v1_fallback.md

# Files to modify
# - sayc_interference.json
# - sayc_responses.json

# Test after changes
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 2>&1 | grep "v1_fallback"
```

### Agent 2: RKCB/Slam (13 failures)
```bash
# Investigate
cat ISSUE_rkcb_slam.md

# Files to modify
# - sayc_rkcb.json
# - sayc_slam_controls.json

# Test after changes
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 2>&1 | grep -E "(rkcb|slam)"
```

### Agent 3: Responder Rebids (25 failures)
```bash
# Investigate
cat ISSUE_responder_rebids.md

# Files to modify
# - sayc_responder_rebids.json

# Test after changes
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 2>&1 | grep "responder"
```

### Agent 4: Preempts & Opener Rebids (9 failures)
```bash
# Investigate
cat ISSUE_preempt_raises.md
cat ISSUE_opener_rebids.md

# Files to modify
# - sayc_preempts.json
# - sayc_rebids.json

# Test after changes
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42 2>&1 | grep -E "(preempt|opener)"
```

---

## Workflow

1. **Read your issue file** - Contains root cause, examples, and proposed fixes
2. **Find the rule in the schema file** - Located in `engine/v2/schemas/`
3. **Apply the fix** - Modify conditions as proposed
4. **Test with provided commands** - Each issue file has test commands
5. **Verify improvement** - Run full analysis to check gap reduction

---

## Schema File Locations

```
engine/v2/schemas/
├── sayc_openings.json
├── sayc_responses.json
├── sayc_responder_rebids.json
├── sayc_rebids.json
├── sayc_interference.json
├── sayc_overcalls.json
├── sayc_preempts.json
├── sayc_rkcb.json
├── sayc_slam_controls.json
├── sayc_advancer.json
└── sayc_balancing.json
```

---

## Verification Command

After all fixes, run comprehensive analysis:

```bash
cd /Users/simonroy/Desktop/bridge_bidding_app/backend
source venv/bin/activate
USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py \
  --hands 200 \
  --seed 42 \
  --chart bidding_efficiency_after.png \
  --output efficiency_report_after.json
```

Compare with baseline:
- Accuracy: 9.1% → Target 25%+
- Mean Gap: +2.80 → Target <+1.5
- Critical Failures: 109 → Target <40
