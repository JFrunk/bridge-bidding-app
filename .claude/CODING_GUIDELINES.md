# Claude Coding Guidelines - Bridge Bidding App

## Systematic Issue Analysis Protocol

### When Investigating Any Issue

**MANDATORY**: Before implementing any fix, complete this systematic analysis:

#### 🔍 Step 1: Identify & Search (2 minutes)
```bash
# After finding root cause, immediately search for similar patterns
# Example: If issue involves useEffect + data fetching
grep -r "useEffect" --include="*.js" --include="*.jsx" frontend/src/
grep -r "modal.*useState\|Dialog.*useState" --include="*.js*" frontend/src/
```

**Questions**:
- [ ] Does this pattern appear in other components?
- [ ] Are there similar hooks/lifecycle patterns?
- [ ] Do other features use the same data fetching approach?

#### 📊 Step 2: Document Scope (1 minute)
Create a quick list:
- **Immediate issue**: [component/feature affected]
- **Pattern found in**: [list all similar occurrences]
- **Actually affected**: [which ones exhibit the bug]
- **Preventatively fix**: [which ones could have the bug later]

#### 💡 Step 3: Solution Design (1 minute)
- **1 occurrence**: Fix locally
- **2-3 occurrences**: Fix all instances, consider shared utility
- **4+ occurrences**: Create abstraction (hook/service), fix architecturally

#### 📝 Step 4: Present to User
```
## Systematic Analysis Complete

**Reported**: [user's description]
**Root Cause**: [technical cause]
**Scope**: Found in [N] components

**All Affected**:
1. ComponentA - [status]
2. ComponentB - [status]

**Solution**: [approach that fixes all instances]

Proceed with implementation?
```

---

## Common Patterns in This Codebase

### Modal/Dialog Data Refresh Pattern

**Problem**: Modals that fetch data on mount show stale data when reopened.

**Detection**:
```bash
# Find potentially affected modals
grep -r "Modal\|Dialog.*useState.*show" --include="*.js*" frontend/src/
grep -r "useEffect.*\[\]" --include="*.js*" frontend/src/components/
```

**Solution**:
```jsx
// Option 1: Force remount with key
{showModal && <Modal key={Date.now()} />}

// Option 2: Fetch on open change
useEffect(() => {
  if (isOpen) {
    loadData();
  }
}, [isOpen]);
```

**When to use which**:
- Use `key` when: Component is complex, has internal state, simpler implementation
- Use `isOpen` effect when: Fine-grained control needed, performance critical

### Data Fetching in Components

**Red Flags**:
```jsx
// ⚠️ Only fetches once - check if this is intentional
useEffect(() => {
  fetchData();
}, []);

// ⚠️ Might not update when parent re-renders
const [data, setData] = useState(null);
```

**Questions to ask**:
- Should this data refresh when component becomes visible again?
- Is this inside a modal/tab/collapsible section?
- Does user expect fresh data each time they view this?

---

## Specific Issue Types & Search Commands

### Issue: Stale Data in UI

**Search for**:
```bash
# Find all data caching patterns
grep -r "useState.*Data" --include="*.js*" frontend/src/
grep -r "setState.*fetch\|setData.*fetch" --include="*.js*" frontend/src/

# Find components that might not refresh
grep -r "useEffect.*load.*\[\]" --include="*.js*" frontend/src/
```

### Issue: Race Conditions

**Search for**:
```bash
# Find async state updates
grep -r "async.*set[A-Z]" --include="*.js*" frontend/src/
grep -r "setTimeout.*set[A-Z]" --include="*.js*" frontend/src/
```

### Issue: Memory Leaks

**Search for**:
```bash
# Find effects without cleanup
grep -B5 "useEffect" frontend/src/**/*.js | grep -v "return () =>"
grep -r "addEventListener" --include="*.js*" frontend/src/
```

### Issue: Props Drilling

**Search for**:
```bash
# Find deeply passed props
grep -r "props\.[a-z]*\.[a-z]*\.[a-z]*" --include="*.js*" frontend/src/
```

---

## Quick Reference: When Claude Finds...

| Root Cause | Immediate Action | Search For |
|------------|------------------|------------|
| useEffect fetches once | Search other modals | `grep -r "Modal.*useEffect"` |
| State not updating | Find similar state patterns | `grep -r "useState.*[DataState]"` |
| Prop not passed down | Check component tree | `grep -r "props\.[prop]"` |
| API call issues | Find all API calls | `grep -r "fetch.*API_URL"` |
| Memory leak | Find all subscriptions | `grep -r "addEventListener\|subscribe"` |

---

## Project-Specific Patterns

### Dashboard Components
All dashboard components fetch from single API endpoint:
- **API**: `/api/analytics/dashboard`
- **Components**: LearningDashboard → 7 sub-components
- **Pattern**: Single fetch on mount populates all cards
- **Refresh strategy**: Remount entire dashboard (key prop)

### Modal Components
Current modals in project:
1. **LearningDashboard** - Refreshes on open (fixed 2025-10-19)
2. **ReviewModal** - Static content (OK)
3. **ConventionHelpModal** - Static content (OK)
4. **ScoreDisplay** - Fresh data passed via props (OK)
5. **SimpleLogin** - No data fetching (OK)

**Pattern**: Only LearningDashboard needs refresh-on-open behavior.

### Session Management
- Session data flows from App.js → components via props
- Backend maintains session state
- Frontend polls on user actions, not on timers
- **No automatic refresh needed** - user-driven updates only

---

## Examples: Good Systematic Analysis

### Example 1: The Dashboard Issue

```
## Issue Analysis

**Reported**: "Recent bidding decisions appear static"

**Root Cause**: LearningDashboard only fetches data on mount
- useEffect([userId]) doesn't re-run on modal reopen
- React reuses component instance, serves cached state

**Pattern Search**:
grep -r "Modal.*useEffect" frontend/src/
Found:
- ✅ LearningDashboard - AFFECTED (fetches dynamic data)
- ⚠️ ReviewModal - Uses passed data (OK)
- ⚠️ ConventionHelpModal - Fetches static content (OK)

**Scope**: 1 modal, but affects ALL 7 dashboard cards:
1. User stats
2. Gameplay stats
3. Bidding quality
4. Recent decisions ← reported
5. Growth areas
6. Recent wins
7. Practice recommendations

**Solution**: key={Date.now()} on LearningDashboard
- Fixes all 7 components with 1 line
- Forces fresh data on every open
- No component modifications needed

**Why not fix inside LearningDashboard?**
- Would require tracking isOpen state
- Would need to pass isOpen prop through
- Current API design expects mount = fetch
- Key approach is simpler & idiomatic React

Proceed? ✅
```

### Example 2: Hypothetical API Timeout Issue

```
## Issue Analysis

**Reported**: "Sometimes bids don't register"

**Root Cause**: No timeout on fetch() calls
- Network delays cause indefinite hangs
- User doesn't get feedback
- Might retry, causing double-submissions

**Pattern Search**:
grep -r "fetch(" frontend/src/
Found 47 instances! Check each:

Categories:
- API calls: 23 instances
- Image loads: 8 instances
- External resources: 3 instances
- Test mocks: 13 instances

**Affected API Calls**:
1. /api/get-next-bid - CRITICAL
2. /api/play-card - CRITICAL
3. /api/deal-hands - HIGH
4. /api/get-feedback - MEDIUM
... (list all)

**Solution**: Create fetchWithTimeout utility
```javascript
// utils/api.js
export const fetchWithTimeout = (url, options = {}, timeout = 5000) => {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), timeout)
    )
  ]);
};
```

**Implementation**:
1. Create utility (1 file)
2. Replace all API fetch() calls (23 files)
3. Add error handling UI
4. Add retry logic for critical calls

Proceed? ✅
```

---

## Meta-Guideline: Training the Model

### Prime Claude at Session Start

Good opening prompt:
```
Hi Claude! We're debugging [ISSUE].

Please use systematic analysis:
1. Find immediate cause
2. Search codebase for similar patterns
3. Assess full scope
4. Propose comprehensive solution

Reference: .claude/CODING_GUIDELINES.md
```

### Mid-Session Reminders

When Claude identifies root cause, ask:
- "Have you searched for this pattern elsewhere?"
- "What else might be affected?"
- "Let's do a systematic check before implementing"

### Positive Reinforcement

When Claude does systematic analysis unprompted:
- "Great systematic analysis!"
- "Thanks for checking the broader scope"
- This trains both you and the model

---

## Success Checklist

After each issue resolution, verify:

- [ ] Root cause identified
- [ ] Similar patterns searched
- [ ] All affected components listed
- [ ] Comprehensive solution proposed
- [ ] Fix applied to all instances
- [ ] Pattern documented to prevent recurrence
- [ ] Tests added if applicable

---

## Emergency Override

Sometimes you KNOW it's isolated. Use this:

```
Claude, I've verified this is an isolated issue.
Please fix only [SPECIFIC_COMPONENT].
Skip systematic analysis for this one.
```

Use sparingly - usually broad analysis finds hidden issues!

---

---

## Bidding Logic Quality Assurance Protocol

### MANDATORY: Baseline Quality Score Before Bidding Changes

**ALWAYS run baseline quality score before committing any changes to bidding logic.**

#### 🎯 When to Run Baseline Quality Score

Run baseline quality score test BEFORE:
- Modifying any bidding module (`backend/engine/*.py`)
- Changing convention logic (`backend/engine/ai/conventions/*.py`)
- Updating bid validation (`backend/engine/bidding_validation.py`)
- Modifying base convention class
- Any change that affects bid generation or evaluation

#### 📊 How to Run Baseline Quality Score

**Quick Test (5 minutes):**
```bash
# 100 hands - fast feedback during development
python3 backend/test_bidding_quality_score.py --hands 100 --output baseline_quick.json
```

**Comprehensive Test (15 minutes):**
```bash
# 500 hands - required before commits/PRs
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_comprehensive.json
```

#### 📋 Standard Workflow

**1. Before Starting Work:**
```bash
# Establish baseline
git checkout main
git pull
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_before.json
```

**2. During Development:**
```bash
# Quick checks during iteration (100 hands)
python3 backend/test_bidding_quality_score.py --hands 100
```

**3. Before Committing:**
```bash
# Comprehensive test (500 hands)
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_after.json

# Compare scores
python3 compare_scores.py baseline_before.json baseline_after.json
```

#### ✅ Quality Score Requirements

**Minimum Requirements (BLOCKING):**
- ✅ **Legality: 100%** (no illegal bids allowed)
- ✅ **Composite: ≥ baseline** (no regression)
- ✅ **Appropriateness: ≥ baseline** (no regression)

**Target Scores:**
- 🎯 **Legality: 100%** (must be perfect)
- 🎯 **Appropriateness: 95%+** (excellent)
- 🎯 **Conventions: 90%+** (good)
- 🎯 **Composite: 95%+** (Grade A - production ready)

**Grade Scale:**
- A (95-100%): Production ready ✅
- B (90-94%): Good, minor issues ⚠️
- C (85-89%): Acceptable, needs work ⚠️
- D (80-84%): Poor, major issues ❌
- F (<80%): Failing, do not deploy ⛔

#### 🚫 When to Block Commits

**DO NOT COMMIT if:**
- Legality score < 100% (illegal bids)
- Composite score drops >2% from baseline
- Appropriateness score drops >5% from baseline
- Any new "Terrible" bids introduced

**Example:**
```
Baseline:  89.7% composite, 78.7% appropriateness
After fix: 87.2% composite, 75.1% appropriateness
         ❌ BLOCKED - regression detected
```

#### 📈 Score Comparison Script

Create `compare_scores.py` to compare before/after:

```python
#!/usr/bin/env python3
"""Compare two quality score reports."""
import json
import sys

def compare_scores(baseline_file, new_file):
    with open(baseline_file) as f:
        baseline = json.load(f)
    with open(new_file) as f:
        new = json.load(f)

    b_scores = baseline['scores']['scores']
    n_scores = new['scores']['scores']

    print("=" * 80)
    print("QUALITY SCORE COMPARISON")
    print("=" * 80)
    print()
    print(f"Baseline: {baseline_file}")
    print(f"New:      {new_file}")
    print()
    print("-" * 80)
    print(f"{'Metric':<20} {'Baseline':>10} {'New':>10} {'Delta':>10} {'Status':>10}")
    print("-" * 80)

    metrics = ['legality', 'appropriateness', 'conventions', 'reasonableness', 'game_slam', 'composite']
    regression = False

    for metric in metrics:
        baseline_score = b_scores[metric]
        new_score = n_scores[metric]
        delta = new_score - baseline_score

        if metric == 'legality' and new_score < 100:
            status = "❌ FAIL"
            regression = True
        elif metric == 'composite' and delta < -2:
            status = "❌ REGR"
            regression = True
        elif metric == 'appropriateness' and delta < -5:
            status = "❌ REGR"
            regression = True
        elif delta >= 5:
            status = "✅ IMPR"
        elif delta >= 0:
            status = "✅ OK"
        elif delta >= -2:
            status = "⚠️  MINOR"
        else:
            status = "❌ REGR"

        print(f"{metric.capitalize():<20} {baseline_score:>9.1f}% {new_score:>9.1f}% {delta:>+9.1f}% {status:>10}")

    print("-" * 80)
    print()

    if regression:
        print("⛔ REGRESSION DETECTED - Do not commit!")
        return 1
    else:
        print("✅ Quality score acceptable")
        return 0

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 compare_scores.py baseline.json new.json")
        sys.exit(1)

    sys.exit(compare_scores(sys.argv[1], sys.argv[2]))
```

#### 📁 File Organization

Keep quality score reports organized:

```
project_root/
├── baseline_quality_score_500.json       # Current baseline (500 hands)
├── quality_scores/                       # Historical scores
│   ├── 2025-10-28_baseline.json
│   ├── 2025-10-29_after_appropriateness_fix.json
│   ├── 2025-10-30_after_convention_fix.json
│   └── README.md                         # Score history log
└── backend/
    └── test_bidding_quality_score.py     # Test script
```

#### 🔄 CI/CD Integration

**Git Pre-Commit Hook:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if bidding logic files changed
BIDDING_FILES=$(git diff --cached --name-only | grep -E 'backend/engine/(.*\.py|ai/conventions/.*\.py)')

if [ -n "$BIDDING_FILES" ]; then
    echo "🎯 Bidding logic changed - running quality score..."
    python3 backend/test_bidding_quality_score.py --hands 100

    if [ $? -ne 0 ]; then
        echo "❌ Quality score check failed!"
        exit 1
    fi
fi
```

**GitHub Actions:**
```yaml
# .github/workflows/bidding_quality.yml
name: Bidding Quality Check

on:
  pull_request:
    paths:
      - 'backend/engine/**/*.py'
      - 'backend/engine/ai/conventions/**/*.py'

jobs:
  quality_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Quality Score (100 hands for speed)
        run: python3 backend/test_bidding_quality_score.py --hands 100
      - name: Check for regressions
        run: |
          if [ -f baseline_quality_score_500.json ]; then
            python3 compare_scores.py baseline_quality_score_500.json quality_score.json
          fi
```

#### 📊 Example: Good Quality Score Workflow

**Scenario:** Fixing appropriateness validation

```bash
# 1. Establish baseline
git checkout main
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_before_fix.json
# Result: 89.7% composite, 78.7% appropriateness (Grade C)

# 2. Create feature branch
git checkout -b fix/bid-appropriateness

# 3. Implement fix
# ... make changes ...

# 4. Quick test during development
python3 backend/test_bidding_quality_score.py --hands 100
# Result: 91.2% composite - looking good!

# 5. Comprehensive test before commit
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_after_fix.json
# Result: 92.4% composite, 90.1% appropriateness (Grade B)

# 6. Compare scores
python3 compare_scores.py baseline_before_fix.json baseline_after_fix.json
# Result: +2.7% composite, +11.4% appropriateness ✅

# 7. Commit with confidence
git add .
git commit -m "fix: Add bid appropriateness validation

- Implemented centralized appropriateness checking in base class
- Updated all 16 bidding modules
- Quality score improved: 89.7% → 92.4% (+2.7 points)
- Appropriateness improved: 78.7% → 90.1% (+11.4 points)
- Grade: C → B

Tested: 500 hands, no regressions detected"
```

#### 🎓 Historical Baseline

**Current Baseline (as of 2025-10-28):**
```
Test: 500 hands, 3,013 bids, 919 non-pass bids
Composite Score: 89.7% (Grade C)

Breakdown:
- Legality:        100.0% ✅ (0 errors)
- Appropriateness:  78.7% ❌ (196 errors)
- Conventions:      99.7% ✅ (1 error)
- Reasonableness:   92.1% ✅
- Game/Slam:        24.7% ❌ (113 errors)

Key Issues:
- 48% of errors: Bidding 3-card suits (94 errors)
- 15.8% of errors: Weak hands at 4-level (31 errors)
- 13.8% of errors: Weak hands at 3-level (27 errors)
```

**Target Baseline (after appropriateness fix):**
```
Expected Composite: 92-95% (Grade B to A)
Expected Appropriateness: 90-95%
```

#### 💡 Pro Tips

**1. Test incrementally:**
- Use 100 hands during development (fast feedback)
- Use 500 hands before commits (comprehensive)

**2. Save baselines:**
- Tag major baselines in git: `git tag baseline-2025-10-28`
- Keep JSON files for comparison

**3. Watch for patterns:**
- Recurring error types indicate systemic issues
- Use detailed error analysis to guide fixes

**4. Don't over-optimize:**
- 95% is excellent (Grade A)
- 100% is impossible (some edge cases are debatable)

**5. Context matters:**
- Some "errors" might be advanced techniques
- Review error details, not just scores

---

## Play Logic Quality Assurance Protocol

### MANDATORY: Baseline Play Quality Score Before Play Logic Changes

**ALWAYS run baseline play quality score before committing any changes to play logic.**

#### 🎯 When to Run Baseline Play Quality Score

Run baseline play quality score test BEFORE:
- Modifying play engine (`backend/engine/play_engine.py`)
- Changing play AI logic (`backend/engine/play/ai/*.py`)
- Updating card selection algorithms
- Modifying trick evaluation or winner determination
- Changing contract execution logic
- Any change that affects card play decisions or gameplay

#### 📊 How to Run Baseline Play Quality Score

**Quick Test (10 minutes):**
```bash
# 100 hands - fast feedback during development
python3 backend/test_play_quality_integrated.py --hands 100 --output play_baseline_quick.json
```

**Comprehensive Test (30 minutes):**
```bash
# 500 hands - required before commits/PRs
python3 backend/test_play_quality_integrated.py --hands 500 --output play_baseline_comprehensive.json
```

**Specify AI Level:**
```bash
# Test specific AI level (1-10)
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_baseline_level8.json
```

**Expert DDS Testing (Production Only - Linux):**
```bash
# DDS testing - only on Linux production servers
python3 backend/test_play_quality_integrated.py --hands 500 --level 10 --output play_baseline_dds.json
```

#### 📋 Standard Workflow

**1. Before Starting Work:**
```bash
# Establish baseline for current AI level
git checkout main
git pull
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_baseline_before.json
```

**2. During Development:**
```bash
# Quick checks during iteration (100 hands)
python3 backend/test_play_quality_integrated.py --hands 100 --level 8
```

**3. Before Committing:**
```bash
# Comprehensive test (500 hands)
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_baseline_after.json

# Compare scores
python3 compare_play_scores.py play_baseline_before.json play_baseline_after.json
```

#### ✅ Play Quality Score Requirements

**Minimum Requirements (BLOCKING):**
- ✅ **Legality: 100%** (no illegal plays allowed)
- ✅ **Success Rate: ≥ baseline** (no regression in contracts made)
- ✅ **Composite: ≥ baseline - 2%** (small regression tolerance)

**Target Scores by AI Level:**

| AI Level | Legality | Success Rate | Efficiency | Tactical | Composite |
|----------|----------|--------------|------------|----------|-----------|
| 1-2 (Beginner) | 100% | 40-50% | 30-40% | 20-30% | 50-60% |
| 3-4 (Intermediate) | 100% | 50-60% | 40-50% | 30-40% | 60-70% |
| 5-6 (Advanced-) | 100% | 60-70% | 50-60% | 40-50% | 70-80% |
| 7-8 (Advanced) | 100% | 70-80% | 60-70% | 50-60% | 80-85% |
| 9-10 (Expert/DDS) | 100% | 85-95% | 80-90% | 70-85% | 90-95% |

**Grade Scale:**
- A (90-100%): Expert level ✅
- B (80-89%): Advanced level ✅
- C (70-79%): Intermediate level ⚠️
- D (60-69%): Beginner level ⚠️
- F (<60%): Poor play ❌

#### 🚫 When to Block Commits

**DO NOT COMMIT if:**
- Legality score < 100% (illegal plays detected)
- Composite score drops >2% from baseline
- Success rate drops >5% from baseline
- Timing increases >50% from baseline
- Any critical errors introduced (contract failures that shouldn't occur)

**Example:**
```
Baseline:  85.3% composite, 78.2% success rate, 2.15s avg time
After fix: 83.1% composite, 72.5% success rate, 3.82s avg time
         ❌ BLOCKED - regression detected (composite -2.2%, success -5.7%, time +77%)
```

#### 📈 Score Comparison Script

Use `compare_play_scores.py` to compare before/after:

```bash
python3 compare_play_scores.py play_baseline_before.json play_baseline_after.json
```

The script will display:
- Score comparison across all 5 dimensions
- Performance metrics (contracts made %, overtricks, undertricks)
- Timing analysis
- Grade comparison
- Automatic regression detection with blocking criteria

#### 📁 File Organization

Keep play quality score reports organized:

```
project_root/
├── play_baseline_level8.json            # Current baseline for Level 8
├── play_baseline_level10_dds.json       # DDS baseline (production only)
├── play_baselines/                      # Historical scores
│   ├── 2025-10-28_level8_baseline.json
│   ├── 2025-10-29_after_minimax_fix.json
│   ├── 2025-10-30_after_trick_fix.json
│   └── README.md                        # Score history log
└── backend/
    ├── test_play_quality_integrated.py  # Integrated test script
    └── compare_play_scores.py           # Comparison utility
```

#### 🔄 CI/CD Integration

**Git Pre-Commit Hook:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if play logic files changed
PLAY_FILES=$(git diff --cached --name-only | grep -E 'backend/engine/(play_engine\.py|play/.*\.py)')

if [ -n "$PLAY_FILES" ]; then
    echo "🎯 Play logic changed - running play quality score..."
    python3 backend/test_play_quality_integrated.py --hands 100 --level 8

    if [ $? -ne 0 ]; then
        echo "❌ Play quality score check failed!"
        exit 1
    fi
fi
```

**GitHub Actions:**
```yaml
# .github/workflows/play_quality.yml
name: Play Quality Check

on:
  pull_request:
    paths:
      - 'backend/engine/play_engine.py'
      - 'backend/engine/play/**/*.py'

jobs:
  quality_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Play Quality Score (100 hands for speed)
        run: python3 backend/test_play_quality_integrated.py --hands 100 --level 8
      - name: Check for regressions
        run: |
          if [ -f play_baseline_level8.json ]; then
            python3 compare_play_scores.py play_baseline_level8.json play_quality_score.json
          fi
```

#### 📊 Example: Good Play Quality Score Workflow

**Scenario:** Improving minimax AI depth evaluation

```bash
# 1. Establish baseline
git checkout main
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_before_fix.json
# Result: 83.2% composite, 76.5% success rate (Grade B)

# 2. Create feature branch
git checkout -b improve/minimax-depth

# 3. Implement improvement
# ... make changes to minimax_ai.py ...

# 4. Quick test during development
python3 backend/test_play_quality_integrated.py --hands 100 --level 8
# Result: 84.1% composite - looking good!

# 5. Comprehensive test before commit
python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_after_fix.json
# Result: 85.7% composite, 79.2% success rate (Grade B)

# 6. Compare scores
python3 compare_play_scores.py play_before_fix.json play_after_fix.json
# Result: +2.5% composite, +2.7% success rate ✅

# 7. Commit with confidence
git add .
git commit -m "improve: Enhance minimax depth evaluation

- Improved position evaluation heuristics
- Better trump management in minimax search
- Play quality improved: 83.2% → 85.7% (+2.5 points)
- Success rate improved: 76.5% → 79.2% (+2.7 points)
- Grade: B (maintained with improvement)

Tested: 500 hands, Level 8 AI, no regressions detected"
```

#### 🎓 Play Quality Score Dimensions

**1. Legality (30%)** - Must be 100%
- All plays must follow bridge rules
- Correct suit following
- Proper trump usage
- No impossible plays

**2. Success Rate (25%)** - Contracts made
- Percentage of contracts that make exactly or with overtricks
- Key metric for play competency
- Critical for user experience

**3. Efficiency (20%)** - Overtricks and undertricks
- Making contracts with maximum overtricks
- Minimizing undertricks when going down
- Reward for optimal play

**4. Tactical (15%)** - Advanced play concepts
- Finessing opportunities taken
- Trump management quality
- Entry preservation
- Card counting and inference

**5. Timing (10%)** - Performance
- Average time per hand
- Average time per card play
- Consistency of timing
- Scales with AI complexity

#### 🔬 AI Level Testing Guide

**Development Testing (Local - macOS/Linux):**
- **Levels 1-8**: Full testing available
  - Level 1-2: SimplePlayAI with basic heuristics
  - Level 3-6: SimplePlayAI with advanced heuristics
  - Level 7-8: MinimaxPlayAI (depth 2-3)
- **Levels 9-10**: DDS - crashes on macOS M1/M2, Linux only

**Production Testing (Linux Server):**
- **All Levels 1-10**: Full testing including DDS
  - Level 9: DDS with standard settings
  - Level 10: DDS with maximum analysis

**Testing Protocol for Production DDS:**
```bash
# SSH to Linux production server
ssh production-server

# Navigate to project
cd /path/to/bridge_bidding_app

# Activate virtual environment
source venv/bin/activate

# Run DDS baseline (Level 10)
python3 backend/test_play_quality_integrated.py --hands 500 --level 10 --output play_baseline_dds.json

# Expected results: 90-95% composite, 85-95% success rate
```

#### 💡 Pro Tips

**1. Test incrementally:**
- Use 100 hands during development (fast feedback)
- Use 500 hands before commits (comprehensive)

**2. Save baselines per AI level:**
- Each AI level has different expected performance
- Tag major baselines: `git tag play-baseline-level8-2025-10-28`

**3. Watch for patterns:**
- Recurring illegal plays indicate rule enforcement issues
- Low success rates on specific contract types indicate tactical weaknesses
- High timing variance indicates algorithm inefficiency

**4. DDS Testing Limitations:**
- DDS requires Linux (crashes on macOS M1/M2)
- DDS is slow (10-20x slower than Minimax)
- Only test DDS on production servers
- Use Level 8 (Minimax) for development

**5. Performance vs Quality Tradeoff:**
- Higher AI levels = better play + slower performance
- Monitor timing metrics carefully
- User experience: prefer consistent 2s over variable 1-5s

**6. Context matters:**
- Some contracts are impossible to make
- Aggressive play might have lower success but higher overtricks
- Review error details, not just scores

#### 🎯 Established Baselines by AI Level

**Status: ✅ OPERATIONAL - Baseline established 2025-10-29**

**Level 8 (Advanced - Minimax depth 2) - ESTABLISHED:**

```
Test: 500 hands, 385 contracts, 115 passed out
Composite Score: 75.3% (Grade F)
Test Date: 2025-10-29

Breakdown:
- Legality:      100.0% ✅ (0 illegal plays)
- Success Rate:   46.8% ❌ (180/385 contracts made)
- Efficiency:     43.2% ❌ (292 overtricks, 553 undertricks)
- Tactical:      100.0% ✅ (0 tactical errors)
- Timing:        100.0% ✅ (0.161s avg per hand)

Performance:
- Cards Played:    20,020
- Avg Time/Hand:   0.161s
- Min Time:        0.111s
- Max Time:        0.350s

Baseline File: play_baselines/2025-10-29_level8_initial_baseline.json
```

**Level 10 (Expert - DDS) - PENDING:**
```
Status: Requires Linux production server (DDS crashes on macOS M1/M2)
Expected: 85-95% composite (Grade A-B)
Expected: 85-95% success rate
Expected: 15-30s average time per hand (much slower than Minimax)
```

**Interpretation:**
- Grade F (75.3%) is the **current baseline** for Level 8 AI
- This represents the starting point for improvements
- Success rate of 46.8% indicates room for tactical improvements
- Perfect legality shows the play engine rules are correct
- Fast performance (0.161s/hand) allows for testing iterations

**Current Status (2025-10-29):**
- ✅ Play quality scoring framework complete and operational
- ✅ Comparison utility (`compare_play_scores.py`) functional
- ✅ Protocol documentation added to guidelines
- ✅ Test script fully debugged and working
- ✅ Level 8 baseline established (75.3% composite)
- ⏳ Level 10 (DDS) baseline pending Linux server access

---

## Version History

- 2025-10-19: Initial version based on Dashboard Refresh issue discovery
- 2025-10-28: Added Bidding Logic Quality Assurance Protocol
- 2025-10-29: Added Play Logic Quality Assurance Protocol
- Next update: After establishing play quality baselines
