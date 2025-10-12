# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Bridge Bidding Application.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. It helps us:

- **Understand WHY** decisions were made, not just what was implemented
- **Learn from history** and avoid repeating mistakes
- **Onboard quickly** by understanding the architectural evolution
- **Make better decisions** by forcing systematic evaluation of alternatives

## ADR Process

See [ARCHITECTURAL_DECISION_FRAMEWORK.md](../../.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md) for the full process.

**Quick summary:**
1. Detect architectural trigger (new structure, API change, etc.)
2. Complete 30-minute review checklist
3. Evaluate 3+ alternatives using decision matrix
4. Create ADR documenting decision
5. Get user approval for high-risk decisions
6. Implement and validate

## ADR Index

| # | Title | Status | Date | Summary |
|---|-------|--------|------|---------|
| [0000](ADR-0000-use-architecture-decision-records.md) | Use Architecture Decision Records | Accepted | 2025-10-12 | Adopt ADR process for documenting significant architectural decisions |
| [0001](ADR-0001-shared-infrastructure-architecture.md) | Shared Infrastructure Architecture | Proposed | 2025-10-12 | Extract shared components (Hand, Card, display) while creating independent operational modules for bidding and play testing |

## ADR Statuses

- **Proposed** - Under consideration, not yet decided
- **Accepted** - Decision approved and being/has been implemented
- **Rejected** - Considered but not chosen (kept for historical reference)
- **Deprecated** - No longer relevant but kept for history
- **Superseded** - Replaced by a newer ADR (link to replacement)

## Creating a New ADR

1. Determine the next ADR number (NNNN)
2. Copy the template from `.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md`
3. Create file: `ADR-NNNN-short-title.md`
4. Complete all sections
5. Add entry to this README.md index
6. Reference from relevant documentation

## ADR Template

```markdown
# ADR-NNNN: [Short Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Rejected | Superseded
**Decider:** Claude Code (or User)

## Context
[What is the issue? What factors are driving this decision?]

## Decision
[What is the change we're proposing/doing?]

## Alternatives Considered
### Option A: [Name]
[Description, pros, cons, evaluation score]

### Chosen Option: [Name]
[Rationale]

## Consequences
### Positive Consequences
- [Benefit 1]

### Negative Consequences / Trade-offs
- [Trade-off 1]

### Risks
- [Risk 1] - **Mitigation:** [Strategy]

## Implementation Notes
[Files affected, testing strategy, rollback plan, success criteria]

## References
[Related ADRs, docs, external resources]
```

## Guidelines

### When to Create an ADR

**DO create an ADR for:**
- New directories or major reorganization
- Adding dependencies
- Changing data structures across modules
- Modifying API contracts
- New state management patterns
- Database schema changes
- Build/deployment changes
- Security pattern changes

**DON'T create an ADR for:**
- Bug fixes that don't change interfaces
- Documentation-only changes
- Adding tests without code changes
- Refactoring within a single file
- Formatting/linting fixes

### ADR Writing Tips

1. **Be Concise:** Target 1-2 pages max
2. **Focus on WHY:** The code shows what, ADR explains why
3. **Show Alternatives:** Always evaluate at least 3 options
4. **Be Honest:** Document trade-offs and risks
5. **Link Everything:** Reference related ADRs and docs
6. **Update Status:** Mark as Superseded when replaced

### Reviewing Old ADRs

Periodically review ADRs to:
- Mark deprecated decisions
- Link to superseding ADRs
- Extract patterns for reuse
- Update success metrics

## Project-Specific Context

**This project's architectural history:**

- **Tight Coupling:** Had to plan major refactoring (MODULAR_ARCHITECTURE_PLAN.md)
- **Global State:** Caused session conflicts (ARCHITECTURE_RISK_ANALYSIS.md)
- **Documentation Debt:** 79 files created 50% maintenance burden

These past issues inform our architectural decision making. Each ADR should consider:
- How does this avoid past mistakes?
- Does this improve or worsen coupling?
- What's the maintenance burden?
- Is this easily testable?

## ADR Maintenance & Continuous Improvement

### Monthly Review Process

**Schedule:** First week of each month

**Checklist:**
- [ ] Review all ADRs created last month
- [ ] Aggregate process feedback from ADRs
- [ ] Update decision matrix weights if needed
- [ ] Add new triggers based on patterns
- [ ] Mark deprecated/superseded ADRs
- [ ] Update framework based on learnings
- [ ] Capture monthly metrics:
  - ADRs created this month
  - Average time per ADR
  - User satisfaction average
  - Refactorings avoided (qualitative)

### When to Update an ADR

**NEVER edit existing ADR** (preserve history). Instead:

1. **Create superseding ADR:**
   ```
   ADR-NNNN-new-approach.md
   ```

2. **Mark old ADR as superseded:**
   Add to old ADR:
   ```markdown
   **Status:** Superseded by ADR-NNNN
   **Date Superseded:** YYYY-MM-DD
   ```

3. **Link from new ADR:**
   ```markdown
   **Supersedes:** ADR-XXXX
   **Reason:** [Why the change]
   ```

### Handling Wrong Decisions

If an ADR decision proves wrong:

1. **Create reversal ADR:**
   ```
   ADR-NNNN-reversal-of-XXXX-reason.md
   ```

2. **Document what went wrong:**
   - What assumptions were incorrect?
   - What changed that invalidated the decision?
   - What signals did we miss?

3. **Update framework:**
   - Add new trigger if missed
   - Adjust scoring criteria if needed
   - Document in anti-patterns if applicable

**This creates a learning trail, not a cover-up.**

### Metrics Tracking

**Baseline Captured:** 2025-10-12
- God classes: 1 (server.py - 677 lines)
- Global state instances: 12
- Circular dependencies: 0
- Excessive dependencies: 2 modules (server.py, bidding_engine.py - 19 each)
- ADRs: 1 (ADR-0000)
- Health Score: 70/100 (Grade C)

**Track Monthly:**
```bash
# Generate report
python3 .claude/scripts/architectural_compliance_report.py --verbose > monthly_report_YYYY-MM.txt

# Compare to baseline
# Track improvements/regressions
```

**Target Goals (6 months):**
- God classes: 0
- Global state instances: < 5
- Health Score: ≥ 85/100 (Grade B+)
- ADRs: 10-15 (1-2 per month average)

## Questions?

- See [ARCHITECTURAL_DECISION_FRAMEWORK.md](../../.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md) for detailed guidance
- Check [PROJECT_CONTEXT.md](../../.claude/PROJECT_CONTEXT.md) for project-specific context
- Review existing ADRs for examples

---

**Status:** Active
**Owner:** Claude Code (with user oversight)
**Last Updated:** 2025-10-12
**Baseline Metrics:** Captured 2025-10-12 (see `.claude/baseline_metrics_2025-10-12.txt`)
**Next Review:** 2025-11-01 (first monthly review)
