from engine.hand import Hand, Card
from engine.responses import ResponseModule

def test_simple_raise_of_major():
    """Tests 1S -> 2S simple raise."""
    cards = [
        Card('Q','♠'), Card('J','♠'), Card('2','♠'),
        Card('K','♥'), Card('5','♥'), Card('4','♥'),
        Card('Q','♦'), Card('5','♦'), Card('4','♦'),
        Card('J','♣'), Card('T','♣'), Card('2','♣'), Card('3','♣')
    ] # 8 HCP, 3-card spade support
    hand = Hand(cards)
    features = {
        'auction_features': {
            'opening_bid': '1♠',
            'opener_relationship': 'Partner',
            'opener_index': 0,
            'interference': {'present': False}
        },
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 2,
        'auction_history': ['1♠', 'Pass']
    }
    specialist = ResponseModule()
    result = specialist.evaluate(hand, features)
    assert result is not None and result[0] == "2♠"

def test_respond_to_2c_negative():
    """Tests 2C -> 2D negative response."""
    cards = [
        Card('T','♠'), Card('9','♠'), Card('8','♠'),
        Card('7','♥'), Card('6','♥'), Card('5','♥'),
        Card('4','♦'), Card('3','♦'), Card('2','♦'),
        Card('T','♣'), Card('9','♣'), Card('8','♣'), Card('7','♣')
    ] # 0 HCP
    hand = Hand(cards)
    features = {
        'auction_features': {
            'opening_bid': '2♣',
            'opener_relationship': 'Partner',
            'opener_index': 0,
            'interference': {'present': False}
        },
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 2,
        'auction_history': ['2♣', 'Pass']
    }
    specialist = ResponseModule()
    result = specialist.evaluate(hand, features)
    assert result is not None and result[0] == "2♦"