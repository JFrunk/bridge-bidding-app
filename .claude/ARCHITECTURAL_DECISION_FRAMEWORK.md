# Architectural Decision Framework

**Purpose:** Ensure Claude Code performs systematic architectural review before making significant changes
**Created:** 2025-10-12
**Auto-loads:** Yes (in `.claude/` directory)

---

## 🚨 CRITICAL: When to Trigger Architectural Review

Claude Code **MUST** perform architectural review when encountering ANY of these triggers:

### High-Risk Triggers (MANDATORY REVIEW)
- [ ] Creating new directories or reorganizing project structure
- [ ] Adding new dependencies (npm, pip, etc.)
- [ ] Changing data structures used across multiple modules
- [ ] Modifying API contracts (endpoints, request/response formats)
- [ ] Introducing new state management patterns
- [ ] Creating new database schemas or migrations
- [ ] Modifying build/deployment configuration
- [ ] Changing authentication or security patterns
- [ ] Refactoring code used by 3+ other modules

### Medium-Risk Triggers (STRONGLY RECOMMENDED)
- [ ] Creating new classes/services with 200+ lines
- [ ] Adding new environment variables or configuration
- [ ] Introducing new design patterns (singleton, factory, etc.)
- [ ] Modifying shared utilities or helper functions
- [ ] Changes affecting test infrastructure
- [ ] Adding new CLI commands or scripts
- [ ] Modifying error handling strategy
- [ ] Creating new reusable components

### Automatic Exemptions (Skip Review)
- Bug fixes that don't change interfaces
- Documentation-only changes
- Adding tests without code changes
- Renaming variables/functions within single file
- Formatting/linting fixes

---

## 🚀 TL;DR - Quick Start (Read This First!)

**For 90% of cases, you need this:**

1. **Check triggers:** `python3 .claude/scripts/check_architectural_triggers.py --verbose`
2. **If HIGH-RISK:** Generate 3 alternatives, score them using decision matrix below
3. **Create ADR:** Copy template (see bottom of this doc), fill in sections
4. **Check score and authority matrix:**
   - Score ≥ 8.5 AND no security risk? → Proceed + notify user
   - Score 7.0-8.4? → Get user approval first
   - Score < 7.0? → Discuss with user
5. **Implement** after appropriate approval

**Emergency?** Production down or security issue? → Fix immediately, create "EMERGENCY" ADR within 24 hours

**Read full framework below when you need details.**

---

## 📊 Decision Authority Matrix

**WHO decides and WHEN to proceed:**

| Risk Level | Score Range | User Approval | Claude Can Proceed When... |
|------------|-------------|---------------|----------------------------|
| **HIGH** | ≥ 8.5 | Optional (notify after) | Score ≥ 8.5 AND ADR created AND no security/data loss risk |
| **HIGH** | 7.0-8.4 | Required (before) | User approves within 24h OR user says "Claude decide" |
| **HIGH** | < 7.0 | Required + discussion | User actively engaged in discussing alternatives |
| **MEDIUM** | ≥ 7.0 | No (notify after) | ADR created and documented |
| **MEDIUM** | < 7.0 | Optional (notify) | Claude's judgment + create ADR |
| **LOW** | Any | No | Proceed normally |

### Special Cases

**Emergency Override Protocol:**
- **When:** Production outage, security vulnerability (CVE), data loss in progress, complete system failure
- **Action:** Fix immediately WITHOUT review
- **Required:** Create "EMERGENCY" ADR within 24 hours documenting:
  - What broke
  - What you changed (with justification)
  - Why normal review was skipped
  - Post-mortem: Could this have been prevented?
- **Schedule:** Post-incident review within 1 week

**NOT Emergencies:**
- "I want to ship faster"
- "Review seems like too much work"
- "I forgot to do review earlier"
- Single user reporting a bug (unless critical)

**User Unavailable (> 24 hours):**
- If score ≥ 8.0 and no security risk → Proceed with ADR, notify when back
- If score < 8.0 → Wait OR escalate to "Claude decide" authority if previously granted

---

## ⏱️ Time Estimates (Realistic)

**Don't rush complex decisions to fit arbitrary time box:**

| Complexity | Time Needed | Example |
|------------|-------------|---------|
| **Simple** | 15-30 min | Should we use library X or Y? New dependency choice. |
| **Moderate** | 45-60 min | How should we structure this new feature? API endpoint design. |
| **Complex** | 2-4 hours | Major refactoring, architecture change, state management overhaul. |

**Rule:** Time-box to these limits. If exceeding, escalate to user for discussion.

---

## 📋 Architectural Review Checklist

When a trigger is detected, **PAUSE** and complete this checklist BEFORE implementing:

### 1. Problem Analysis (5 minutes)

**Document the problem clearly:**
```markdown
## Problem Statement
- What problem are we solving?
- Why is this change needed?
- What happens if we don't make this change?
- What is the scope of impact?
```

**Analyze current pain points:**
- What similar issues have occurred in the past?
- Review: ARCHITECTURE_RISK_ANALYSIS.md, MODULAR_ARCHITECTURE_PLAN.md
- What refactoring has been required previously?
- What velocity was lost due to architectural issues?

### 2. Alternative Solutions (10 minutes)

**Generate at least 3 alternatives:**

```markdown
## Option A: [Approach Name]
**Description:** [Brief description]
**Pros:**
- [Advantage 1]
- [Advantage 2]
**Cons:**
- [Disadvantage 1]
- [Disadvantage 2]
**Effort:** [Hours/Days]
**Risk:** [Low/Medium/High]

## Option B: [Approach Name]
[Repeat format]

## Option C: [Approach Name]
[Repeat format]
```

**Evaluation Criteria:**
- Maintainability (ease of future changes)
- Testability (can it be unit/integration tested)
- Performance impact
- Security implications
- Developer experience
- Deployment complexity
- Rollback capability

### 3. Dependency Analysis (5 minutes)

**Map dependencies:**
```markdown
## Affected Components
- [Component 1] - How affected?
- [Component 2] - How affected?

## Dependency Chain
[Component A] → [Component B] → [Component C]

## Risk of Circular Dependencies
- Does this create import cycles?
- Run: python .claude/scripts/check_dependencies.py
```

**Check existing patterns:**
- How do similar problems get solved in the codebase?
- Are there existing utilities/patterns we should reuse?
- Would this create inconsistency with existing architecture?

### 4. Future Impact Assessment (5 minutes)

**Think ahead:**
```markdown
## How does this affect future development?

### Extensibility
- How easy is it to add new features?
- What's the plan for scaling this?

### Maintenance
- What's the maintenance burden?
- How many files need updating for common changes?
- Is this documented clearly for future developers?

### Technical Debt
- Does this introduce technical debt?
- Is this a temporary solution or long-term architecture?
- What's the refactoring risk in 6 months?

### Breaking Changes
- Does this break existing APIs?
- What's the migration path?
- How many tests need updating?
```

### 5. Testing Strategy (5 minutes)

```markdown
## Testing Plan
- [ ] Unit tests: [What to test]
- [ ] Integration tests: [What to test]
- [ ] Regression tests: [What existing functionality to verify]
- [ ] Performance tests: [What to benchmark]
- [ ] Rollback test: [Can we revert easily?]
```

### 6. Documentation Requirements (2 minutes)

```markdown
## Documentation Needed
- [ ] Architecture Decision Record (ADR)
- [ ] API documentation updates
- [ ] README updates
- [ ] Code comments for complex logic
- [ ] Migration guide (if breaking changes)
- [ ] Update PROJECT_CONTEXT.md
```

---

## 📚 Worked Examples

**Learn by example - these show the complete process:**

### Example 1: Adding New Dependency (Statistics Library)

**Scenario:** Need to calculate standard deviation for hand strength analysis in bidding engine.

**Problem Analysis:**
- Current code has no statistics capabilities
- Hand evaluation could be improved with statistical measures
- Scope: Affects `engine/bidding_engine.py` and evaluation logic

**Alternative A: Add numpy dependency**
- **Description:** Install numpy for scientific computing
- **Pros:** Industry standard, comprehensive, well-tested, fast (C-optimized)
- **Cons:** Large dependency (~15MB), overkill for simple statistics
- **Effort:** 1 hour (pip install + integration)
- **Risk:** Medium (adds significant dependency)

**Scoring:**
- Maintainability: 9/10 (well-maintained, stable API)
- Testability: 10/10 (pure functions, deterministic)
- Future-proofing: 9/10 (likely need more stats functions)
- Implementation Effort: 9/10 (very easy - just import)
- Risk: 7/10 (adds 15MB, but widely used)
- Performance: 10/10 (optimized C code)

**Weighted Score:** (9×0.25) + (10×0.20) + (9×0.20) + (9×0.15) + (7×0.10) + (10×0.10) = **9.05/10**

**Alternative B: Use Python statistics module (stdlib)**
- **Description:** Use built-in `statistics.stdev()` from Python standard library
- **Pros:** Zero dependencies, already available, good enough for basic stats
- **Cons:** Limited functionality, pure Python (slower), can't do advanced stats
- **Effort:** 30 minutes (already available)
- **Risk:** Minimal (stdlib)

**Scoring:**
- Maintainability: 10/10 (Python stdlib - always available)
- Testability: 10/10 (well-tested in stdlib)
- Future-proofing: 7/10 (limited to basic statistics)
- Implementation Effort: 10/10 (zero setup required)
- Risk: 10/10 (no new dependencies)
- Performance: 8/10 (pure Python - adequate for our needs)

**Weighted Score:** (10×0.25) + (10×0.20) + (7×0.20) + (10×0.15) + (10×0.10) + (8×0.10) = **9.2/10** ✅

**Alternative C: Implement own calculation**
- **Description:** Write custom standard deviation function
- **Pros:** No dependencies, full control, exactly what we need
- **Cons:** Reinventing wheel, potential bugs, maintenance burden
- **Effort:** 3 hours (implement + test edge cases)
- **Risk:** Medium (math errors possible)

**Scoring:**
- Maintainability: 6/10 (custom code to maintain forever)
- Testability: 8/10 (can write tests, but must verify correctness)
- Future-proofing: 4/10 (only does std dev, will need more later)
- Implementation Effort: 4/10 (3 hours is significant)
- Risk: 6/10 (potential for subtle math bugs)
- Performance: 7/10 (pure Python, not optimized)

**Weighted Score:** (6×0.25) + (8×0.20) + (4×0.20) + (4×0.15) + (6×0.10) + (7×0.10) = **5.8/10**

**DECISION:** Use `statistics.stdev()` from Python stdlib (Option B, score 9.2/10)

**Rationale:**
- Meets current needs perfectly
- Zero dependencies (big win)
- If we need advanced stats later, can add numpy then
- User approval: Not needed (score ≥ 8.5, no security risk)

**Action:** Create ADR-0001, proceed with implementation, notify user after

---

### Example 2: State Management Change (Session-based vs Global)

**Scenario:** Implementing play-only mode requires managing play state separately from bidding state.

**Problem Analysis:**
- Current code uses global `current_play_state` variable
- Past issues: ARCHITECTURE_RISK_ANALYSIS.md Risk #1 documented global state conflicts
- Scope: HIGH-RISK - affects `server.py`, all API endpoints, affects testing

**Alternative A: Session-based state management**
- **Description:** Create `SessionManager` class, each request includes `session_id`
- **Pros:** No conflicts, supports multiple concurrent users, testable
- **Cons:** Requires refactoring all endpoints, more complex initially
- **Effort:** 20 hours (major refactoring)
- **Risk:** High (touches many files)

**Scoring:**
- Maintainability: 9/10 (clean architecture, scales well)
- Testability: 10/10 (can test sessions independently)
- Future-proofing: 10/10 (enables multi-user, prevents conflicts)
- Implementation Effort: 4/10 (20 hours is significant)
- Risk: 6/10 (touches many files, but well-understood pattern)
- Performance: 9/10 (dictionary lookups are fast)

**Weighted Score:** (9×0.25) + (10×0.20) + (10×0.20) + (4×0.15) + (6×0.10) + (9×0.10) = **8.35/10**

**Alternative B: Add flag to global state**
- **Description:** Add `mode` flag to distinguish bidding vs play
- **Pros:** Quick to implement, minimal changes
- **Cons:** Doesn't solve underlying problem, still has conflicts, technical debt
- **Effort:** 2 hours
- **Risk:** Low (minimal changes)

**Scoring:**
- Maintainability: 3/10 (band-aid, increases complexity)
- Testability: 4/10 (harder to test with global state)
- Future-proofing: 2/10 (kicks can down road)
- Implementation Effort: 9/10 (very quick)
- Risk: 7/10 (quick but creates debt)
- Performance: 10/10 (no performance change)

**Weighted Score:** (3×0.25) + (4×0.20) + (2×0.20) + (9×0.15) + (7×0.10) + (10×0.10) = **4.8/10**

**Alternative C: Hybrid - session-based for play only**
- **Description:** Keep global state for bidding, add sessions just for play
- **Pros:** Less refactoring, solves immediate problem
- **Cons:** Inconsistent architecture, confusing for future work
- **Effort:** 10 hours
- **Risk:** Medium

**Scoring:**
- Maintainability: 5/10 (inconsistent patterns)
- Testability: 7/10 (better than global, but inconsistent)
- Future-proofing: 5/10 (will still need to fix bidding state later)
- Implementation Effort: 6/10 (moderate effort)
- Risk: 7/10 (manageable risk)
- Performance: 9/10 (good performance)

**Weighted Score:** (5×0.25) + (7×0.20) + (5×0.20) + (6×0.15) + (7×0.10) + (9×0.10) = **6.05/10**

**DECISION:** Session-based state management (Option A, score 8.35/10)

**Rationale:**
- Solves root cause (documented past issue in ARCHITECTURE_RISK_ANALYSIS.md)
- Prevents future conflicts
- Enables future features (multi-user, proper testing)
- Score is 8.35 (< 8.5) so **REQUIRES USER APPROVAL**

**Action:**
1. Create ADR-0002 (hypothetical)
2. Present to user: "I recommend session-based state (score 8.35) over quick fix (score 4.8). It requires 20 hours but prevents repeating past mistakes. Approve?"
3. Wait for user response
4. Implement after approval

---

## 🎯 Decision Framework Matrix

Use this matrix to evaluate options:

| Criteria | Weight | Option A | Option B | Option C |
|----------|--------|----------|----------|----------|
| **Maintainability** | 25% | Score 1-10 | Score 1-10 | Score 1-10 |
| **Testability** | 20% | Score 1-10 | Score 1-10 | Score 1-10 |
| **Future-proofing** | 20% | Score 1-10 | Score 1-10 | Score 1-10 |
| **Implementation Effort** | 15% | Score 1-10 | Score 1-10 | Score 1-10 |
| **Risk** | 10% | Score 1-10 | Score 1-10 | Score 1-10 |
| **Performance** | 10% | Score 1-10 | Score 1-10 | Score 1-10 |
| **TOTAL** | 100% | **Score** | **Score** | **Score** |

**Scoring Guide:**
- 10: Excellent - No concerns
- 7-9: Good - Minor concerns
- 4-6: Acceptable - Manageable issues
- 1-3: Poor - Significant concerns

**Decision Threshold:**
- Score ≥ 8.0: Proceed with confidence
- Score 6.0-7.9: Proceed with caution, document risks
- Score < 6.0: Reconsider or get user approval

---

## 📝 Architecture Decision Record (ADR) Template

After completing review, create an ADR:

**File naming:** `docs/architecture/decisions/ADR-NNNN-title.md`

```markdown
# ADR-NNNN: [Short Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Rejected | Superseded
**Decider:** Claude Code (or User if user provided direction)

## Context

What is the issue we're addressing? What factors are driving this decision?

[2-3 paragraphs describing the context, including:
- Current situation
- Problem being solved
- Constraints and requirements
- Past issues that inform this decision]

## Decision

What is the change we're proposing or doing?

[1-2 paragraphs with clear statement of the decision]

## Alternatives Considered

### Option A: [Name]
**Description:** [Brief description]
**Pros:** [List]
**Cons:** [List]
**Evaluation Score:** X.X/10

### Option B: [Name]
[Repeat]

### Chosen Option: [Name]
**Rationale:** [Why this was chosen over alternatives]

## Consequences

What becomes easier or more difficult after this change?

### Positive Consequences
- [Benefit 1]
- [Benefit 2]

### Negative Consequences / Trade-offs
- [Trade-off 1]
- [Trade-off 2]

### Risks
- [Risk 1] - **Mitigation:** [Strategy]
- [Risk 2] - **Mitigation:** [Strategy]

## Implementation Notes

### Files Affected
- [File 1] - [What changes]
- [File 2] - [What changes]

### Testing Strategy
- [Test plan summary]

### Rollback Plan
[How to revert if this doesn't work]

### Success Criteria
- [ ] [Measurable success criterion 1]
- [ ] [Measurable success criterion 2]

## Process Feedback

**REQUIRED: Fill this out after completing the ADR**

- **Actual Time Spent:** [X hours/minutes - compare to estimate]
- **Process Followed:** [Yes/Partial/No - explain if partial/no]
- **User Satisfaction:** [1-5 scale, if user involved]
- **What Worked Well:**
  - [Thing 1 that worked]
  - [Thing 2 that worked]
- **What Could Be Improved:**
  - [Issue 1 encountered]
  - [Issue 2 encountered]
- **Suggestions for Framework:**
  - [Any improvements to the review process]
  - [New triggers to add]
  - [Scoring adjustments needed]

**Note:** This feedback drives continuous improvement of the architectural decision process.

## References

- Related ADRs: ADR-XXXX, ADR-YYYY
- Related docs: [Document names]
- External resources: [Links]
```

---

## 🔍 Common Architectural Anti-Patterns to Avoid

Claude Code should watch for these red flags:

### 1. Tight Coupling
**Warning Signs:**
- Class A can't function without Class B
- Changes to one module require changes to many others
- Difficult to test components in isolation

**Solution:**
- Use dependency injection
- Define clear interfaces/contracts
- Apply SOLID principles

### 2. God Classes/Functions
**Warning Signs:**
- Single file > 500 lines
- Class with 10+ responsibilities
- Function with 50+ lines

**Solution:**
- Extract services/utilities
- Apply Single Responsibility Principle
- Break into smaller, focused components

### 3. Global State Hell
**Warning Signs:**
- Multiple global variables
- Unclear ownership of state
- Race conditions possible

**Solution:**
- Session-based state management
- Clear state ownership
- Immutable state patterns

### 4. Copy-Paste Programming
**Warning Signs:**
- Similar logic in 3+ places
- Bug fixes need replication
- High maintenance burden

**Solution:**
- Extract shared utilities
- Create reusable components
- DRY principle

### 5. Circular Dependencies
**Warning Signs:**
- Module A imports B, B imports A
- Import errors at runtime
- Can't reason about load order

**Solution:**
- Strict dependency hierarchy
- Extract shared code to lower layer
- Use dependency injection

### 6. Shotgun Surgery
**Warning Signs:**
- Single feature requires changes to 10+ files
- Hard to track all necessary changes
- High risk of missing updates

**Solution:**
- Improve cohesion
- Co-locate related functionality
- Reduce coupling

### 7. Leaky Abstractions
**Warning Signs:**
- Implementation details leak through API
- Users need to know internal workings
- Changes to internals break users

**Solution:**
- Better encapsulation
- Clear API boundaries
- Hide implementation details

### 8. Premature Optimization
**Warning Signs:**
- Complex code for unmeasured performance gains
- Sacrificing readability for speed
- No benchmarks to justify complexity

**Solution:**
- Measure first, optimize second
- Prefer simple, readable code
- Optimize only proven bottlenecks

---

## 🚀 Quick Reference: Decision Process

```
┌─────────────────────────────────────────────────────────────┐
│ 1. TRIGGER DETECTED                                         │
│    → Pause implementation                                   │
│    → Identify trigger type (High/Medium)                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. REVIEW CHECKLIST (30 min)                                │
│    → Problem analysis                                       │
│    → Generate 3 alternatives                                │
│    → Dependency analysis                                    │
│    → Future impact assessment                               │
│    → Testing strategy                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SCORE OPTIONS                                            │
│    → Use decision matrix                                    │
│    → Calculate weighted scores                              │
│    → Identify winner                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CREATE ADR                                               │
│    → Document decision                                      │
│    → File in docs/architecture/decisions/                   │
│    → Reference in PROJECT_CONTEXT.md                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. PRESENT TO USER                                          │
│    → Summary of problem                                     │
│    → Recommended solution with score                        │
│    → Key trade-offs                                         │
│    → Ask for approval before implementing                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. IMPLEMENT & VALIDATE                                     │
│    → Follow implementation plan                             │
│    → Run tests continuously                                 │
│    → Update documentation                                   │
│    → Mark ADR as "Accepted"                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 Learning from Past Mistakes

**This project's history shows these architectural issues:**

### Issue 1: Tight Coupling (Bidding ↔ Play)
**Problem:** Had to create MODULAR_ARCHITECTURE_PLAN.md to decouple
**Impact:** Development velocity loss, testing difficulty
**Lesson:** Always design for independent testability from day 1
**Prevention:** Use service layer pattern, clear API boundaries

### Issue 2: Global State Management
**Problem:** `current_deal`, `current_play_state` as globals
**Impact:** Session conflicts, race conditions, hard to test
**Lesson:** Session-based state from the start
**Prevention:** Review ARCHITECTURE_RISK_ANALYSIS.md Risk #1

### Issue 3: Documentation Proliferation
**Problem:** 79 documentation files, 350 min/sprint overhead
**Impact:** 50% doc maintenance burden
**Lesson:** Just-in-time documentation, consolidate aggressively
**Prevention:** Follow .claude/DOCUMENTATION_PRACTICES.md

---

## ✅ Success Patterns to Replicate

**Good architectural decisions in this project:**

1. **Engine Separation** (`engine/bidding_engine.py` vs `engine/play_engine.py`)
   - Clean separation of concerns
   - Independent testing
   - Reusable components

2. **Convention Modules** (`engine/ai/conventions/`)
   - Modular design
   - Easy to add new conventions
   - Clear interfaces

3. **Test Organization** (unit/, integration/, regression/)
   - Fast feedback loops (30 sec quick tests)
   - Clear categorization
   - Easy to run subsets

4. **Development Templates** (`.claude/templates/`)
   - Eliminate decision fatigue
   - Ensure consistency
   - Faster development

---

## 📊 Metrics to Track

After implementing architectural decisions, track these metrics:

### Code Quality Metrics
- Lines of code per module (target: < 500)
- Cyclomatic complexity (target: < 10 per function)
- Test coverage (target: > 80%)
- Number of dependencies per module (target: < 10)

### Development Velocity Metrics
- Time to implement new features
- Number of files touched per feature (target: < 5)
- Time to run test suite (target: < 5 min full, < 30 sec quick)
- Time to debug issues (track over time)

### Maintenance Metrics
- Number of bugs caused by architectural issues
- Time spent on refactoring vs new features
- Documentation maintenance time
- Onboarding time for new developers

---

## 🤝 Integration with Existing Workflow

This framework integrates with existing processes:

### With Feature Checklist
```markdown
## Pre-Implementation (from FEATURE_CHECKLIST.md)
- [ ] Read feature requirements
- [ ] 🏗️ **CHECK ARCHITECTURAL TRIGGERS** ← ADD THIS
- [ ] Identify affected files
- [ ] Run quick tests
```

### With Bug Fix Checklist
```markdown
## Investigation (from BUG_FIX_CHECKLIST.md)
- [ ] Reproduce bug
- [ ] Identify root cause
- [ ] 🏗️ **CHECK IF FIX REQUIRES ARCHITECTURAL REVIEW** ← ADD THIS
- [ ] Write failing test
```

### With Documentation Checklist
```markdown
## Always Update (from DOCUMENTATION_CHECKLIST.md)
- [ ] Update relevant documentation
- [ ] 🏗️ **CREATE ADR IF ARCHITECTURAL DECISION** ← ADD THIS
- [ ] Run documentation compliance
```

---

## 🎯 Next Steps for Claude Code

When encountering a potential architectural decision:

1. **STOP** - Don't implement immediately
2. **DETECT** - Check against trigger list
3. **REVIEW** - Complete 30-minute review checklist
4. **DECIDE** - Use decision matrix to score options
5. **DOCUMENT** - Create ADR
6. **PRESENT** - Show user the analysis and recommendation
7. **IMPLEMENT** - Only after user approval (or high confidence)
8. **VALIDATE** - Run tests, check metrics
9. **REFLECT** - Update this framework if new patterns emerge

---

**Status:** ✅ ACTIVE - Use this framework for all significant architectural decisions
**Owner:** Claude Code (with user approval for high-risk decisions)
**Review Frequency:** Update after each major architectural decision
**Last Updated:** 2025-10-12
