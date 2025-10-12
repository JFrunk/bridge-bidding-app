# Documentation Maintenance Practices

**IMPORTANT**: This file provides mandatory guidelines for maintaining documentation in this project. Claude Code MUST follow these practices for every feature, bug fix, or modification.

## Core Principle

**Documentation updates are NOT optional** - they are a required part of Definition of Done for any code change.

## Mandatory Documentation Update Workflow

### For EVERY code change, follow this checklist:

#### 1. Before Starting Work
- [ ] Identify which documentation files may be affected
- [ ] Read current documentation to understand existing context
- [ ] Note any discrepancies between docs and actual code

#### 2. During Development
- [ ] Update inline code comments for complex logic
- [ ] Update docstrings for modified functions/classes
- [ ] Keep a mental note of user-facing changes

#### 3. After Implementation
- [ ] Update technical documentation for the specific feature/fix
- [ ] Update test documentation if test coverage changed
- [ ] Add entries to relevant bug fix or feature documentation

#### 4. Before Completing (CRITICAL)
Use this systematic review process:

##### Always Update:
- [ ] **Feature-specific docs** in `docs/features/` if feature behavior changed
- [ ] **README files** if user-facing functionality changed
- [ ] **API documentation** for any endpoint/interface changes
- [ ] **Architecture docs** in `docs/architecture/` if design patterns changed
- [ ] **Bug fix docs** in `docs/bug-fixes/` for resolved issues (create new file if needed)

##### Consider Updating:
- [ ] **Test documentation** if test approach or coverage changed
- [ ] **Configuration guides** for new settings/options
- [ ] **Development phase docs** in `docs/development-phases/` for milestone progress
- [ ] **Guides** in `docs/guides/` if procedures changed

##### Sometimes Update:
- [ ] **FEATURES_SUMMARY.md** for significant new features
- [ ] **PROJECT_STATUS.md** for major milestones
- [ ] **DOCUMENTATION_INDEX.md** if new docs were created
- [ ] **README.md** (root) for major user-visible changes

#### 5. Documentation Quality Standards
- [ ] All code examples are accurate and tested
- [ ] All internal links work correctly
- [ ] No contradictions with actual code behavior
- [ ] "Last Updated" dates are current
- [ ] No TODO/FIXME markers left unresolved
- [ ] New features are discoverable from index/summary docs

## File Organization Standards

### Creating New Documentation Files

**File Naming Convention:**
- Use UPPERCASE for major documents: `FEATURE_NAME.md`
- Use descriptive, specific names: `TAKEOUT_DOUBLE_FIX.md` not `fix1.md`
- Include dates for time-sensitive docs: `DOCUMENTATION_UPDATE_2025-10-12.md`

**File Location:**
```
docs/
├── architecture/          # System design, patterns, technical architecture
├── bug-fixes/            # Historical bug fix documentation
├── development-phases/   # Milestone and phase completion docs
├── features/             # Feature-specific implementation guides
├── guides/               # How-to guides, simulation guides, test guides
├── project-overview/     # High-level summaries, feature lists, documentation index
└── debug-archive/        # Archived debugging information
```

### Archiving Old Documentation

When documentation becomes obsolete:
1. **Don't delete immediately** - move to appropriate archive folder
2. **Add deprecation notice** at top with link to current doc
3. **Update the index** to remove or mark as archived
4. **Check for broken links** in other documents

Example deprecation notice:
```markdown
> **DEPRECATED**: This document is archived. See [NEW_DOC.md](../path/to/NEW_DOC.md) for current information.
> Archived: 2025-10-12
```

## Documentation Templates

### Bug Fix Documentation Template
```markdown
# [Bug Name/Description]

**Date Fixed**: YYYY-MM-DD
**Related Issue**: #123 (if applicable)
**Files Modified**: List key files

## Problem Description
Clear description of the bug and its impact.

## Root Cause
Technical explanation of why the bug occurred.

## Solution Implemented
How the bug was fixed, including code changes.

## Testing
How the fix was verified.

## Related Documentation Updated
- List all docs that were updated
- Include links to changed files
```

### Feature Documentation Template
```markdown
# [Feature Name]

**Status**: [In Progress / Complete / Deprecated]
**Last Updated**: YYYY-MM-DD

## Overview
Brief description of the feature.

## Implementation Details
Technical details of how it works.

## Usage
How users interact with this feature.

## Testing
Test coverage and validation approach.

## Related Files
- List key implementation files with links
- List related test files

## Future Enhancements
Planned improvements or known limitations.
```

## Commit Message Standards for Documentation

When committing documentation changes:
- **With code**: Include in the same commit as the code change
- **Standalone**: Use prefix `docs:` in commit message
- **Examples**:
  - `docs: Update bidding system documentation for negative doubles`
  - `feat: Add takeout double support (includes documentation)`

## Links and Cross-References

### Internal Links
Always use relative paths:
```markdown
See [Architecture Overview](../architecture/OVERVIEW.md)
```

### Code References
Use markdown links to specific files and line numbers:
```markdown
The bug is fixed in [rebids.py:145](../../backend/engine/rebids.py#L145)
```

### Maintaining Link Integrity
- When moving/renaming files, search for references: `grep -r "old-filename.md" docs/`
- Update all references in the same commit

## Automation and Tools

### Pre-commit Hook
The project includes a pre-commit hook (`.git/hooks/pre-commit`) that:
- Reminds you to update documentation
- Checks for common documentation issues
- Can be bypassed in emergencies with `git commit --no-verify` (use sparingly!)

### Documentation Checklist
Use `docs/DOCUMENTATION_CHECKLIST.md` for systematic review.

## Claude Code Specific Instructions

### When Implementing Features:
1. **Plan Phase**: Identify affected documentation files
2. **Implementation Phase**: Update technical/feature docs inline
3. **Testing Phase**: Update test documentation
4. **Completion Phase**:
   - Systematically review ALL potentially affected docs
   - Update summary/index files
   - Create bug fix documentation if applicable
   - Use the documentation checklist

### When Creating Commits:
- Always include documentation updates in the same commit as code changes
- If documentation is extensive, commit separately but reference the feature commit

### When Creating Pull Requests:
- Use the PR template which includes documentation checklist
- Ensure all documentation updates are mentioned in PR description

### Common Scenarios:

**Scenario: Fixed a bug in bidding logic**
- Create/update file in `docs/bug-fixes/[BUG_NAME].md`
- Update `docs/features/[RELATED_FEATURE].md` if behavior changed
- Update `docs/project-overview/FEATURES_SUMMARY.md` if significant
- Update test documentation in `docs/guides/`

**Scenario: Added new bidding convention**
- Create feature doc in `docs/features/[CONVENTION_NAME].md`
- Update `docs/project-overview/FEATURES_SUMMARY.md`
- Update `docs/README.md` if user-facing
- Update `docs/project-overview/DOCUMENTATION_INDEX.md`
- Add tests and document in feature doc

**Scenario: Refactored code structure**
- Update `docs/architecture/` documentation
- Update any guides that reference file structure
- Update code examples in feature docs

**Scenario: Completed development phase**
- Create summary in `docs/development-phases/[PHASE_NAME]_COMPLETE.md`
- Update `PROJECT_STATUS.md`
- Update `docs/project-overview/FEATURES_SUMMARY.md`
- Archive any obsolete planning documents

## Documentation Review Questions

Before marking any task complete, ask:

1. ✅ Would a new developer understand this change from the docs?
2. ✅ Are all code examples still accurate?
3. ✅ Do any diagrams need updating?
4. ✅ Are configuration examples current?
5. ✅ Is the feature discoverable from index/summary docs?
6. ✅ Are there broken links?
7. ✅ Are there any TODO/FIXME comments to address?
8. ✅ Is the "Last Updated" date current?
9. ✅ Does the documentation contradict the actual code behavior?
10. ✅ Are related test files documented?

## What NOT to Document

Avoid these anti-patterns:
- ❌ Implementation details that change frequently (put in code comments instead)
- ❌ Obvious functionality that's self-explanatory
- ❌ Temporary debugging information (archive after use)
- ❌ Duplicate information (link to canonical source instead)
- ❌ Speculative future plans (use TODO comments or issue tracker)

## Emergency Procedures

If you must skip documentation updates due to critical hotfix:
1. Create a TODO comment in the code: `# TODO: Update docs/features/X.md`
2. Create a follow-up task immediately
3. Update documentation within 24 hours
4. This should be RARE - documentation is part of the fix

## Success Metrics

Documentation is successful when:
- A new team member can understand the system from docs alone
- Code and docs never contradict each other
- Features are discoverable through documentation
- Historical context is preserved for debugging
- Documentation stays current without becoming a burden

---

**Remember**: Documentation is not an afterthought - it's an integral part of software craftsmanship. Treat documentation updates with the same rigor as code reviews.
