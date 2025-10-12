# Contributing to Bridge Bidding App

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Documentation Requirements](#documentation-requirements)
4. [Code Standards](#code-standards)
5. [Testing Requirements](#testing-requirements)
6. [Commit Guidelines](#commit-guidelines)
7. [Pull Request Process](#pull-request-process)

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+
- Git

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd bridge_bidding_app

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### Running the Application

```bash
# Backend (from backend/ directory)
python server.py

# Frontend (from frontend/ directory)
npm start
```

## Development Workflow

We use the **development branch workflow**:

1. **Main branch** (`main` or `master`): Production-ready code
2. **Development branch** (`development`): Integration branch for features
3. **Feature branches**: Individual features or bug fixes

### Creating a Feature Branch

```bash
# Start from development branch
git checkout development
git pull origin development

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### Branch Naming Conventions

- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates
- `test/description` - Test additions/updates

## Documentation Requirements

**CRITICAL**: Documentation updates are MANDATORY for all code changes.

### Documentation is Part of Definition of Done

No PR will be merged without appropriate documentation updates. This is not optional.

### Required Documentation

For every code change, you must:

1. **Review the checklist**: Use [docs/DOCUMENTATION_CHECKLIST.md](docs/DOCUMENTATION_CHECKLIST.md)
2. **Follow the practices**: Read [.claude/DOCUMENTATION_PRACTICES.md](.claude/DOCUMENTATION_PRACTICES.md)
3. **Update all affected docs**: See the checklist for which files to update

### Documentation Standards

#### Always Update:
- Feature-specific docs in `docs/features/` if behavior changed
- README files if user-facing functionality changed
- API documentation for endpoint/interface changes
- Architecture docs if design patterns changed
- Bug fix docs in `docs/bug-fixes/` for resolved issues

#### File Organization:
```
docs/
├── architecture/          # System design and technical architecture
├── bug-fixes/            # Historical bug fix documentation
├── development-phases/   # Milestone and phase completion docs
├── features/             # Feature-specific implementation guides
├── guides/               # How-to guides and test documentation
├── project-overview/     # High-level summaries and index
└── debug-archive/        # Archived debugging information
```

#### Documentation Templates:

**Bug Fix Documentation:**
```markdown
# [Bug Name]

**Date Fixed**: YYYY-MM-DD
**Files Modified**: List key files

## Problem Description
What was the bug?

## Root Cause
Why did it happen?

## Solution Implemented
How was it fixed?

## Testing
How was the fix verified?

## Related Documentation Updated
- List of updated docs with links
```

**Feature Documentation:**
```markdown
# [Feature Name]

**Status**: [In Progress / Complete / Deprecated]
**Last Updated**: YYYY-MM-DD

## Overview
Brief description

## Implementation Details
Technical details

## Usage
How users interact with it

## Testing
Test coverage

## Related Files
- Links to implementation files
- Links to test files

## Future Enhancements
Planned improvements
```

### Documentation Quality Checks

Before submitting a PR, verify:
- [ ] All code examples are accurate and tested
- [ ] All internal links work
- [ ] No contradictions with actual code
- [ ] "Last Updated" dates are current
- [ ] New features are discoverable from index docs

## Code Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all functions/classes
- Keep functions focused and single-purpose

```python
def calculate_hcp(hand: List[str]) -> int:
    """
    Calculate high card points for a bridge hand.

    Args:
        hand: List of card strings (e.g., ['AS', 'KH', '2D'])

    Returns:
        Total HCP as integer
    """
    # Implementation
```

### JavaScript/React (Frontend)

- Use functional components with hooks
- Follow ESLint configuration
- Use meaningful variable names
- Keep components small and focused

### Code Comments

- Comment **why**, not **what**
- Explain complex algorithms or business logic
- Document edge cases and assumptions
- Keep comments up to date with code

## Testing Requirements

### Backend Tests

All backend changes must include tests:

```bash
# Run all tests
pytest

# Run specific test file
pytest backend/tests/test_opening_bids.py

# Run with verbose output
pytest -v
```

### Test Coverage

- New features must have test coverage
- Bug fixes must include a test that would have caught the bug
- Aim for meaningful tests, not just coverage numbers

### Test Documentation

- Document test approach in feature docs
- Explain any complex test setups or mocks
- Update test guides if testing patterns change

## Commit Guidelines

### Commit Message Format

```
type: Brief description (50 chars or less)

Longer description if needed. Explain the why, not the what.
Include any context, edge cases, or important decisions.

Closes #123 (if applicable)
```

### Commit Types

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes only
- `refactor:` Code refactoring (no functional changes)
- `test:` Adding or updating tests
- `chore:` Build process, dependencies, etc.

### Examples

```
feat: Add support for negative doubles

Implements negative doubles for responder after opponent's overcall.
Includes point range requirements and suit length validation.

Closes #45

---

fix: Correct 2♣ forcing to game rebid logic

The opener was not properly forcing to game after 2♣ opening.
Now correctly requires rebid to continue forcing until game is reached.

Related to issue #67

---

docs: Update bidding system documentation for takeout doubles

Added comprehensive documentation for takeout double implementation
including point requirements, shape requirements, and responding logic.
```

### Documentation in Commits

- **Preferred**: Include documentation updates in the same commit as code
- **Alternative**: Separate commit with `docs:` prefix, referencing feature commit
- **Never**: Leave documentation for later

## Pull Request Process

### Before Creating PR

1. **Run all tests**: Ensure tests pass locally
2. **Update documentation**: Use the documentation checklist
3. **Review your changes**: Read through every file you modified
4. **Check for TODOs**: Resolve or document any TODO comments
5. **Update branch**: Merge latest from development

```bash
git checkout development
git pull origin development
git checkout your-feature-branch
git merge development
# Resolve any conflicts
```

### Creating the PR

1. **Use the PR template** (see `.github/pull_request_template.md`)
2. **Write a clear title**: Summarize the change
3. **Fill out description**: Explain what, why, and how
4. **List documentation updates**: Be explicit about which docs you updated
5. **Link related issues**: Use "Closes #123" syntax
6. **Self-review**: Review your own PR first

### PR Template Checklist

Your PR must include:

- [ ] Description of changes
- [ ] Why this change is needed
- [ ] How it was tested
- [ ] List of documentation files updated
- [ ] Screenshots (if UI changes)
- [ ] Breaking changes noted (if any)

### Review Process

- PRs require review before merging
- Address all review comments
- Update documentation based on review feedback
- Re-request review after making changes

### Merging

- **Squash and merge** for feature branches (preferred)
- **Merge commit** for significant multi-commit features
- Delete feature branch after merge
- Ensure development branch tests pass after merge

## Special Scenarios

### Hotfixes

For critical production bugs:

1. Create branch from `main`: `hotfix/critical-bug`
2. Fix the bug with minimal changes
3. Create documentation (can be minimal for urgent fixes)
4. PR to `main` and `development`
5. Document any skipped docs as TODOs
6. Follow up with complete documentation within 24 hours

### Refactoring

For code refactoring without functional changes:

1. Update architecture documentation if structure changed
2. Update code examples in feature docs
3. Ensure no broken references
4. Note in PR description that behavior is unchanged
5. Include tests demonstrating equivalent behavior

### Breaking Changes

For changes that break existing functionality:

1. Document the breaking change prominently
2. Create migration guide if needed
3. Update all affected documentation
4. Include in commit message with `BREAKING CHANGE:` footer
5. Consider deprecation period before removing functionality

## Getting Help

- Review existing documentation in `docs/`
- Check [DOCUMENTATION_INDEX.md](docs/project-overview/DOCUMENTATION_INDEX.md)
- Look at recent PRs for examples
- Ask questions in pull request comments

## Code Review Guidelines

When reviewing PRs:

- Check that documentation is updated
- Verify code examples in docs are accurate
- Test the changes locally
- Ensure tests are meaningful
- Be constructive and respectful
- Approve only when documentation is complete

## Recognition

Contributors will be recognized in:
- Git commit history
- Pull request comments
- Project documentation (for significant contributions)

Thank you for contributing and maintaining high-quality documentation!
