# Feature Development Checklist

**Feature Name**: _____________________
**Date Started**: _____________________
**Estimated Completion**: _____________________

## Pre-Implementation

- [ ] Read feature requirements thoroughly
- [ ] Identify affected files and components
- [ ] 🏗️ **CHECK ARCHITECTURAL TRIGGERS** - Does this feature involve:
  - [ ] New directories or project reorganization?
  - [ ] New dependencies (npm, pip)?
  - [ ] Changes to data structures used across modules?
  - [ ] API modifications (endpoints, request/response)?
  - [ ] New state management patterns?
  - [ ] Creating classes > 200 lines?
  - [ ] Modifying shared utilities?
  - **IF YES**: Run `python3 .claude/scripts/check_architectural_triggers.py --verbose`
  - **IF HIGH-RISK**: Complete [ARCHITECTURAL_DECISION_FRAMEWORK.md](../.claude/ARCHITECTURAL_DECISION_FRAMEWORK.md) review (30 min)
  - **IF HIGH-RISK**: Create ADR in `docs/architecture/decisions/` and get user approval
- [ ] Identify which documentation will need updates
- [ ] Review related existing code
- [ ] Plan test approach

## Implementation

- [ ] Create feature branch: `git checkout -b feature/feature-name`
- [ ] Implement core functionality
- [ ] Add docstrings to all new functions/classes
- [ ] Add inline comments for complex logic
- [ ] Write unit tests (aim for >90% coverage)

## Testing

- [ ] Run quick tests: `./backend/test_quick.sh`
- [ ] All unit tests pass
- [ ] Write integration tests if needed
- [ ] All integration tests pass
- [ ] Manual testing completed
- [ ] Edge cases tested

## Documentation

- [ ] Update or create feature documentation in `docs/features/`
- [ ] Update README if user-facing
- [ ] Update architecture docs if design changed
- [ ] Update `PROJECT_STATUS.md` if significant feature
- [ ] Run compliance checker: `python3 .claude/scripts/check_documentation_compliance.py --verbose`
- [ ] All documentation checks pass

## Code Quality

- [ ] Code follows project standards (PEP 8 for Python)
- [ ] No unnecessary TODOs or FIXMEs left
- [ ] Type hints added (Python)
- [ ] No debugging print statements left
- [ ] Code is DRY (Don't Repeat Yourself)

## Pre-Commit

- [ ] Run full test suite: `./backend/test_full.sh`
- [ ] All tests pass
- [ ] Run compliance checker (with --verbose)
- [ ] Stage all files: `git add .`
- [ ] Review staged changes: `git diff --cached`

## Commit

- [ ] Write clear commit message:
  ```
  feat: Brief description of feature

  Detailed explanation of what the feature does and why.
  Include any important implementation decisions.
  ```
- [ ] Commit: `git commit` (pre-commit hook will run)
- [ ] Address any pre-commit hook issues

## Completion

- [ ] Mark task complete in TodoWrite
- [ ] Update project status if needed
- [ ] Note any follow-up tasks

## Notes

(Add any relevant notes, decisions, or context here)
