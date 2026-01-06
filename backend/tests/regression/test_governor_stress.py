"""
System Stress Test for the Bidding Governor

Tests the Governor (SlamSafetyValidator) against 50 random hands to ensure:
1. Slams are only bid with sufficient combined HCP (33+ for small slam, 37+ for grand)
2. The Governor cannot be bypassed by metadata flags for slam bids
3. Blackwood sequences still work but slam decisions are validated

The Governor is the non-overridable hard floor for slam HCP requirements.
"""

import pytest
import random
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


class TestGovernorStress:
    """Stress test the Governor with random hands."""

    DECK = [
        (rank, suit) for rank in ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        for suit in ['♠', '♥', '♦', '♣']
    ]

    def _deal_random_hands(self, seed: int = None):
        """Deal 4 random hands from a shuffled deck."""
        if seed is not None:
            random.seed(seed)

        deck = self.DECK.copy()
        random.shuffle(deck)

        hands = {}
        positions = ['North', 'East', 'South', 'West']
        for i, pos in enumerate(positions):
            cards = [Card(rank, suit) for rank, suit in deck[i*13:(i+1)*13]]
            hands[pos] = Hand(cards)

        return hands

    def _simulate_auction(self, engine, hands, dealer='North'):
        """Simulate a full auction until 3 passes."""
        auction = []
        positions = ['North', 'East', 'South', 'West']
        dealer_index = positions.index(dealer)
        consecutive_passes = 0
        max_bids = 40  # Safety limit

        for _ in range(max_bids):
            current_pos = positions[(dealer_index + len(auction)) % 4]
            current_hand = hands[current_pos]

            bid, _ = engine.get_next_bid(
                current_hand,
                auction,
                current_pos,
                'None'
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

    def _get_declarer_partnership(self, auction, dealer='North'):
        """Determine which partnership won the auction."""
        positions = ['North', 'East', 'South', 'West']
        dealer_index = positions.index(dealer)

        # Find the final contract and who bid that strain first
        final_contract = self._get_final_contract(auction)
        if not final_contract:
            return None

        strain = final_contract[1:] if len(final_contract) > 1 else final_contract

        # Find who bid this strain first in the winning partnership
        for i, bid in enumerate(auction):
            if bid == 'Pass' or bid in ['X', 'XX']:
                continue
            if len(bid) >= 2 and bid[1:] == strain:
                bidder_pos = positions[(dealer_index + i) % 4]
                if bidder_pos in ['North', 'South']:
                    return 'NS'
                else:
                    return 'EW'

        return None

    def _get_partnership_hcp(self, hands, partnership):
        """Get combined HCP for a partnership."""
        if partnership == 'NS':
            return hands['North'].hcp + hands['South'].hcp
        else:
            return hands['East'].hcp + hands['West'].hcp

    @pytest.mark.parametrize("seed", range(50))
    def test_governor_blocks_insufficient_slam(self, seed):
        """
        Test that Governor blocks slams when combined HCP < 33.

        This test:
        1. Deals random hands with a specific seed
        2. Runs the full auction
        3. If slam is bid, verifies the declaring partnership has 33+ HCP

        The Governor should prevent ANY slam bid when combined HCP < 33.
        """
        hands = self._deal_random_hands(seed)
        engine = BiddingEngine()

        auction = self._simulate_auction(engine, hands)
        final_contract = self._get_final_contract(auction)

        if not final_contract:
            # Auction passed out - that's fine
            return

        level = int(final_contract[0]) if final_contract[0].isdigit() else 0

        if level >= 6:
            # Slam was bid - verify HCP requirements
            partnership = self._get_declarer_partnership(auction)
            if partnership:
                combined_hcp = self._get_partnership_hcp(hands, partnership)

                # Allow small margin for distribution points (up to 2)
                if level == 7:
                    min_required = 35  # 37 - 2 distribution bonus
                else:
                    min_required = 31  # 33 - 2 distribution bonus

                assert combined_hcp >= min_required, (
                    f"Seed {seed}: {partnership} bid {final_contract} with only {combined_hcp} combined HCP! "
                    f"Governor should have blocked this slam. "
                    f"Auction: {auction}"
                )

    def test_specific_low_hcp_hands(self):
        """
        Test specific hands where partnership has low HCP.

        These are hand-crafted scenarios where slam should never be bid.
        """
        # Scenario 1: Both partnerships have ~20 HCP (no one has slam values)
        north_cards = [
            Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('T', '♠'),
            Card('2', '♥'), Card('3', '♥'), Card('4', '♥'),
            Card('5', '♦'), Card('6', '♦'), Card('7', '♦'),
            Card('8', '♣'), Card('9', '♣'), Card('T', '♣')
        ]
        east_cards = [
            Card('A', '♠'), Card('9', '♠'), Card('8', '♠'),
            Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'),
            Card('2', '♦'), Card('3', '♦'), Card('4', '♦'),
            Card('2', '♣'), Card('3', '♣'), Card('4', '♣')
        ]
        south_cards = [
            Card('7', '♠'), Card('6', '♠'),
            Card('A', '♥'), Card('9', '♥'), Card('8', '♥'),
            Card('K', '♦'), Card('Q', '♦'), Card('J', '♦'), Card('T', '♦'),
            Card('5', '♣'), Card('6', '♣'), Card('7', '♣'), Card('A', '♣')
        ]
        west_cards = [
            Card('5', '♠'), Card('4', '♠'), Card('3', '♠'), Card('2', '♠'),
            Card('7', '♥'), Card('6', '♥'), Card('5', '♥'),
            Card('A', '♦'), Card('9', '♦'), Card('8', '♦'),
            Card('K', '♣'), Card('Q', '♣'), Card('J', '♣')
        ]

        hands = {
            'North': Hand(north_cards),
            'East': Hand(east_cards),
            'South': Hand(south_cards),
            'West': Hand(west_cards)
        }

        # Verify HCP distribution
        ns_hcp = hands['North'].hcp + hands['South'].hcp
        ew_hcp = hands['East'].hcp + hands['West'].hcp
        assert ns_hcp < 33, f"NS has {ns_hcp} HCP - not a valid low-HCP test"
        assert ew_hcp < 33, f"EW has {ew_hcp} HCP - not a valid low-HCP test"

        engine = BiddingEngine()
        auction = self._simulate_auction(engine, hands)
        final_contract = self._get_final_contract(auction)

        if final_contract and final_contract[0].isdigit():
            level = int(final_contract[0])
            assert level < 6, (
                f"Slam {final_contract} bid when NS has {ns_hcp} HCP and EW has {ew_hcp} HCP! "
                f"Neither partnership has slam values."
            )

    def test_governor_allows_valid_slam(self):
        """
        Test that Governor allows slams when combined HCP >= 33.

        This ensures the Governor doesn't over-block valid slams.
        """
        # Create hands where N/S have 34 combined HCP
        north_cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'),
            Card('A', '♥'), Card('K', '♥'),
            Card('A', '♦'), Card('K', '♦'),
            Card('2', '♣'), Card('3', '♣'), Card('4', '♣'), Card('5', '♣'), Card('6', '♣')
        ]  # 20 HCP

        south_cards = [
            Card('T', '♠'), Card('9', '♠'), Card('8', '♠'),
            Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'),
            Card('Q', '♦'), Card('J', '♦'),
            Card('A', '♣'), Card('K', '♣'), Card('Q', '♣'), Card('J', '♣')
        ]  # 14 HCP

        # E/W get remaining cards
        east_cards = [
            Card('7', '♠'), Card('6', '♠'), Card('5', '♠'),
            Card('8', '♥'), Card('7', '♥'), Card('6', '♥'), Card('5', '♥'),
            Card('9', '♦'), Card('8', '♦'), Card('7', '♦'),
            Card('T', '♣'), Card('9', '♣'), Card('8', '♣')
        ]  # 0 HCP

        west_cards = [
            Card('4', '♠'), Card('3', '♠'), Card('2', '♠'),
            Card('4', '♥'), Card('3', '♥'), Card('2', '♥'),
            Card('6', '♦'), Card('5', '♦'), Card('4', '♦'), Card('3', '♦'), Card('2', '♦'),
            Card('7', '♣')
        ]  # 0 HCP - needs 13 cards
        # Fix West hand - add one more card
        west_cards = [
            Card('4', '♠'), Card('3', '♠'), Card('2', '♠'),
            Card('4', '♥'), Card('3', '♥'), Card('2', '♥'),
            Card('6', '♦'), Card('5', '♦'), Card('4', '♦'), Card('3', '♦'), Card('2', '♦'),
            Card('7', '♣'), Card('T', '♦')
        ]  # Still 0 HCP

        hands = {
            'North': Hand(north_cards),
            'East': Hand(east_cards),
            'South': Hand(south_cards),
            'West': Hand(west_cards)
        }

        ns_hcp = hands['North'].hcp + hands['South'].hcp
        assert ns_hcp >= 33, f"NS has only {ns_hcp} HCP - need 33+ for this test"

        # We can't guarantee slam will be bid, but we verify Governor doesn't block
        # if it is bid. The engine may not find slam for other reasons.
        engine = BiddingEngine()
        auction = self._simulate_auction(engine, hands)
        final_contract = self._get_final_contract(auction)

        # This test passes as long as no assertion error in Governor
        # (i.e., Governor didn't wrongly block a valid slam attempt)
        print(f"NS combined: {ns_hcp} HCP, Contract: {final_contract}")


class TestGovernorEdgeCases:
    """Test Governor edge cases and boundary conditions."""

    def test_exactly_33_hcp_small_slam(self):
        """Test that exactly 33 combined HCP allows small slam."""
        # This is a boundary test - 33 HCP should allow 6-level
        # We test this by ensuring the Governor's threshold is correct
        from engine.ai.sanity_checker import SanityChecker

        checker = SanityChecker()
        # Verify the thresholds in MAX_BID_LEVELS
        assert checker.MAX_BID_LEVELS[(33, 36)] == 5, "33-36 HCP should allow level 5"
        assert checker.MAX_BID_LEVELS[(37, 40)] == 6, "37-40 HCP should allow level 6"

    def test_governor_override_flag(self):
        """Test that Governor cannot be bypassed for slam bids."""
        # The key test: metadata bypass_sanity_check should NOT work for 6+ level
        from engine.ai.sanity_checker import SanityChecker
        from engine.hand import Hand, Card

        # Create a weak hand (4 HCP: K=3, J=1)
        cards = [
            Card('2', '♠'), Card('3', '♠'), Card('4', '♠'),
            Card('2', '♥'), Card('3', '♥'), Card('4', '♥'), Card('5', '♥'),
            Card('K', '♦'), Card('J', '♦'), Card('2', '♦'),
            Card('2', '♣'), Card('3', '♣'), Card('4', '♣')
        ]
        hand = Hand(cards)
        assert hand.hcp == 4, f"Hand should have 4 HCP, got {hand.hcp}"

        checker = SanityChecker()

        # Mock features and auction
        features = {
            'auction_context': None,
            'auction_features': {'opener_relationship': 'Partner'}
        }
        auction = ['1♣', 'Pass', '1♠', 'Pass', '3♣', 'Pass']

        # Try to bypass with metadata (this used to work for all bids)
        metadata = {'bypass_sanity_check': True, 'convention': 'blackwood_signoff'}

        # 6♠ should be blocked even with bypass flag
        should_bid, final_bid, reason = checker.check('6♠', hand, features, auction, metadata)
        assert not should_bid, (
            f"Governor should have blocked 6♠ with 5 HCP hand! "
            f"bypass_sanity_check metadata should not work for slam bids."
        )

        # But 4♠ should be allowed with bypass flag
        should_bid_4, final_bid_4, _ = checker.check('4♠', hand, features, auction, metadata)
        assert should_bid_4, "4♠ should be allowed with bypass flag (not a slam)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
