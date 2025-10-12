# Test Organization

**Last Updated**: 2025-10-12

## Directory Structure

```
tests/
├── unit/              # Fast unit tests (core bidding logic)
├── integration/       # Integration tests (multiple components)
├── regression/        # Bug fix verification tests
├── features/          # Feature-specific tests
├── scenarios/         # Scenario-based tests
└── play/              # Card play engine tests
```

## Running Tests

### Fast Feedback Loop (30 seconds)
```bash
# Run only unit tests
pytest backend/tests/unit/ -v

# Run specific test file
pytest backend/tests/unit/test_opening_bids.py -v
```

### Medium Feedback (2 minutes)
```bash
# Run unit + integration tests
pytest backend/tests/unit/ backend/tests/integration/ -v
```

### Full Test Suite (5+ minutes)
```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ -v --cov=backend/engine --cov-report=html
```

### Test by Category
```bash
# Unit tests only
pytest backend/tests/unit/ -v

# Integration tests
pytest backend/tests/integration/ -v

# Regression tests (bug fixes)
pytest backend/tests/regression/ -v

# Feature tests
pytest backend/tests/features/ -v

# Scenario tests
pytest backend/tests/scenarios/ -v

# Card play tests
pytest backend/tests/play/ -v
```

## Test Categories Explained

### Unit Tests (`unit/`)
- **Purpose**: Test individual components in isolation
- **Speed**: Very fast (< 1 second per test)
- **Examples**: Opening bids, responses, Stayman, Jacoby transfers
- **When to run**: During development, constantly

### Integration Tests (`integration/`)
- **Purpose**: Test multiple components working together
- **Speed**: Medium (1-5 seconds per test)
- **Examples**: Full bidding sequences, phase integration tests
- **When to run**: Before committing changes

### Regression Tests (`regression/`)
- **Purpose**: Verify specific bug fixes don't reoccur
- **Speed**: Fast to medium
- **Examples**: Each file represents a specific bug fix
- **When to run**: Before major releases, in CI/CD

### Feature Tests (`features/`)
- **Purpose**: Test complete features end-to-end
- **Speed**: Slow (5+ seconds per test)
- **Examples**: AI review, gameplay review, enhanced explanations
- **When to run**: When working on features, before release

### Scenario Tests (`scenarios/`)
- **Purpose**: Test specific bidding scenarios and conventions
- **Speed**: Medium
- **Examples**: Convention combinations, edge cases
- **When to run**: When working on conventions

### Play Tests (`play/`)
- **Purpose**: Test card play engine
- **Speed**: Medium to slow
- **Examples**: Minimax AI, hand evaluation
- **When to run**: When working on card play features

## Pytest Markers

Tests are marked with pytest markers for easy filtering:

```bash
# Run only fast tests
pytest -m fast

# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"

# Run only bidding tests
pytest -m bidding

# Run only play tests
pytest -m play
```

## Best Practices

1. **Default to unit tests** during development
2. **Run integration tests** before committing
3. **Run full suite** before pushing to remote
4. **Run regression tests** before releases
5. **Keep tests fast** - mock external dependencies
6. **Name tests clearly** - test name should describe what's being tested

## Adding New Tests

### For a new feature:
```bash
# Create in features/
backend/tests/features/test_my_new_feature.py
```

### For a bug fix:
```bash
# Create in regression/
backend/tests/regression/test_fix_bug_name.py
```

### For core bidding logic:
```bash
# Add to or create in unit/
backend/tests/unit/test_new_bidding_rule.py
```

### For integration:
```bash
# Create in integration/
backend/tests/integration/test_component_interaction.py
```

## Continuous Integration

Tests run automatically on:
- Every commit (unit tests)
- Every pull request (full suite)
- Before deployment (full suite with coverage)

## Coverage Goals

- **Unit tests**: > 90% coverage of engine/ code
- **Integration tests**: All major user flows covered
- **Regression tests**: Every bug fix has a test
- **Feature tests**: All features have end-to-end tests

## Quick Reference

```bash
# Development (fastest)
pytest backend/tests/unit/ -v

# Pre-commit (thorough)
pytest backend/tests/unit/ backend/tests/integration/ -v

# Pre-push (complete)
pytest backend/tests/ -v

# Coverage report
pytest backend/tests/ --cov=backend/engine --cov-report=html
# View report: open htmlcov/index.html
```
