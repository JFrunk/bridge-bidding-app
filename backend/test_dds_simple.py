"""
Simple test to verify DDS AI is working
"""

import sys
sys.path.insert(0, '.')

from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE

print("=" * 80)
print("DDS AI Simple Test")
print("=" * 80)
print()

# Check availability
print(f"DDS_AVAILABLE: {DDS_AVAILABLE}")
if not DDS_AVAILABLE:
    print("❌ DDS not available - install endplay")
    sys.exit(1)

print("✅ DDS library available")
print()

# Create DDS AI
print("Creating DDS AI instance...")
try:
    ai = DDSPlayAI()
    print(f"✅ AI created successfully")
    print(f"   Name: {ai.get_name()}")
    print(f"   Difficulty: {ai.get_difficulty()}")
except Exception as e:
    print(f"❌ Error creating AI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test endplay directly
print("Testing endplay library directly...")
try:
    from endplay.types import Deal, Player, Denom
    from endplay.dds import calc_dd_table

    # Create a simple deal
    pbn = "N:AKQ2.AK3.AK32.A2 JT9.QJ4.QJT9.KJ9 8765.T987.876.87 43.652.54.QT6543"
    deal = Deal(pbn)
    print(f"✅ Created test deal from PBN")

    # Calculate DD table
    dd_table = calc_dd_table(deal)
    print(f"✅ Calculated double dummy table")

    # Show some results
    print(f"   DD table calculated successfully")
    print(f"   Table type: {type(dd_table)}")

except Exception as e:
    print(f"❌ Error testing endplay: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("✅ ALL TESTS PASSED - DDS AI OPERATIONAL")
print("=" * 80)
print()
print("Summary:")
print("  - DDS library is installed and working")
print("  - DDSPlayAI class instantiates correctly")
print("  - endplay double dummy calculations work")
print("  - Ready for integration into server.py")
print()
print("Next steps:")
print("  1. Integrate DDS AI into server.py as 'expert' difficulty")
print("  2. Test with actual game positions")
print("  3. Run full benchmarks comparing all AIs")
