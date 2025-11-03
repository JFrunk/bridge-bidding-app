# Claude Quick Start - Systematic Debugging

## When You Get a Bug Report...

### FIRST: Check Error Logs (30 seconds)

Before investigating manually, check if the bug was already logged:

```bash
cd backend
python3 analyze_errors.py                    # Quick summary
python3 analyze_errors.py --recent 10        # Recent errors with details
python3 analyze_errors.py --patterns         # Detect recurring issues
python3 analyze_errors.py --category bidding_logic  # Filter by subsystem
```

**Why check error logs first:**
- ✅ Instant stack traces (no debugging needed)
- ✅ Full context captured (auction, hand, session)
- ✅ See if it's recurring (error patterns)
- ✅ Track with error hash
- ✅ Know when it started (timestamp)

**If error is logged:** Skip manual debugging, go straight to fix implementation using stack trace and context.

**If error is NOT logged:** Proceed with manual investigation below.

**Slash command:** `/analyze-errors`

---

## When You Find a Bug's Root Cause...

### STOP! Before implementing the fix:

Run this slash command:
```
/check-scope
```

Or manually ask yourself:

1. **"Where else does this pattern exist?"**
   ```bash
   grep -r "similar_pattern" --include="*.js*" frontend/src/
   ```

2. **"What else might be affected?"**
   - List all similar components
   - Check all related features
   - Think: modals, dialogs, tabs, collapsible sections

3. **"How many places need fixing?"**
   - 1 place → Fix it
   - 2-3 places → Fix all + document pattern
   - 4+ places → Create shared abstraction

### Example from Today's Issue

**Bad Response:**
> "I found the issue! LearningDashboard doesn't refresh. Let me fix it."

**Good Response:**
> "I found the issue! LearningDashboard doesn't refresh on reopen.
>
> Let me check if other modals have the same pattern...
> [searches codebase]
>
> Found: Same pattern affects ALL 7 dashboard components, plus potentially 2 other modals.
>
> Here's my comprehensive analysis..."

## Quick Commands

```bash
# Find similar useEffect patterns
grep -r "useEffect" --include="*.js*" frontend/src/

# Find all modals
grep -r "Modal\|Dialog" --include="*.js*" frontend/src/

# Find all API calls
grep -r "fetch.*API_URL" --include="*.js*" frontend/src/

# Find similar state patterns
grep -r "useState" --include="*.js*" frontend/src/
```

## The Golden Rule

**One issue reported → Check if it's actually N issues with same root cause**

This saves:
- Time (fix once, not repeatedly)
- User frustration (they don't have to report same issue multiple times)
- Technical debt (comprehensive fix prevents recurrence)

## Full Guidelines

See [CODING_GUIDELINES.md](.claude/CODING_GUIDELINES.md) for complete systematic analysis framework.
