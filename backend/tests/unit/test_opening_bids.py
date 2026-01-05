"""
DEPRECATED: V1 Module Tests (2026-01-05)

These tests directly test V1 OpeningBidsModule which has been deprecated.
V2 Schema Engine is now the default. These tests are skipped.

For V2 opening bid tests, see:
- tests/integration/test_v2_schema_openings.py
- tests/acbl_sayc/test_opening_bids.py (updated for V2)
"""
import pytest

# Skip entire module - V1 has been deprecated
pytestmark = pytest.mark.skip(reason="V1 OpeningBidsModule deprecated - use V2 Schema tests")

from engine.hand import Hand, Card
from engine.opening_bids import OpeningBidsModule

def test_1nt_opening():
    """Tests that a 16 HCP balanced hand correctly opens 1NT."""
    cards = [
        Card('A','♠'), Card('K','♠'), Card('2','♠'),
        Card('Q','♥'), Card('5','♥'), Card('3','♥'),
        Card('A','♦'), Card('K','♦'), Card('3','♦'),
        Card('7','♣'), Card('6','♣'), Card('4','♣'), Card('2','♣')
    ] # 16 HCP, Balanced (A+K=7 spades, Q=2 hearts, A+K=7 diamonds = 16)
    hand = Hand(cards)
    specialist = OpeningBidsModule()
    result = specialist.evaluate(hand, {})
    assert result is not None and result[0] == "1NT"

def test_strong_2nt_opening():
    """Tests that a 23 HCP balanced hand correctly opens 2NT."""
    cards = [
        Card('A','♠'), Card('K','♠'), Card('Q','♠'),
        Card('A','♥'), Card('K','♥'), Card('Q','♥'),
        Card('A','♦'), Card('K','♦'), Card('2','♦'),
        Card('K','♣'), Card('J','♣'), Card('2','♣'), Card('3','♣')
    ] # 23 HCP, Balanced (A+K+Q=9 spades, A+K+Q=9 hearts, A+K=7 diamonds, K+J=4 clubs = 29... no)
    # Try: A+K+Q=9 spades, A+K+Q=9 hearts, A=4 diamonds, K=3 clubs = 25... no
    # Try: A+K+Q=9 spades, A+K=7 hearts, A+K=7 diamonds, K=3 clubs = 26... no
    # 23 HCP: A+K+Q=9 spades, A+K=7 hearts, A+K=7 diamonds = 23!
    cards = [
        Card('A','♠'), Card('K','♠'), Card('Q','♠'),
        Card('A','♥'), Card('K','♥'), Card('5','♥'),
        Card('A','♦'), Card('K','♦'), Card('2','♦'),
        Card('7','♣'), Card('6','♣'), Card('3','♣'), Card('2','♣')
    ] # 23 HCP, Balanced (A+K+Q=9 spades, A+K=7 hearts, A+K=7 diamonds = 23)
    hand = Hand(cards)
    specialist = OpeningBidsModule()
    result = specialist.evaluate(hand, {})
    assert result is not None and result[0] == "2NT"

def test_strong_2c_opening():
    """Tests that a 23 total points hand correctly opens 2C."""
    cards = [
        Card('A','♠'), Card('K','♠'), Card('Q','♠'), Card('J','♠'),
        Card('A','♥'), Card('K','♥'), Card('Q','♥'),
        Card('A','♦'), Card('K','♦'), Card('Q','♦'),
        Card('A','♣'), Card('K','♣'), Card('2','♣')
    ] # 23 HCP
    hand = Hand(cards)
    specialist = OpeningBidsModule()
    result = specialist.evaluate(hand, {})
    assert result is not None and result[0] == "2♣"