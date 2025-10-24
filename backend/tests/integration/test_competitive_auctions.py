"""
Integration tests for competitive bidding scenarios.

Tests multi-module interactions in competitive auctions including:
- Overcalls and advances
- Doubles and redoubles
- Preemptive interference
- Michaels Cuebid
- Long competitive sequences
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


class TestCompetitiveAuctions:
    """Test AI behavior in competitive auctions."""

    def test_advancer_doesnt_escalate_after_double(self):
        """
        Test advancer doesn't bid slam after partner's overcall is doubled.

        Scenario: 1♠ - 2♥ (overcall) - X (penalty) - ?
        Advancer has 8 HCP
        Should: Bid 2♠ or 3♥ support
        Bug: Could escalate to 5♥ or 6♥
        """
        # Create hands for this scenario
        hands = self._create_advancer_competitive_hands()
        engine = BiddingEngine()

        # Simulate auction: 1♠ - 2♥ - X - ?
        auction = ['1♠', '2♥', 'X']
        advancer_hand = hands['advancer']

        bid, _ = engine.get_next_bid(
            advancer_hand,
            auction,
            'West',  # Advancer position
            'None'
        )

        # Should not bid to slam level
        if bid != 'Pass':
            level = int(bid[0])
            assert level < 6, (
                f"Advancer with 8 HCP bid {bid} after partner doubled! "
                f"Should bid 2-3 level, not slam."
            )

    def test_no_unreasonable_slam_in_competitive_auction(self):
        """
        Test that competitive pressure doesn't cause unreasonable slams.

        When opponents preempt and auction gets high quickly,
        AI shouldn't panic and bid slam with insufficient values.
        """
        hands = self._create_competitive_preempt_hands()
        engine = BiddingEngine()

        # Simulate: 1♥ - 3♠ (preempt) - 4♥ - Pass - ?
        auction = ['1♥', '3♠', '4♥', 'Pass']
        opener_hand = hands['opener']

        # Opener should pass or bid 5♥, not 6♥
        bid, _ = engine.get_next_bid(
            opener_hand,
            auction,
            'North',
            'None'
        )

        if bid != 'Pass':
            level = int(bid[0])
            assert level < 6, (
                f"Opener bid {bid} in competitive auction! "
                f"Insufficient values for slam."
            )

    def test_michaels_cuebid_doesnt_escalate(self):
        """
        Test Michaels Cuebid responses don't escalate unreasonably.

        Scenario: 1♦ - 2♦ (Michaels) - 4♦ (preempt) - ?
        Responder to Michaels has to choose a suit
        Should: Bid 4♥ or 4♠
        Bug: Could escalate to 5♥, 6♥, or slam
        """
        hands = self._create_michaels_hands()
        engine = BiddingEngine()

        # Auction: 1♦ - 2♦ - 4♦ - ?
        auction = ['1♦', '2♦', '4♦']
        responder_hand = hands['responder']

        bid, _ = engine.get_next_bid(
            responder_hand,
            auction,
            'West',
            'None'
        )

        if bid != 'Pass':
            level = int(bid[0])
            # Should stay at 4-level or pass
            assert level <= 4, (
                f"Responder to Michaels bid {bid} after 4♦ preempt! "
                f"Should bid 4-level or pass."
            )

    def test_long_competitive_auction_stability(self):
        """
        Test that long competitive auctions remain stable.

        Ensures:
        - Auction terminates (no infinite loops)
        - No unreasonable escalation
        - AI doesn't get stuck
        """
        hands = self._create_long_competitive_hands()
        engine = BiddingEngine()

        auction = self._simulate_long_competitive_auction(engine, hands)

        # Should terminate in reasonable time
        assert len(auction) < 40, (
            f"Auction took {len(auction)} bids! "
            f"May indicate infinite loop or stuck bidding."
        )

        # Check for unreasonable final contract
        final_contract = self._get_final_contract(auction)
        if final_contract:
            level = int(final_contract[0])
            # In competitive auction with moderate values, shouldn't reach 7
            assert level < 7, (
                f"Competitive auction reached {final_contract}! "
                f"Likely unreasonable given competition."
            )

    def test_balancing_seat_doesnt_overcommit(self):
        """
        Test that balancing bids don't overcommit to slam.

        Scenario: 1♥ - Pass - Pass - ?
        Balancing with 11 HCP
        Should: Bid 1♠ or 1NT, maybe 2♥
        Bug: Could overcall and then get pushed to slam
        """
        hands = self._create_balancing_hands()
        engine = BiddingEngine()

        # Simulate: 1♥ - Pass - Pass - ?
        auction = ['1♥', 'Pass', 'Pass']
        balancer_hand = hands['balancer']

        bid, _ = engine.get_next_bid(
            balancer_hand,
            auction,
            'West',
            'None'
        )

        # Initial balance should be reasonable
        if bid != 'Pass':
            # Handle doubles (X, XX) and regular bids
            if bid in ['X', 'XX']:
                # Doubles are acceptable in balancing seat
                pass
            else:
                level = int(bid[0])
                assert level <= 2, (
                    f"Balancing with 11 HCP bid {bid}! "
                    f"Should balance at 1 or 2 level."
                )

    # Helper methods

    def _create_advancer_competitive_hands(self):
        """Create hands for advancer competitive scenario."""
        # Advancer with 8 HCP
        advancer_cards = [
            Card('Q', '♠'), Card('J', '♠'), Card('9', '♠'),
            Card('K', '♥'), Card('9', '♥'), Card('8', '♥'), Card('7', '♥'),
            Card('T', '♦'), Card('6', '♦'), Card('4', '♦'),
            Card('8', '♣'), Card('5', '♣'), Card('3', '♣')
        ]

        return {
            'advancer': Hand(advancer_cards)
        }

    def _create_competitive_preempt_hands(self):
        """Create hands for competitive preempt scenario."""
        # Opener with 14 HCP, good hearts
        opener_cards = [
            Card('A', '♠'), Card('Q', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('J', '♥'),
            Card('T', '♥'), Card('9', '♥'),
            Card('Q', '♦'), Card('8', '♦'), Card('7', '♦'),
            Card('K', '♣'), Card('6', '♣'), Card('3', '♣')
        ]

        return {
            'opener': Hand(opener_cards)
        }

    def _create_michaels_hands(self):
        """Create hands for Michaels Cuebid scenario."""
        # Responder to Michaels with 9 HCP, prefers hearts
        responder_cards = [
            Card('K', '♠'), Card('9', '♠'), Card('6', '♠'),
            Card('Q', '♥'), Card('J', '♥'), Card('8', '♥'), Card('7', '♥'),
            Card('A', '♦'), Card('5', '♦'),
            Card('9', '♣'), Card('7', '♣'), Card('4', '♣'), Card('2', '♣')
        ]

        return {
            'responder': Hand(responder_cards)
        }

    def _create_long_competitive_hands(self):
        """Create hands that lead to extended competition."""
        # Four hands with moderate values for back-and-forth bidding
        north_cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
            Card('9', '♥'), Card('8', '♥'),
            Card('A', '♦'), Card('K', '♦'), Card('5', '♦'),
            Card('Q', '♣'), Card('J', '♣'), Card('8', '♣'),
            Card('6', '♣'), Card('3', '♣')
        ]

        east_cards = [
            Card('J', '♠'), Card('T', '♠'), Card('7', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'),
            Card('J', '♥'), Card('T', '♥'),
            Card('Q', '♦'), Card('9', '♦'),
            Card('K', '♣'), Card('5', '♣'), Card('4', '♣')
        ]

        south_cards = [
            Card('9', '♠'), Card('6', '♠'), Card('5', '♠'),
            Card('J', '♥'), Card('7', '♥'), Card('6', '♥'),
            Card('A', '♦'), Card('K', '♦'), Card('T', '♦'),
            Card('8', '♦'), Card('7', '♦'),
            Card('A', '♣'), Card('2', '♣')
        ]

        west_cards = [
            Card('8', '♠'), Card('4', '♠'), Card('3', '♠'), Card('2', '♠'),
            Card('5', '♥'), Card('4', '♥'), Card('3', '♥'), Card('2', '♥'),
            Card('J', '♦'), Card('6', '♦'), Card('4', '♦'), Card('3', '♦'),
            Card('T', '♣')
        ]

        return {
            'North': Hand(north_cards),
            'East': Hand(east_cards),
            'South': Hand(south_cards),
            'West': Hand(west_cards)
        }

    def _create_balancing_hands(self):
        """Create hands for balancing scenario."""
        # Balancer with 11 HCP
        balancer_cards = [
            Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('9', '♠'),
            Card('9', '♥'), Card('8', '♥'),
            Card('A', '♦'), Card('Q', '♦'), Card('6', '♦'),
            Card('K', '♣'), Card('8', '♣'), Card('4', '♣'), Card('2', '♣')
        ]

        return {
            'balancer': Hand(balancer_cards)
        }

    def _simulate_long_competitive_auction(self, engine, hands):
        """Simulate a competitive auction that could go many rounds."""
        auction = []
        positions = ['North', 'East', 'South', 'West']
        consecutive_passes = 0
        max_bids = 40

        for _ in range(max_bids):
            pos = positions[len(auction) % 4]
            hand = hands[pos]

            bid, _ = engine.get_next_bid(
                hand, auction, pos, 'None'
            )

            auction.append(bid)

            if bid == 'Pass':
                consecutive_passes += 1
            else:
                consecutive_passes = 0

            if consecutive_passes >= 3 and len(auction) > 3:
                break

        return auction

    def _get_final_contract(self, auction):
        """Extract final contract from auction."""
        for bid in reversed(auction):
            if bid not in ['Pass', 'X', 'XX']:
                return bid
        return None


class TestBlackwoodInCompetition:
    """Test Blackwood convention with opponent interference."""

    def test_blackwood_doesnt_escalate_with_interference(self):
        """
        Test that Blackwood doesn't automatically bid 7NT with interference.

        Scenario: 4NT (Blackwood) - 5♦ (interference) - ?
        Partner shows aces at 5♥ level
        Should: Sign off at 5♥ or bid 6-level if appropriate
        Bug: Could escalate to 7NT without proper evaluation
        """
        # Create hands with slam interest
        hands = self._create_blackwood_competitive_hands()
        engine = BiddingEngine()

        # After Blackwood and interference, check response
        # This would require more complex setup
        # TODO: Implement detailed Blackwood+competition test
        pass  # Placeholder for now

    def _create_blackwood_competitive_hands(self):
        """Create hands for Blackwood with competition."""
        # Hands with slam interest (18+ HCP each)
        # TODO: Implement
        return {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
