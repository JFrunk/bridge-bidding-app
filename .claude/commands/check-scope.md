# Check Scope

After identifying the root cause of an issue, systematically check if it affects other parts of the codebase: $ARGUMENTS

## Steps

### 1. Search for Similar Patterns

Based on the root cause, search for the same pattern elsewhere:

```bash
# Adapt these to your specific issue
grep -r "pattern" --include="*.py" backend/
grep -r "pattern" --include="*.js" --include="*.jsx" frontend/src/
```

### 2. Document What You Find

- **Immediate issue:** [the component/file you're fixing]
- **Same pattern found in:** [list other files]
- **Actually affected:** [which ones have the bug]
- **Preventatively fix:** [which could develop the bug]

### 3. Decide on Approach

- **1 occurrence:** Fix locally
- **2-3 occurrences:** Fix all instances
- **4+ occurrences:** Consider creating a shared utility/abstraction

### 4. Report Before Implementing

```
## Scope Analysis

**Root Cause:** [what causes the bug]
**Found in:** [N] locations
**Affected:** [list]
**Recommended fix:** [local fix vs shared utility]

Proceed with implementation?
```
