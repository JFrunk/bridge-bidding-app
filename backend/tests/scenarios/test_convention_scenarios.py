#!/usr/bin/env python3
"""
Test script to validate that each convention scenario generates appropriate hands
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_scenario(scenario_name):
    """Load a scenario and check if generated hands are appropriate"""
    print(f"\n{'='*70}")
    print(f"Testing: {scenario_name}")
    print(f"{'='*70}")

    # Load the scenario
    response = requests.post(f"{BASE_URL}/api/load-scenario",
                            json={"name": scenario_name})

    if response.status_code != 200:
        print(f"❌ Failed to load scenario: {response.text}")
        return False

    data = response.json()
    hand = data['hand']
    points = data['points']

    # Get all hands to see what was generated
    all_hands_response = requests.get(f"{BASE_URL}/api/get-all-hands")
    if all_hands_response.status_code != 200:
        print(f"❌ Failed to get all hands")
        return False

    all_hands_data = all_hands_response.json()
    all_hands = all_hands_data['hands']

    print(f"\nGenerated Hands:")
    for position in ['North', 'East', 'South', 'West']:
        h = all_hands[position]
        p = h['points']
        print(f"  {position}: {p['hcp']} HCP, {p['suit_lengths']['♠']}-{p['suit_lengths']['♥']}-{p['suit_lengths']['♦']}-{p['suit_lengths']['♣']}")

    # Validate based on scenario
    issues = []

    if scenario_name == "Jacoby Transfer Test":
        # South should have 5+ card major
        south = all_hands['South']['points']
        if south['suit_lengths']['♥'] < 5 and south['suit_lengths']['♠'] < 5:
            issues.append(f"South doesn't have 5+ card major (♥:{south['suit_lengths']['♥']}, ♠:{south['suit_lengths']['♠']})")

        # North should be 15-17 HCP and balanced
        north = all_hands['North']['points']
        if not (15 <= north['hcp'] <= 17):
            issues.append(f"North has {north['hcp']} HCP (expected 15-17)")

        # Check if balanced (no suit > 5, at least 2 suits with 2+ cards)
        max_suit_length = max(north['suit_lengths'].values())
        suits_with_2plus = sum(1 for length in north['suit_lengths'].values() if length >= 2)
        if max_suit_length > 5 or suits_with_2plus < 2:
            issues.append(f"North not balanced: {north['suit_lengths']}")

    elif scenario_name == "Stayman Test":
        # South should have 8+ HCP (or 7 with 4-4 majors) and 4-card major
        south = all_hands['South']['points']
        has_4_card_major = south['suit_lengths']['♥'] >= 4 or south['suit_lengths']['♠'] >= 4
        has_both_majors = south['suit_lengths']['♥'] >= 4 and south['suit_lengths']['♠'] >= 4

        if not has_4_card_major:
            issues.append(f"South doesn't have 4-card major (♥:{south['suit_lengths']['♥']}, ♠:{south['suit_lengths']['♠']})")

        if south['hcp'] < 7:
            issues.append(f"South has only {south['hcp']} HCP (need 7+ or 8+)")
        elif south['hcp'] == 7 and not has_both_majors:
            issues.append(f"South has 7 HCP but not 4-4 in majors (♥:{south['suit_lengths']['♥']}, ♠:{south['suit_lengths']['♠']})")

        # North should be 15-17 HCP and balanced
        north = all_hands['North']['points']
        if not (15 <= north['hcp'] <= 17):
            issues.append(f"North has {north['hcp']} HCP (expected 15-17)")

    elif scenario_name == "Opener Rebid Test":
        # North should have 16-18 HCP and 5+ spades
        north = all_hands['North']['points']
        if not (16 <= north['hcp'] <= 18):
            issues.append(f"North has {north['hcp']} HCP (expected 16-18)")
        if north['suit_lengths']['♠'] < 5:
            issues.append(f"North has only {north['suit_lengths']['♠']} spades (expected 5+)")

        # South should have 6-9 HCP
        south = all_hands['South']['points']
        if not (6 <= south['hcp'] <= 9):
            issues.append(f"South has {south['hcp']} HCP (expected 6-9)")

    elif scenario_name == "Preemptive Bid Test":
        # North should have weak two requirements: 6-10 HCP, 6-card suit
        north = all_hands['North']['points']
        max_suit_length = max(north['suit_lengths'].values())

        if not (6 <= north['hcp'] <= 10):
            issues.append(f"North has {north['hcp']} HCP (expected 6-10 for preempt)")
        if max_suit_length < 6:
            issues.append(f"North's longest suit is only {max_suit_length} cards (expected 6+ for preempt)")

    elif scenario_name == "Blackwood Test":
        # North should have slam-interest hand
        north = all_hands['North']['points']
        # Blackwood typically used with 17+ HCP or strong distributional hand
        if north['hcp'] < 15:
            issues.append(f"North has only {north['hcp']} HCP (may be too weak for Blackwood)")

        # South should have 13-15 HCP
        south = all_hands['South']['points']
        if not (13 <= south['hcp'] <= 15):
            issues.append(f"South has {south['hcp']} HCP (expected 13-15)")

    elif scenario_name in ["Takeout Double Test", "Negative Double Test", "Michaels Cuebid Test",
                          "Unusual 2NT Test", "Splinter Bid Test", "Fourth Suit Forcing Test"]:
        # These have empty setup, so they just generate random hands
        print("  ℹ️  This scenario has no specific hand requirements (empty setup)")
        return True

    # Report results
    if issues:
        print(f"\n❌ FAILED - Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"\n✅ PASSED - Generated hands match convention requirements")
        return True

def run_all_tests():
    """Test all scenarios"""
    print("\n" + "="*70)
    print("CONVENTION SCENARIO VALIDATION TESTS")
    print("="*70)

    scenarios = [
        "Jacoby Transfer Test",
        "Stayman Test",
        "Opener Rebid Test",
        "Preemptive Bid Test",
        "Blackwood Test",
        "Takeout Double Test",
        "Negative Double Test",
        "Michaels Cuebid Test",
        "Unusual 2NT Test",
        "Splinter Bid Test",
        "Fourth Suit Forcing Test"
    ]

    passed = 0
    failed = 0

    for scenario in scenarios:
        if test_scenario(scenario):
            passed += 1
        else:
            failed += 1

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Scenarios Tested: {len(scenarios)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n✅ ALL SCENARIOS GENERATE APPROPRIATE HANDS!")
    else:
        print(f"\n❌ {failed} SCENARIOS NEED FIXING")

    return failed == 0

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
