from engine.hand import Hand, Card
from engine.ai.conventions.negative_doubles import NegativeDoubleConvention

def test_negative_double_is_applicable():
    """
    Tests that with 8 HCP and 4 hearts after a 1C - 1S auction,
    the correct bid is a Negative Double.
    """
    # Setup: A hand suitable for a negative double
    cards = [
        Card('5','♠'), Card('4','♠'), Card('3','♠'),
        Card('A','♥'), Card('K','♥'), Card('Q','♥'), Card('2','♥'),
        Card('A','♦'), Card('5','♦'), Card('4','♦'),
        Card('T','♣'), Card('9','♣'), Card('8','♣')
    ] # 8 HCP, 4 hearts
    hand = Hand(cards)
    
    # Context: Partner opened 1C, RHO overcalled 1S
    features = {
        'hand': hand,
        'auction_history': ['1♣', '1♠'],
        'my_index': 2, # South's turn
        'positions': ['North', 'East', 'South', 'West'],
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Partner',
        }
    }
    
    specialist = NegativeDoubleConvention()
    result = specialist.evaluate(hand, features)
    
    assert result is not None
    assert result[0] == "X"