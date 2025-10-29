# Systematic Issue Analysis Framework
## Making Claude Automatically Check for Broader Issues

## The Pattern We Just Experienced

### What Happened
1. **User reported**: "Recent bidding decisions appear static"
2. **Claude found**: LearningDashboard only fetches data once on mount
3. **User asked**: "Do other components have the same issue?"
4. **Claude discovered**: YES - ALL 7 dashboard components were affected

### The Missed Opportunity
Claude should have **proactively** checked if the issue was broader before presenting the initial fix.

---

## Recommended Implementation Approaches

### Option 1: Custom Slash Command (Recommended)
Create a slash command that triggers systematic analysis mode.

**File:** `.claude/commands/analyze-issue.md`

```markdown
# Analyze Issue Systematically

When you've identified the root cause of an issue, ALWAYS perform this systematic analysis before proposing a fix:

## 1. SCOPE ANALYSIS
- [ ] What is the immediate issue?
- [ ] What is the root cause?
- [ ] Are there similar patterns elsewhere in the codebase?
- [ ] What other components use the same pattern?

## 2. SEARCH FOR SIMILAR PATTERNS
Run these searches:
- Same hook patterns (e.g., useEffect with same dependencies)
- Same API calls or data fetching patterns
- Same component mounting/unmounting behaviors
- Similar state management approaches

## 3. IMPACT ASSESSMENT
List ALL affected:
- [ ] Components
- [ ] Features
- [ ] User workflows
- [ ] Data sources

## 4. PROPOSED SOLUTION SCOPE
- [ ] Does the fix need to be applied in multiple places?
- [ ] Can we fix it once in a shared location?
- [ ] What's the most maintainable approach?

## 5. PRESENT FINDINGS
Format your response as:
1. **Immediate Issue**: [what user reported]
2. **Root Cause**: [technical explanation]
3. **Broader Impact**: [all affected components/features]
4. **Recommended Solution**: [fix that addresses ALL instances]
5. **Why This Approach**: [justify the solution]

Only after completing this analysis should you implement the fix.
```

**Usage:** User types `/analyze-issue` and Claude automatically goes through the checklist.

---

### Option 2: Hook-Based Automation
Add a post-diagnosis hook that triggers automatically.

**File:** `.claude/settings.json`

```json
{
  "hooks": {
    "post-diagnosis": {
      "enabled": true,
      "command": "echo '⚠️ Before implementing fix: Check if this pattern exists elsewhere in the codebase. Search for similar components, hooks, or patterns that might have the same issue.'",
      "trigger": "after_root_cause_identified"
    }
  }
}
```

**Limitation:** Hooks currently don't have "after_root_cause_identified" trigger. This would be a feature request.

---

### Option 3: Enhanced Prompt Template
Create a template for issue investigation that includes systematic checking.

**File:** `.claude/templates/investigate-bug.md`

```markdown
# Bug Investigation Template

## Phase 1: Reproduce & Identify
1. Reproduce the issue
2. Identify immediate cause
3. Find root cause

## Phase 2: Systematic Scope Analysis (REQUIRED)
Before proposing any fix, complete this analysis:

### Pattern Search
```bash
# Search for similar patterns
grep -r "useEffect" --include="*.js" --include="*.jsx"
grep -r "useState" --include="*.js" --include="*.jsx"
grep -r "similar API calls"
```

### Questions to Answer
1. **Is this pattern used elsewhere?**
   - Same hook combination?
   - Same component lifecycle?
   - Same data fetching approach?

2. **What other features might be affected?**
   - List all components using similar patterns
   - List all API endpoints with similar behavior
   - List all user workflows that could exhibit same symptoms

3. **Scope of fix**
   - Single component fix?
   - Multiple component fix?
   - Architectural pattern fix?
   - Shared utility/hook creation?

### Impact Assessment
Create a table:

| Component/Feature | Uses Same Pattern | Affected | Fix Required |
|-------------------|-------------------|----------|--------------|
| Example Component | Yes/No            | Yes/No   | Yes/No       |

## Phase 3: Solution Design
Only after completing Phase 2, design solution that:
- Fixes root cause everywhere
- Prevents recurrence
- Follows DRY principles
- Is maintainable

## Phase 4: Implementation
Implement the comprehensive fix.

## Phase 5: Documentation
Document:
- What was found
- How widespread the issue was
- Why this solution was chosen
- How to avoid in future
```

---

### Option 4: Checklist in System Instructions (Most Practical)
Add to Claude Code configuration or project README.

**File:** `CLAUDE_CODING_GUIDELINES.md`

```markdown
# Claude Coding Guidelines for This Project

## When Investigating Issues

### Mandatory Systematic Analysis Checklist

When you identify the root cause of any issue, BEFORE implementing a fix:

#### 🔍 Step 1: Pattern Detection
- [ ] Search codebase for identical or similar code patterns
- [ ] Use grep/glob to find similar hooks, components, API calls
- [ ] Document all instances found

#### 📊 Step 2: Impact Analysis
- [ ] List ALL components using the same pattern
- [ ] List ALL features potentially affected
- [ ] List ALL user workflows that could show same symptoms
- [ ] Estimate: Is this a 1-component issue or N-component issue?

#### 💡 Step 3: Solution Design
- [ ] If pattern appears once: Fix locally
- [ ] If pattern appears 2-3 times: Consider shared utility
- [ ] If pattern appears 4+ times: Create abstraction/hook/service
- [ ] If architectural: Propose pattern change project-wide

#### 📝 Step 4: Communicate Findings
Present to user:
```
## Issue Analysis Complete

**Reported Issue**: [what user said]
**Root Cause**: [technical explanation]
**Scope**: [1 component | N components | architectural]

**All Affected Components**:
1. Component A - [description]
2. Component B - [description]
...

**Recommended Solution**: [approach]
**Why**: [justification]

Shall I proceed with implementation?
```

#### ⚙️ Step 5: Implement Comprehensively
- Fix all instances at once
- Create tests if needed
- Document the pattern to avoid future occurrences

### Example Searches to Run

When you find an issue with:
- **useEffect**: `grep -r "useEffect" --include="*.js*"`
- **useState**: `grep -r "useState" --include="*.js*"`
- **API calls**: `grep -r "fetch.*api" --include="*.js*"`
- **Component mounting**: `grep -r "componentDidMount\|useEffect.*\[\]" --include="*.js*"`
- **Data caching**: `grep -r "useState.*Data\|setData" --include="*.js*"`

### Red Flags That Suggest Broader Issues
- "This component only fetches once..."
- "Data is cached in state..."
- "Modal/dialog shows stale data..."
- "Same pattern in multiple places..."
- "This feels like it could happen elsewhere..."

When you encounter these phrases in your own analysis, STOP and run systematic check.
```

---

## Recommended Implementation Strategy

### Immediate (Today)
1. ✅ Create `CLAUDE_CODING_GUIDELINES.md` with the checklist above
2. ✅ Add reference to it in project README
3. ✅ Include it in `.claude/` directory for visibility

### Short-term (This Week)
1. Create custom slash command `/analyze-issue`
2. Update `.claude/settings.json` with prompts
3. Create bug investigation template

### Long-term (Future Enhancement)
1. Request Claude Code feature: Post-diagnosis hooks
2. Create automated scripts that run pattern searches
3. Build a linting rule for common patterns

---

## Specific Recommendations for This Project

### Create Shared Data Fetching Patterns

**Issue**: Modal components often have stale data because they don't refresh on open.

**Pattern to Prevent**:
```javascript
// ❌ BAD: Only fetches once
useEffect(() => {
  loadData();
}, [userId]);

// ✅ GOOD: Fetches on every open
useEffect(() => {
  if (isOpen) {
    loadData();
  }
}, [isOpen, userId]);

// ✅ ALSO GOOD: Force remount with key
<Component key={Date.now()} />
```

**Recommendation**: Create a shared hook
```javascript
// hooks/useRefreshOnOpen.js
export const useRefreshOnOpen = (isOpen, loadDataFn) => {
  useEffect(() => {
    if (isOpen) {
      loadDataFn();
    }
  }, [isOpen]);
};

// Usage
const MyModal = ({ isOpen }) => {
  useRefreshOnOpen(isOpen, loadDashboardData);
  // ...
};
```

### Audit Checklist for This Codebase

Run these searches to find similar patterns:

```bash
# Find all modal/dialog components
grep -r "Modal\|Dialog\|Overlay" --include="*.js*" frontend/src/

# Find all useEffect with static dependencies
grep -r "useEffect.*\[\]" --include="*.js*" frontend/src/

# Find all components fetching data on mount
grep -r "useEffect.*load.*Data" --include="*.js*" frontend/src/

# Find all components with show/hide state
grep -r "show.*useState\|isOpen.*useState" --include="*.js*" frontend/src/
```

---

## Training Claude to Be More Systematic

### Prompt Engineering Approach

When starting a debugging session, prime Claude with:

```
Before we fix this issue, let's be systematic:
1. First, identify the immediate cause
2. Then, search for similar patterns in the codebase
3. Assess the full scope of impact
4. Only then propose a comprehensive solution

Use the Systematic Issue Analysis Framework.
```

### In-Session Reminders

When Claude identifies a root cause, ask:
- "Before implementing, have you checked if this pattern exists elsewhere?"
- "What other components might have this same issue?"
- "Is this a symptom of a broader architectural pattern we should address?"

---

## Success Metrics

### How to Know It's Working

After implementing this framework, you should see Claude:
1. ✅ Automatically searching for similar patterns after finding root cause
2. ✅ Presenting comprehensive impact analysis before proposing fixes
3. ✅ Suggesting architectural improvements when finding repeated patterns
4. ✅ Fixing N instances at once instead of fixing 1 and waiting for "what about the others?"

### Example of Good Systematic Analysis

```
## Analysis Complete

**Issue**: Recent bidding decisions appear static

**Root Cause**: LearningDashboard component only fetches data once on mount
via useEffect with [userId] dependency. When modal closes/reopens, React
reuses same component instance with cached state.

**Pattern Search Results**:
- Searched for: useEffect with data fetching + modal components
- Found 3 modal components with similar pattern:
  1. ✅ LearningDashboard - ALL 7 sub-components affected
  2. ⚠️ ReviewModal - May have same issue (needs testing)
  3. ⚠️ ConventionHelpModal - Fetches once (but data is static, so OK)

**Scope**: System-wide modal data refresh issue

**Recommended Solution**:
Apply key={Date.now()} pattern to all modals that fetch dynamic data.
This forces remount and refresh on every open.

**Implementation Plan**:
1. Fix LearningDashboard (affects 7 components)
2. Test ReviewModal behavior
3. Document pattern in coding guidelines
4. Create useRefreshOnOpen hook for future modals

Proceed?
```

---

## Conclusion

The key insight is: **When Claude finds one issue, it should automatically ask "Where else does this pattern exist?"**

The most practical implementation is:
1. **Create `CLAUDE_CODING_GUIDELINES.md`** with the systematic checklist
2. **Reference it at the start of debugging sessions**
3. **Train yourself to ask "What else?" when Claude finds a root cause**

This creates a feedback loop where both human and AI become more systematic over time.
