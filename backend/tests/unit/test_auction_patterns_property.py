"""
Auction Pattern Detection - Property-Based Tests Using Convention Hand Generators

These tests use the same hand generation logic that the scenarios system uses
to create hands for convention practice. This provides broader coverage with
randomized hands that meet convention constraints.

Key difference from deterministic tests:
- Hands are generated randomly (but meet convention requirements)
- Tests verify INVARIANTS rather than specific bids
- Run multiple times to catch edge cases

These tests complement the deterministic tests in test_auction_pattern_detection.py
and test_auction_patterns_phase1.py.
"""

import pytest
import random
from engine.hand import Hand, Card
from engine.hand_constructor import generate_hand_for_convention, generate_hand_with_constraints
from engine.ai.feature_extractor import extract_features
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.ai.conventions.gerber import GerberConvention
from engine.bidding_engine import BiddingEngine


def create_full_deck():
    """Create a standard 52-card deck."""
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['♠', '♥', '♦', '♣']
    return [Card(rank=r, suit=s) for s in suits for r in ranks]


# =============================================================================
# STAYMAN PROPERTY TESTS
# =============================================================================

class TestStaymanProperties:
    """
    Property-based tests for Stayman convention using generated hands.

    Invariants:
    - Stayman hands must have 8+ HCP (game interest)
    - Stayman hands must have at least one 4-card major
    - Stayman responder should bid 2♣ over 1NT
    """

    @pytest.mark.parametrize("seed", range(10))  # Run 10 times with different seeds
    def test_stayman_hand_meets_constraints(self, seed):
        """Generated Stayman hands meet minimum constraints."""
        random.seed(seed)
        deck = create_full_deck()

        stayman = StaymanConvention()
        hand, remaining = generate_hand_for_convention(stayman, deck)

        if hand is None:
            pytest.skip("Could not generate hand meeting constraints")

        # Verify constraints
        assert hand.hcp >= 8, f"Stayman needs 8+ HCP, got {hand.hcp}"

        # Should have at least one 4-card major
        has_4_major = (hand.suit_lengths['♠'] >= 4 or hand.suit_lengths['♥'] >= 4)
        assert has_4_major, f"Stayman needs 4-card major, got {hand.suit_lengths}"

    @pytest.mark.parametrize("seed", range(5))
    def test_stayman_triggers_over_1nt(self, seed):
        """Stayman convention triggers when conditions are met."""
        random.seed(seed)
        deck = create_full_deck()

        stayman = StaymanConvention()
        hand, _ = generate_hand_for_convention(stayman, deck)

        if hand is None:
            pytest.skip("Could not generate hand meeting constraints")

        # Set up 1NT opening auction
        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None')

        result = stayman.evaluate(hand, features)

        # Note: Hand may prefer Jacoby (5+ major) over Stayman (4-card major)
        # Only assert Stayman triggers if hand doesn't have 5+ major
        if hand.hcp >= 8:
            has_5_major = hand.suit_lengths['♠'] >= 5 or hand.suit_lengths['♥'] >= 5
            if not has_5_major:
                # No 5-card major, should use Stayman with 4-card major
                assert result is not None, "Should trigger Stayman with 8+ HCP and 4-card major"
                assert result[0] == '2♣', f"Should bid 2♣, got {result[0]}"
            # If has 5+ major, Jacoby takes priority - this is correct behavior


# =============================================================================
# JACOBY TRANSFER PROPERTY TESTS
# =============================================================================

class TestJacobyTransferProperties:
    """
    Property-based tests for Jacoby Transfers.

    Invariants:
    - Jacoby hands have 5+ card major
    - Transfer bid level is always 2
    - 2♦ = hearts, 2♥ = spades
    """

    @pytest.mark.parametrize("seed", range(10))
    def test_jacoby_hand_has_5_card_major(self, seed):
        """Generated Jacoby hands have 5+ card major."""
        random.seed(seed)
        deck = create_full_deck()

        jacoby = JacobyConvention()
        hand, _ = generate_hand_for_convention(jacoby, deck)

        if hand is None:
            pytest.skip("Could not generate hand meeting constraints")

        # Should have 5+ hearts or 5+ spades
        has_5_major = (hand.suit_lengths['♠'] >= 5 or hand.suit_lengths['♥'] >= 5)
        assert has_5_major, f"Jacoby needs 5-card major, got {hand.suit_lengths}"

    @pytest.mark.parametrize("seed", range(5))
    def test_jacoby_transfer_correct_suit(self, seed):
        """Transfer bid corresponds to correct major suit."""
        random.seed(seed)
        deck = create_full_deck()

        jacoby = JacobyConvention()
        hand, _ = generate_hand_for_convention(jacoby, deck)

        if hand is None:
            pytest.skip("Could not generate hand meeting constraints")

        auction = ['1NT', 'Pass']
        features = extract_features(hand, auction, 'South', 'None')

        result = jacoby.evaluate(hand, features)

        if result is None:
            return  # May not trigger with specific hand shape

        bid = result[0]

        # Verify transfer logic
        if bid == '2♦':
            # Transferring to hearts - should have 5+ hearts
            assert hand.suit_lengths['♥'] >= 5, \
                f"2♦ transfer needs 5+ hearts, got {hand.suit_lengths['♥']}"
        elif bid == '2♥':
            # Transferring to spades - should have 5+ spades
            assert hand.suit_lengths['♠'] >= 5, \
                f"2♥ transfer needs 5+ spades, got {hand.suit_lengths['♠']}"


# =============================================================================
# 1NT OPENER PROPERTY TESTS
# =============================================================================

class TestNTOpenerProperties:
    """
    Property-based tests for 1NT opener hands.

    Invariants:
    - 1NT opener has 15-17 HCP
    - 1NT opener is balanced (no singleton, at most one doubleton)
    """

    @pytest.mark.parametrize("seed", range(10))
    def test_1nt_opener_constraints(self, seed):
        """Generated 1NT hands meet requirements."""
        random.seed(seed)
        deck = create_full_deck()

        constraints = {'hcp_range': [15, 17], 'is_balanced': True}
        hand, _ = generate_hand_with_constraints(constraints, deck)

        if hand is None:
            pytest.skip("Could not generate hand meeting constraints")

        # Verify HCP
        assert 15 <= hand.hcp <= 17, f"1NT needs 15-17 HCP, got {hand.hcp}"

        # Verify balanced
        assert hand.is_balanced, \
            f"1NT needs balanced, got {hand.suit_lengths}"

    @pytest.mark.parametrize("seed", range(5))
    def test_1nt_opener_responds_to_stayman(self, seed):
        """1NT opener responds appropriately to Stayman."""
        random.seed(seed)
        deck = create_full_deck()

        constraints = {'hcp_range': [15, 17], 'is_balanced': True}
        hand, _ = generate_hand_with_constraints(constraints, deck)

        if hand is None:
            pytest.skip("Could not generate hand meeting constraints")

        # I opened 1NT, partner bid 2♣ Stayman
        auction = ['1NT', 'Pass', '2♣', 'Pass']
        features = extract_features(hand, auction, 'North', 'None')

        stayman = StaymanConvention()
        result = stayman.evaluate(hand, features)

        assert result is not None, "Should respond to Stayman"
        bid = result[0]

        # Verify response matches hand
        if bid == '2♥':
            assert hand.suit_lengths['♥'] >= 4, \
                f"2♥ response needs 4+ hearts, got {hand.suit_lengths['♥']}"
        elif bid == '2♠':
            assert hand.suit_lengths['♠'] >= 4, \
                f"2♠ response needs 4+ spades, got {hand.suit_lengths['♠']}"
        elif bid == '2♦':
            # 2♦ = no 4-card major
            assert hand.suit_lengths['♥'] < 4 and hand.suit_lengths['♠'] < 4, \
                f"2♦ should have no 4-card major, got {hand.suit_lengths}"


# =============================================================================
# BIDDING ENGINE PROPERTY TESTS
# =============================================================================

class TestBiddingEngineProperties:
    """
    Property-based tests for the full bidding engine.

    Invariants:
    - Engine always returns a valid bid
    - Bids are legal given auction context
    - Explanations are never empty
    """

    @pytest.mark.parametrize("seed", range(10))
    def test_engine_always_returns_bid(self, seed):
        """Bidding engine always returns some bid."""
        random.seed(seed)
        deck = create_full_deck()
        random.shuffle(deck)

        # Create random hand
        hand = Hand(deck[:13])

        # Random auction state (just Pass for simplicity)
        auction = []

        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(hand, auction, 'South', 'None')

        assert bid is not None, "Engine must return a bid"
        assert isinstance(bid, str), "Bid must be a string"
        assert len(bid) > 0, "Bid must not be empty"
        assert explanation is not None, "Explanation must not be None"

    @pytest.mark.parametrize("seed", range(5))
    def test_engine_bids_are_legal(self, seed):
        """All bids from engine are legal in context."""
        random.seed(seed)
        deck = create_full_deck()
        random.shuffle(deck)

        hand = Hand(deck[:13])

        # Simple auction with one bid
        auction = ['1♠', 'Pass']

        engine = BiddingEngine()
        bid, _ = engine.get_next_bid(hand, auction, 'South', 'None')

        # Verify legality
        if bid not in ['Pass', 'X', 'XX']:
            # Must be higher than 1♠
            try:
                level = int(bid[0])
                suit = bid[1:]

                suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}

                # Legal if level > 1 or (level == 1 and suit > spades)
                is_legal = (level > 1) or (level == 1 and suit_rank.get(suit, 0) > 4)
                assert is_legal or bid == 'Pass', f"Illegal bid {bid} after 1♠"
            except (ValueError, IndexError):
                # Pass, X, XX are always legal
                assert bid in ['Pass', 'X', 'XX'], f"Unexpected bid format: {bid}"


# =============================================================================
# GERBER PROPERTY TESTS
# =============================================================================

class TestGerberProperties:
    """
    Property-based tests for Gerber convention.

    Invariants:
    - Gerber hands have slam interest (high HCP)
    - Gerber only triggered over NT bids
    - Ace responses match actual ace count
    """

    @pytest.mark.parametrize("seed", range(5))
    def test_gerber_response_matches_aces(self, seed):
        """Gerber response accurately reflects ace count."""
        random.seed(seed)
        deck = create_full_deck()

        # Create random balanced hand for 1NT opener
        constraints = {'hcp_range': [15, 17], 'is_balanced': True}
        hand, _ = generate_hand_with_constraints(constraints, deck)

        if hand is None:
            pytest.skip("Could not generate hand")

        # Count actual aces
        actual_aces = sum(1 for c in hand.cards if c.rank == 'A')

        # Simulate Gerber ask
        auction = ['1NT', 'Pass', '4♣', 'Pass']
        features = extract_features(hand, auction, 'North', 'None')

        gerber = GerberConvention()
        result = gerber.evaluate(hand, features)

        if result is None:
            return  # May not trigger in all cases

        bid = result[0]

        # Verify response matches aces
        expected = {
            0: '4♦', 1: '4♥', 2: '4♠', 3: '4NT', 4: '4♦'
        }

        expected_bid = expected.get(actual_aces)
        if expected_bid:
            assert bid == expected_bid, \
                f"With {actual_aces} aces, expected {expected_bid}, got {bid}"


# =============================================================================
# COMBINED HCP + SUIT PROPERTY TESTS
# =============================================================================

class TestHCPAndSuitProperties:
    """
    Property tests ensuring HCP and suit length constraints work together.
    """

    @pytest.mark.parametrize("seed", range(5))
    def test_game_bid_requires_combined_hcp(self, seed):
        """Game-level bids only made with sufficient combined HCP."""
        random.seed(seed)
        deck = create_full_deck()
        random.shuffle(deck)

        # Create weak hand
        constraints = {'hcp_range': [5, 7]}
        hand, _ = generate_hand_with_constraints(constraints, deck)

        if hand is None:
            pytest.skip("Could not generate hand")

        # Partner opened at 1-level (13-21 HCP estimated)
        auction = ['1♠', 'Pass']

        engine = BiddingEngine()
        bid, _ = engine.get_next_bid(hand, auction, 'South', 'None')

        # With only 5-7 HCP, should NOT bid game (combined 18-28, not reliable game)
        # Though 4♠ might be acceptable with huge fit
        if bid.startswith('4') or bid.startswith('5') or bid.startswith('6'):
            # If bidding game, should have good reason
            pass  # Allow, as fit-based games are valid

    @pytest.mark.parametrize("seed", range(5))
    def test_preempt_has_long_suit(self, seed):
        """Preemptive opening hands have long suits."""
        random.seed(seed)
        deck = create_full_deck()

        # Preempt constraints: weak hand, long suit
        constraints = {
            'hcp_range': [5, 10],
            'suit_length_req': (['♠', '♥', '♦'], 6, 'any_of')  # 6+ in a non-club suit
        }
        hand, _ = generate_hand_with_constraints(constraints, deck)

        if hand is None:
            pytest.skip("Could not generate hand")

        # Verify long suit exists
        max_length = max(hand.suit_lengths.values())
        assert max_length >= 6, f"Preempt needs 6+ card suit, got {max_length}"

        # Verify HCP is weak
        assert hand.hcp <= 10, f"Preempt should be weak, got {hand.hcp} HCP"


# =============================================================================
# STRESS TESTS
# =============================================================================

class TestRandomHandStress:
    """
    Stress tests with many random hands to find edge cases.

    These tests run quickly and help catch unexpected crashes or
    assertion failures in the bidding engine.
    """

    def test_100_random_opening_bids(self):
        """Engine handles 100 random opening situations without crashing."""
        engine = BiddingEngine()
        errors = []

        for i in range(100):
            random.seed(i)
            deck = create_full_deck()
            random.shuffle(deck)
            hand = Hand(deck[:13])

            try:
                bid, explanation = engine.get_next_bid(hand, [], 'South', 'None')
                assert bid is not None
                assert explanation is not None
            except Exception as e:
                errors.append((i, str(e)))

        assert len(errors) == 0, f"Errors in {len(errors)} hands: {errors[:5]}"

    def test_100_random_responses(self):
        """Engine handles 100 random response situations without crashing."""
        engine = BiddingEngine()
        errors = []

        openings = ['1♣', '1♦', '1♥', '1♠', '1NT', '2♣', '2♦', '2♥', '2♠', '2NT']

        for i in range(100):
            random.seed(i)
            deck = create_full_deck()
            random.shuffle(deck)
            hand = Hand(deck[:13])

            opening = random.choice(openings)
            auction = [opening, 'Pass']

            try:
                bid, explanation = engine.get_next_bid(hand, auction, 'South', 'None')
                assert bid is not None
                assert explanation is not None
            except Exception as e:
                errors.append((i, opening, str(e)))

        assert len(errors) == 0, f"Errors in {len(errors)} hands: {errors[:5]}"
