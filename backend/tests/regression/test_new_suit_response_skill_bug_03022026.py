"""
Regression test: NewSuitResponseGenerator bid selection bug (2026-03-02)

User Feedback: "This is contradictory from the advice of going up the line
with major suits. I thought I should start with hearts if I have 4 plus
even with 4 plus spades."

Bug: The 'one_spade_over_minor' variant always returned 1♠ as the expected
bid, even when the generated hand had more hearts than spades (e.g. 6H-4S).
SAYC requires bidding the longer major first.

Hand: ♠J652, ♥Q109865, ♦A6, ♣7 (7 HCP, responding to partner's 1♦)
User bid 1♥ (correct), system said 1♠ was correct (wrong).
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine.hand import Hand, Card
from engine.learning.skill_hand_generators import NewSuitResponseGenerator


def make_hand(spades: str, hearts: str, diamonds: str, clubs: str) -> Hand:
    """Create a Hand from rank strings (e.g. 'AKQ2' for A, K, Q, 2)."""
    cards = []
    for suit, holding in [('♠', spades), ('♥', hearts), ('♦', diamonds), ('♣', clubs)]:
        for rank in holding:
            cards.append(Card(rank, suit))
    return Hand(cards)


class TestNewSuitResponseExpectedBid:
    """Verify get_expected_response() returns correct bid based on hand shape."""

    def test_longer_hearts_over_shorter_spades(self):
        """6 hearts + 4 spades responding to 1♦ → 1♥ (exact user-reported hand)."""
        gen = NewSuitResponseGenerator(variant='one_spade_over_minor')
        hand = make_hand('J652', 'QT9865', 'A6', '7')
        result = gen.get_expected_response(hand)
        assert result['bid'] == '1♥', (
            f"With 6H-4S, should bid 1♥ (longer major), got {result['bid']}"
        )

    def test_longer_spades_over_shorter_hearts(self):
        """5 spades + 4 hearts responding to 1♦ → 1♠."""
        gen = NewSuitResponseGenerator(variant='one_heart_over_minor')
        hand = make_hand('KJ652', 'QT98', 'A6', '73')
        result = gen.get_expected_response(hand)
        assert result['bid'] == '1♠', (
            f"With 5S-4H, should bid 1♠ (longer major), got {result['bid']}"
        )

    def test_equal_length_4_4_bids_hearts_first(self):
        """4 hearts + 4 spades responding to 1♦ → 1♥ (up the line)."""
        gen = NewSuitResponseGenerator(variant='one_spade_over_minor')
        hand = make_hand('KJ52', 'QT98', 'A6', '732')
        result = gen.get_expected_response(hand)
        assert result['bid'] == '1♥', (
            f"With 4H-4S (equal), should bid 1♥ (up the line), got {result['bid']}"
        )

    def test_equal_length_5_5_bids_hearts_first(self):
        """5 hearts + 5 spades responding to 1♦ → 1♥ (up the line)."""
        gen = NewSuitResponseGenerator(variant='one_spade_over_minor')
        hand = make_hand('KJ652', 'QT985', 'A', '72')
        result = gen.get_expected_response(hand)
        assert result['bid'] == '1♥', (
            f"With 5H-5S (equal), should bid 1♥ (up the line), got {result['bid']}"
        )

    def test_spade_over_heart_variant_always_bids_spade(self):
        """Over 1♥ opening, only spades can be shown at 1-level."""
        gen = NewSuitResponseGenerator(variant='one_spade_over_heart')
        hand = make_hand('KJ52', 'Q2', 'AT98', '765')
        result = gen.get_expected_response(hand)
        assert result['bid'] == '1♠'
        assert result['partner_opened'] == '1♥'

    def test_too_weak_passes(self):
        """Under 6 HCP → Pass regardless of suit length."""
        gen = NewSuitResponseGenerator(variant='too_weak')
        hand = make_hand('T9765', 'K43', '942', 'J5')
        result = gen.get_expected_response(hand)
        assert result['bid'] == 'Pass'

    def test_only_hearts_no_spades(self):
        """5 hearts, 2 spades → 1♥ (only biddable major)."""
        gen = NewSuitResponseGenerator(variant='one_heart_over_minor')
        hand = make_hand('Q2', 'KJ985', 'AT9', '765')
        result = gen.get_expected_response(hand)
        assert result['bid'] == '1♥'

    def test_only_spades_no_hearts(self):
        """5 spades, 2 hearts → 1♠ (only biddable major)."""
        gen = NewSuitResponseGenerator(variant='one_spade_over_minor')
        hand = make_hand('KJ985', 'Q2', 'AT9', '765')
        result = gen.get_expected_response(hand)
        assert result['bid'] == '1♠'
