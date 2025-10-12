# Documentation Update Checklist

Use this checklist for every feature, bug fix, or code modification to ensure all relevant documentation is updated.

## Pre-Work Assessment

- [ ] I have identified which documentation files may be affected by this change
- [ ] I have read the current documentation to understand existing context
- [ ] I have noted any discrepancies between current docs and actual code

## Always Update (Check All That Apply)

- [ ] **Feature-specific documentation** in `docs/features/` (if feature behavior changed)
- [ ] **README files** (if user-facing functionality changed)
- [ ] **API documentation** (for any endpoint/interface changes)
- [ ] **Architecture documentation** in `docs/architecture/` (if design patterns changed)
- [ ] **Bug fix documentation** in `docs/bug-fixes/` (for resolved issues - create new file if needed)

## Consider Updating (Check If Applicable)

- [ ] **Test documentation** (if test approach or coverage changed)
- [ ] **Configuration guides** (for new settings/options)
- [ ] **Development phase documentation** in `docs/development-phases/` (for milestone progress)
- [ ] **Guides** in `docs/guides/` (if procedures changed)
- [ ] **Code comments and docstrings** (for complex logic or modified functions)

## Sometimes Update (For Significant Changes)

- [ ] **FEATURES_SUMMARY.md** (for significant new features)
- [ ] **PROJECT_STATUS.md** (for major milestones)
- [ ] **DOCUMENTATION_INDEX.md** (if new documentation files were created)
- [ ] **Root README.md** (for major user-visible changes)

## Documentation Quality Checks

- [ ] All code examples in documentation are accurate and tested
- [ ] All internal links work correctly (no broken links)
- [ ] Documentation does not contradict actual code behavior
- [ ] "Last Updated" dates are current in modified files
- [ ] No unresolved TODO/FIXME markers in documentation
- [ ] New features are discoverable from index/summary documents
- [ ] Complex features have usage examples
- [ ] Related test files are documented

## Archival and Cleanup

- [ ] Obsolete documentation moved to archive folders (not deleted)
- [ ] Deprecation notices added to archived documents
- [ ] Index files updated to reflect archived documents
- [ ] Checked for broken links to moved/renamed files

## File Organization

If you created new documentation:

- [ ] File is in the correct directory (`architecture/`, `bug-fixes/`, `features/`, etc.)
- [ ] File name follows naming conventions (UPPERCASE, descriptive)
- [ ] File added to `docs/project-overview/DOCUMENTATION_INDEX.md`
- [ ] File header includes status and last updated date

## Commit Preparation

- [ ] Documentation updates included in same commit as code changes (preferred)
- [ ] OR separate documentation commit with `docs:` prefix
- [ ] Commit message mentions documentation updates
- [ ] All modified files staged for commit

## Final Review Questions

Answer these before marking work complete:

1. [ ] Would a new developer understand this change from the documentation alone?
2. [ ] If I looked at this code in 6 months, would the docs help me understand why it exists?
3. [ ] Are there any edge cases or limitations that should be documented?
4. [ ] Have I documented the "why" not just the "what"?
5. [ ] If this change breaks something, is there enough information to debug it?

## Special Cases

### For Bug Fixes:
- [ ] Created bug fix documentation using template in `docs/bug-fixes/`
- [ ] Documented root cause and solution
- [ ] Listed all files modified
- [ ] Explained how fix was tested/verified

### For New Features:
- [ ] Created feature documentation using template in `docs/features/`
- [ ] Documented implementation details
- [ ] Included usage examples
- [ ] Listed test coverage
- [ ] Noted any future enhancements or limitations

### For Refactoring:
- [ ] Updated architecture documentation if structure changed
- [ ] Updated all guides that reference old file structure
- [ ] Updated code examples in feature documentation
- [ ] Ensured no broken references to old code locations

### For Test Updates:
- [ ] Documented new test approach in feature or guide documentation
- [ ] Updated test coverage information
- [ ] Explained any new testing patterns or helpers

---

## Notes Section

Use this space to note which documentation files you updated and why:

```
Files Updated:
- [file path]: [brief description of changes]
- [file path]: [brief description of changes]

Rationale:
[Explain your documentation decisions]
```

---

**Remember**: Documentation is complete when a new developer could understand, use, and modify your changes based solely on the documentation.
