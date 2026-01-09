---
description: Debug complex issue using systematic analysis
---

---
description: Debug complex issue using systematic analysis
---

Debug complex issue using systematic analysis: $ARGUMENTS

Issue description: $ARGUMENTS

⚠️  **MANDATORY: Use systematic 4-step protocol before implementing fix**

---

## Step 1: Identify Root Cause (DO NOT FIX YET)

**Investigation:**
1. Reproduce the issue (if possible)
2. Read error logs, stack traces, and related code
3. Use subagent to gather context if needed
4. **Think hard** about the root cause
5. Document technical cause (not just symptoms)

**Output:** "Root cause: [technical explanation]"

---

## Step 2: Search for Similar Patterns (2 minutes)

**Pattern Search:**
```bash
# Example searches based on issue type:
# - React hooks: grep -r "useEffect" --include="*.js*" frontend/src/
# - State management: grep -r "useState.*Data" --include="*.js*" frontend/src/
# - API calls: grep -r "fetch.*api" --include="*.js*" frontend/src/
# - Bidding logic: grep -r "def evaluate" backend/engine/
```

6. Search codebase for similar patterns
7. List ALL files with similar code
8. Identify which ones exhibit the bug
9. Identify which ones COULD have the bug (preventative)

**Questions to answer:**
- Does this pattern appear in other components? (List them)
- Are there similar lifecycle/hook patterns? (List them)
- Do other features use the same approach? (List them)

---

## Step 3: Assess Scope & Design Solution (1 minute)

**Scope Assessment:**
- **Immediate issue:** [component/feature affected]
- **Pattern found in:** [N] files
- **Actually affected:** [list files with active bug]
- **Preventatively fix:** [list files that could have bug]

**Solution Strategy:**
- **1 occurrence:** Fix locally in that file
- **2-3 occurrences:** Fix all instances, consider shared utility
- **4+ occurrences:** Create abstraction (hook/service), fix architecturally

---

## Step 4: Present Analysis to User (MANDATORY)

**DO NOT IMPLEMENT YET - Present this analysis:**

```
## Systematic Analysis Complete

**Reported Issue:** [user's description]

**Root Cause:** [technical cause with file:line references]

**Scope:** Found in [N] components/files

**All Occurrences:**
1. [Component/File A] - ❌ AFFECTED (exhibits bug)
2. [Component/File B] - ⚠️  AT RISK (similar pattern, no bug yet)
3. [Component/File C] - ⚠️  AT RISK (similar pattern, no bug yet)

**Solution Approach:**
[Describe local fix OR architectural fix with reasoning]

**Files to Change:**
- [List all files that will be modified]

**Testing Plan:**
- [How to verify the fix]
- [What quality baselines to run]

Proceed with implementation?
```

**Wait for user approval before coding**

---

## Step 5: Implement (After User Approval)

10. Implement fix across all identified files
11. Add regression tests to prove bug is fixed
12. Run tests: `cd backend && ./test_quick.sh`
13. Run quality baselines (if bidding/play logic changed)
14. Commit with systematic analysis in commit message

---

## Success Criteria

- [ ] Root cause identified (not just symptoms)
- [ ] Codebase searched for similar patterns
- [ ] All affected files listed
- [ ] Solution designed (local vs architectural)
- [ ] Analysis presented to user BEFORE implementing
- [ ] Fix applied to all instances (not just reported one)
- [ ] Regression tests added
- [ ] Pattern documented to prevent recurrence

Reference: .claude/CODING_GUIDELINES.md Systematic Issue Analysis Protocol
