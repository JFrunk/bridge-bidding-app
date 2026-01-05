#!/bin/bash
# Full test runner - runs all tests with coverage
# Run time: ~5+ minutes (plus optional efficiency test)
#
# Options:
#   --with-efficiency    Also run V2 bidding efficiency test (requires SSH to production)
#   --efficiency-only    Only run V2 bidding efficiency test

set -e

# Parse arguments
RUN_EFFICIENCY=false
EFFICIENCY_ONLY=false

for arg in "$@"; do
    case $arg in
        --with-efficiency)
            RUN_EFFICIENCY=true
            shift
            ;;
        --efficiency-only)
            EFFICIENCY_ONLY=true
            shift
            ;;
    esac
done

if [ "$EFFICIENCY_ONLY" = false ]; then
    echo "🔍 Running full test suite with coverage..."
    pytest tests/ -v --cov=engine --cov-report=html --cov-report=term

    if [ $? -eq 0 ]; then
        echo "✅ All tests passed!"
        echo "📊 Coverage report generated in htmlcov/index.html"
    else
        echo "❌ Some tests failed"
        exit 1
    fi
fi

if [ "$RUN_EFFICIENCY" = true ] || [ "$EFFICIENCY_ONLY" = true ]; then
    echo ""
    echo "🎯 Running V2 bidding efficiency test (200 hands)..."
    echo "   This requires SSH access to production for DDS analysis."
    echo ""
    USE_V2_SCHEMA_ENGINE=true python3 analyze_bidding_efficiency.py --hands 200 --seed 42

    if [ $? -eq 0 ]; then
        echo "✅ Efficiency test complete!"
        echo "📊 Chart saved to bidding_efficiency.png"
    else
        echo "⚠️  Efficiency test failed (may require SSH access to production)"
    fi
fi
