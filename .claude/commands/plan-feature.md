Plan feature implementation before coding: $ARGUMENTS

Feature description: $ARGUMENTS

⚠️  **CRITICAL: Plan FIRST, get approval, THEN code**

---

## Phase 1: Research (DO NOT CODE YET)

**Think hard about the feature:**

1. **Understand Requirements:**
   - What problem does this solve?
   - Who is the user?
   - What are acceptance criteria?
   - Are there examples or mockups?

2. **Explore Codebase:**
   - Read relevant existing code
   - Identify similar features
   - Find patterns to follow
   - Locate dependencies

3. **Architectural Implications:**
   - Does this require database changes?
   - New API endpoints?
   - Frontend components?
   - State management changes?
   - External dependencies?

---

## Phase 2: Design (PRESENT TO USER)

**Create comprehensive plan:**

### 4. Architecture Diagram

```
[Describe data flow: User → Frontend → API → Backend → Database]
```

### 5. Components to Create/Modify

**Backend:**
- [ ] New files to create: [list]
- [ ] Existing files to modify: [list]
- [ ] Database schema changes: [list]
- [ ] API endpoints: [list with methods]

**Frontend:**
- [ ] New components: [list]
- [ ] Existing components to modify: [list]
- [ ] New state management: [list]
- [ ] API integration: [list]

### 6. Implementation Steps (in order)

**Step-by-step breakdown:**
1. [First step - most foundational]
2. [Second step - builds on first]
3. [Third step - builds on second]
...
N. [Final step - integration]

### 7. Testing Strategy

**Tests to write:**
- Unit tests for: [list components/functions]
- Integration tests for: [list endpoints/flows]
- Feature tests for: [list user scenarios]
- Quality baselines: [bidding/play if applicable]

### 8. Documentation Plan

**Docs to create/update:**
- Feature doc: `docs/features/[FEATURE_NAME].md`
- CLAUDE.md: [sections to update]
- API docs: [endpoints to document]
- README: [if setup changed]

### 9. Risk Assessment

**Potential risks:**
- Technical: [list technical challenges]
- Performance: [potential bottlenecks]
- Security: [security considerations]
- User experience: [UX concerns]

**Mitigation strategies:**
- [How to address each risk]

### 10. Time Estimate

**Estimated effort:**
- Research & planning: [X hours]
- Implementation: [X hours]
- Testing: [X hours]
- Documentation: [X hours]
- **Total: [X hours]**

### 11. Success Criteria

**Feature is complete when:**
- [ ] All acceptance criteria met
- [ ] Tests written and passing
- [ ] Quality baselines show no regression
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Deployed to staging
- [ ] User acceptance testing passed

---

## Phase 3: Present Plan (GET APPROVAL)

**Present this plan to user:**

```
## Feature Implementation Plan

**Feature:** [Name]
**Problem:** [What it solves]
**User:** [Who benefits]

### Architecture
[Diagram/description]

### Changes Required
- Backend: [summary]
- Frontend: [summary]
- Database: [summary]

### Implementation Steps (N steps)
1. [Step 1]
2. [Step 2]
...

### Testing
- [Test strategy summary]

### Risks
- [Key risks and mitigations]

### Effort
- Total: [X hours]

### Alternatives Considered
1. **Option A (Recommended):** [Approach]
   - Pros: [list]
   - Cons: [list]

2. **Option B:** [Alternative approach]
   - Pros: [list]
   - Cons: [list]
   - Why not chosen: [reason]

Proceed with implementation?
```

**Wait for user approval before coding**

---

## Phase 4: Implementation (After Approval)

12. Use `/project:start-tdd-feature` to implement with TDD
13. Follow the plan step-by-step
14. Update plan if discoveries made during implementation
15. Mark steps complete using TodoWrite

---

## Success Criteria

- [ ] Requirements clearly understood
- [ ] Codebase explored thoroughly
- [ ] Comprehensive plan created
- [ ] Architecture designed
- [ ] Risks identified and mitigated
- [ ] Plan presented to user BEFORE coding
- [ ] User approved plan
- [ ] Implementation follows plan
- [ ] All success criteria met

Reference: .claude/EFFECTIVENESS_IMPROVEMENTS.md Planning-First Workflow
