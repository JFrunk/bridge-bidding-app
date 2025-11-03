# Quick Start: Baseline Quality Scores

**Purpose:** Rapid access to current baseline scores and comparison commands for developers.

---

## 🚀 Instant Status Check

```bash
# Quick visual status (with colors)
python3 quick_baseline_check.py

# Shell script version
./check_baseline_status.sh

# CSV format (for parsing)
python3 quick_baseline_check.py --csv

# JSON format (for tools)
python3 quick_baseline_check.py --json
```

---

## 📊 Current Baselines (2025-10-30)

| System | Score | Grade | Status |
|--------|-------|-------|--------|
| **Bidding** | 94.8% | B | 🟡 Near Ready (+0.2 pts needed) |
| **Play** | 80.3% | C | 🟢 Baseline Acceptable |

**Bidding:** `quality_scores/baseline_20251030_145945.json`
**Play:** `quality_scores/play_baseline_20251030_151213.json`

---

## ⚡ Before Committing Changes

### Bidding Engine Changes

```bash
# Run test
python3 backend/test_bidding_quality_score.py --hands 500 \
  --output quality_scores/test_$(date +%Y%m%d_%H%M%S).json

# Compare (replace YYYYMMDD_HHMMSS with your file)
python3 compare_scores.py \
  quality_scores/baseline_20251030_145945.json \
  quality_scores/test_YYYYMMDD_HHMMSS.json

# Must maintain or improve:
# - Legality: 100%
# - Appropriateness: ≥95%
# - Composite: ≥90%
```

### Play Engine Changes

```bash
# Run test
python3 backend/test_play_quality_score.py --hands 500 \
  --output quality_scores/play_test_$(date +%Y%m%d_%H%M%S).json

# Compare
python3 compare_play_scores.py \
  quality_scores/play_baseline_20251030_151213.json \
  quality_scores/play_test_YYYYMMDD_HHMMSS.json

# Must maintain:
# - Legality: 100%
# - Composite: ≥75%
```

---

## 🎯 Production Deployment Gates

### ✅ Bidding System (Blocking)
- [ ] Legality: 100% (current: ✅ 100%)
- [ ] Appropriateness: ≥95% (current: ✅ 100%)
- [ ] Conventions: ≥98% (current: ✅ 98.8%)
- [ ] **Composite: ≥95%** (current: ⚠️ 94.8% - **NEEDS +0.2**)

**Status:** 🟡 **NEAR PRODUCTION READY** - Fix 3 Stayman errors to reach 95%

### ✅ Play System (Non-Blocking)
- [ ] Legality: 100% (current: ✅ 100%)
- [ ] Success Rate: ≥65% (current: ⚠️ 60.4%)
- [ ] Composite: ≥80% (current: ✅ 80.3%)

**Status:** 🟢 **BASELINE ACCEPTABLE** - Improvement recommended but not blocking

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| [BASELINE_SCORES.md](BASELINE_SCORES.md) | Comprehensive baseline documentation |
| [quality_scores/README.md](quality_scores/README.md) | Historical tracking |
| [quality_scores/baseline_history.csv](quality_scores/baseline_history.csv) | Machine-readable history |
| `quick_baseline_check.py` | Python status checker |
| `check_baseline_status.sh` | Shell status checker |

---

## 🔧 Common Commands

```bash
# Check status
python3 quick_baseline_check.py

# Run comprehensive baseline (12 min)
/quality-baseline

# Quick smoke test (100 hands, 2 min)
python3 backend/test_bidding_quality_score.py --hands 100
python3 backend/test_play_quality_score.py --hands 100

# View recent tests
ls -lt quality_scores/*.json | head -5

# Check production readiness
./check_baseline_status.sh --production
```

---

## 📈 Next Milestones

| Milestone | Target | ETA | Impact |
|-----------|--------|-----|--------|
| Grade A Bidding | 96% | 1 week | Fix Stayman + Game/Slam |
| Grade B Play | 85% | 2 weeks | Minimax depth 3 |
| Grade A Play | 92% | 1 month | DDS integration |
| Production Ready | All systems 95%+ | 2 weeks | Full deployment |

---

## ⚠️ Regression Alerts

**Auto-reject commit if:**
- Legality drops below 100% (either system)
- Bidding appropriateness drops below 95%
- Bidding composite drops below 90%

**Warning triggers if:**
- Any metric drops > 2 percentage points
- Composite drops > 1 percentage point

---

## 🆘 Troubleshooting

**"Baseline file not found" error:**
```bash
# Verify files exist
ls -l quality_scores/baseline_20251030_145945.json
ls -l quality_scores/play_baseline_20251030_151213.json

# If missing, regenerate
/quality-baseline
```

**"Regression detected" during commit:**
```bash
# View comparison
python3 compare_scores.py quality_scores/baseline_*.json quality_scores/test_*.json

# If regression is intentional (rare):
git commit --no-verify -m "Intentional change with regression"
```

---

## 📚 Documentation

- **Quick Reference:** This file
- **Detailed Baseline Info:** [BASELINE_SCORES.md](BASELINE_SCORES.md)
- **Full QA Protocols:** [.claude/CODING_GUIDELINES.md](.claude/CODING_GUIDELINES.md)
- **Project Guide:** [CLAUDE.md](CLAUDE.md)

---

**Last Updated:** 2025-10-30 15:41:00
