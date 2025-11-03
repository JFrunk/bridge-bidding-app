# Baseline Tracking System - Complete Index

**Last Updated:** 2025-10-30
**Status:** ✅ Fully Operational

This document serves as the central index for the baseline quality score tracking system.

---

## 🎯 Quick Start (Choose Your Tool)

| Tool | Use Case | Command |
|------|----------|---------|
| **Python Script** | Visual display with colors | `python3 quick_baseline_check.py` |
| **Shell Script** | Portable bash version | `./check_baseline_status.sh` |
| **CSV Output** | Parse in scripts/tools | `python3 quick_baseline_check.py --csv` |
| **JSON Output** | API/automation | `python3 quick_baseline_check.py --json` |
| **Comprehensive Run** | Generate new baselines | `/quality-baseline` |

---

## 📊 Current Baseline Files (2025-10-30)

### Bidding Quality: 94.8% (Grade B)
- **File:** `quality_scores/baseline_20251030_145945.json`
- **Size:** 32 KB
- **Hands Tested:** 500
- **Status:** 🟡 Near Production Ready (+0.2 points needed)

### Play Quality: 80.3% (Grade C)
- **File:** `quality_scores/play_baseline_20251030_151213.json`
- **Size:** 814 B
- **Hands Tested:** 500
- **Status:** 🟢 Baseline Acceptable

---

## 📁 Documentation Files

### Primary Documentation

1. **[QUICK_START_BASELINE.md](QUICK_START_BASELINE.md)** ⭐ **START HERE**
   - Rapid developer reference
   - Common commands
   - Quick workflows
   - Best for: Day-to-day development

2. **[BASELINE_SCORES.md](BASELINE_SCORES.md)** 📚 **COMPREHENSIVE**
   - Complete baseline documentation
   - Historical tracking
   - Production gates
   - Quality thresholds
   - Best for: Understanding full system

3. **This File** 🗺️ **NAVIGATION**
   - System index
   - File locations
   - Tool comparison
   - Best for: Finding what you need

### Supporting Documentation

4. **[quality_scores/README.md](quality_scores/README.md)**
   - Detailed historical tracking
   - All past baselines
   - Comparison instructions

5. **[quality_scores/baseline_history.csv](quality_scores/baseline_history.csv)**
   - Machine-readable history
   - All baselines in CSV format
   - Easy parsing for tools

---

## 🛠️ Tools & Scripts

### Status Check Tools

| Tool | Type | Output | Use Case |
|------|------|--------|----------|
| `quick_baseline_check.py` | Python | Visual/CSV/JSON | Primary tool, multiple formats |
| `check_baseline_status.sh` | Bash | Visual | Portable, no Python needed |

### Test Running Tools

| Tool | Type | Duration | Purpose |
|------|------|----------|---------|
| `/quality-baseline` | Slash cmd | 12 min | Run both baselines (500 hands) |
| `test_bidding_quality_score.py` | Python | 10 min | Bidding only (500 hands) |
| `test_play_quality_score.py` | Python | 2 min | Play only (500 hands) |

### Comparison Tools

| Tool | Type | Purpose |
|------|------|---------|
| `compare_scores.py` | Python | Compare bidding baselines |
| `compare_play_scores.py` | Python | Compare play baselines |

---

## 🎨 Output Format Comparison

### Visual Display (Default)
```bash
python3 quick_baseline_check.py
```
- ✅ Color-coded
- ✅ Production readiness
- ✅ Detailed breakdown
- Best for: Human reading

### CSV Format
```bash
python3 quick_baseline_check.py --csv
```
```
Timestamp,System,Composite,Grade,Legality,Key_Metric,Status
2025-10-30T14:59:45.869044,Bidding,94.8,B,100.0,100.0,NEAR_READY
```
- ✅ Machine-readable
- ✅ Easy parsing
- Best for: Scripts, spreadsheets

### JSON Format
```bash
python3 quick_baseline_check.py --json
```
```json
{
  "bidding": {
    "composite": 94.8,
    "grade": "B",
    "production_ready": false
  }
}
```
- ✅ Structured data
- ✅ API-friendly
- Best for: Automation, tools

---

## 🔄 Common Workflows

### 1. Check Current Status
```bash
# Quick visual check
python3 quick_baseline_check.py

# Production readiness only
./check_baseline_status.sh --production
```

### 2. Before Committing Bidding Changes
```bash
# Run test
python3 backend/test_bidding_quality_score.py --hands 500 \
  --output quality_scores/test_$(date +%Y%m%d_%H%M%S).json

# Compare
python3 compare_scores.py \
  quality_scores/baseline_20251030_145945.json \
  quality_scores/test_YYYYMMDD_HHMMSS.json
```

### 3. Before Committing Play Changes
```bash
# Run test
python3 backend/test_play_quality_score.py --hands 500 \
  --output quality_scores/play_test_$(date +%Y%m%d_%H%M%S).json

# Compare
python3 compare_play_scores.py \
  quality_scores/play_baseline_20251030_151213.json \
  quality_scores/play_test_YYYYMMDD_HHMMSS.json
```

### 4. Generate New Comprehensive Baseline
```bash
# Run comprehensive test (both systems, 500 hands each)
/quality-baseline

# Files created:
# - quality_scores/baseline_YYYYMMDD_HHMMSS.json
# - quality_scores/play_baseline_YYYYMMDD_HHMMSS.json
# - Updated quality_scores/README.md
```

### 5. Quick Smoke Test During Development
```bash
# Fast 100-hand tests for iteration
python3 backend/test_bidding_quality_score.py --hands 100
python3 backend/test_play_quality_score.py --hands 100
```

---

## 📈 Integration Points

### Current Integrations

- ✅ **Pre-commit Hook:** Warns on regressions
- ✅ **Slash Command:** `/quality-baseline` runs comprehensive tests
- ✅ **CSV Export:** Machine-readable tracking
- ✅ **JSON Export:** API-ready format

### Future Integrations (Planned)

- ⏳ **GitHub Actions:** Auto-run on PR creation
- ⏳ **PR Comments:** Post comparison reports automatically
- ⏳ **CI/CD Pipeline:** Block merge on critical regression
- ⏳ **Trend Charts:** Visualize quality over time
- ⏳ **Slack Alerts:** Notify on quality drops

---

## 🎯 Quality Gates

### Production Deployment Requirements

**Bidding System (BLOCKING):**
- Legality: 100% (current: ✅ 100%)
- Appropriateness: ≥95% (current: ✅ 100%)
- Conventions: ≥98% (current: ✅ 98.8%)
- Composite: ≥95% (current: ⚠️ 94.8% - **NEEDS +0.2**)

**Play System (NON-BLOCKING):**
- Legality: 100% (current: ✅ 100%)
- Success Rate: ≥65% (current: ⚠️ 60.4%)
- Composite: ≥80% (current: ✅ 80.3%)

### Regression Thresholds

**Auto-reject commit if:**
- Legality drops below 100%
- Bidding appropriateness < 95%
- Bidding composite < 90%

**Warning triggers if:**
- Any metric drops > 2 points
- Composite drops > 1 point

---

## 📊 Current Status Summary

```
╔══════════════════════════════════════════════════════════════╗
║  BASELINE QUALITY SCORES - CURRENT STATUS (2025-10-30)      ║
╠══════════════════════════════════════════════════════════════╣
║  📊 BIDDING: 94.8% (Grade B) - 🟡 NEAR READY               ║
║     • Legality:        100.0% ✅                             ║
║     • Appropriateness: 100.0% ✅ (major improvement!)       ║
║     • Conventions:      98.8% ✅                             ║
║     • Action: Fix 3 Stayman errors → 95% composite          ║
║                                                              ║
║  🃏 PLAY: 80.3% (Grade C) - 🟢 ACCEPTABLE                   ║
║     • Legality:     100.0% ✅                                ║
║     • Success Rate:  60.4% ⚠️                                ║
║     • Efficiency:    50.9% ⚠️                                ║
║     • Recommended: Increase Minimax depth 2 → 3             ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🆘 Troubleshooting

### "Baseline file not found"
```bash
# Verify files exist
ls -l quality_scores/baseline_20251030_145945.json
ls -l quality_scores/play_baseline_20251030_151213.json

# If missing, regenerate
/quality-baseline
```

### "Permission denied" on scripts
```bash
# Make scripts executable
chmod +x quick_baseline_check.py
chmod +x check_baseline_status.sh
```

### "No such file or directory" on compare
```bash
# Ensure compare scripts exist
ls -l compare_scores.py
ls -l compare_play_scores.py

# If missing, check project root
find . -name "compare_*.py"
```

---

## 📚 Related Documentation

### In This Project
- [CLAUDE.md](CLAUDE.md) - Quality Assurance Protocols section
- [.claude/CODING_GUIDELINES.md](.claude/CODING_GUIDELINES.md) - Lines 343-1027 (QA protocols)
- [READY_FOR_PRODUCTION.md](READY_FOR_PRODUCTION.md) - Deployment checklist

### External Resources
- Standard American Yellow Card (SAYC) specification
- Bridge Laws by World Bridge Federation
- Double Dummy Solver documentation

---

## 🚀 Next Steps

### Immediate (This Week)
1. Fix 3 Stayman errors
2. Reach 95% bidding composite
3. Update baselines

### Short Term (Next 2 Weeks)
1. Implement Game/Slam scoring
2. Increase Play Minimax depth to 3
3. Reach 85% play composite

### Medium Term (Next Month)
1. Optimize play heuristics
2. Achieve Grade A for both systems
3. Production deployment

---

**Quick Access:**
- Status Check: `python3 quick_baseline_check.py`
- Documentation: [QUICK_START_BASELINE.md](QUICK_START_BASELINE.md)
- Full Details: [BASELINE_SCORES.md](BASELINE_SCORES.md)

---

**Last Updated:** 2025-10-30 15:45:00
**Maintained By:** Development Team
**Status:** ✅ Fully Operational
