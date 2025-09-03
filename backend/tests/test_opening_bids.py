from engine.hand import Hand, Card
from engine.opening_bids import OpeningBidsModule

def test_1nt_opening():
    """Tests that a 16 HCP balanced hand correctly opens 1NT."""
    cards = [
        Card('A','♠'), Card('K','♠'), Card('2','♠'),
        Card('A','♥'), Card('K','♥'), Card('3','♥'),
        Card('A','♦'), Card('K','♦'), Card('3','♦'),
        Card('J','♣'), Card('T','♣'), Card('2','♣'), Card('4','♣')
    ] # 16 HCP, Balanced (3-3-3-4 shape)
    hand = Hand(cards)
    specialist = OpeningBidsModule()
    result = specialist.evaluate(hand, {})
    assert result is not None
    assert result[0] == "1NT"

def test_strong_2nt_opening():
    """Tests that a 21 HCP balanced hand correctly opens 2NT."""
    cards = [
        Card('A','♠'), Card('K','♠'), Card('Q','♠'),
        Card('A','♥'), Card('K','♥'), Card('Q','♥'),
        Card('A','♦'), Card('K','♦'), Card('2','♦'),
        Card('A','♣'), Card('K','♣'), Card('2','♣'), Card('3','♣')
    ] # 21 HCP, Balanced (3-3-3-4 shape)
    hand = Hand(cards)
    specialist = OpeningBidsModule()
    result = specialist.evaluate(hand, {})
    assert result is not None
    assert result[0] == "2NT"

def test_strong_2c_opening():
    """Tests that a 23 HCP hand correctly opens 2C."""
    cards = [
        Card('A','♠'), Card('K','♠'), Card('Q','♠'), Card('J','♠'),
        Card('A','♥'), Card('K','♥'), Card('Q','♥'),
        Card('A','♦'), Card('K','♦'), Card('Q','♦'),
        Card('A','♣'), Card('K','♣'), Card('2','♣')
    ] # 23 HCP
    hand = Hand(cards)
    specialist = OpeningBidsModule()
    result = specialist.evaluate(hand, {})
    assert result is not None
    assert result[0] == "2♣"