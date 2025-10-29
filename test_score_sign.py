#!/usr/bin/env python3
"""
Test to verify scoring perspective is correct
"""

import sys
sys.path.insert(0, 'backend')

from engine.play_engine import PlayEngine, Contract

print("=" * 70)
print("SCORING PERSPECTIVE TEST")
print("=" * 70)
print()

# Test Case 1: NS declares and makes
print("TEST 1: NS declares 3NT and makes (+3 overtricks)")
print("-" * 70)
contract1 = Contract(level=3, strain='NT', declarer='S', doubled=0)
tricks1 = 12
vuln1 = {'ns': False, 'ew': False}
result1 = PlayEngine.calculate_score(contract1, tricks1, vuln1)
print(f"Contract: {contract1}")
print(f"Tricks taken: {tricks1}")
print(f"Backend score (declarer perspective): {result1['score']}")
print(f"Expected: +490 (positive because declarer made)")
print(f"Status: {'✓ PASS' if result1['score'] == 490 else '✗ FAIL'}")
print()

# Test Case 2: NS declares and goes down
print("TEST 2: NS declares 6NT and goes down (-3)")
print("-" * 70)
contract2 = Contract(level=6, strain='NT', declarer='S', doubled=0)
tricks2 = 9  # Needs 12, only took 9
vuln2 = {'ns': False, 'ew': False}
result2 = PlayEngine.calculate_score(contract2, tricks2, vuln2)
print(f"Contract: {contract2}")
print(f"Tricks taken: {tricks2} (needed {contract2.tricks_needed})")
print(f"Backend score (declarer perspective): {result2['score']}")
print(f"Expected: -150 (negative because declarer went down)")
print(f"Status: {'✓ PASS' if result2['score'] == -150 else '✗ FAIL'}")
print()

# Test Case 3: EW declares and makes
print("TEST 3: EW declares 4♥ and makes (exactly)")
print("-" * 70)
contract3 = Contract(level=4, strain='♥', declarer='E', doubled=0)
tricks3 = 10
vuln3 = {'ns': False, 'ew': False}
result3 = PlayEngine.calculate_score(contract3, tricks3, vuln3)
print(f"Contract: {contract3}")
print(f"Tricks taken: {tricks3}")
print(f"Backend score (declarer perspective): {result3['score']}")
print(f"Expected: +420 (positive because declarer made)")
print(f"Status: {'✓ PASS' if result3['score'] == 420 else '✗ FAIL'}")
print()

# Test Case 4: EW declares and goes down
print("TEST 4: EW declares 7♣ and goes down (-6)")
print("-" * 70)
contract4 = Contract(level=7, strain='♣', declarer='W', doubled=0)
tricks4 = 7  # Needs 13, only took 7
vuln4 = {'ns': False, 'ew': False}
result4 = PlayEngine.calculate_score(contract4, tricks4, vuln4)
print(f"Contract: {contract4}")
print(f"Tricks taken: {tricks4} (needed {contract4.tricks_needed})")
print(f"Backend score (declarer perspective): {result4['score']}")
print(f"Expected: -300 (negative because declarer went down)")
print(f"Status: {'✓ PASS' if result4['score'] == -300 else '✗ FAIL'}")
print()

print("=" * 70)
print("FRONTEND CONVERSION LOGIC TEST")
print("=" * 70)
print()

def convert_to_ns_perspective(backend_score, declarer):
    """This is what the frontend does"""
    declarer_is_ns = declarer in ['N', 'S']
    user_score = backend_score if declarer_is_ns else -backend_score
    return user_score

print("Converting backend scores to NS (user) perspective:")
print("-" * 70)
print(f"Test 1 (NS makes 3NT+3):   Backend={result1['score']:+5d} → NS={convert_to_ns_perspective(result1['score'], 'S'):+5d} (should be +490)")
print(f"Test 2 (NS down 3 in 6NT): Backend={result2['score']:+5d} → NS={convert_to_ns_perspective(result2['score'], 'S'):+5d} (should be -150)")
print(f"Test 3 (EW makes 4♥):      Backend={result3['score']:+5d} → NS={convert_to_ns_perspective(result3['score'], 'E'):+5d} (should be -420)")
print(f"Test 4 (EW down 6 in 7♣):  Backend={result4['score']:+5d} → NS={convert_to_ns_perspective(result4['score'], 'W'):+5d} (should be +300)")
print()

# Check if all conversions are correct
all_correct = (
    convert_to_ns_perspective(result1['score'], 'S') == 490 and
    convert_to_ns_perspective(result2['score'], 'S') == -150 and
    convert_to_ns_perspective(result3['score'], 'E') == -420 and
    convert_to_ns_perspective(result4['score'], 'W') == 300
)

if all_correct:
    print("✓ ALL TESTS PASS - Frontend conversion logic is CORRECT")
else:
    print("✗ TESTS FAIL - There is a bug in the conversion logic")

print()
print("=" * 70)
print("CONCLUSION")
print("=" * 70)
print()
print("Backend returns scores from DECLARER's perspective:")
print("  - Positive when declarer makes contract")
print("  - Negative when declarer goes down")
print()
print("Frontend must convert to NS (user) perspective:")
print("  - If NS declares: use score as-is")
print("  - If EW declares: flip the sign")
print()
print("This is because user plays South, so user's team is NS.")
print("When EW makes, NS loses (so positive backend score becomes negative)")
print("When EW goes down, NS wins (so negative backend score becomes positive)")
print()
