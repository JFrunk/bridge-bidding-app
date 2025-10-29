#!/usr/bin/env python3
"""
Check which AI is configured for gameplay
Run this to see what AI level will be used in production
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 80)
print("BRIDGE AI CONFIGURATION CHECK")
print("=" * 80)

# Check environment variable
default_ai = os.environ.get('DEFAULT_AI_DIFFICULTY', 'advanced')
print(f"\n📋 Environment Variable:")
print(f"   DEFAULT_AI_DIFFICULTY = '{default_ai}'")
print(f"   (Set in .env file or export DEFAULT_AI_DIFFICULTY=expert)")

# Check DDS availability
print(f"\n🔍 Checking DDS (Double Dummy Solver) availability...")
try:
    from engine.play.ai.dds_ai import DDS_AVAILABLE
    if DDS_AVAILABLE:
        print(f"   ✅ DDS is AVAILABLE")
        print(f"   Expert level will use DDS (9/10 perfect play)")
    else:
        print(f"   ⚠️  DDS is NOT available (library imported but not working)")
        print(f"   Expert level will use Minimax depth 4 (8/10)")
        print(f"   Common on macOS M1/M2 - DDS works on Linux")
except ImportError as e:
    print(f"   ❌ DDS is NOT available (import failed)")
    print(f"   Error: {e}")
    print(f"   Expert level will use Minimax depth 4 (8/10)")
    DDS_AVAILABLE = False

# Show AI mapping
print(f"\n🎮 AI Difficulty Levels:")
print(f"   beginner     → Simple Rule-Based AI (6/10)")
print(f"   intermediate → Minimax depth 2 (7.5/10)")
print(f"   advanced     → Minimax depth 3 (8/10)")
if DDS_AVAILABLE:
    print(f"   expert       → Double Dummy Solver (9/10) ✅ BEST")
else:
    print(f"   expert       → Minimax depth 4 (8+/10)")

print(f"\n🎯 CURRENT CONFIGURATION:")
print(f"   Default difficulty: {default_ai}")

# Import and show actual AI instance
try:
    from engine.play.ai.minimax_ai import MinimaxPlayAI
    from engine.play.ai.simple_ai import SimplePlayAI
    if DDS_AVAILABLE:
        from engine.play.ai.dds_ai import DDSPlayAI
        ai_instances = {
            'beginner': SimplePlayAI(),
            'intermediate': MinimaxPlayAI(max_depth=2),
            'advanced': MinimaxPlayAI(max_depth=3),
            'expert': DDSPlayAI()
        }
    else:
        ai_instances = {
            'beginner': SimplePlayAI(),
            'intermediate': MinimaxPlayAI(max_depth=2),
            'advanced': MinimaxPlayAI(max_depth=3),
            'expert': MinimaxPlayAI(max_depth=4)
        }

    current_ai = ai_instances[default_ai]
    print(f"   AI Engine: {current_ai.get_name()}")
    print(f"   AI Level: {current_ai.get_difficulty()}")

except Exception as e:
    print(f"   ⚠️  Could not load AI: {e}")

print(f"\n💡 RECOMMENDATIONS:")
print(f"   Development (macOS): DEFAULT_AI_DIFFICULTY=advanced (DDS may crash)")
print(f"   Production (Linux):  DEFAULT_AI_DIFFICULTY=expert (DDS works)")
print(f"\n   To change: Add to backend/.env file:")
print(f"   DEFAULT_AI_DIFFICULTY=expert")

print("\n" + "=" * 80)

# Show how to set for production
print("\n📝 TO SET FOR PRODUCTION:")
print(f"   1. Create backend/.env file (if it doesn't exist)")
print(f"   2. Add this line:")
print(f"      DEFAULT_AI_DIFFICULTY=expert")
print(f"   3. On Linux, ensure endplay is installed:")
print(f"      pip install endplay")
print(f"   4. Restart server")

print("\n" + "=" * 80)
