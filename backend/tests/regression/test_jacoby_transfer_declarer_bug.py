#!/usr/bin/env python3
"""
Regression test for bug where Jacoby Transfer auction assigned wrong declarer.

BUG REPORT (2025-11-28):
- User did a Jacoby transfer (1NT - 2♥ - 2♠ - 4♠) with South as responder
- Expected: North (1NT opener who completed transfer) to be declarer
- Actual: East was incorrectly assigned as declarer

ROOT CAUSE:
The auction was built with the correct dealer (based on frontend state), but
/api/start-play was overriding the frontend's dealer with session.get_current_dealer(),
which could return a different value if session state was out of sync.

This caused the auction parsing to use the wrong position offsets, resulting
in incorrect declarer determination.

FIX:
Trust the frontend's dealer parameter in /api/start-play since the frontend
knows the actual dealer that was used when the auction was built.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pytest
from engine.play_engine import PlayEngine


class TestJacobyTransferDeclarerBug:
    """Test cases for Jacoby Transfer declarer determination"""

    def test_jacoby_transfer_north_dealer_north_opens(self):
        """Jacoby Transfer with North as dealer - North should be declarer"""
        # North opens 1NT, South transfers to spades, North completes, South bids game
        auction = ['1NT', 'Pass', '2♥', 'Pass', '2♠', 'Pass', '4♠', 'Pass', 'Pass', 'Pass']

        contract = PlayEngine.determine_contract(auction, dealer_index=0)  # North = 0

        # North opened 1NT and was first to bid spades (completing transfer)
        assert contract is not None
        assert contract.declarer == 'N', f"Expected North as declarer, got {contract.declarer}"
        assert contract.level == 4
        assert contract.strain == '♠'
        print(f"✅ North dealer: {contract} - Declarer = {contract.declarer}")

    def test_jacoby_transfer_east_dealer_north_opens(self):
        """
        Jacoby Transfer with East as dealer but North opens 1NT.
        This tests the exact scenario from the bug report.

        Dealer: East (index 1)
        Auction order: East, South, West, North, East, South, ...

        So the auction with dealer=East:
        - Position 0 (East): Pass
        - Position 1 (South): Pass
        - Position 2 (West): Pass
        - Position 3 (North): 1NT
        - Position 4 (East): Pass
        - Position 5 (South): 2♥ (transfer)
        - Position 6 (West): Pass
        - Position 7 (North): 2♠ (complete transfer)
        - Position 8 (East): Pass
        - Position 9 (South): 4♠ (game bid)
        - Position 10 (West): Pass
        - Position 11 (North): Pass
        - Position 12 (East): Pass
        """
        # East is dealer, so we need 3 passes before North can open
        auction = ['Pass', 'Pass', 'Pass', '1NT', 'Pass', '2♥', 'Pass', '2♠', 'Pass', '4♠', 'Pass', 'Pass', 'Pass']

        contract = PlayEngine.determine_contract(auction, dealer_index=1)  # East = 1

        # North was first on NS side to bid spades (completing the transfer)
        assert contract is not None
        assert contract.declarer == 'N', f"Expected North as declarer, got {contract.declarer}"
        assert contract.level == 4
        assert contract.strain == '♠'
        print(f"✅ East dealer, North opens: {contract} - Declarer = {contract.declarer}")

    def test_jacoby_transfer_south_dealer_north_opens(self):
        """Jacoby Transfer with South as dealer - still North should be declarer"""
        # South passes, West passes, North opens 1NT
        auction = ['Pass', 'Pass', '1NT', 'Pass', '2♥', 'Pass', '2♠', 'Pass', '4♠', 'Pass', 'Pass', 'Pass']

        contract = PlayEngine.determine_contract(auction, dealer_index=2)  # South = 2

        assert contract is not None
        assert contract.declarer == 'N', f"Expected North as declarer, got {contract.declarer}"
        assert contract.level == 4
        assert contract.strain == '♠'
        print(f"✅ South dealer: {contract} - Declarer = {contract.declarer}")

    def test_jacoby_transfer_west_dealer_north_opens(self):
        """Jacoby Transfer with West as dealer - still North should be declarer"""
        # West passes, North opens 1NT
        auction = ['Pass', '1NT', 'Pass', '2♥', 'Pass', '2♠', 'Pass', '4♠', 'Pass', 'Pass', 'Pass']

        contract = PlayEngine.determine_contract(auction, dealer_index=3)  # West = 3

        assert contract is not None
        assert contract.declarer == 'N', f"Expected North as declarer, got {contract.declarer}"
        assert contract.level == 4
        assert contract.strain == '♠'
        print(f"✅ West dealer: {contract} - Declarer = {contract.declarer}")

    def test_mismatched_dealer_causes_bug(self):
        """
        Demonstrate the bug: if auction is built with dealer=North but
        parsed with dealer=East, the declarer is wrong.

        This shows why we must trust the frontend's dealer parameter.
        """
        # Auction built assuming North is dealer (first bidder is North)
        auction = ['1NT', 'Pass', '2♥', 'Pass', '2♠', 'Pass', '4♠', 'Pass', 'Pass', 'Pass']

        # CORRECT: Parse with North as dealer
        contract_correct = PlayEngine.determine_contract(auction, dealer_index=0)
        assert contract_correct.declarer == 'N', "With correct dealer, North should be declarer"

        # BUG: Parse with East as dealer (mismatched)
        contract_wrong = PlayEngine.determine_contract(auction, dealer_index=1)
        # With East as dealer, position 0 = East, so "1NT" appears to be from East
        # And position 4 = East again, so "2♠" appears to be from East
        # East would be incorrectly identified as declarer
        assert contract_wrong.declarer == 'E', "With mismatched dealer, East is incorrectly declarer"

        print(f"✅ Bug demonstration:")
        print(f"   Correct (dealer=N): {contract_correct} - Declarer = {contract_correct.declarer}")
        print(f"   Wrong (dealer=E):   {contract_wrong} - Declarer = {contract_wrong.declarer}")
        print(f"   This is why we must trust frontend's dealer!")

    def test_hearts_jacoby_transfer(self):
        """Jacoby Transfer to hearts - opener should be declarer"""
        # 2♦ is transfer to hearts
        auction = ['1NT', 'Pass', '2♦', 'Pass', '2♥', 'Pass', '4♥', 'Pass', 'Pass', 'Pass']

        contract = PlayEngine.determine_contract(auction, dealer_index=0)

        assert contract is not None
        assert contract.declarer == 'N', f"Expected North as declarer, got {contract.declarer}"
        assert contract.level == 4
        assert contract.strain == '♥'
        print(f"✅ Hearts transfer: {contract} - Declarer = {contract.declarer}")


if __name__ == '__main__':
    print("=" * 70)
    print("REGRESSION TEST: JACOBY TRANSFER DECLARER BUG")
    print("=" * 70)
    print()

    test = TestJacobyTransferDeclarerBug()
    test.test_jacoby_transfer_north_dealer_north_opens()
    test.test_jacoby_transfer_east_dealer_north_opens()
    test.test_jacoby_transfer_south_dealer_north_opens()
    test.test_jacoby_transfer_west_dealer_north_opens()
    test.test_mismatched_dealer_causes_bug()
    test.test_hearts_jacoby_transfer()

    print()
    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
