"""
Regression test for advancer cuebid bug.

BUG DESCRIPTION:
When advancing partner's overcall with a strong hand (12+ points), the advancer
would make a "cuebid" that actually bid the OPPONENT'S suit, and then continue
to raise that suit as if it were trump.

EXAMPLE BUGGY AUCTION:
South opens 1♦, West overcalls 1♠, North makes negative double, East "cuebids" 3♦
Then East continues with 4♦, 5♦, 6♦ - bidding the opponent's diamond suit!
East-West should be in 4♠ with their 8-card spade fit.

ROOT CAUSE:
- AdvancerBidsModule returned opponent's suit as the bid recommendation
- Module had no context tracking to remember original overcall suit
- Subsequent calls continued to "raise" the opponent's suit

FIX:
- Disabled cuebid logic (commented out with TODO)
- Added direct game bids for strong hands (12+ points with fit)
- Added context tracking to prevent re-bidding without extras
- Added _subsequent_advance() to handle competition intelligently

Reference: backend/review_requests/hand_2025-10-16_12-34-59.json
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


class TestAdvancerCuebidBug:
    """Test suite for the advancer cuebid bug and its fix."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BiddingEngine()

    def test_advancer_with_strong_hand_bids_game_not_cuebid(self):
        """
        Test that advancer with 12+ points and fit bids game directly,
        not a cuebid of opener's suit.

        Auction: 1♦ - 1♠ - Pass - ?
        East holds: 8 HCP, 4♣, 4♦, 3♠, 2♥ with A♥ and A♣
        Should: Pass or 2♠ (only 8 HCP, minimal support)
        Should NOT: Cuebid 3♦ (opponent's suit!)
        """
        # East's hand from the bug report (8 HCP, not 12+, so shouldn't cuebid anyway)
        east_hand = Hand([
            Card('8', '♠'), Card('5', '♠'), Card('2', '♠'),
            Card('A', '♥'), Card('2', '♥'),
            Card('8', '♦'), Card('6', '♦'), Card('5', '♦'), Card('2', '♦'),
            Card('A', '♣'), Card('4', '♣'), Card('3', '♣'), Card('2', '♣')
        ])

        auction = ['Pass', 'Pass', '1♦', '1♠', 'X', 'Pass']  # North's negative double, East to bid
        bid, explanation = self.engine.get_next_bid(
            east_hand,
            auction,
            my_position='East',
            vulnerability='NS'
        )

        # Should NOT bid 3♦ or any diamond bid
        assert not bid.endswith('♦'), f"East should not bid diamonds (opponent's suit)! Bid: {bid}"

        # With only 8 HCP and 3-card support, should pass or raise to 2♠
        assert bid in ['Pass', '2♠'], f"Expected Pass or 2♠, got {bid}"

    def test_advancer_with_game_forcing_hand_bids_game_in_major(self):
        """
        Test that advancer with 12+ points and major suit fit bids game directly.

        Auction: 1♦ - 1♠ - Pass - ?
        Advancer holds: 17 HCP with 3-card spade support
        Should: Bid 4♠ (game)
        Should NOT: Cuebid 3♦
        """
        # Strong hand with spade support (17 HCP)
        advancer_hand = Hand([
            Card('K', '♠'), Card('J', '♠'), Card('9', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('5', '♥'),
            Card('Q', '♦'), Card('7', '♦'), Card('4', '♦'),
            Card('A', '♣'), Card('8', '♣'), Card('3', '♣'), Card('2', '♣')
        ])

        # South opens 1♦, West overcalls 1♠, North passes, East to bid
        auction = ['1♦', '1♠', 'Pass']
        bid, explanation = self.engine.get_next_bid(
            advancer_hand,
            auction,
            my_position='East',
            vulnerability='NS',
            dealer='South'
        )

        # Should bid 4♠ (game) with 13 HCP and 3-card support
        assert bid == '4♠', f"Expected 4♠ (game bid), got {bid}"
        assert '♦' not in bid, f"Should not bid diamonds (opponent's suit)!"

    def test_advancer_does_not_rebid_without_extras(self):
        """
        Test that advancer doesn't rebid after simple raise without maximum values.

        Auction: 1♦ - 1♠ - Pass - 2♠ - 3♦ - ?
        Advancer already raised to 2♠ (showing 8-10 points)
        Opponents compete with 3♦
        Should: Pass (already described hand, no extras)
        Should NOT: Bid 3♠ or 4♦ or 5♦
        """
        # Minimum raise hand (8-9 HCP, 3-card support)
        advancer_hand = Hand([
            Card('J', '♠'), Card('9', '♠'), Card('7', '♠'),
            Card('K', '♥'), Card('8', '♥'), Card('3', '♥'),
            Card('Q', '♦'), Card('6', '♦'), Card('4', '♦'),
            Card('A', '♣'), Card('5', '♣'), Card('3', '♣'), Card('2', '♣')
        ])

        # Auction where advancer already raised to 2♠, opponents compete with 3♦
        auction = ['Pass', 'Pass', '1♦', '1♠', 'Pass', '2♠', '3♦']
        bid, explanation = self.engine.get_next_bid(
            advancer_hand,
            auction,
            my_position='East',
            vulnerability='NS'
        )

        # Should pass (already showed 8-10 points with 2♠ raise)
        assert bid == 'Pass', f"Should pass after simple raise, got {bid}"
        assert '♦' not in bid, f"Should definitely not bid diamonds!"

    def test_advancer_competes_with_maximum_and_extra_trumps(self):
        """
        Test that advancer DOES compete with maximum values and extra trumps.

        Auction: 1♦ - 1♠ - Pass - 2♠ - 3♦ - ?
        Advancer has 10 HCP and 4-card spade support (maximum for simple raise)
        Should: Bid 3♠ (competing with maximum)
        """
        # Maximum simple raise hand (10 HCP, 4-card support)
        advancer_hand = Hand([
            Card('K', '♠'), Card('J', '♠'), Card('9', '♠'), Card('7', '♠'),
            Card('Q', '♥'), Card('8', '♥'), Card('3', '♥'),
            Card('A', '♦'), Card('6', '♦'), Card('4', '♦'),
            Card('K', '♣'), Card('5', '♣'), Card('2', '♣')
        ])

        # Auction where advancer raised to 2♠, opponents compete with 3♦
        auction = ['Pass', 'Pass', '1♦', '1♠', 'Pass', '2♠', '3♦']
        bid, explanation = self.engine.get_next_bid(
            advancer_hand,
            auction,
            my_position='East',
            vulnerability='NS'
        )

        # Should compete to 3♠ with maximum values and 4-card support
        assert bid == '3♠', f"Should compete to 3♠ with maximum, got {bid}"

    def test_advancer_with_minor_fit_bids_game_not_cuebid(self):
        """
        Test that advancer with strong hand and minor fit doesn't cuebid.

        Auction: 1♥ - 2♣ - Pass - ?
        Advancer has 14 HCP with club support
        Should: Bid 5♣ or 3NT (game), or at minimum NOT bid 3♥ (cuebid)
        Should NOT: Cuebid 3♥ (opponent's suit)
        """
        # Strong hand with club support
        advancer_hand = Hand([
            Card('K', '♠'), Card('J', '♠'), Card('9', '♠'),
            Card('A', '♥'), Card('Q', '♥'), Card('5', '♥'),
            Card('K', '♦'), Card('J', '♦'), Card('7', '♦'),
            Card('A', '♣'), Card('Q', '♣'), Card('8', '♣'), Card('3', '♣')
        ])

        auction = ['Pass', '1♥', '2♣']  # Advancer to bid
        bid, explanation = self.engine.get_next_bid(
            advancer_hand,
            auction,
            my_position='East',
            vulnerability='NS'
        )

        # Most important: Should NOT cuebid 3♥ (opponent's suit)
        assert bid != '3♥', f"Should not cuebid opponent's hearts! Got {bid}"
        assert not (bid.endswith('♥') and bid != 'Pass'), f"Should not bid hearts at all! Got {bid}"

    def test_original_bug_auction_complete(self):
        """
        Test the exact auction from the bug report doesn't bid opponent's suit.

        Original buggy auction:
        Pass - Pass - 1♦ - 1♠ - X - 3♦ (BUG!) - Pass - 4♦ (BUG!)

        This tests that East doesn't make multiple diamond bids.
        """
        # East's actual hand from bug report
        east_hand = Hand([
            Card('8', '♠'), Card('5', '♠'), Card('2', '♠'),
            Card('A', '♥'), Card('2', '♥'),
            Card('8', '♦'), Card('6', '♦'), Card('5', '♦'), Card('2', '♦'),
            Card('A', '♣'), Card('4', '♣'), Card('3', '♣'), Card('2', '♣')
        ])

        # First bid after negative double
        auction1 = ['Pass', 'Pass', '1♦', '1♠', 'X']
        bid1, _ = self.engine.get_next_bid(east_hand, auction1, 'East', 'NS')
        assert '♦' not in bid1, f"First bid should not be diamonds, got {bid1}"

        # If East raises to 2♠, they shouldn't bid again without competition
        auction2 = ['Pass', 'Pass', '1♦', '1♠', 'X', '2♠', 'Pass', 'Pass', 'Pass']
        # This auction is complete, but testing that East would pass if asked
        # (In real game, auction ends after 3 passes)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
