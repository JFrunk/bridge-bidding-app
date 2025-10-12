"""
Unit tests for DealGenerator.

Tests hand generation for various scenarios.
"""

import pytest
from core.deal_generator import DealGenerator
from engine.hand import Hand


class TestDealGenerator:
    """Test DealGenerator functionality."""

    def test_generate_random_deal(self):
        """Test generating a random deal."""
        hands = DealGenerator.generate_random_deal()

        assert len(hands) == 4
        assert all(pos in hands for pos in ['N', 'E', 'S', 'W'])
        assert all(isinstance(hand, Hand) for hand in hands.values())
        assert all(len(hand.cards) == 13 for hand in hands.values())

        # Check that all 52 cards are dealt
        all_cards = []
        for hand in hands.values():
            all_cards.extend(hand.cards)
        assert len(all_cards) == 52
        assert len(set(all_cards)) == 52  # No duplicates

    def test_generate_random_deal_uniqueness(self):
        """Test that random deals are actually random."""
        deal1 = DealGenerator.generate_random_deal()
        deal2 = DealGenerator.generate_random_deal()

        # Very unlikely to be identical
        south1_cards = [f"{c.rank}{c.suit}" for c in deal1['S'].cards]
        south2_cards = [f"{c.rank}{c.suit}" for c in deal2['S'].cards]

        assert south1_cards != south2_cards

    def test_generate_constrained_deal_hcp(self):
        """Test generating deal with HCP constraints."""
        constraints = {
            'S': {'hcp_range': (15, 17), 'is_balanced': True},
            'N': None,
            'E': None,
            'W': None
        }

        hands = DealGenerator.generate_constrained_deal(constraints)

        assert 15 <= hands['S'].hcp <= 17
        assert hands['S'].is_balanced

    def test_generate_constrained_deal_suit_length(self):
        """Test generating deal with suit length constraints."""
        constraints = {
            'S': {
                'hcp_range': (12, 18),
                'suit_length_req': (['♠'], 5, 'any_of')
            },
            'N': None,
            'E': None,
            'W': None
        }

        hands = DealGenerator.generate_constrained_deal(constraints)

        assert hands['S'].suit_lengths['♠'] >= 5
        assert 12 <= hands['S'].hcp <= 18

    def test_generate_constrained_deal_multiple_positions(self):
        """Test generating deal with constraints on multiple positions."""
        constraints = {
            'S': {'hcp_range': (12, 14)},
            'N': {'hcp_range': (15, 17), 'is_balanced': True},
            'E': None,
            'W': None
        }

        hands = DealGenerator.generate_constrained_deal(constraints)

        assert 12 <= hands['S'].hcp <= 14
        assert 15 <= hands['N'].hcp <= 17
        assert hands['N'].is_balanced

    def test_generate_for_contract_notrump(self):
        """Test generating hands for NT contract."""
        hands = DealGenerator.generate_for_contract("3NT", "S")

        # Declarer and dummy should have reasonable HCP
        total_hcp = hands['S'].hcp + hands['N'].hcp
        assert total_hcp >= 20  # Reasonable for 3NT

        # Both likely balanced for NT
        assert hands['S'].is_balanced
        assert hands['N'].is_balanced

    def test_generate_for_contract_suit(self):
        """Test generating hands for suit contract."""
        hands = DealGenerator.generate_for_contract("4♥", "S")

        # Declarer should have hearts
        assert hands['S'].suit_lengths['♥'] >= 4

        # Dummy should have support
        assert hands['N'].suit_lengths['♥'] >= 3

    def test_generate_for_contract_different_declarers(self):
        """Test generating contracts with different declarers."""
        for declarer in ['N', 'E', 'S', 'W']:
            hands = DealGenerator.generate_for_contract("3NT", declarer)

            dummy = {'N': 'S', 'E': 'W', 'S': 'N', 'W': 'E'}[declarer]

            # Both declarer and dummy should be balanced
            assert hands[declarer].is_balanced
            assert hands[dummy].is_balanced

            # Combined HCP should be reasonable for game
            total_hcp = hands[declarer].hcp + hands[dummy].hcp
            assert total_hcp >= 20  # Reasonable for 3NT game

    def test_generate_balanced_hand(self):
        """Test generating a single balanced hand."""
        hand = DealGenerator.generate_balanced_hand((15, 17))

        assert isinstance(hand, Hand)
        assert len(hand.cards) == 13
        assert 15 <= hand.hcp <= 17
        assert hand.is_balanced

    def test_generate_balanced_hand_different_ranges(self):
        """Test generating balanced hands with different HCP ranges."""
        weak_hand = DealGenerator.generate_balanced_hand((10, 12))
        strong_hand = DealGenerator.generate_balanced_hand((20, 22))

        assert 10 <= weak_hand.hcp <= 12
        assert 20 <= strong_hand.hcp <= 22
        assert weak_hand.is_balanced
        assert strong_hand.is_balanced

    def test_deal_all_cards_accounted_for(self):
        """Test that all 52 cards are dealt exactly once."""
        hands = DealGenerator.generate_random_deal()

        # Count cards by rank and suit
        card_counts = {}
        for hand in hands.values():
            for card in hand.cards:
                key = f"{card.rank}{card.suit}"
                card_counts[key] = card_counts.get(key, 0) + 1

        # Should be 52 unique cards
        assert len(card_counts) == 52
        assert all(count == 1 for count in card_counts.values())

    def test_constrained_deal_impossible_constraints(self):
        """Test that truly impossible constraints eventually raise an error."""
        # Use constraints that are impossible even with retry widening
        constraints = {
            'S': {'hcp_range': (38, 40)},  # Truly impossible - max HCP in a hand is 37
            'N': None,
            'E': None,
            'W': None
        }

        with pytest.raises(ValueError):
            DealGenerator.generate_constrained_deal(constraints)

    def test_generate_for_contract_slam(self):
        """Test generating hands for slam contract."""
        hands = DealGenerator.generate_for_contract("6♠", "S")

        # Should have significant combined strength (allow for distribution)
        total_hcp = hands['S'].hcp + hands['N'].hcp
        assert total_hcp >= 25  # Slam-level strength (with distribution)

        # Should have spade fit
        total_spades = hands['S'].suit_lengths['♠'] + hands['N'].suit_lengths['♠']
        assert total_spades >= 8

    def test_generate_for_contract_partscore(self):
        """Test generating hands for partscore contract."""
        hands = DealGenerator.generate_for_contract("2♥", "S")

        # Check that hands are generated (no crash)
        assert len(hands) == 4
        assert all(pos in hands for pos in ['N', 'E', 'S', 'W'])
