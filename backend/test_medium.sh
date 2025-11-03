#!/bin/bash
# Medium test runner - runs unit + integration tests
# Run time: ~2 minutes

echo "🏃 Running unit and integration tests..."
pytest tests/unit/ tests/integration/ -v

if [ $? -eq 0 ]; then
    echo "✅ All unit and integration tests passed!"
else
    echo "❌ Some tests failed"
    exit 1
fi
