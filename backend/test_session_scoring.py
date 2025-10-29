"""
Test session scoring logic to verify positive/negative assignment

This test verifies that the session scoring correctly assigns points:
- When NS makes a contract, NS gets positive points
- When NS sets EW (defeats their contract), NS gets positive points
- When NS goes down, EW gets positive points (penalty)
- When EW makes a contract, EW gets positive points (NS sees this as negative in display)
"""

from engine.session_manager import GameSession
from engine.play_engine import Contract


def test_ns_makes_contract():
    """NS declares and makes 3NT (+400) - NS should get +400"""
    session = GameSession(id=1, user_id=1)

    # NS declares 3NT and makes it
    session.add_hand_score(declarer='S', score=400)

    assert session.ns_score == 400, f"NS should have +400, got {session.ns_score}"
    assert session.ew_score == 0, f"EW should have 0, got {session.ew_score}"
    print("✓ NS makes contract: NS gets +400")


def test_ns_goes_down():
    """NS declares 3NT and goes down 1 (-50) - EW should get +50"""
    session = GameSession(id=1, user_id=1)

    # NS declares 3NT and goes down 1
    session.add_hand_score(declarer='N', score=-50)

    assert session.ns_score == 0, f"NS should have 0, got {session.ns_score}"
    assert session.ew_score == 50, f"EW should have +50 (penalty), got {session.ew_score}"
    print("✓ NS goes down: EW gets +50 penalty")


def test_ew_makes_contract():
    """EW declares 4♠ and makes it (+420) - EW should get +420"""
    session = GameSession(id=1, user_id=1)

    # EW declares 4♠ and makes it
    session.add_hand_score(declarer='E', score=420)

    assert session.ns_score == 0, f"NS should have 0, got {session.ns_score}"
    assert session.ew_score == 420, f"EW should have +420, got {session.ew_score}"
    print("✓ EW makes contract: EW gets +420")


def test_ew_goes_down():
    """EW declares 4♠ and goes down 2 (-100) - NS should get +100"""
    session = GameSession(id=1, user_id=1)

    # EW declares 4♠ and goes down 2
    session.add_hand_score(declarer='W', score=-100)

    assert session.ns_score == 100, f"NS should have +100 (penalty), got {session.ns_score}"
    assert session.ew_score == 0, f"EW should have 0, got {session.ew_score}"
    print("✓ EW goes down: NS gets +100 penalty (NS set the contract)")


def test_complete_session():
    """Test a complete 4-hand Chicago session with mixed results"""
    session = GameSession(id=1, user_id=1, session_type='chicago', max_hands=4)

    # Hand 1: NS declares 3NT, makes +400
    session.add_hand_score(declarer='S', score=400)
    assert session.ns_score == 400
    assert session.ew_score == 0
    print(f"  Hand 1: NS +400, EW 0 → Total: NS {session.ns_score}, EW {session.ew_score}")

    # Hand 2: EW declares 4♠, makes +420
    session.add_hand_score(declarer='E', score=420)
    assert session.ns_score == 400
    assert session.ew_score == 420
    print(f"  Hand 2: EW +420 → Total: NS {session.ns_score}, EW {session.ew_score}")

    # Hand 3: NS declares 2♥, goes down 1 (-50)
    session.add_hand_score(declarer='N', score=-50)
    assert session.ns_score == 400
    assert session.ew_score == 470  # 420 + 50 penalty
    print(f"  Hand 3: NS down 1, EW +50 penalty → Total: NS {session.ns_score}, EW {session.ew_score}")

    # Hand 4: EW declares 3NT, goes down 2 (-100)
    session.add_hand_score(declarer='W', score=-100)
    assert session.ns_score == 500  # 400 + 100 penalty
    assert session.ew_score == 470
    print(f"  Hand 4: EW down 2, NS +100 penalty → Total: NS {session.ns_score}, EW {session.ew_score}")

    assert session.is_complete()
    assert session.get_winner() == 'NS'
    print(f"✓ Complete session: NS wins {session.ns_score} to {session.ew_score}")


def test_doubled_contracts():
    """Test that doubled/redoubled penalties work correctly"""
    session = GameSession(id=1, user_id=1)

    # NS declares 3NT doubled, goes down 1 vulnerable (-200)
    session.add_hand_score(declarer='S', score=-200)
    assert session.ns_score == 0
    assert session.ew_score == 200
    print("✓ NS goes down 1 doubled vulnerable: EW gets +200 penalty")

    # EW declares 5♣ doubled, goes down 3 not vulnerable (-500)
    session.add_hand_score(declarer='E', score=-500)
    assert session.ns_score == 500
    assert session.ew_score == 200
    print("✓ EW goes down 3 doubled: NS gets +500 penalty")


if __name__ == '__main__':
    print("\n=== Testing Session Scoring Logic ===\n")

    print("Test 1: NS Makes Contract")
    test_ns_makes_contract()

    print("\nTest 2: NS Goes Down")
    test_ns_goes_down()

    print("\nTest 3: EW Makes Contract")
    test_ew_makes_contract()

    print("\nTest 4: EW Goes Down (NS Sets Contract)")
    test_ew_goes_down()

    print("\nTest 5: Complete 4-Hand Session")
    test_complete_session()

    print("\nTest 6: Doubled Contracts")
    test_doubled_contracts()

    print("\n=== All Tests Passed! ===\n")

    print("Summary:")
    print("- When NS makes a contract → NS gets positive points ✓")
    print("- When NS sets EW (defeats EW contract) → NS gets positive points (penalty) ✓")
    print("- When NS goes down → EW gets positive points (penalty) ✓")
    print("- When EW makes a contract → EW gets positive points ✓")
