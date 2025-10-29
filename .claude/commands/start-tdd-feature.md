Start new feature using test-driven development: $ARGUMENTS

Feature description: $ARGUMENTS

⚠️  **IMPORTANT: Write tests FIRST, implementation SECOND**

---

## Phase 1: Research & Plan (DO NOT CODE YET)

**Think hard about the feature requirements:**

1. Read relevant existing code and documentation
2. Identify affected components (backend/frontend/both)
3. List dependencies and potential conflicts
4. Search for similar patterns in codebase
5. Design the solution architecture
6. **Create implementation checklist** (use TodoWrite)

**Output:** Present plan to user for approval before proceeding

---

## Phase 2: Write Tests First (MANDATORY)

⚠️  **Do NOT write implementation code in this phase**

7. Create test file(s):
   - Unit tests: `backend/tests/unit/test_[feature].py`
   - Integration tests: `backend/tests/integration/test_[feature]_integration.py`
   - Feature tests: `backend/tests/features/test_[feature]_e2e.py`
8. Write failing tests for:
   - Happy path (expected usage)
   - Edge cases (boundary conditions)
   - Error conditions (invalid input)
   - Integration points (API contracts)
9. **Run tests to confirm they fail:**
   - `cd backend && pytest tests/unit/test_[feature].py -v`
   - Verify failures are for the right reasons (not syntax errors)
10. Commit tests: `git add tests/ && git commit -m "test: Add tests for [feature]"`

---

## Phase 3: Implement (Make Tests Pass)

11. Implement **minimal** code to make first test pass
12. Run tests frequently: `pytest tests/unit/test_[feature].py -v`
13. Iterate until all tests pass
14. Refactor for quality once tests are green
15. **Run quality baselines** (if bidding/play logic changed):
    - Bidding: `python3 backend/test_bidding_quality_score.py --hands 100`
    - Play: `python3 backend/test_play_quality_integrated.py --hands 100 --level 8`
16. Commit implementation: `git add . && git commit -m "feat: Implement [feature]"`

---

## Phase 4: Verify & Document

17. Run full test suite: `cd backend && ./test_full.sh`
18. **Update documentation:**
    - Feature doc: `docs/features/FEATURE_NAME.md`
    - CLAUDE.md (if architecture changed)
    - API docs (if endpoints added)
19. Create examples (if applicable)
20. Commit docs: `git add docs/ && git commit -m "docs: Document [feature]"`

---

## Success Criteria

- [ ] Tests written and committed BEFORE implementation
- [ ] All tests pass
- [ ] Quality baselines show no regression (if applicable)
- [ ] Full test suite passes
- [ ] Documentation updated
- [ ] Code reviewed (if team project)

Reference: CLAUDE.md Testing Strategy, .claude/EFFECTIVENESS_IMPROVEMENTS.md TDD workflow
