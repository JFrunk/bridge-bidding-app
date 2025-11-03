# DDS Testing - Next Steps (Quick Reference)

**Date:** 2025-10-30
**Status:** GitHub Actions DDS test failed - need diagnostic

---

## 🎯 What You Asked

> "Is the issue that DDS is just enabled once the code is promoted to production, so a development branch will not have DDS testing ability?"

**Answer:** **Yes, exactly!** And that's the **correct approach**.

---

## ✅ The Right Philosophy

### **Development Branch (Your Local):**
- Uses **Minimax** (Level 8, ~80% quality)
- No DDS needed (macOS doesn't support it anyway)
- Tests pass locally with Minimax

### **GitHub Actions (Linux CI/CD):**
- Tests **both Minimax AND DDS**
- Verifies DDS works before production
- Catches Linux-specific issues

### **Production (Render):**
- Uses **DDS** (Level 10, ~95% quality)
- Enabled via environment variable
- Automatic fallback to Minimax if DDS crashes

---

## 🔍 Why GitHub Actions Failed

**Most likely cause:** Import path issue (test ran from wrong directory)

**What I fixed:**
1. Updated workflow to run from `backend/` directory
2. Added verification step to check DDS availability
3. Added better error messages

**But we need to verify the fix works!**

---

## 🚀 Next Steps (What to Do Now)

### **Step 1: Commit New Files**

```bash
git add .github/workflows/dds_diagnostic.yml
git add .github/workflows/dds_baseline.yml
git add DDS_TESTING_PHILOSOPHY.md
git add DDS_TESTING_WITHOUT_SHELL_ACCESS.md
git add DDS_TESTING_NEXT_STEPS.md
git commit -m "test: Add DDS diagnostic workflow and fix baseline test"
git push origin development
```

### **Step 2: Run Diagnostic Workflow**

1. Go to: **https://github.com/[your-repo]/actions**
2. Click: **"DDS Diagnostic Test"** workflow
3. Click: **"Run workflow"** button
4. Click: **"Run workflow"** to confirm
5. Wait: ~2 minutes

### **Step 3: Check Diagnostic Results**

The diagnostic will test **7 steps** to find exactly where DDS fails:

- ✅ Step 1: Is `endplay` installed?
- ✅ Step 2: Can we import `endplay.types` and `endplay.dds`?
- ✅ Step 3: Can we import our DDS module from root?
- ✅ Step 4: Can we import our DDS module from backend?
- ✅ Step 5: Can we create a DDSPlayAI instance?
- ✅ Step 6: Platform info (should be Linux)
- ✅ Step 7: Can we run test with 1 hand?

**Look for the first ❌** - that's where it fails!

### **Step 4: Fix Based on Results**

**If Step 1 fails** (endplay not installed):
```yaml
# Check requirements.txt has:
endplay>=0.5.0
```

**If Step 3 or 4 fails** (import path):
```yaml
# Workflow should have:
cd backend
python3 test_play_quality_integrated.py ...
```

**If Step 5 fails** (DDS import but not available):
```python
# Check engine/play/ai/dds_ai.py line 23-28
# The import might be failing silently
```

**If Step 7 fails** (test script):
```python
# Check test_play_quality_integrated.py line 82-84
# Might need better error handling
```

### **Step 5: Once Working, Run Full Test**

```bash
# On GitHub Actions:
# Run "DDS Play Quality Baseline" workflow
# - hands: 100
# - ai_level: dds
# Duration: ~20 minutes
# Expected: Composite 90-95%, Grade A
```

---

## 📊 Expected Outcomes

### **Minimax Baseline (Local & CI):**
```
AI Type:         Minimax (depth 3)
Hands:          100
Composite:      75-80%
Success Rate:   60-75%
Grade:          C-B
```

### **DDS Baseline (CI & Production):**
```
AI Type:         DDS
Hands:          100
Composite:      90-95%
Success Rate:   85-95%
Grade:          A
```

### **Improvement:**
DDS should be **+15-20 points** better than Minimax.

---

## 🎓 Key Insights

### **Your Development Workflow:**

```
┌─────────────────────────────────────────────┐
│ Local Development (macOS)                   │
│ - Code changes                              │
│ - Test with Minimax                         │
│ - ./test_all.sh passes                      │
└─────────────────┬───────────────────────────┘
                  │ git push
                  ↓
┌─────────────────────────────────────────────┐
│ GitHub Actions (Ubuntu Linux)               │
│ - Test 1: Minimax baseline (ensure no reg)  │
│ - Test 2: DDS baseline (verify DDS works)   │
│ - Both pass → approve merge                  │
└─────────────────┬───────────────────────────┘
                  │ merge to main
                  ↓
┌─────────────────────────────────────────────┐
│ Production (Render Linux)                   │
│ - DDS enabled (DEFAULT_AI_DIFFICULTY=expert)│
│ - Monitor via /api/dds-health                │
│ - Automatic fallback if DDS crashes          │
└─────────────────────────────────────────────┘
```

### **You DON'T need to:**
- ❌ Enable DDS in development branch
- ❌ Test DDS on your local machine
- ❌ Change code between dev and production

### **You DO need to:**
- ✅ Test Minimax locally before committing
- ✅ Let GitHub Actions test DDS (on Linux)
- ✅ Use environment variables to enable DDS in production
- ✅ Monitor DDS health via API endpoints

---

## 📞 What to Share

After running the diagnostic, share:

1. **Which step failed?** (Step 1-7)
2. **What error message?** (from the logs)
3. **Any red ❌ output?**

Then I can provide the exact fix!

---

## 📚 Documentation Created

1. **[.github/workflows/dds_diagnostic.yml](.github/workflows/dds_diagnostic.yml)** - Diagnostic workflow (NEW)
2. **[.github/workflows/dds_baseline.yml](.github/workflows/dds_baseline.yml)** - Fixed baseline test (UPDATED)
3. **[DDS_TESTING_PHILOSOPHY.md](DDS_TESTING_PHILOSOPHY.md)** - Complete philosophy (NEW)
4. **[DDS_TESTING_WITHOUT_SHELL_ACCESS.md](DDS_TESTING_WITHOUT_SHELL_ACCESS.md)** - Alternative methods (EXISTING)
5. **[DDS_TESTING_NEXT_STEPS.md](DDS_TESTING_NEXT_STEPS.md)** - This quick reference (NEW)

---

## ⏰ Time Estimate

- Commit files: **2 minutes**
- Run diagnostic: **2 minutes**
- Review results: **1 minute**
- Apply fix: **5 minutes** (depends on issue)
- Run full test: **20 minutes**
- **Total: ~30 minutes** to get DDS baseline working

---

## 🎯 TL;DR

1. **Commit the new files** (diagnostic workflow + docs)
2. **Run "DDS Diagnostic Test"** on GitHub Actions
3. **Share which step fails** and the error message
4. **Apply the fix** based on diagnostic
5. **Run full DDS test** (100 hands)
6. **Compare with Minimax** baseline

**Your philosophy is correct:** Keep development branch simple (Minimax), test DDS in CI/CD (Linux), enable DDS in production (env vars).

Let's run that diagnostic! 🚀
