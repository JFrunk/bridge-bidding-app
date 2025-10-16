#!/usr/bin/env python3
"""
Integration test: Verify doubled contracts work correctly end-to-end
including declarer determination and scoring.
"""

import sys
import os
# Add backend directory to path so we can import engine modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from engine.play_engine import PlayEngine, Contract
from engine.hand import Hand, Card

def create_hand_from_string(hand_str):
    """Helper to create a hand from string like '♠AKQ ♥432 ♦765 ♣432'"""
    cards = []
    parts = hand_str.split()
    for part in parts:
        suit = part[0]
        for rank in part[1:]:
            cards.append(Card(rank, suit))
    return Hand(cards)

def test_doubled_contract_integration():
    """
    Full integration test: Auction ending with double should:
    1. Correctly identify declarer (first to bid the strain on winning side)
    2. Record doubled=1 status
    3. Calculate doubled scoring correctly
    """

    print("Integration Test: Doubled 4♠ Contract")
    print("=" * 70)

    # Auction: North opens 1♠, South raises to 4♠, West doubles, all pass
    auction = ['1♠', 'Pass', '4♠', 'X', 'Pass', 'Pass', 'Pass']
    print(f"\nAuction: {' - '.join(auction)}")

    # Step 1: Determine contract
    contract = PlayEngine.determine_contract(auction, dealer_index=0)
    print(f"\nContract determined: {contract}")
    print(f"  Level: {contract.level}")
    print(f"  Strain: {contract.strain}")
    print(f"  Declarer: {contract.declarer}")
    print(f"  Doubled: {contract.doubled}")

    # Verify contract details
    assert contract.level == 4, "Should be 4-level contract"
    assert contract.strain == '♠', "Should be spades contract"
    assert contract.declarer == 'N', "North should be declarer (opened spades)"
    assert contract.doubled == 1, "Should be doubled (X)"

    print("\n✅ Step 1 PASSED: Contract correctly determined")

    # Step 2: Create hands for play (exactly 13 cards each)
    hands = {
        'N': create_hand_from_string('♠AKQ32 ♥432 ♦432 ♣43'),    # 5+3+3+2=13
        'E': create_hand_from_string('♠765 ♥765 ♦7654 ♣765'),    # 3+3+4+3=13
        'S': create_hand_from_string('♠JT984 ♥AKQ ♦AK ♣AKQ'),    # 5+3+2+3=13
        'W': create_hand_from_string('♠ ♥JT98 ♦QJT98 ♣JT98')    # 0+4+5+4=13
    }

    print("\nHands created")

    # Step 3: Test scoring scenarios
    vulnerability = {'ns': False, 'ew': False}

    # Scenario A: Making exactly 4♠ doubled (10 tricks)
    print("\n" + "-" * 70)
    print("Scenario A: Making 4♠X (10 tricks, not vulnerable)")
    result_making = PlayEngine.calculate_score(contract, 10, vulnerability, hands)

    print(f"  Score: {result_making['score']}")
    print(f"  Made: {result_making['made']}")
    print(f"  Breakdown:")
    for key, value in result_making['breakdown'].items():
        print(f"    {key}: {value}")

    # Verify doubled scoring:
    # - Trick score: 240 (4 tricks * 30 per trick * 2 for double)
    # - Double bonus: 50
    # - Game bonus: 300 (not vulnerable)
    # Total should be 240 + 50 + 300 = 590
    assert result_making['made'] == True
    assert result_making['score'] == 590, f"Expected 590, got {result_making['score']}"
    assert result_making['breakdown']['trick_score'] == 240
    assert result_making['breakdown']['double_bonus'] == 50
    assert result_making['breakdown']['game_bonus'] == 300

    print("  ✅ Scoring correct for making doubled contract")

    # Scenario B: Going down 1 in 4♠X (9 tricks)
    print("\n" + "-" * 70)
    print("Scenario B: Down 1 in 4♠X (9 tricks, not vulnerable)")
    result_down = PlayEngine.calculate_score(contract, 9, vulnerability, hands)

    print(f"  Score: {result_down['score']}")
    print(f"  Made: {result_down['made']}")
    print(f"  Undertricks: {result_down.get('undertricks', 0)}")
    print(f"  Breakdown:")
    for key, value in result_down['breakdown'].items():
        print(f"    {key}: {value}")

    # Verify penalty scoring:
    # - Down 1 doubled not vul = -100
    assert result_down['made'] == False
    assert result_down['score'] == -100, f"Expected -100, got {result_down['score']}"
    assert result_down.get('undertricks') == 1

    print("  ✅ Penalty correct for going down doubled")

    print("\n" + "=" * 70)
    print("✅ INTEGRATION TEST PASSED")
    print("=" * 70)
    print("\nVerified:")
    print("  • Doubles (X) do not affect declarer determination")
    print("  • First player to bid strain on winning side is declarer")
    print("  • Doubled status correctly set (doubled=1)")
    print("  • Doubled scoring works correctly (2x tricks + bonuses)")
    print("  • Doubled penalties calculated correctly")


def test_redoubled_contract_integration():
    """Test redoubled contract end-to-end"""

    print("\n\nIntegration Test: Redoubled 3NT Contract")
    print("=" * 70)

    # Auction: South opens 1NT, North raises to 3NT,
    # East doubles, South redoubles, all pass
    auction = ['Pass', 'Pass', '1NT', 'Pass', '3NT', 'X', 'XX', 'Pass', 'Pass', 'Pass']
    print(f"\nAuction: {' - '.join(auction)}")

    contract = PlayEngine.determine_contract(auction, dealer_index=0)
    print(f"\nContract: {contract}")

    assert contract.level == 3, "Should be 3-level"
    assert contract.strain == 'NT', "Should be NT"
    assert contract.declarer == 'S', "South opened NT, so South is declarer"
    assert contract.doubled == 2, "Should be redoubled (XX)"

    print("\n✅ Redoubled contract correctly determined")
    print(f"  • Declarer: {contract.declarer} (correct - opened NT)")
    print(f"  • Doubled: {contract.doubled} (correct - redoubled)")

    # Test redoubled scoring
    hands = {
        'N': create_hand_from_string('♠432 ♥432 ♦432 ♣4322'),     # 3+3+3+4=13
        'E': create_hand_from_string('♠765 ♥765 ♦765 ♣7654'),     # 3+3+3+4=13
        'S': create_hand_from_string('♠AKQJ ♥AKQJ ♦AKQJ ♣A'),     # 4+4+4+1=13
        'W': create_hand_from_string('♠T98 ♥T98 ♦T98 ♣JT98')     # 3+3+3+4=13
    }

    vulnerability = {'ns': False, 'ew': False}
    result = PlayEngine.calculate_score(contract, 9, vulnerability, hands)

    print(f"\nMaking 3NTXX (9 tricks, not vulnerable):")
    print(f"  Score: {result['score']}")
    print(f"  Breakdown:")
    for key, value in result['breakdown'].items():
        print(f"    {key}: {value}")

    # Redoubled: 4x trick score + 100 bonus
    # 3NT = 40 + 30 + 30 = 100 base
    # Redoubled = 100 * 4 = 400 trick score
    # + 100 redouble bonus
    # + 300 game bonus (not vul)
    # + 150 honors (South has all 4 aces)
    # Total = 950
    assert result['score'] == 950, f"Expected 950, got {result['score']}"
    assert result['breakdown']['trick_score'] == 400
    assert result['breakdown']['double_bonus'] == 100
    assert result['breakdown']['honors_bonus'] == 150

    print("  ✅ Redoubled scoring correct")

    print("\n" + "=" * 70)
    print("✅ REDOUBLED INTEGRATION TEST PASSED")
    print("=" * 70)


if __name__ == '__main__':
    try:
        test_doubled_contract_integration()
        test_redoubled_contract_integration()

        print("\n\n" + "=" * 70)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("=" * 70)
        print("\nThe fix is working correctly:")
        print("  ✅ Declarer determination ignores X and XX")
        print("  ✅ Doubled/redoubled status only affects scoring")
        print("  ✅ Contract assignment works correctly")
        print("  ✅ Scoring calculations include double/redouble bonuses")

    except AssertionError as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
