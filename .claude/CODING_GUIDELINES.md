# Claude Coding Guidelines - Bridge Bidding App

## Systematic Issue Analysis Protocol

### When Investigating Any Issue

**MANDATORY**: Before implementing any fix, use `/debug-systematic` for the full protocol. Key steps:

**Step 0:** Use `/analyze-errors` to check error logs FIRST.

**See:** [ERROR_LOGGING_QUICKSTART.md](../ERROR_LOGGING_QUICKSTART.md), [docs/features/ERROR_LOGGING_SYSTEM.md](../docs/features/ERROR_LOGGING_SYSTEM.md)

**Step 1:** Use `/check-scope` to search for similar patterns across the codebase.

**Steps 2-4:** Scope assessment, solution design, and presenting analysis to user are handled by `/debug-systematic`.

**Solution strategy:**
- **1 occurrence**: Fix locally
- **2-3 occurrences**: Fix all instances, consider shared utility
- **4+ occurrences**: Create abstraction (hook/service), fix architecturally

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

- [ ] Error logs checked before starting (Step 0)
- [ ] Root cause identified
- [ ] Similar patterns searched
- [ ] All affected components listed
- [ ] Comprehensive solution proposed
- [ ] Fix applied to all instances
- [ ] Pattern documented to prevent recurrence
- [ ] Tests added if applicable
- [ ] **Verify fix in error logs** - Monitor error hash after deployment
  ```bash
  # After deploying fix, check that error hash stops appearing
  python3 analyze_errors.py --patterns
  # Look for the error hash - should not appear after fix timestamp
  ```

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

**Use `/quality-baseline` to capture scores, `/compare-quality` to check for regressions, or `/smart-commit` to auto-detect and run the right gates.**

### When to Run

Run quality scores BEFORE modifying:
- Bidding modules (`backend/engine/*.py`)
- Convention logic (`backend/engine/ai/conventions/*.py`)
- Bid validation, base convention class

### Blocking Criteria

- Legality < 100%
- Composite drops > 2% from baseline
- Appropriateness drops > 5% from baseline

### Grade Scale

| Grade | Range | Status |
|-------|-------|--------|
| A | 95-100% | Production ready |
| B | 90-94% | Good |
| C | 85-89% | Acceptable |
| D | 80-84% | Poor |
| F | < 80% | Do not deploy |

---

## Play Logic Quality Assurance Protocol

**Use `/quality-baseline` to capture scores, `/compare-quality` to check for regressions, or `/smart-commit` to auto-detect and run the right gates.**

### When to Run

Run quality scores BEFORE modifying:
- Play engine (`backend/engine/play_engine.py`)
- Play AI logic (`backend/engine/play/ai/*.py`)
- Card selection, trick evaluation, contract execution

### Blocking Criteria

- Legality < 100%
- Composite drops > 2% from baseline
- Success rate drops > 5% from baseline
- Timing increases > 50% from baseline

### DDS Limitations

- DDS only works on Linux (crashes on macOS M1/M2)
- Use Level 8 (Minimax) for local development
- Level 10 (DDS) testing requires production server

### Play Quality Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Legality | 30% | Must be 100% — correct suit following, trump usage |
| Success Rate | 25% | Contracts made at or above bid level |
| Efficiency | 20% | Overtricks maximized, undertricks minimized |
| Tactical | 15% | Finesses, trump management, entries |
| Timing | 10% | Performance consistency |

---

## Version History

- 2025-10-19: Initial version based on Dashboard Refresh issue discovery
- 2025-10-28: Added Bidding Logic Quality Assurance Protocol
- 2025-10-29: Added Play Logic Quality Assurance Protocol
- Next update: After establishing play quality baselines
