#!/bin/bash
# Full test runner - runs all tests with coverage
# Run time: ~5+ minutes

echo "🔍 Running full test suite with coverage..."
pytest tests/ -v --cov=engine --cov-report=html --cov-report=term

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "📊 Coverage report generated in htmlcov/index.html"
else
    echo "❌ Some tests failed"
    exit 1
fi
