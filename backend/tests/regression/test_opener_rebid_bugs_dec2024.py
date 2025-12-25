"""
Regression tests for opener rebid bugs fixed in December 2024.

Bug: Opener with 18-19 HCP was incorrectly passing after various partner responses.

Root Causes Fixed:
1. SuitLengthValidator blocked reverse bids (requires 5+ cards, but reverse only needs 4)
2. Grand Slam Force incorrectly claimed trump agreement after NT bids
3. SanityChecker didn't recognize 3NT response = 13+ HCP

Test Scenarios:
- 1♣ - 1♦: Should rebid 2♠ (reverse)
- 1♣ - 2♦: Should rebid 2♠ (reverse)
- 1♣ - 2♣: Should rebid 2♠ (reverse)
- 1♣ - 3NT: Should rebid 4♣ (Gerber, asking for aces)
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


def create_north_18_hcp_hand():
    """
    Create North's hand: ♠AKQ4 ♥KJ4 ♦62 ♣AJ97
    18 HCP, 18 total points
    4 clubs (opened 1♣), 4 spades (can reverse to 2♠)

    HCP calculation:
    - ♠: A(4) + K(3) + Q(2) = 9 HCP
    - ♥: K(3) + J(1) = 4 HCP
    - ♦: 0 HCP
    - ♣: A(4) + J(1) = 5 HCP
    - Total: 18 HCP
    """
    north_cards = [
        Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('4', '♠'),
        Card('K', '♥'), Card('J', '♥'), Card('4', '♥'),
        Card('6', '♦'), Card('2', '♦'),
        Card('A', '♣'), Card('J', '♣'), Card('9', '♣'), Card('7', '♣')
    ]
    return Hand(north_cards)


class TestOpenerReverseBidAfter1Diamond:
    """Test that opener rebids 2♠ (reverse) after partner's 1♦ response."""

    def test_north_rebids_2_spades_after_1_diamond(self):
        """
        Auction: 1♣ - Pass - 1♦ - Pass - ?
        North should bid 2♠ (reverse showing 17+ HCP and 4+ spades)

        Previously: North passed because SuitLengthValidator required 5+ cards
        for 2-level bids, but reverse bids only need 4 cards.
        """
        north_hand = create_north_18_hcp_hand()

        auction_history = [
            '1♣',   # North opens 1♣
            'Pass', # East passes
            '1♦',   # South responds 1♦
            'Pass'  # West passes
        ]

        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(
            hand=north_hand,
            auction_history=auction_history,
            my_position='North',
            vulnerability='None'
        )

        assert bid == '2♠', f"Expected 2♠ reverse bid, got {bid}. Explanation: {explanation}"
        assert 'reverse' in explanation.lower() or '17+' in explanation or '19+' in explanation


class TestOpenerReverseBidAfter2Diamond:
    """Test that opener rebids 2♠ (reverse) after partner's 2♦ response."""

    def test_north_rebids_2_spades_after_2_diamond(self):
        """
        Auction: 1♣ - Pass - 2♦ - Pass - ?
        North should bid 2♠ (reverse showing 17+ HCP and 4+ spades)

        Previously: North passed because SuitLengthValidator blocked the bid.
        """
        north_hand = create_north_18_hcp_hand()

        auction_history = [
            '1♣',   # North opens 1♣
            'Pass', # East passes
            '2♦',   # South responds 2♦ (10+ HCP, 5+ diamonds)
            'Pass'  # West passes
        ]

        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(
            hand=north_hand,
            auction_history=auction_history,
            my_position='North',
            vulnerability='None'
        )

        assert bid == '2♠', f"Expected 2♠ reverse bid, got {bid}. Explanation: {explanation}"


class TestOpenerReverseBidAfter2Club:
    """Test that opener rebids 2♠ (reverse) after partner's 2♣ raise."""

    def test_north_rebids_2_spades_after_2_club_raise(self):
        """
        Auction: 1♣ - Pass - 2♣ - Pass - ?
        North should bid 2♠ (reverse showing 17+ HCP and 4+ spades)

        Previously: North passed due to multiple issues:
        - SuitLengthValidator blocked the bid
        - GSF incorrectly claimed trump agreement after simple raise
        """
        north_hand = create_north_18_hcp_hand()

        auction_history = [
            '1♣',   # North opens 1♣
            'Pass', # East passes
            '2♣',   # South raises to 2♣ (6-10 points, 4+ clubs)
            'Pass'  # West passes
        ]

        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(
            hand=north_hand,
            auction_history=auction_history,
            my_position='North',
            vulnerability='None'
        )

        assert bid == '2♠', f"Expected 2♠ reverse bid, got {bid}. Explanation: {explanation}"


class TestOpenerGerberAfter3NT:
    """Test that opener bids 4♣ (Gerber) after partner's 3NT response."""

    def test_north_bids_gerber_after_3nt(self):
        """
        Auction: 1♣ - Pass - 3NT - Pass - ?
        North should bid 4♣ (Gerber, asking for aces) to explore slam.

        Combined points: 18 + 13-15 (3NT shows 13-15 balanced) = 31-33 HCP
        This is enough to explore slam with Gerber.

        Previously: North passed because SanityChecker didn't recognize
        that 3NT response = 13+ HCP.
        """
        north_hand = create_north_18_hcp_hand()

        auction_history = [
            '1♣',   # North opens 1♣
            'Pass', # East passes
            '3NT',  # South responds 3NT (13-15 balanced)
            'Pass'  # West passes
        ]

        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(
            hand=north_hand,
            auction_history=auction_history,
            my_position='North',
            vulnerability='None'
        )

        # Should bid Gerber (4♣) to explore slam
        assert bid == '4♣', f"Expected 4♣ Gerber bid, got {bid}. Explanation: {explanation}"
        assert 'gerber' in explanation.lower() or 'ace' in explanation.lower()


class TestGSFDoesNotTriggerAfter3NT:
    """Test that Grand Slam Force does NOT trigger after 3NT response."""

    def test_gsf_requires_suit_agreement(self):
        """
        GSF (5NT) should only be bid when there's a clear trump suit agreement.
        After 1♣ - 3NT, there is NO suit agreement (3NT denies club support).

        Previously: GSF incorrectly returned the sole suit (♣) as "agreed"
        when only one suit was mentioned.
        """
        from engine.ai.conventions.grand_slam_force import GrandSlamForceConvention

        gsf = GrandSlamForceConvention()

        features = {
            'auction_history': ['1♣', 'Pass', '3NT', 'Pass'],
            'auction_features': {
                'opening_bid': '1♣',
                'opener_relationship': 'Me',
                'partner_bids': ['3NT'],
            },
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 0
        }

        # GSF should return None (no agreed trump suit after 3NT)
        trump_suit = gsf._get_agreed_trump_suit(features)
        assert trump_suit is None, f"Expected no trump agreement after 3NT, got {trump_suit}"


class TestGSFDoesNotTriggerAfterSimpleRaise:
    """Test that GSF does not trigger after simple raise (insufficient values)."""

    def test_gsf_requires_slam_values(self):
        """
        After 1♣ - 2♣, partner has shown only 6-10 points.
        Combined points are 18 + 8 = 26, not enough for slam.
        GSF should not trigger.
        """
        from engine.ai.conventions.grand_slam_force import GrandSlamForceConvention

        north_hand = create_north_18_hcp_hand()
        gsf = GrandSlamForceConvention()

        features = {
            'auction_history': ['1♣', 'Pass', '2♣', 'Pass'],
            'auction_features': {
                'opening_bid': '1♣',
                'opener_relationship': 'Me',
                'partner_bids': ['2♣'],
            },
            'positions': ['North', 'East', 'South', 'West'],
            'my_index': 0
        }

        # GSF should not activate (partner doesn't have slam values)
        should_bid = gsf._should_bid_gsf(north_hand, features)
        assert should_bid is False, "GSF should not trigger after simple raise"


class TestSanityCheckerRecognizes3NTResponse:
    """Test that SanityChecker recognizes 3NT response = 13+ HCP."""

    def test_sanity_checker_estimates_3nt_correctly(self):
        """
        When partner responds 3NT to our opening, SanityChecker should
        estimate partner has 13+ HCP.
        """
        from engine.ai.sanity_checker import SanityChecker

        checker = SanityChecker()

        features = {
            'auction_features': {
                'opening_bid': '1♣',
                'opener_relationship': 'Me',
                'partner_bids': ['3NT'],
            }
        }

        auction = ['1♣', 'Pass', '3NT', 'Pass']

        estimated_hcp = checker._estimate_partner_hcp(features, auction)
        assert estimated_hcp >= 13, f"Expected 13+ HCP for 3NT response, got {estimated_hcp}"


class TestSanityCheckerRecognizes2NTJacoby:
    """Test that SanityChecker recognizes Jacoby 2NT = 13+ HCP."""

    def test_sanity_checker_estimates_jacoby_2nt_correctly(self):
        """
        When partner responds 2NT to our major opening (Jacoby 2NT),
        SanityChecker should estimate partner has 13+ HCP.
        """
        from engine.ai.sanity_checker import SanityChecker

        checker = SanityChecker()

        features = {
            'auction_features': {
                'opening_bid': '1♥',
                'opener_relationship': 'Me',
                'partner_bids': ['2NT'],
            }
        }

        auction = ['1♥', 'Pass', '2NT', 'Pass']

        estimated_hcp = checker._estimate_partner_hcp(features, auction)
        assert estimated_hcp >= 13, f"Expected 13+ HCP for Jacoby 2NT, got {estimated_hcp}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
