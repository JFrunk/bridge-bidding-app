# DDS Testing Philosophy - Development vs Production

**Date:** 2025-10-30
**Issue:** DDS only works on Linux (production), not macOS (local development)
**Question:** Where and how should we test DDS?

---

## The Core Problem

### **Platform Differences:**

| Environment | OS | DDS Available? | Why? |
|-------------|----|-----------------|------|
| **Local Dev (You)** | macOS M1/M2 | ❌ No | DDS crashes on Apple Silicon |
| **GitHub Actions** | Ubuntu Linux | ✅ Yes | Linux x86_64 supported |
| **Production (Render)** | Ubuntu Linux | ✅ Yes | Linux x86_64 supported |

### **The Dilemma:**

You can't test DDS locally, but you need to verify it works before deploying to production.

---

## Philosophy Options

### **Option A: Test in CI/CD (GitHub Actions) - RECOMMENDED**

**Approach:**
- Development branch doesn't need DDS locally
- GitHub Actions (Linux) runs DDS tests automatically
- Only merge to `main` if tests pass
- Production gets pre-tested code

**Workflow:**
```
Local Dev (macOS)
  ↓ (no DDS, use Minimax)
Push to GitHub
  ↓
GitHub Actions (Linux)
  ↓ (runs DDS tests)
  ✅ Pass → merge to main
  ❌ Fail → fix and retry
  ↓
Deploy to Production
  ↓ (DDS already tested)
Production (Linux)
```

**Pros:**
- ✅ Tests DDS before production
- ✅ Catches bugs early
- ✅ No local setup needed
- ✅ Development branch stays consistent with local
- ✅ CI/CD best practice

**Cons:**
- ⚠️ Can't test DDS on your machine
- ⚠️ Need GitHub Actions to verify changes

---

### **Option B: Only Test in Production**

**Approach:**
- Skip DDS testing in CI/CD
- Deploy to production
- Test DDS manually in production
- Monitor with logging system

**Workflow:**
```
Local Dev (macOS)
  ↓ (no DDS testing)
Push to GitHub
  ↓ (skip DDS tests)
Deploy to Production
  ↓
Test in Production
  ↓ (first time you see if DDS works)
Monitor with API endpoints
```

**Pros:**
- ✅ Simple - no CI/CD complexity
- ✅ Matches local dev exactly

**Cons:**
- ❌ Production becomes test environment
- ❌ Users see bugs first
- ❌ Risky deployments
- ❌ Hard to rollback
- ❌ Not recommended practice

---

### **Option C: Hybrid Approach (Best of Both)**

**Approach:**
- Local dev: Use Minimax (Level 8)
- CI/CD: Test both Minimax and DDS
- Production: Enable DDS, with Minimax fallback
- Monitoring: Track DDS health via API

**Workflow:**
```
Local Dev (macOS)
  ↓ (develop with Minimax Level 8)
  ↓ (run: ./test_all.sh)
Push to GitHub
  ↓
GitHub Actions (Linux)
  ↓ (Test 1: Minimax baseline - ensures no regressions)
  ↓ (Test 2: DDS baseline - verifies DDS quality)
  ↓ Both pass → merge to main
  ↓
Deploy to Production
  ↓ (DDS active with fallback)
Production Monitoring
  ↓ (API shows DDS health)
  ↓ (Fallback to Minimax if DDS crashes)
```

**Pros:**
- ✅ Best safety - tests everything
- ✅ Graceful degradation (fallback)
- ✅ Production monitoring
- ✅ Can develop without DDS locally

**Cons:**
- ⚠️ More complex CI/CD setup
- ⚠️ Longer test times

---

## **Recommended Solution: Option C (Hybrid)**

### **Configuration:**

#### **1. Local Development (macOS)**

**Your setup:**
```bash
# In backend/.env (or environment)
DEFAULT_AI_DIFFICULTY=advanced  # Uses Minimax depth 3 (8/10 rating)
```

**What you test:**
```bash
# Run all tests locally
./test_all.sh

# Check play quality with Minimax
python3 backend/test_play_quality_integrated.py --hands 100 --ai minimax --depth 3
```

**Expected:**
- Composite: 75-80% (Grade C-B)
- Success: 60-75%
- Legality: 100%

#### **2. GitHub Actions (Linux)**

**Two workflows:**

**Workflow 1: Minimax Baseline (Always Runs)**
```yaml
# .github/workflows/quality_baseline.yml
- run: python3 backend/test_play_quality_integrated.py --hands 100 --ai minimax --depth 3
```

**Workflow 2: DDS Baseline (Manual or on main branch)**
```yaml
# .github/workflows/dds_baseline.yml
- run: python3 backend/test_play_quality_integrated.py --hands 100 --ai dds
```

**Expected:**
- Minimax: 75-80% (same as local)
- DDS: 90-95% (Grade A)

#### **3. Production (Render Linux)**

**Configuration:**
```bash
# Render Environment Variables
DEFAULT_AI_DIFFICULTY=expert  # Tries DDS first, falls back to Minimax
```

**Monitoring:**
```bash
# Check DDS status
curl https://bridge-bidding-api.onrender.com/api/dds-health

# Expected:
# - dds_fallback_rate < 5%
# - expert_plays > 0
# - avg_solve_time_ms < 200
```

---

## **Why GitHub Actions DDS Test Failed**

### **Most Likely Causes:**

1. **Import Path Issue** (Most Common)
   - Test ran from wrong directory
   - Fixed in updated workflow: `cd backend` before running test

2. **endplay Not Installed Properly**
   - Package installed but imports fail
   - Solution: Run diagnostic workflow to see exact error

3. **DDS Import Error**
   - `engine.play.ai.dds_ai` has bug
   - `DDS_AVAILABLE` stays False even on Linux

### **How to Diagnose:**

Run the diagnostic workflow I just created:

```bash
# Commit the diagnostic workflow
git add .github/workflows/dds_diagnostic.yml
git commit -m "test: Add DDS diagnostic workflow"
git push

# Run it on GitHub
# Go to: Actions → "DDS Diagnostic Test" → Run workflow
```

This will tell you **exactly** where DDS fails in GitHub Actions.

---

## **Your Question: Development Branch Consistency**

### **Should development branch enable DDS just for testing?**

**Answer: No, don't enable DDS in development branch.**

**Reasoning:**

1. **DDS won't work on your local machine anyway** (macOS)
2. **Development branch should match local development environment**
3. **CI/CD is where you test Linux-specific features** (like DDS)
4. **This is standard practice** - dev environment ≠ production environment

**The Right Approach:**

```
Development Branch (development)
├── Code: Works with Minimax
├── Tests: Pass with Minimax
├── Local Testing: Minimax only
└── GitHub Actions: Tests BOTH Minimax AND DDS

Production Branch (main)
├── Code: Same code as development
├── Tests: Already passed in CI/CD
├── Configuration: DDS enabled (via env var)
└── Monitoring: Track DDS health
```

**Key Insight:**
- **Code** is the same in development and production
- **Configuration** (environment variables) changes per environment
- **Testing** happens at different levels (local = Minimax, CI = both, prod = DDS)

---

## **Action Plan**

### **Immediate Steps:**

1. **Commit diagnostic workflow:**
   ```bash
   git add .github/workflows/dds_diagnostic.yml
   git add DDS_TESTING_PHILOSOPHY.md
   git commit -m "docs: Add DDS testing philosophy and diagnostic workflow"
   git push origin development
   ```

2. **Run diagnostic on GitHub Actions:**
   - Go to Actions → "DDS Diagnostic Test" → Run workflow
   - This will show exactly why DDS test is failing

3. **Fix based on diagnostic results:**
   - If import error → fix module path
   - If endplay missing → check requirements.txt
   - If platform issue → verify running on Linux

4. **Once working:**
   - Run full DDS test: 100 hands (~20 min)
   - Verify composite score 90-95%
   - Compare with Minimax baseline

### **Long-term Setup:**

1. **Local Development:**
   - Use Minimax (advanced level)
   - Run `./test_all.sh` before commits
   - Don't worry about DDS

2. **CI/CD (GitHub Actions):**
   - Minimax tests run automatically on every push
   - DDS tests run manually or on main branch merge
   - Block merge if tests fail

3. **Production:**
   - DDS enabled via `DEFAULT_AI_DIFFICULTY=expert`
   - Monitor with `/api/dds-health` endpoint
   - Automatic fallback to Minimax if DDS crashes

---

## **Summary**

**Your development workflow:**
```
Local (macOS) → Minimax only → Push to GitHub
  ↓
GitHub Actions (Linux) → Test Minimax + DDS → Merge if pass
  ↓
Production (Linux) → DDS active → Monitor health
```

**You asked:**
> "Is the issue that DDS is just enabled once the code is promoted to production?"

**Answer:** Yes! And that's the **correct approach**:
- Development = Minimax (what you can test locally)
- CI/CD = Both (verifies Linux compatibility)
- Production = DDS (optimal performance)

**You asked:**
> "Should we enable DDS in development branch for testing then disable it?"

**Answer:** No! Because:
- DDS won't work on your macOS anyway
- Development branch should match your local environment
- GitHub Actions (Linux) is where you test DDS
- Use configuration (env vars), not code changes, to enable DDS

---

## **Next Step**

**Run the diagnostic workflow to see exactly why GitHub Actions DDS test failed:**

1. Push the diagnostic workflow
2. Run it manually on GitHub
3. Share the results
4. I'll help fix the specific issue

The diagnostic will tell us whether it's:
- Import path problem → Fix workflow
- endplay installation → Fix requirements
- Module bug → Fix code

Let's find out! 🔍
