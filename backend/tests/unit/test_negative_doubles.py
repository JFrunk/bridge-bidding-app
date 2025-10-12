from engine.hand import Hand, Card
from engine.ai.conventions.negative_doubles import NegativeDoubleConvention

def test_negative_double_is_applicable():
    """
    Tests that with 8 HCP and 4 hearts after a 1C - 1S auction,
    the correct bid is a Negative Double.
    """
    cards = [
        Card('5','♠'), Card('4','♠'), Card('3','♠'),
        Card('A','♥'), Card('K','♥'), Card('Q','♥'), Card('2','♥'),
        Card('A','♦'), Card('5','♦'), Card('4','♦'),
        Card('T','♣'), Card('9','♣'), Card('8','♣')
    ] # 8 HCP, 4 hearts
    hand = Hand(cards)
    
    features = {
        'hand': hand,
        'auction_history': ['1♣', '1♠'],
        'my_index': 2,
        'positions': ['North', 'East', 'South', 'West'],
        'auction_features': {
            'opening_bid': '1♣',
            'opener_relationship': 'Partner',
            'opener_index': 0,
            'interference': {
                'present': True,
                'type': 'suit_overcall',
                'bid': '1♠',
                'level': 1
            }
        },
    }
    
    specialist = NegativeDoubleConvention()
    result = specialist.evaluate(hand, features)
    
    assert result is not None and result[0] == "X"