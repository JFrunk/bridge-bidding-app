# Automated Documentation Checks Guide

**Status**: Complete
**Last Updated**: 2025-10-12

## Overview

This guide documents the automated checking system implemented to ensure documentation stays current with code changes. Since Claude Code is the sole developer for this project, these automated checks provide critical validation that documentation standards are being followed.

## Why Automated Checks?

With Claude Code as the sole developer:
- **No human review** - Automated checks catch issues automatically
- **Consistency enforcement** - Standards are applied uniformly
- **Immediate feedback** - Issues are caught before commit
- **Quality assurance** - Multiple layers of validation
- **Documentation coverage tracking** - Identify gaps systematically

## Automated Tools

### 1. Documentation Compliance Checker

**Location**: [.claude/scripts/check_documentation_compliance.py](../../.claude/scripts/check_documentation_compliance.py)

**Purpose**: Comprehensive validation of documentation practices

**When to Run**:
- Before every commit
- After implementing any feature
- After fixing any bug
- Before marking tasks complete

**What It Checks**:

1. **Code Without Documentation**
   - Detects staged code files without corresponding documentation
   - Fails if code changes exist without doc changes
   - Lists which files are affected

2. **Documentation Dates**
   - Checks "Last Updated" dates in documentation
   - Warns if dates are not current
   - Identifies files missing dates that should have them

3. **Broken Links**
   - Validates internal markdown links
   - Checks that linked files actually exist
   - Reports broken relative paths

4. **TODO/FIXME Markers**
   - Finds unresolved TODO or FIXME markers
   - Ensures documentation is complete, not draft
   - Warns about markers in committed docs

5. **Required Documentation Files**
   - Verifies all mandatory documentation exists
   - Checks for core files like CONTRIBUTING.md, README.md
   - Ensures documentation system is complete

6. **Feature Documentation**
   - Checks if features have corresponding docs
   - Basic validation of feature documentation presence

7. **Bug Fix Documentation**
   - Analyzes recent commits for bug fixes
   - Checks if bug fix documentation exists
   - Recommends creating missing bug fix docs

**Usage**:

```bash
# Basic run (quiet mode)
python3 .claude/scripts/check_documentation_compliance.py

# Verbose mode (recommended)
python3 .claude/scripts/check_documentation_compliance.py --verbose

# With date fixing (not yet implemented)
python3 .claude/scripts/check_documentation_compliance.py --fix-dates
```

**Exit Codes**:
- `0` - All checks passed
- `1` - Checks failed (errors found)

**Sample Output**:

```
===========================================================
Documentation Compliance Checker
===========================================================

Checking: Required documentation files
✓ Required file exists: .claude/DOCUMENTATION_PRACTICES.md
✓ Required file exists: docs/DOCUMENTATION_CHECKLIST.md
...

Checking: Code without documentation
✓ Found 3 code file(s) and 2 documentation file(s) staged

Checking: Documentation dates
✓ docs/features/FEATURE.md: Last Updated date is current

...

===========================================================
Summary
===========================================================
Errors: 0
Warnings: 0
Successes: 15

✅ All documentation compliance checks PASSED!
```

### 2. Documentation Validation Script

**Location**: [.claude/scripts/validate_documentation.sh](../../.claude/scripts/validate_documentation.sh)

**Purpose**: Validate overall documentation structure and health

**When to Run**:
- Periodically (weekly or after major changes)
- When restructuring documentation
- After creating new documentation directories
- As part of milestone validation

**What It Checks**:

1. **Required Files Existence**
   - All core documentation files present
   - Validates documentation system is complete

2. **Directory Structure**
   - All required documentation directories exist
   - Proper organization maintained

3. **Documentation Structure**
   - Files have proper headers
   - Basic structure standards followed

4. **Link Validation**
   - Checks for obvious broken links
   - Validates relative paths

5. **Bug Fix Documentation**
   - Counts bug fix documentation files
   - Ensures docs/bug-fixes/ exists

6. **Feature Documentation**
   - Counts feature documentation files
   - Ensures docs/features/ exists

7. **Python Compliance Checks**
   - Runs the Python compliance checker
   - Comprehensive validation layer

**Usage**:

```bash
# Run validation
./.claude/scripts/validate_documentation.sh
```

**Exit Codes**:
- `0` - All checks passed (or only warnings)
- `1` - Errors found

**Sample Output**:

```
========================================
Documentation Validation Tool
========================================

[1/7] Checking required documentation files...
  ✓ Found: .claude/DOCUMENTATION_PRACTICES.md
  ✓ Found: CONTRIBUTING.md
  ...

[2/7] Checking documentation directory structure...
  ✓ Found: docs/architecture
  ✓ Found: docs/bug-fixes
  ...

========================================
Validation Summary
========================================
✅ All checks passed! Documentation is in good shape.
```

### 3. Documentation Coverage Report

**Location**: [.claude/scripts/documentation_coverage_report.py](../../.claude/scripts/documentation_coverage_report.py)

**Purpose**: Analyze documentation coverage across the codebase

**When to Run**:
- After completing a development phase
- After implementing major features
- Monthly as part of health check
- When planning documentation improvements

**What It Analyzes**:

1. **Module Documentation Coverage**
   - Lists Python modules in backend/engine
   - Identifies which have documentation
   - Calculates coverage percentage
   - Lists undocumented modules

2. **Bug Fix Documentation**
   - Analyzes recent bug fix commits
   - Checks for corresponding documentation
   - Identifies fixes without docs

3. **Documentation Health Metrics**
   - Total documentation file count
   - Feature documentation count
   - Bug fix documentation count
   - Guide and architecture doc counts

4. **Overall Assessment**
   - Rates documentation health
   - Provides grade (Excellent/Good/Needs Improvement)

5. **Recommendations**
   - Specific suggestions for improvement
   - Prioritized list of documentation to create

**Usage**:

```bash
# Console output
python3 .claude/scripts/documentation_coverage_report.py

# Generate HTML report
python3 .claude/scripts/documentation_coverage_report.py --html
```

**Sample Output**:

```
======================================================================
DOCUMENTATION COVERAGE REPORT
======================================================================
Generated: 2025-10-12 08:00:00

1. MODULE DOCUMENTATION COVERAGE
----------------------------------------------------------------------
Total Python modules in backend/engine: 5
Modules with documentation: 5
Coverage: 100.0%

✓ All modules have documentation!

2. BUG FIX DOCUMENTATION
----------------------------------------------------------------------
Recent bug fix commits analyzed: 8
Bug fix documentation files: 7

Recent fixes that may need documentation:
  • a1b2c3d: fix: Correct edge case in bidding logic

3. DOCUMENTATION HEALTH METRICS
----------------------------------------------------------------------
Total documentation files: 45
  • Feature documentation: 12
  • Bug fix documentation: 8
  • Guides: 8
  • Architecture docs: 5

4. OVERALL ASSESSMENT
----------------------------------------------------------------------
✅ EXCELLENT: Documentation coverage is very good

5. RECOMMENDATIONS
----------------------------------------------------------------------
• Keep up the excellent documentation practices!
• Continue to document all new features and bug fixes

======================================================================
```

### 4. Enhanced Pre-Commit Hook

**Location**: [.git/hooks/pre-commit](../../.git/hooks/pre-commit)

**Purpose**: Automatic validation on every commit

**When It Runs**: Automatically with every `git commit` command

**What It Does**:

1. **Detects Code Changes**
   - Identifies Python, JavaScript, TypeScript files
   - Distinguishes between code and documentation changes
   - Tracks test file changes

2. **Documentation Change Detection**
   - Checks if documentation files are staged
   - Warns if code changes without docs

3. **Interactive Prompts**
   - Prompts user if code without docs detected
   - Lists which documentation should be updated
   - Provides resources and checklist references

4. **Issue Detection**
   - Checks for TODO/FIXME in staged docs
   - Basic broken link detection
   - Warns about potential issues

5. **Automated Compliance Run**
   - Automatically runs Python compliance checker
   - Fails commit if compliance checks fail
   - Provides option to bypass (strongly discouraged)

6. **User Feedback**
   - Color-coded output (green/yellow/red)
   - Lists all staged documentation files
   - Encourages good practices

**How to Use**:

```bash
# Normal commit (hook runs automatically)
git commit -m "feat: Add new feature with documentation"

# The hook will:
# 1. Check for documentation
# 2. Run automated checks
# 3. Prompt if issues found
# 4. Allow commit if checks pass

# Bypass (NOT RECOMMENDED)
git commit --no-verify -m "emergency fix"
```

**Sample Interaction**:

```bash
=== Documentation Check ===

✓ Documentation updates detected - excellent!

Documentation files being committed:
  • docs/features/NEW_FEATURE.md
  • docs/README.md

=== Running Automated Compliance Checks ===

[Compliance checker output...]

Automated compliance checks passed!

Documentation check complete!
```

## Workflow Integration

### Standard Development Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Receive task or identify work needed                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ 2. Identify affected documentation files                   │
│    - Read current documentation                             │
│    - Note what needs updating                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ 3. Implement code changes                                   │
│    - Write code                                             │
│    - Update inline documentation/comments                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ 4. Update documentation                                     │
│    - Update all affected documentation files                │
│    - Use documentation checklist                            │
│    - Update "Last Updated" dates                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ 5. Run automated checks                                     │
│    python3 .claude/scripts/check_documentation_compliance.py │
│    --verbose                                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼────────┐
                    │  Checks Pass? │
                    └───┬───────┬───┘
                   Yes  │       │  No
              ┌─────────┘       └────────┐
              │                           │
    ┌─────────▼────────┐        ┌────────▼──────────┐
    │ 6. Run tests     │        │ Fix documentation │
    │    pytest        │        │ or code issues    │
    └─────────┬────────┘        └────────┬──────────┘
              │                           │
              │                     ┌─────▼──────┐
              │                     │  Rerun     │
              │                     │  checks    │
              │                     └─────┬──────┘
              │                           │
              └───────────┬───────────────┘
                          │
                  ┌───────▼─────────┐
                  │  Tests Pass?    │
                  └───┬─────────┬───┘
                 Yes  │         │  No
            ┌─────────┘         └────────┐
            │                             │
    ┌───────▼────────┐          ┌────────▼────────┐
    │ 7. Stage files │          │  Fix tests      │
    │    git add .   │          │                 │
    └───────┬────────┘          └────────┬────────┘
            │                             │
            │                    ┌────────▼────────┐
            │                    │   Rerun tests   │
            │                    └────────┬────────┘
            │                             │
            └─────────────┬───────────────┘
                          │
                  ┌───────▼────────┐
                  │  8. Commit     │
                  │  git commit    │
                  └───────┬────────┘
                          │
                  ┌───────▼────────┐
                  │ Pre-commit     │
                  │ hook runs      │
                  └───────┬────────┘
                          │
                  ┌───────▼─────────┐
                  │ Hook Passes?    │
                  └───┬─────────┬───┘
                 Yes  │         │  No
            ┌─────────┘         └────────┐
            │                             │
    ┌───────▼─────────┐         ┌────────▼───────────┐
    │ 9. Commit       │         │ Fix issues found   │
    │    succeeds     │         │ by hook & re-commit│
    └───────┬─────────┘         └────────┬───────────┘
            │                             │
            │                             │
            └─────────────┬───────────────┘
                          │
                  ┌───────▼─────────┐
                  │ 10. Mark task   │
                  │     complete    │
                  └─────────────────┘
```

### Periodic Health Checks

Run these periodically (weekly or monthly):

```bash
# 1. Full validation
./.claude/scripts/validate_documentation.sh

# 2. Coverage analysis
python3 .claude/scripts/documentation_coverage_report.py

# 3. Review recommendations and address gaps
```

## Best Practices

### DO ✅

1. **Run compliance checker before every commit**
   ```bash
   python3 .claude/scripts/check_documentation_compliance.py --verbose
   ```

2. **Address all errors immediately**
   - Don't commit with failing checks
   - Fix issues right away

3. **Review warnings seriously**
   - Warnings indicate potential issues
   - Address them proactively

4. **Run coverage report after major work**
   - After completing phases
   - After implementing several features
   - Monthly health check

5. **Use verbose mode to learn**
   - Understand what's being checked
   - See successes as well as failures

6. **Maintain high coverage**
   - Aim for >90% documentation coverage
   - Address undocumented modules promptly

### DON'T ❌

1. **Never use `--no-verify`**
   - Don't bypass pre-commit hook
   - Only in true emergencies

2. **Don't ignore warnings**
   - Warnings can become errors
   - Address them before they multiply

3. **Don't commit with failing checks**
   - Fix issues before committing
   - Don't create technical debt

4. **Don't skip automated checks**
   - They're there for a reason
   - They catch issues you might miss

5. **Don't let coverage drop**
   - Keep documentation current
   - Don't create new undocumented features

## Troubleshooting

### Compliance Checker Fails

**Issue**: Compliance checker reports errors

**Solution**:
1. Read the error messages carefully
2. Fix each issue listed
3. Rerun the checker
4. Repeat until all checks pass

**Common Issues**:
- Missing "Last Updated" dates → Add current date
- Broken links → Fix the path or create missing file
- TODO markers → Remove or resolve TODOs
- Code without docs → Update relevant documentation

### Pre-Commit Hook Blocks Commit

**Issue**: Pre-commit hook prevents commit

**Solution**:
1. Read the hook output
2. Stage missing documentation files
3. Fix issues identified
4. Try committing again

**DON'T**: Use `--no-verify` to bypass

### Low Coverage Report

**Issue**: Coverage report shows <90% coverage

**Solution**:
1. Review list of undocumented modules
2. Create documentation for each
3. Follow feature documentation template
4. Rerun coverage report to verify improvement

## Integration with Claude Code

As the sole developer, Claude Code should:

1. **Always run compliance checker** before marking tasks complete
2. **Never mark task complete** with failing checks
3. **Use TodoWrite** to track documentation tasks
4. **Include check results** in task completion notes
5. **Run coverage report** after major milestones
6. **Proactively address** warnings and low coverage

### Claude Code Checklist

Before completing any task:
- [ ] Implementation complete
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Compliance checker passes (`--verbose`)
- [ ] Pre-commit hook would pass
- [ ] All errors resolved
- [ ] Warnings addressed or documented
- [ ] Task marked complete in TodoWrite

## Future Enhancements

Potential improvements to automated checks:

1. **Automated date updates**
   - Script to update "Last Updated" dates automatically
   - `--fix-dates` flag implementation

2. **More sophisticated link checking**
   - Check external links (with rate limiting)
   - Validate anchor links within files
   - Check for redirect chains

3. **API documentation generation**
   - Auto-generate API docs from docstrings
   - Keep API documentation in sync with code

4. **Documentation style checking**
   - Enforce consistent formatting
   - Check for markdown linting
   - Validate code block syntax

5. **Coverage metrics tracking**
   - Track coverage over time
   - Generate trend reports
   - Alert on coverage drops

6. **CI/CD integration**
   - Run checks automatically in CI
   - Block merges with failing checks
   - Generate coverage reports in CI

## Summary

The automated checking system provides:

✅ **Multiple layers of validation**
✅ **Immediate feedback on issues**
✅ **Consistent standards enforcement**
✅ **Documentation coverage tracking**
✅ **Pre-commit protection**
✅ **Comprehensive reporting**

With these tools, documentation quality is maintained systematically, ensuring the codebase remains understandable and maintainable over time.

---

**Last Updated**: 2025-10-12
**Maintained by**: Claude Code
**Review**: After implementing future enhancements or identifying gaps
