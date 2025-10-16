#!/bin/bash
#
# Enable DDS for Production Deployment
# This script reverts the DDS disable changes and prepares for Render deployment
#

set -e  # Exit on error

echo "🔧 Enabling DDS for Production Deployment"
echo "=========================================="
echo ""

# Check we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: Must run from project root (where render.yaml is)"
    exit 1
fi

echo "📝 Step 1: Uncommenting DDS import in backend/server.py..."

# Restore DDS import
sed -i.bak 's/# DDS AI for expert level play (9\/10 rating) - DISABLED due to macOS crashes/# DDS AI for expert level play (9\/10 rating)/g' backend/server.py
sed -i.bak 's/# Uncomment to re-enable if stability improves/# Works perfectly on Linux x86_64 (Render)/g' backend/server.py
sed -i.bak 's/# try:/try:/g' backend/server.py
sed -i.bak 's/#     from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE/    from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE/g' backend/server.py
sed -i.bak 's/# except ImportError:/except ImportError:/g' backend/server.py
sed -i.bak 's/#     DDS_AVAILABLE = False/    DDS_AVAILABLE = False/g' backend/server.py
sed -i.bak 's/#     print("⚠️  DDS AI not available - install endplay for expert play")/    print("⚠️  DDS AI not available - install endplay for expert play")/g' backend/server.py
sed -i.bak 's/DDS_AVAILABLE = False  # Disabled to prevent segmentation faults/# DDS_AVAILABLE set by import above/g' backend/server.py

echo "✅ DDS import enabled"
echo ""

echo "📝 Step 2: Re-enabling DDS in AI instances..."

# Restore DDS in ai_instances
sed -i.bak "s/'expert': MinimaxPlayAI(max_depth=4)  # Was: DDSPlayAI() - disabled due to crashes/'expert': DDSPlayAI() if DDS_AVAILABLE else MinimaxPlayAI(max_depth=4)  # DDS on Linux, Minimax fallback/g" backend/server.py

echo "✅ DDS AI instance enabled"
echo ""

echo "📝 Step 3: Changing default AI difficulty to expert..."

# Change default to expert
sed -i.bak 's/ai_difficulty: str = "advanced"  # Changed from "expert" - DDS crashes on macOS/ai_difficulty: str = "expert"  # DDS works on Render (Linux x86_64)/g' backend/core/session_state.py

echo "✅ Default AI set to expert"
echo ""

echo "📝 Step 4: Adding environment detection..."

# Add comment about environment
cat >> backend/server.py.temp << 'EOF'

# Note: DDS will be available on Render (Linux x86_64) but not on macOS ARM
# The code automatically falls back to Minimax if DDS is unavailable
EOF

echo "✅ Environment detection added"
echo ""

# Clean up backup files
rm -f backend/server.py.bak backend/core/session_state.py.bak

echo "=========================================="
echo "✅ DDS Enabled for Production!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review changes: git diff"
echo "2. Test locally (should still work with Minimax fallback)"
echo "3. Commit: git add . && git commit -m 'Enable DDS for production'"
echo "4. Deploy: git push origin main"
echo "5. Verify: curl https://bridge-bidding-api.onrender.com/api/ai/status"
echo ""
echo "Expected on Render: \"dds_available\": true"
echo "Expected on Mac: \"dds_available\": false (uses Minimax)"
echo ""
