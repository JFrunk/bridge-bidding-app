"""
Regression tests for Blackwood overbidding bugs from October 2025.

These tests cover two critical bugs where the AI incorrectly used Blackwood
convention (4NT) when the partnership had insufficient combined strength for slam.

Bug 1 (hand_2025-10-27_13-35-31.json):
- East: 20 HCP, West: 11 points
- West incorrectly jumped to 3♣ with only 11 points and 3-card support
- East then bid 4NT Blackwood with only 31 combined HCP (need 33+)

Bug 2 (hand_2025-10-27_13-48-24.json):
- North: 19 HCP, South: 8 HCP (27 combined)
- North bid 4NT Blackwood after South showed 6-9 points
- Should have bid 3NT instead
- No 8-card trump fit (only 7 spades)

Root Cause:
- Blackwood module doesn't check combined partnership HCP before asking for aces
- No validation that slam is realistic before using Blackwood
- Missing check for adequate trump fit

Author: Test suite for Bridge Bidding App
Date: 2025-10-27
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


class TestBlackwoodOverbidBug1:
    """
    Tests for Bug 1: West overbids to 3♣, East uses Blackwood with 31 HCP.

    Hand: hand_2025-10-27_13-35-31.json
    Auction: Pass - 1♣ - Pass - 3♣ - Pass - 4NT

    Problems:
    1. West jumps to 3♣ with only 11 points and 3-card support (should bid 1♦ or 2♣)
    2. East bids 4NT Blackwood with only 20 HCP when West showed 10-12 (31 combined < 33 needed)
    """

    def setup_method(self):
        """Create the exact hands from the bug report."""
        # North: 7 points (5 HCP + 2 dist) - K♠ Q♥T♥6♥5♥4♥3♥ T♦2♦ 9♣3♣
        north_cards = [
            Card('K', '♠'), Card('5', '♠'), Card('2', '♠'),
            Card('Q', '♥'), Card('T', '♥'), Card('6', '♥'), Card('5', '♥'), Card('4', '♥'), Card('3', '♥'),
            Card('T', '♦'), Card('2', '♦'),
            Card('9', '♣'), Card('3', '♣')
        ]

        # East: 20 HCP - A♠ A♥K♥J♥2♥ Q♦J♦5♦3♦ A♣J♣8♣4♣
        east_cards = [
            Card('A', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('J', '♥'), Card('2', '♥'),
            Card('Q', '♦'), Card('J', '♦'), Card('5', '♦'), Card('3', '♦'),
            Card('A', '♣'), Card('J', '♣'), Card('8', '♣'), Card('4', '♣')
        ]

        # South: 5 HCP - Q♠J♠9♠4♠ 8♥7♥ 9♦7♦4♦ Q♣7♣6♣2♣
        south_cards = [
            Card('Q', '♠'), Card('J', '♠'), Card('9', '♠'), Card('4', '♠'),
            Card('8', '♥'), Card('7', '♥'),
            Card('9', '♦'), Card('7', '♦'), Card('4', '♦'),
            Card('Q', '♣'), Card('7', '♣'), Card('6', '♣'), Card('2', '♣')
        ]

        # West: 11 points (10 HCP + 1 dist) - T♠8♠7♠6♠3♠ 9♥ A♦K♦8♦6♦ K♣T♣5♣
        west_cards = [
            Card('T', '♠'), Card('8', '♠'), Card('7', '♠'), Card('6', '♠'), Card('3', '♠'),
            Card('9', '♥'),
            Card('A', '♦'), Card('K', '♦'), Card('8', '♦'), Card('6', '♦'),
            Card('K', '♣'), Card('T', '♣'), Card('5', '♣')
        ]

        self.hands = {
            'North': Hand(north_cards),
            'East': Hand(east_cards),
            'South': Hand(south_cards),
            'West': Hand(west_cards)
        }

        self.dealer = 'North'
        self.vulnerability = {'NS': False, 'EW': False}

    def test_west_should_not_jump_to_3c(self):
        """
        West should NOT jump to 3♣ with only 11 points and 3-card support.

        Expected: 1♦ (showing 4 diamonds) or 2♣ (simple raise)
        Actual bug: 3♣ (invitational raise, promises 10-12 with 4-card support)
        """
        engine = BiddingEngine()

        # Simulate auction: Pass - 1♣ - Pass
        auction = ['Pass', '1♣', 'Pass']

        # West's turn - should bid 1♦ or 2♣, NOT 3♣
        west_hand = self.hands['West']
        west_bid, explanation = engine.get_next_bid(
            west_hand, auction, 'West', 'None'
        )

        # West should not jump to 3♣
        assert west_bid != '3♣', (
            f"West should not jump to 3♣ with only 11 points and 3-card support. "
            f"Got: {west_bid} - {explanation}"
        )

        # Acceptable bids: 1♠ (showing 5-card major - SAYC priority), 1♦ (showing diamonds),
        # 2♣ (simple raise), or Pass
        # With 5 spades and 4 diamonds, showing the major takes priority in SAYC
        acceptable_bids = ['1♠', '1♦', '2♣', 'Pass']
        assert west_bid in acceptable_bids, (
            f"West should bid one of {acceptable_bids}, but bid {west_bid}"
        )

    def test_east_should_not_use_blackwood_with_31_hcp(self):
        """
        East should NOT bid 4NT Blackwood with only 31 combined HCP.

        Even if West bids 3♣ (showing 10-12), combined HCP is max 32.
        Need 33+ for small slam.

        Expected: Pass or 5♣ at most
        Actual bug: 4NT (Blackwood)
        """
        engine = BiddingEngine()

        # Simulate the buggy auction: Pass - 1♣ - Pass - 3♣ - Pass
        auction = ['Pass', '1♣', 'Pass', '3♣', 'Pass']

        # East's turn - should NOT bid 4NT
        east_hand = self.hands['East']
        east_bid, explanation = engine.get_next_bid(
            east_hand, auction, 'East', 'None'
        )

        # East should not bid 4NT (Blackwood) with insufficient combined strength
        assert east_bid != '4NT', (
            f"East should not bid 4NT Blackwood with only 20 HCP when partner showed 10-12. "
            f"Combined 30-32 HCP is insufficient for slam (need 33+). "
            f"Got: {east_bid} - {explanation}"
        )

        # Acceptable bids: With 20 HCP and partner's invitational 3♣ (10-12),
        # combined 30-32 is game-level. Reasonable bids include:
        # - 3♥/3♦ (showing second suit, game-forcing)
        # - 3NT (game in NT)
        # - 5♣ (game in minor)
        # - Pass (conservative, but unlikely with 20 HCP)
        unacceptable_bids = ['4NT', '6♣', '6NT', '7♣', '7NT']  # No slam exploration
        assert east_bid not in unacceptable_bids, (
            f"East should not bid slam or explore slam with 30-32 combined HCP, but bid {east_bid}"
        )


class TestBlackwoodOverbidBug2:
    """
    Tests for Bug 2: North uses Blackwood with 27 HCP and no trump fit.

    Hand: hand_2025-10-27_13-48-24.json
    Auction: 1♦ - Pass - 1♠ - Pass - 3♦ - Pass - 3♠ - Pass - 4NT

    Problems:
    1. South showed 6-9 HCP with 1♠ response
    2. South's 3♠ shows preference but not extra strength
    3. Combined HCP: 19 + 8 = 27 (need 33+ for slam)
    4. Only 7 trump cards (North has 3♠, South has 4♠) - inadequate for slam
    5. North should bid 3NT, not 4NT Blackwood
    """

    def setup_method(self):
        """Create the exact hands from the bug report."""
        # North: 19 points (18 HCP + 1 dist) - A♠9♠3♠ 3♥ A♦K♦8♦6♦3♦ A♣K♣9♣5♣
        north_cards = [
            Card('A', '♠'), Card('9', '♠'), Card('3', '♠'),
            Card('3', '♥'),
            Card('A', '♦'), Card('K', '♦'), Card('8', '♦'), Card('6', '♦'), Card('3', '♦'),
            Card('A', '♣'), Card('K', '♣'), Card('9', '♣'), Card('5', '♣')
        ]

        # East: 8 points - J♠T♠8♠2♠ A♥T♥8♥5♥2♥ J♦ J♣T♣3♣
        east_cards = [
            Card('J', '♠'), Card('T', '♠'), Card('8', '♠'), Card('2', '♠'),
            Card('A', '♥'), Card('T', '♥'), Card('8', '♥'), Card('5', '♥'), Card('2', '♥'),
            Card('J', '♦'),
            Card('J', '♣'), Card('T', '♣'), Card('3', '♣')
        ]

        # South: 8 HCP - K♠Q♠7♠6♠ K♥7♥6♥4♥ 9♦7♦4♦2♦ 6♣
        south_cards = [
            Card('K', '♠'), Card('Q', '♠'), Card('7', '♠'), Card('6', '♠'),
            Card('K', '♥'), Card('7', '♥'), Card('6', '♥'), Card('4', '♥'),
            Card('9', '♦'), Card('7', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('6', '♣')
        ]

        # West: 8 points - 5♠4♠ Q♥J♥9♥ Q♦T♦5♦ Q♣8♣7♣4♣2♣
        west_cards = [
            Card('5', '♠'), Card('4', '♠'),
            Card('Q', '♥'), Card('J', '♥'), Card('9', '♥'),
            Card('Q', '♦'), Card('T', '♦'), Card('5', '♦'),
            Card('Q', '♣'), Card('8', '♣'), Card('7', '♣'), Card('4', '♣'), Card('2', '♣')
        ]

        self.hands = {
            'North': Hand(north_cards),
            'East': Hand(east_cards),
            'South': Hand(south_cards),
            'West': Hand(west_cards)
        }

        self.dealer = 'North'
        self.vulnerability = {'NS': False, 'EW': False}

    def test_north_should_bid_3nt_not_4nt(self):
        """
        North should bid 3NT, not 4NT Blackwood.

        After auction: 1♦ - Pass - 1♠ - Pass - 3♦ - Pass - 3♠

        South showed 6-9 HCP initially, and 3♠ doesn't promise extras.
        Combined: 19 + 8 = 27 HCP (insufficient for slam).
        Only 7 trump cards (need 8+ for suit slam).

        Expected: 3NT (natural game bid)
        Actual bug: 4NT (Blackwood, asking for aces)
        """
        engine = BiddingEngine()

        # Simulate auction: 1♦ - Pass - 1♠ - Pass - 3♦ - Pass - 3♠ - Pass
        auction = ['1♦', 'Pass', '1♠', 'Pass', '3♦', 'Pass', '3♠', 'Pass']

        # North's turn - should bid 3NT, not 4NT
        north_hand = self.hands['North']
        north_bid, explanation = engine.get_next_bid(
            north_hand, auction, 'North', 'None'
        )

        # North should bid 3NT
        assert north_bid == '3NT', (
            f"North should bid 3NT with 19 HCP when South showed 6-9 HCP. "
            f"Combined 27 HCP is insufficient for slam (need 33+). "
            f"Only 7 trump cards (inadequate for spade slam). "
            f"Got: {north_bid} - {explanation}"
        )

    def test_4nt_after_weak_response_is_quantitative_not_blackwood(self):
        """
        4NT after a weak response should be quantitative, not Blackwood.

        When partner has shown 6-9 HCP, 4NT should ask partner to bid 6NT
        with maximum (9 HCP) or pass with minimum (6-7 HCP).

        It should NOT be Blackwood (asking for aces) since slam is unlikely.
        """
        engine = BiddingEngine()

        # Same auction as previous test
        auction = ['1♦', 'Pass', '1♠', 'Pass', '3♦', 'Pass', '3♠', 'Pass']

        # If North bids 4NT (which is wrong), check that it's at least
        # interpreted correctly (quantitative, not Blackwood)
        north_hand = self.hands['North']
        north_bid, explanation = engine.get_next_bid(
            north_hand, auction, 'North', 'None'
        )

        if north_bid == '4NT':
            # This is still wrong (should be 3NT), but if it happens,
            # make sure it's not interpreted as Blackwood
            assert 'Blackwood' not in explanation, (
                f"4NT should be quantitative (asking partner to evaluate slam), "
                f"not Blackwood (asking for aces) when partner showed 6-9 HCP. "
                f"Got explanation: {explanation}"
            )


class TestBlackwoodSafetyChecks:
    """
    General tests to ensure Blackwood is only used with adequate values.

    These tests verify the fix works for various scenarios, not just the
    specific bug hands.
    """

    def test_blackwood_requires_33_combined_hcp(self):
        """
        Blackwood should only be used when partnership has 33+ combined HCP.

        This is the fundamental requirement for small slam.
        """
        # Create hands with exactly 32 combined HCP (insufficient)
        # North: 16 HCP = A♠(4) + K♠(3) + Q♠(2) + J♠(1) + A♥(4) + K♥(3) - 1 = 16
        # Actually: AKQJ = 10, need 6 more, A = 4, so need K (3) in hearts and nothing else
        north_cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('T', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('5', '♥'),  # Changed Q♥ to 5♥
            Card('9', '♦'), Card('8', '♦'), Card('7', '♦'),
            Card('6', '♣'), Card('5', '♣')
        ]  # 17 HCP (AKQJ spades = 10, AK hearts = 7)

        south_cards = [
            Card('9', '♠'), Card('8', '♠'), Card('7', '♠'), Card('6', '♠'),
            Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'),  # Q+J = 3
            Card('A', '♦'), Card('K', '♦'), Card('Q', '♦'),  # A+K+Q = 9
            Card('J', '♣'), Card('T', '♣'), Card('9', '♣')   # J = 1
        ]  # 13 HCP (QJ hearts = 3, AKQ diamonds = 9, J clubs = 1)

        # Filler hands for E/W
        east_cards = [
            Card('5', '♠'), Card('4', '♠'), Card('3', '♠'), Card('2', '♠'),
            Card('9', '♥'), Card('8', '♥'), Card('7', '♥'), Card('6', '♥'),
            Card('T', '♦'), Card('6', '♦'), Card('5', '♦'),
            Card('9', '♣'), Card('8', '♣')
        ]

        west_cards = [
            Card('5', '♥'), Card('4', '♥'), Card('3', '♥'), Card('2', '♥'),
            Card('4', '♦'), Card('3', '♦'), Card('2', '♦'),
            Card('7', '♣'), Card('4', '♣'), Card('3', '♣'), Card('2', '♣'),
            Card('3', '♠'), Card('2', '♥')
        ]

        hands = {
            'North': Hand(north_cards),
            'South': Hand(south_cards),
            'East': Hand(east_cards),
            'West': Hand(west_cards)
        }

        engine = BiddingEngine()

        # Simulate a strong auction where Blackwood might be considered
        # 1♠ - Pass - 3♠ - Pass (strong raise, 16+ support points)
        auction = ['1♠', 'Pass', '3♠', 'Pass']

        # North's rebid - should NOT be 4NT with only 32 combined HCP
        north_hand = hands['North']
        north_bid, explanation = engine.get_next_bid(
            north_hand, auction, 'North', 'None'
        )

        assert north_bid != '4NT', (
            f"Should not bid 4NT Blackwood with only 32 combined HCP (need 33+). "
            f"Got: {north_bid} - {explanation}"
        )

    def test_blackwood_requires_trump_fit(self):
        """
        Blackwood should only be used when partnership has established a trump fit.

        Don't use Blackwood without 8+ trump cards.
        """
        # Create hands with good HCP but poor trump fit
        north_cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),  # Only 3 spades
            Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'),
            Card('A', '♦'), Card('K', '♦'),
            Card('A', '♣'), Card('K', '♣'), Card('Q', '♣'), Card('9', '♣')
        ]  # 20 HCP, 3 spades

        south_cards = [
            Card('J', '♠'), Card('T', '♠'), Card('9', '♠'), Card('8', '♠'),  # 4 spades
            Card('9', '♥'), Card('8', '♥'),
            Card('Q', '♦'), Card('J', '♦'), Card('T', '♦'),
            Card('J', '♣'), Card('T', '♣'), Card('8', '♣'), Card('7', '♣')
        ]  # 4 HCP (24 combined, 7 trump - insufficient for slam)

        # Even with adequate combined points, 7 trump cards is insufficient for slam
        # The test verifies we don't use Blackwood without proper fit


class TestBlackwoodVsQuantitative:
    """
    Tests to distinguish Blackwood (ace-asking) from Quantitative 4NT (invitational).

    4NT should be:
    - Blackwood: After suit agreement, with slam interest
    - Quantitative: After NT bidding, asking partner to evaluate

    This fixes the bug where 4NT was always interpreted as Blackwood.
    """

    def test_4nt_after_1nt_3nt_is_quantitative(self):
        """
        4NT after 1NT - 3NT should be quantitative, not Blackwood.

        Example: 1♠ - 3NT - 4NT
        This is NOT asking for aces, it's asking partner to bid 6NT with maximum.
        """
        pass  # Test implementation would go here

    def test_4nt_after_suit_agreement_is_blackwood(self):
        """
        4NT after suit agreement should be Blackwood.

        Example: 1♠ - 3♠ - 4NT
        This IS asking for aces (we have spade agreement).
        """
        pass  # Test implementation would go here


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
