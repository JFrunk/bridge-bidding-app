"""
Tests for New Losing Trick Count (NLTC) implementation.

NLTC refines standard LTC with probability-weighted honor adjustments:
- Singleton K: 0.5 losers (probabilistic half-stop)
- Doubleton Q without A/K: 0 winners (full 2 losers, dubious honor)
- Doubleton Q with A or K: 0.5 winners (partial protection)

Verification table frozen to prevent regression during future commits.
"""

import pytest
from engine.hand import Hand, Card
from engine.ai.feature_extractor import (
    _evaluate_suit_losers,
    calculate_losing_trick_count,
)


def make_hand(hand_str):
    """Create hand from string like '♠AKT97 ♥JT76 ♦T9 ♣32'."""
    cards = []
    current_suit = None
    for char in hand_str:
        if char in '♠♥♦♣':
            current_suit = char
        elif char in 'AKQJT98765432':
            cards.append(Card(char, current_suit))
    return Hand(cards)


class TestSuitLosers:
    """Verify _evaluate_suit_losers against first-principle edge cases."""

    # --- Singleton honors ---

    def test_singleton_ace(self):
        assert _evaluate_suit_losers({'A'}, 1) == 0.0

    def test_singleton_king(self):
        """Singleton K: probabilistic half-stop = 0.5 losers."""
        assert _evaluate_suit_losers({'K'}, 1) == 0.5

    def test_singleton_queen(self):
        """Singleton Q: full loser (no protection, no length)."""
        assert _evaluate_suit_losers({'Q'}, 1) == 1.0

    # --- Doubleton combinations ---

    def test_doubleton_ak(self):
        assert _evaluate_suit_losers({'A', 'K'}, 2) == 0.0

    def test_doubleton_aq(self):
        """AQ: Ace protects Queen → 0.5 losers."""
        assert _evaluate_suit_losers({'A', 'Q'}, 2) == 0.5

    def test_doubleton_kq(self):
        """KQ: King protects Queen → 0.5 losers."""
        assert _evaluate_suit_losers({'K', 'Q'}, 2) == 0.5

    def test_doubleton_qx_unprotected(self):
        """Qx without A/K: Q worth 0 winners → 2.0 losers."""
        assert _evaluate_suit_losers({'Q', '5'}, 2) == 2.0

    def test_doubleton_kx(self):
        """Kx: K = 1 winner → 1.0 losers."""
        assert _evaluate_suit_losers({'K', '5'}, 2) == 1.0

    def test_doubleton_ax(self):
        """Ax: A = 1 winner → 1.0 losers."""
        assert _evaluate_suit_losers({'A', '5'}, 2) == 1.0

    def test_doubleton_xx(self):
        assert _evaluate_suit_losers({'5', '3'}, 2) == 2.0

    # --- Three-card suits ---

    def test_akq(self):
        assert _evaluate_suit_losers({'A', 'K', 'Q'}, 3) == 0.0

    def test_akx(self):
        assert _evaluate_suit_losers({'A', 'K', '5'}, 3) == 1.0

    def test_aqx(self):
        """AQx: A + Q(protected by length) → 1.0 losers."""
        assert _evaluate_suit_losers({'A', 'Q', '5'}, 3) == 1.0

    def test_kqx(self):
        """KQx: K + Q(protected by length) → 1.0 losers."""
        assert _evaluate_suit_losers({'K', 'Q', '5'}, 3) == 1.0

    def test_kxx(self):
        assert _evaluate_suit_losers({'K', '5', '3'}, 3) == 2.0

    def test_qxx(self):
        assert _evaluate_suit_losers({'Q', '5', '3'}, 3) == 2.0

    def test_xxx(self):
        assert _evaluate_suit_losers({'5', '3', '2'}, 3) == 3.0

    # --- Longer suits (only first 3 count) ---

    def test_akqxx(self):
        assert _evaluate_suit_losers({'A', 'K', 'Q', '5', '3'}, 5) == 0.0

    def test_axxxx(self):
        assert _evaluate_suit_losers({'A', '5', '4', '3', '2'}, 5) == 2.0

    def test_kj109(self):
        """KJ109: only K matters in top-3 evaluation → 2.0 losers."""
        assert _evaluate_suit_losers({'K', 'J', 'T', '9'}, 4) == 2.0

    # --- Void ---

    def test_void(self):
        assert _evaluate_suit_losers(set(), 0) == 0.0


class TestHandNLTC:
    """Verify full-hand NLTC calculation."""

    def test_near_perfect_hand(self):
        """AKQ in 3 suits + AK doubleton = 0 losers."""
        hand = make_hand("♠AKQ2 ♥AKQ4 ♦AKQ ♣AK")
        # ♠AKQ2=0, ♥AKQ4=0, ♦AKQ=0, ♣AK=0 → 0 total
        assert calculate_losing_trick_count(hand) == 0.0

    def test_yarborough(self):
        """No honors = max losers (12, capped at 3 per suit)."""
        hand = make_hand("♠9876 ♥543 ♦T98 ♣765")
        assert calculate_losing_trick_count(hand) == 12.0

    def test_typical_opening_hand(self):
        """~14 HCP balanced hand: expect 6-8 losers."""
        hand = make_hand("♠AKJ42 ♥KQ3 ♦J72 ♣85")
        ltc = calculate_losing_trick_count(hand)
        assert 5.0 <= ltc <= 8.0, f"Expected 5-8 losers for opening hand, got {ltc}"

    def test_singleton_king_adjustment(self):
        """Hand with singleton K should reflect 0.5 losers in that suit."""
        hand = make_hand("♠AKQ32 ♥K ♦AK42 ♣765")
        ltc = calculate_losing_trick_count(hand)
        # ♠AKQ32=0, ♥K(singleton)=0.5, ♦AK42=1, ♣765=3 → 4.5
        assert ltc == 4.5, f"Expected 4.5, got {ltc}"

    def test_unprotected_queen_adjustment(self):
        """Doubleton Qx without A/K = full 2 losers (not 1.5)."""
        hand = make_hand("♠AK932 ♥Q5 ♦AK42 ♣76")
        ltc = calculate_losing_trick_count(hand)
        # ♠AK932=1, ♥Q5(unprotected)=2, ♦AK42=1, ♣76=2 → 6.0
        assert ltc == 6.0, f"Expected 6.0, got {ltc}"

    def test_return_type_is_float(self):
        """NLTC must return float (not int) due to 0.5 adjustments."""
        hand = make_hand("♠AKQ32 ♥K ♦AK42 ♣765")
        assert isinstance(calculate_losing_trick_count(hand), float)
