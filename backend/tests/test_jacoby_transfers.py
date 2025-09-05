from engine.hand import Hand, Card
from engine.ai.conventions.jacoby_transfers import JacobyConvention

def test_initiate_transfer_to_spades():
    """Tests responding to 1NT with a 2H transfer bid."""
    cards = [
        Card('K','♠'), Card('Q','♠'), Card('T','♠'), Card('9','♠'), Card('8','♠'),
        Card('7','♥'), Card('6','♥'),
        Card('5','♦'), Card('4','♦'), Card('3','♦'),
        Card('4','♣'), Card('3','♣'), Card('2','♣')
    ] # 5 HCP, 5-card spade suit
    hand = Hand(cards)
    features = {
        'hand': hand,
        'auction_features': {'opening_bid': '1NT', 'opener_relationship': 'Partner'},
        'auction_history': ['1NT', 'Pass']
    }
    specialist = JacobyConvention()
    result = specialist.evaluate(hand, features)
    assert result is not None and result[0] == "2♥"