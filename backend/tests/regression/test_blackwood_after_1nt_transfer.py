"""
Regression Test: Blackwood Response After 1NT Opening with Transfer

Bug Report: hand_2025-12-28_17-18-05.json
Reported: 2025-12-28
Fixed: 2026-01-01

Issue: After 1NT opening followed by Jacoby Transfer and suit agreement,
the system was treating partner's 4NT as quantitative instead of Blackwood.
This caused the responder to Pass instead of showing aces.

Root Cause: In blackwood.py _is_ace_answering_applicable(), the check for
"partner opened NT → quantitative" was happening BEFORE checking for suit
agreement. The fix reorders these checks so suit agreement takes priority.

Test Case:
- North opens 1NT (15-17 HCP balanced)
- South transfers to spades via 2♥
- North completes transfer with 2♠
- South bids game (4♠)
- North explores slam with 4NT (Blackwood)
- South MUST respond with ace count (5♦ for 1 ace), NOT Pass

Expected: South responds 5♦ (showing 1 ace)
Actual (bug): South passed
"""

import pytest
from engine.hand import Hand, Card
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.ai.feature_extractor import extract_features


class TestBlackwoodAfter1NTTransfer:
    """Regression test for Blackwood after 1NT opening + Jacoby Transfer."""

    @pytest.fixture
    def blackwood_convention(self):
        """Create Blackwood convention module."""
        return BlackwoodConvention()

    @pytest.fixture
    def south_hand_with_one_ace(self):
        """
        South's hand from the bug report:
        ♠AKT972 ♥JT76 ♦T9 ♣-
        8 HCP, 6 spades, 1 ace (♠A)
        Note: Hand requires 13 cards, so adding a club for test validity
        """
        return Hand([
            Card('A', '♠'), Card('K', '♠'), Card('T', '♠'), Card('9', '♠'), Card('7', '♠'), Card('2', '♠'),
            Card('J', '♥'), Card('T', '♥'), Card('7', '♥'), Card('6', '♥'),
            Card('T', '♦'), Card('9', '♦'),
            Card('2', '♣'),  # Need 13 cards
        ])

    def test_blackwood_response_after_1nt_and_transfer(self, blackwood_convention, south_hand_with_one_ace):
        """
        Test that South responds to Blackwood with ace count, not Pass.

        Auction: 1NT(N) - Pass(E) - 2♥(S) - Pass(W) - 2♠(N) - Pass(E) - 4♠(S) - Pass(W) - 4NT(N) - Pass(E) - ?

        South has 1 ace (♠A), so should respond 5♦.
        """
        # Build the auction history
        # North is dealer, auction starts with North
        auction_history = [
            '1NT',  # North opens 1NT (pos 0)
            'Pass', # East passes (pos 1)
            '2♥',   # South transfers to spades (pos 2)
            'Pass', # West passes (pos 3)
            '2♠',   # North completes transfer (pos 0)
            'Pass', # East passes (pos 1)
            '4♠',   # South bids game (pos 2)
            'Pass', # West passes (pos 3)
            '4NT',  # North asks for aces (pos 0) - THIS IS BLACKWOOD
            'Pass', # East passes (pos 1)
            # Now it's South's turn to respond (pos 2)
        ]

        # Use extract_features with correct parameters
        features = extract_features(
            hand=south_hand_with_one_ace,
            auction_history=auction_history,
            my_position='South',
            vulnerability='None',
            dealer='North'
        )

        # Get Blackwood's evaluation
        result = blackwood_convention.evaluate(south_hand_with_one_ace, features)

        # MUST return a bid, not None (which would fall through to Pass)
        assert result is not None, "Blackwood should recognize this as Blackwood, not quantitative 4NT"

        # Extract bid (result could be 2-tuple or 3-tuple)
        bid = result[0] if result else None
        explanation = result[1] if result and len(result) >= 2 else ""

        # South has 1 ace, so should bid 5♦
        assert bid == '5♦', f"Expected 5♦ (1 ace), got {bid}. Explanation: {explanation}"
        assert 'ace' in explanation.lower(), f"Explanation should mention aces: {explanation}"

    def test_additional_blackwood_after_stayman(self, blackwood_convention):
        """
        Test Blackwood after Stayman (another NT convention followed by suit agreement).

        Auction: 1NT(N) - Pass(E) - 2♣(S Stayman) - Pass(W) - 2♥(N) - Pass(E) - 4♥(S) - Pass(W) - 4NT(N) - Pass(E) - ?
        """
        # Hand with 3 aces
        south_hand = Hand([
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'),
            Card('A', '♦'), Card('K', '♦'),
            Card('Q', '♣'), Card('J', '♣'), Card('T', '♣')
        ])

        # Auction with Stayman leading to heart fit
        auction_history = [
            '1NT',  # North opens 1NT
            'Pass',
            '2♣',   # South asks for major (Stayman)
            'Pass',
            '2♥',   # North shows 4 hearts
            'Pass',
            '4♥',   # South bids game
            'Pass',
            '4NT',  # North asks for aces (Blackwood)
            'Pass',
        ]

        features = extract_features(
            hand=south_hand,
            auction_history=auction_history,
            my_position='South',
            vulnerability='None',
            dealer='North'
        )

        result = blackwood_convention.evaluate(south_hand, features)

        assert result is not None, "Should recognize as Blackwood after Stayman + heart fit"
        assert result[0] == '5♠', f"Should respond 5♠ (3 aces), got {result[0]}"


class TestBlackwoodSuitAgreementPriority:
    """Test that suit agreement takes priority over NT opening check."""

    @pytest.fixture
    def blackwood_convention(self):
        return BlackwoodConvention()

    def test_suit_agreement_via_transfer_is_blackwood(self, blackwood_convention):
        """Transfer creates suit agreement, so 4NT is Blackwood."""
        # Hand with 2 aces
        hand = Hand([
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('T', '♠'),
            Card('A', '♥'), Card('K', '♥'),
            Card('Q', '♦'), Card('J', '♦'),
            Card('T', '♣'), Card('9', '♣'), Card('8', '♣'), Card('7', '♣')
        ])

        auction_history = [
            '1NT', 'Pass', '2♦',   # South transfers to hearts
            'Pass', '2♥', 'Pass', '4♥',  # North completes, South bids game
            'Pass', '4NT', 'Pass'  # North asks for aces
        ]

        features = extract_features(
            hand=hand,
            auction_history=auction_history,
            my_position='South',
            vulnerability='None',
            dealer='North'
        )

        result = blackwood_convention.evaluate(hand, features)

        assert result is not None, "Should recognize as Blackwood due to heart suit agreement"
        assert result[0] == '5♥', f"Should respond 5♥ (2 aces), got {result[0]}"

    def test_responder_shows_suit_after_1nt_then_blackwood(self, blackwood_convention):
        """
        When responder shows a suit after 1NT (not transfer), 4NT is still Blackwood.

        Auction: 1NT(N) - Pass(E) - 3♠(S game force) - Pass(W) - 4♠(N) - Pass(E) - 4NT(S) - Pass(W) - ?

        Note: In this case SOUTH bid 4NT, not North. North must respond with aces.
        """
        # North's hand (responding to South's 4NT Blackwood)
        north_hand = Hand([
            Card('K', '♠'), Card('Q', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'),
            Card('A', '♦'), Card('K', '♦'),
            Card('K', '♣'), Card('Q', '♣'), Card('J', '♣'), Card('T', '♣'), Card('9', '♣')
        ])

        auction_history = [
            '1NT', 'Pass', '3♠',   # South jumps to 3♠ (game forcing)
            'Pass', '4♠', 'Pass', '4NT',  # North raises, South asks for aces
            'Pass'
            # Now it's North's turn to respond with aces
        ]

        features = extract_features(
            hand=north_hand,
            auction_history=auction_history,
            my_position='North',  # North is responding to South's 4NT
            vulnerability='None',
            dealer='North'
        )

        result = blackwood_convention.evaluate(north_hand, features)

        # North has 2 aces (♥A, ♦A)
        assert result is not None, "Should recognize as Blackwood due to spade suit agreement"
        assert result[0] == '5♥', f"Should respond 5♥ (2 aces), got {result[0]}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
