#!/usr/bin/env python3
"""
Test script to verify that doubles (X) and redoubles (XX) do not affect
who is determined to be the declarer.

The fix ensures that only actual suit/NT bids determine the declarer,
not Pass, X, or XX.
"""

import sys
import os
# Add backend directory to path so we can import engine modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from engine.play_engine import PlayEngine

def test_declarer_with_double():
    """Test that a doubled contract correctly identifies declarer"""

    # Auction: North opens 1♠, East passes, South raises to 4♠,
    # West doubles, all pass
    auction = ['1♠', 'Pass', '4♠', 'X', 'Pass', 'Pass', 'Pass']

    contract = PlayEngine.determine_contract(auction, dealer_index=0)

    print("Test 1: Auction with double")
    print(f"  Auction: {auction}")
    print(f"  Contract: {contract}")
    print(f"  Declarer: {contract.declarer}")
    print(f"  Doubled: {contract.doubled}")

    # North opened spades first, so North should be declarer
    assert contract.declarer == 'N', f"Expected declarer to be N, got {contract.declarer}"
    assert contract.doubled == 1, f"Expected doubled=1, got {contract.doubled}"
    assert contract.level == 4, f"Expected level=4, got {contract.level}"
    assert contract.strain == '♠', f"Expected strain=♠, got {contract.strain}"

    print("  ✅ PASSED: Declarer correctly identified as North\n")


def test_declarer_with_redouble():
    """Test that a redoubled contract correctly identifies declarer"""

    # Auction: South opens 1♥, West doubles, North redoubles, all pass
    auction = ['Pass', 'Pass', '1♥', 'X', 'XX', 'Pass', 'Pass', 'Pass']

    contract = PlayEngine.determine_contract(auction, dealer_index=0)

    print("Test 2: Auction with redouble")
    print(f"  Auction: {auction}")
    print(f"  Contract: {contract}")
    print(f"  Declarer: {contract.declarer}")
    print(f"  Doubled: {contract.doubled}")

    # South opened hearts, so South should be declarer
    assert contract.declarer == 'S', f"Expected declarer to be S, got {contract.declarer}"
    assert contract.doubled == 2, f"Expected doubled=2, got {contract.doubled}"
    assert contract.level == 1, f"Expected level=1, got {contract.level}"
    assert contract.strain == '♥', f"Expected strain=♥, got {contract.strain}"

    print("  ✅ PASSED: Declarer correctly identified as South\n")


def test_declarer_no_double():
    """Test normal auction without doubles works as before"""

    # Auction: North opens 1NT, South bids 3NT, all pass
    auction = ['1NT', 'Pass', '3NT', 'Pass', 'Pass', 'Pass']

    contract = PlayEngine.determine_contract(auction, dealer_index=0)

    print("Test 3: Normal auction without double")
    print(f"  Auction: {auction}")
    print(f"  Contract: {contract}")
    print(f"  Declarer: {contract.declarer}")
    print(f"  Doubled: {contract.doubled}")

    # North opened NT, so North should be declarer
    assert contract.declarer == 'N', f"Expected declarer to be N, got {contract.declarer}"
    assert contract.doubled == 0, f"Expected doubled=0, got {contract.doubled}"
    assert contract.level == 3, f"Expected level=3, got {contract.level}"
    assert contract.strain == 'NT', f"Expected strain=NT, got {contract.strain}"

    print("  ✅ PASSED: Declarer correctly identified as North\n")


def test_declarer_competitive_with_double():
    """Test competitive auction with double"""

    # Auction: North opens 1♦, East overcalls 1♠, South bids 2♦,
    # West bids 2♠, North passes, East passes, South doubles, all pass
    auction = ['1♦', '1♠', '2♦', '2♠', 'Pass', 'Pass', 'X', 'Pass', 'Pass', 'Pass']

    contract = PlayEngine.determine_contract(auction, dealer_index=0)

    print("Test 4: Competitive auction with penalty double")
    print(f"  Auction: {auction}")
    print(f"  Contract: {contract}")
    print(f"  Declarer: {contract.declarer}")
    print(f"  Doubled: {contract.doubled}")

    # East bid spades first on the EW side, so East should be declarer
    assert contract.declarer == 'E', f"Expected declarer to be E, got {contract.declarer}"
    assert contract.doubled == 1, f"Expected doubled=1, got {contract.doubled}"
    assert contract.level == 2, f"Expected level=2, got {contract.level}"
    assert contract.strain == '♠', f"Expected strain=♠, got {contract.strain}"

    print("  ✅ PASSED: Declarer correctly identified as East\n")


def test_declarer_partner_supports_with_double():
    """Test where partner supports opener's suit and gets doubled"""

    # Auction: West opens 1♣, North passes, East bids 3♣,
    # South doubles, all pass
    auction = ['Pass', 'Pass', 'Pass', '1♣', 'Pass', '3♣', 'X', 'Pass', 'Pass', 'Pass']

    contract = PlayEngine.determine_contract(auction, dealer_index=0)

    print("Test 5: Partner support with double")
    print(f"  Auction: {auction}")
    print(f"  Contract: {contract}")
    print(f"  Declarer: {contract.declarer}")
    print(f"  Doubled: {contract.doubled}")

    # West opened clubs first, so West should be declarer (not East)
    assert contract.declarer == 'W', f"Expected declarer to be W, got {contract.declarer}"
    assert contract.doubled == 1, f"Expected doubled=1, got {contract.doubled}"
    assert contract.level == 3, f"Expected level=3, got {contract.level}"
    assert contract.strain == '♣', f"Expected strain=♣, got {contract.strain}"

    print("  ✅ PASSED: Declarer correctly identified as West (opener, not raiser)\n")


if __name__ == '__main__':
    print("=" * 70)
    print("TESTING DECLARER DETERMINATION WITH DOUBLES/REDOUBLES")
    print("=" * 70)
    print()

    try:
        test_declarer_with_double()
        test_declarer_with_redouble()
        test_declarer_no_double()
        test_declarer_competitive_with_double()
        test_declarer_partner_supports_with_double()

        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("The fix correctly ensures that:")
        print("  • Only suit/NT bids determine the declarer")
        print("  • Pass, X, and XX are ignored when finding declarer")
        print("  • Doubled/redoubled status only affects scoring")

    except AssertionError as e:
        print("=" * 70)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 70)
        exit(1)
