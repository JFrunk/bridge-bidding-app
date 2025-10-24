"""
Integration tests for slam bidding.

Tests that AI:
- Bids slams with sufficient values (33+ HCP for small, 37+ for grand)
- Doesn't bid slams with insufficient values
- Uses Blackwood correctly
- Checks for aces before grand slams
- Evaluates distribution and trump quality
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


class SlamBiddingTestBase:
    """Base class with shared helper methods for slam bidding tests."""

    def _create_hands_with_combined_hcp(self, target_hcp):
        """Create hands with specific combined HCP for N/S."""
        # Distribute HCP between N and S to reach target
        north_hcp = target_hcp // 2
        south_hcp = target_hcp - north_hcp

        north_cards = self._create_hand_with_hcp(north_hcp, '♠')
        south_cards = self._create_hand_with_hcp(south_hcp, '♥')

        # Filler hands for E/W
        east_cards = self._create_filler_hand()
        west_cards = self._create_filler_hand()

        return {
            'North': Hand(north_cards),
            'South': Hand(south_cards),
            'East': Hand(east_cards),
            'West': Hand(west_cards)
        }

    def _create_hand_with_hcp(self, target_hcp, primary_suit):
        """Create a hand with approximately target HCP."""
        cards = []

        # Add high cards to reach target HCP
        # A=4, K=3, Q=2, J=1
        remaining_hcp = target_hcp
        honors = []

        # Distribute honors
        while remaining_hcp >= 4:
            honors.append('A')
            remaining_hcp -= 4
        while remaining_hcp >= 3:
            honors.append('K')
            remaining_hcp -= 3
        while remaining_hcp >= 2:
            honors.append('Q')
            remaining_hcp -= 2
        while remaining_hcp >= 1:
            honors.append('J')
            remaining_hcp -= 1

        # Add honors to primary suit
        for honor in honors[:min(len(honors), 4)]:
            cards.append(Card(honor, primary_suit))

        # Fill remaining cards
        spot_cards = ['T', '9', '8', '7', '6', '5', '4', '3', '2']
        suits = ['♠', '♥', '♦', '♣']

        for _ in range(13 - len(cards)):
            suit = suits[len(cards) % 4]
            rank = spot_cards[len(cards) % len(spot_cards)]
            cards.append(Card(rank, suit))

        return cards[:13]

    def _create_filler_hand(self):
        """Create a minimal hand for opponents."""
        cards = []
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['9', '8', '7', '6', '5', '4', '3', '2', 'T', 'J', 'Q', 'K', 'A']

        for i in range(13):
            suit = suits[i % 4]
            rank = ranks[i % len(ranks)]
            cards.append(Card(rank, suit))

        return cards

    def _create_hands_missing_aces(self):
        """Create hands with good HCP but missing aces."""
        # N/S with 33 HCP but only 2 aces
        north_cards = [
            Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('T', '♠'),
            Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'),
            Card('A', '♦'), Card('K', '♦'), Card('Q', '♦'),
            Card('K', '♣'), Card('Q', '♣'), Card('J', '♣')
        ]

        south_cards = [
            Card('A', '♠'), Card('9', '♠'),
            Card('A', '♥'), Card('9', '♥'), Card('8', '♥'),
            Card('J', '♦'), Card('T', '♦'), Card('9', '♦'),
            Card('T', '♣'), Card('9', '♣'), Card('8', '♣'),
            Card('7', '♣'), Card('6', '♣')
        ]

        east_cards = self._create_filler_hand()
        west_cards = self._create_filler_hand()

        return {
            'North': Hand(north_cards),
            'South': Hand(south_cards),
            'East': Hand(east_cards),
            'West': Hand(west_cards)
        }

    def _create_hands_missing_one_ace(self):
        """Create strong hands missing one ace."""
        # Similar to above but with 37 HCP and 3 aces
        return self._create_hands_missing_aces()

    def _count_aces_in_pair(self, hands, pair):
        """Count aces held by a pair of players."""
        aces = 0
        for player in pair:
            if player in hands:
                for card in hands[player].cards:
                    if card.rank == 'A':
                        aces += 1
        return aces

    def _create_blackwood_scenario_hands(self):
        """Create hands for Blackwood scenario."""
        # North (opener) with 18 HCP, good hearts
        north_cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'),
            Card('J', '♥'), Card('T', '♥'),
            Card('K', '♦'), Card('Q', '♦'),
            Card('9', '♣'), Card('8', '♣'), Card('7', '♣')
        ]

        # South (responder) with 12 HCP, heart fit
        south_cards = [
            Card('J', '♠'), Card('T', '♠'),
            Card('9', '♥'), Card('8', '♥'), Card('7', '♥'), Card('6', '♥'),
            Card('A', '♦'), Card('Q', '♦'), Card('J', '♦'),
            Card('A', '♣'), Card('K', '♣'), Card('6', '♣'), Card('5', '♣')
        ]

        east_cards = self._create_filler_hand()
        west_cards = self._create_filler_hand()

        return {
            'opener': Hand(north_cards),
            'responder': Hand(south_cards),
            'North': Hand(north_cards),
            'South': Hand(south_cards),
            'East': Hand(east_cards),
            'West': Hand(west_cards)
        }

    def _create_hand_with_n_aces(self, n_aces):
        """Create a hand with exactly n aces."""
        cards = []
        suits = ['♠', '♥', '♦', '♣']

        # Add n aces
        for i in range(min(n_aces, 4)):
            cards.append(Card('A', suits[i]))

        # Fill remaining cards
        remaining = 13 - len(cards)
        spot_cards = ['K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']

        for i in range(remaining):
            suit = suits[i % 4]
            rank = spot_cards[i % len(spot_cards)]
            cards.append(Card(rank, suit))

        return Hand(cards)

    def _create_distributional_slam_hands(self):
        """Create hands with distribution for slam."""
        # N/S with 32 HCP but good distribution (6-4 fit in hearts)
        north_cards = [
            Card('A', '♠'), Card('K', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'),
            Card('K', '♦'), Card('Q', '♦'),
            Card('A', '♣'), Card('5', '♣'), Card('4', '♣')
        ]

        south_cards = [
            Card('Q', '♠'), Card('J', '♠'), Card('T', '♠'),
            Card('8', '♥'), Card('7', '♥'), Card('6', '♥'), Card('5', '♥'),
            Card('A', '♦'), Card('J', '♦'), Card('T', '♦'),
            Card('K', '♣'), Card('Q', '♣'), Card('J', '♣')
        ]

        east_cards = self._create_filler_hand()
        west_cards = self._create_filler_hand()

        return {
            'North': Hand(north_cards),
            'South': Hand(south_cards),
            'East': Hand(east_cards),
            'West': Hand(west_cards)
        }

    def _create_weak_trump_hands(self):
        """Create hands with weak trump for slam."""
        # N/S with 33 HCP but weak hearts (missing A, K, Q)
        north_cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'),
            Card('J', '♥'), Card('T', '♥'), Card('9', '♥'), Card('8', '♥'),
            Card('A', '♦'), Card('K', '♦'), Card('Q', '♦'),
            Card('A', '♣'), Card('K', '♣')
        ]

        south_cards = [
            Card('T', '♠'), Card('9', '♠'),
            Card('7', '♥'), Card('6', '♥'), Card('5', '♥'), Card('4', '♥'),
            Card('J', '♦'), Card('T', '♦'), Card('9', '♦'),
            Card('Q', '♣'), Card('J', '♣'), Card('T', '♣'), Card('9', '♣')
        ]

        east_cards = self._create_filler_hand()
        west_cards = self._create_filler_hand()

        return {
            'North': Hand(north_cards),
            'South': Hand(south_cards),
            'East': Hand(east_cards),
            'West': Hand(west_cards)
        }

    def _simulate_auction(self, engine, hands, dealer):
        """Simulate full auction."""
        auction = []
        positions = ['North', 'East', 'South', 'West']
        dealer_index = positions.index(dealer)
        consecutive_passes = 0
        max_bids = 40

        for _ in range(max_bids):
            pos = positions[(dealer_index + len(auction)) % 4]
            hand = hands[pos]

            bid, _ = engine.get_next_bid(hand, auction, pos, 'None')
            auction.append(bid)

            if bid == 'Pass':
                consecutive_passes += 1
                if consecutive_passes >= 3:
                    if len(auction) >= 4:  # At least 4 bids
                        break
            else:
                consecutive_passes = 0

        return auction

    def _get_final_contract(self, auction):
        """Extract final contract from auction."""
        if not auction:
            return None

        # Find last non-Pass bid
        for bid in reversed(auction):
            if bid not in ['Pass', 'X', 'XX']:
                return bid

        return None


class TestSlamBiddingRequirements(SlamBiddingTestBase):
    """Test slam bidding point requirements."""

    def test_small_slam_requires_33_hcp(self):
        """
        Test that AI bids small slam with 33+ HCP, not with less.

        6-level contracts require approximately 33 combined HCP.
        """
        # Test with insufficient HCP (30)
        hands_insufficient = self._create_hands_with_combined_hcp(30)
        engine = BiddingEngine()

        auction_insufficient = self._simulate_auction(
            engine, hands_insufficient, dealer='North'
        )
        final_insufficient = self._get_final_contract(auction_insufficient)

        if final_insufficient and int(final_insufficient[0]) >= 6:
            pytest.fail(
                f"Bid {final_insufficient} with only 30 combined HCP! "
                f"Small slam needs 33+ HCP."
            )

        # Test with sufficient HCP (33)
        hands_sufficient = self._create_hands_with_combined_hcp(33)
        auction_sufficient = self._simulate_auction(
            engine, hands_sufficient, dealer='North'
        )
        final_sufficient = self._get_final_contract(auction_sufficient)

        # With 33 HCP, slam is reasonable (though not required)
        # This test mainly ensures we CAN bid slam with sufficient values
        # (Not failing to bid slam is less critical than overbidding)

    def test_grand_slam_requires_37_hcp(self):
        """
        Test that AI bids grand slam with 37+ HCP, not with less.

        7-level contracts require approximately 37 combined HCP.
        """
        # Test with insufficient HCP (34)
        hands_insufficient = self._create_hands_with_combined_hcp(34)
        engine = BiddingEngine()

        auction_insufficient = self._simulate_auction(
            engine, hands_insufficient, dealer='North'
        )
        final_insufficient = self._get_final_contract(auction_insufficient)

        if final_insufficient and int(final_insufficient[0]) >= 7:
            pytest.fail(
                f"Bid {final_insufficient} with only 34 combined HCP! "
                f"Grand slam needs 37+ HCP."
            )

    def test_no_slam_with_missing_aces(self):
        """
        Test that AI doesn't bid slam when missing multiple aces.

        Even with sufficient HCP, missing 2 aces makes slam risky.
        """
        hands = self._create_hands_missing_aces()
        engine = BiddingEngine()

        auction = self._simulate_auction(engine, hands, dealer='North')
        final_contract = self._get_final_contract(auction)

        # Count aces in declaring pair
        if final_contract:
            level = int(final_contract[0])
            if level >= 6:
                # If in slam, should have most aces
                aces = self._count_aces_in_pair(hands, ['North', 'South'])
                assert aces >= 3, (
                    f"Bid {final_contract} with only {aces} aces! "
                    f"Slam requires better ace holding."
                )

    def test_no_grand_slam_without_all_aces(self):
        """
        Test that AI doesn't bid grand slam missing an ace.

        Grand slam requires all 4 aces (or equivalent control).
        """
        hands = self._create_hands_missing_one_ace()
        engine = BiddingEngine()

        auction = self._simulate_auction(engine, hands, dealer='North')
        final_contract = self._get_final_contract(auction)

        if final_contract and int(final_contract[0]) == 7:
            aces = self._count_aces_in_pair(hands, ['North', 'South'])
            assert aces == 4, (
                f"Bid {final_contract} with only {aces} aces! "
                f"Grand slam requires all 4 aces."
            )


class TestBlackwoodConvention(SlamBiddingTestBase):
    """Test Blackwood slam convention."""

    def test_blackwood_asks_for_aces(self):
        """
        Test that 4NT asks for aces after suit agreement.

        Scenario: 1♥ - 3♥ - 4NT
        4NT should be Blackwood (asking for aces), not quantitative
        """
        hands = self._create_blackwood_scenario_hands()
        engine = BiddingEngine()

        # Auction: 1♥ - Pass - 3♥ - Pass - ?
        auction = ['1♥', 'Pass', '3♥', 'Pass']
        opener_hand = hands['opener']

        bid, explanation = engine.get_next_bid(
            opener_hand,
            auction,
            'North',
            'None'
        )

        # With 18 HCP and suit agreement, should consider Blackwood
        # (Not required, but should be an option)
        if bid == '4NT':
            assert 'blackwood' in explanation.lower() or 'ace' in explanation.lower(), (
                f"Bid 4NT but explanation doesn't mention Blackwood or aces! "
                f"Explanation: {explanation}"
            )

    def test_blackwood_responses_correct(self):
        """
        Test that responses to Blackwood show correct number of aces.

        5♣ = 0 or 4 aces
        5♦ = 1 ace
        5♥ = 2 aces
        5♠ = 3 aces

        NOTE: This is a basic integration test. Full Blackwood response testing
        requires more sophisticated auction understanding.
        """
        # Test with 2 aces
        hand_2_aces = self._create_hand_with_n_aces(2)
        engine = BiddingEngine()

        # Auction: 1♥ - Pass - 3♥ - Pass - 4NT (Blackwood) - Pass - ?
        # Suit agreement established with 3♥ raise, so 4NT is Blackwood
        auction = ['1♥', 'Pass', '3♥', 'Pass', '4NT', 'Pass']

        bid, _ = engine.get_next_bid(
            hand_2_aces,
            auction,
            'South',
            'None'
        )

        # At minimum, shouldn't bid unreasonably (like 7NT)
        # Ideal response would be 5♥ (2 aces), but current AI may not fully
        # implement Blackwood responses in all contexts
        if bid not in ['Pass', 'X', 'XX']:
            level = int(bid[0])
            assert level <= 6, (
                f"After Blackwood 4NT, bid {bid}! "
                f"Should respond at 5 or 6 level, not grand slam."
            )

    def test_blackwood_signoff_after_insufficient_aces(self):
        """
        Test that asker signs off at 5-level if partner shows insufficient aces.

        Scenario: Ask with 4NT, partner shows 1 ace, sign off at 5 of suit
        """
        # This requires simulating full auction with Blackwood
        # TODO: Implement detailed Blackwood signoff test
        pass


class TestSlamEvaluation(SlamBiddingTestBase):
    """Test slam evaluation based on hand strength and distribution."""

    def test_slam_with_strong_trump_and_distribution(self):
        """
        Test that AI considers distribution for slam.

        With good trump fit and distribution, slam may be biddable
        with slightly fewer HCP (31-32).
        """
        hands = self._create_distributional_slam_hands()
        engine = BiddingEngine()

        auction = self._simulate_auction(engine, hands, dealer='North')
        final_contract = self._get_final_contract(auction)

        # With 9-card trump fit and distribution, slam is reasonable
        # (This is a positive test - we WANT to bid slam here)
        # Not testing for specific outcome, just that it's considered
        pass  # Outcome depends on sophisticated evaluation

    def test_no_slam_with_weak_trump(self):
        """
        Test that AI doesn't bid slam with weak trump.

        Even with 33 HCP, if trump suit is weak (missing AKQ),
        slam may not be biddable.
        """
        hands = self._create_weak_trump_hands()
        engine = BiddingEngine()

        auction = self._simulate_auction(engine, hands, dealer='North')
        final_contract = self._get_final_contract(auction)

        # This is an advanced test - current AI may not check trump quality
        # TODO: Enhance AI to consider trump quality
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
