# ADR-0000: Use Architecture Decision Records

**Date:** 2025-10-12
**Status:** Accepted
**Decider:** User & Claude Code

## Context

The bridge bidding application has experienced architectural issues that required refactoring and caused velocity loss:

1. **Tight Coupling Issue:** Bidding and play modules were tightly coupled, requiring a major refactoring plan (MODULAR_ARCHITECTURE_PLAN.md) to separate concerns.

2. **Global State Problems:** Use of global state variables (`current_deal`, `current_play_state`) created session conflicts and testing difficulties (documented in ARCHITECTURE_RISK_ANALYSIS.md).

3. **Documentation Proliferation:** 79 documentation files created 350 min/sprint overhead, requiring consolidation effort.

4. **Refactoring Burden:** Past architectural choices required significant refactoring work, causing velocity loss and technical debt.

**The Problem:** We need a systematic way to:
- Review architectural implications BEFORE making changes
- Document WHY decisions were made
- Learn from past mistakes
- Avoid repeating architectural anti-patterns

**The Question:** How do we ensure Claude Code (as the sole developer) makes sound architectural decisions and documents them for future reference?

## Decision

We will use **Architecture Decision Records (ADRs)** to document all significant architectural decisions.

**What this means:**
1. Claude Code will detect "architectural triggers" (new directories, data structure changes, API modifications, etc.)
2. Claude Code will pause and complete a 30-minute architectural review checklist
3. Claude Code will evaluate at least 3 alternative approaches using a weighted decision matrix
4. Claude Code will create an ADR documenting the decision, alternatives, and trade-offs
5. For high-risk decisions, Claude Code will present analysis to user for approval before implementing

**Where ADRs live:**
- `docs/architecture/decisions/ADR-NNNN-title.md`
- Numbered sequentially starting from 0001
- Referenced from PROJECT_CONTEXT.md and README.md

**When to create an ADR:**
- Creating new directories or reorganizing structure
- Adding dependencies
- Changing data structures used across modules
- Modifying API contracts
- Introducing new state management patterns
- Creating new database schemas
- Modifying build/deployment configuration
- Refactoring code used by 3+ modules

## Alternatives Considered

### Option A: No Formal Decision Documentation
**Description:** Continue without formal architectural review process
**Pros:**
- Faster development (no review overhead)
- Less documentation to maintain
**Cons:**
- Repeats past mistakes
- No learning from history
- Architectural drift over time
- Hard to understand past decisions
**Evaluation Score:** 3.5/10
**Rejected because:** Already suffered from lack of architectural review (tight coupling, global state issues)

### Option B: Full RFC (Request for Comments) Process
**Description:** Implement heavyweight RFC process like Rust/Python
**Pros:**
- Very thorough review
- Community input (if open source)
- High-quality decisions
**Cons:**
- Too heavy for single developer (Claude Code)
- Slows development significantly
- Requires user involvement for every decision
- Not suitable for AI-driven development
**Evaluation Score:** 5.0/10
**Rejected because:** Overkill for our use case, too slow

### Option C: Architecture Decision Records (ADRs)
**Description:** Lightweight decision documentation with systematic review
**Pros:**
- Lightweight but systematic
- Documents WHY not just WHAT
- Easy to search past decisions
- Learn from mistakes
- Fits AI-driven development model
**Cons:**
- Some overhead (30 min per decision)
- Need to maintain discipline
- Another file format to manage
**Evaluation Score:** 8.5/10
**CHOSEN** ✅

## Consequences

### Positive Consequences
- **Reduced Refactoring:** Better initial decisions → less rework
- **Knowledge Preservation:** Understand why decisions were made
- **Pattern Recognition:** Identify recurring architectural patterns
- **Faster Onboarding:** New developers (or Claude in new sessions) understand architecture quickly
- **Quality Gate:** Forces consideration of alternatives before committing
- **Velocity Improvement:** Avoid architectural mistakes that slow development

### Negative Consequences / Trade-offs
- **Overhead:** ~30 minutes per architectural decision
- **Discipline Required:** Claude Code must detect triggers and follow process
- **Documentation Maintenance:** Another set of files to keep updated

### Risks
- **Risk 1: Process Ignored** - Claude Code might skip review for speed
  - **Mitigation:** Integrate into PROJECT_CONTEXT.md and templates, make it prominent
- **Risk 2: Too Heavy** - Process becomes burdensome and slows development
  - **Mitigation:** Keep it lightweight (30 min max), only for significant decisions
- **Risk 3: Stale ADRs** - Decisions become outdated but not updated
  - **Mitigation:** Mark ADRs as "Superseded" when replaced, link to new ADR

## Implementation Notes

### Files Created
- `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md` - Full framework with checklists
- `docs/architecture/decisions/ADR-0000-use-architecture-decision-records.md` - This ADR
- `docs/architecture/decisions/README.md` - Index of all ADRs

### Integration Points
- Update `.claude/PROJECT_CONTEXT.md` - Add architectural review section at top
- Update `.claude/templates/FEATURE_CHECKLIST.md` - Add architectural trigger check
- Update `.claude/templates/BUG_FIX_CHECKLIST.md` - Add architectural trigger check
- Create `.claude/scripts/check_architectural_triggers.py` - Automated detection

### Testing Strategy
- Test the process on next architectural decision (e.g., implementing modular architecture)
- Measure overhead (should be ~30 minutes)
- Evaluate decision quality after 1 month
- Adjust process based on experience

### Rollback Plan
If this process proves too burdensome:
1. Archive all ADRs to `docs/architecture/decisions/.archive/`
2. Remove integration from PROJECT_CONTEXT.md
3. Return to ad-hoc decision making
4. Document why ADR process was discontinued

### Success Criteria
- [ ] At least 3 ADRs created in first month
- [ ] Zero major refactoring due to poor architectural decisions in next 3 months
- [ ] Overhead remains under realistic time estimates (15-30 min simple, 45-60 min moderate, 2-4 hours complex)
- [ ] User satisfaction ≥ 4/5 on average
- [ ] Demonstrable velocity improvement vs. baseline

## Process Feedback (Meta-feedback for ADR-0000)

**Time Spent:** 7 hours (initial implementation)
**Process Followed:** Yes - created comprehensive framework, templates, scripts
**User Satisfaction:** TBD (awaiting user review)
**What Worked:**
- Comprehensive documentation
- Automated tooling (trigger detection, compliance report)
- Integration into existing workflow

**What Didn't:**
- No baseline captured initially (fixed)
- No worked examples initially (fixed in management review)
- Decision authority was ambiguous (fixed in management review)

**Improvements Made:**
- Added TL;DR and decision authority matrix (2025-10-12)
- Added worked examples (2025-10-12)
- Captured baseline metrics (2025-10-12)
- [ ] User satisfaction with architectural decision quality

## References

- **Related ADRs:** None (this is the first)
- **Related docs:**
  - `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md` - Full framework
  - `ARCHITECTURE_RISK_ANALYSIS.md` - Past architectural issues
  - `MODULAR_ARCHITECTURE_PLAN.md` - Example of needed refactoring
- **External resources:**
  - [Michael Nygard's ADR format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
  - [GitHub ADR organization](https://adr.github.io/)
  - [Joel Parker Henderson's ADR templates](https://github.com/joelparkerhenderson/architecture-decision-record)

---

**Status:** ✅ Accepted and Active
**Next ADR:** ADR-0001 (will document next significant architectural decision)
