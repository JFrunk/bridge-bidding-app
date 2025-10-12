#!/bin/bash
# Quick test runner - runs only unit tests for fast feedback
# Run time: ~30 seconds

echo "🚀 Running quick unit tests..."
pytest tests/unit/ -v

if [ $? -eq 0 ]; then
    echo "✅ All unit tests passed!"
else
    echo "❌ Some tests failed"
    exit 1
fi
