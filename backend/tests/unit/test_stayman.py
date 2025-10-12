from engine.hand import Hand, Card
from engine.ai.conventions.stayman import StaymanConvention

def test_should_initiate_stayman():
    """Tests that a hand with 9 HCP and a 4-card major bids 2C over 1NT."""
    cards = [
        Card('K','♠'), Card('Q','♠'), Card('J','♠'), Card('9','♠'),
        Card('A','♥'), Card('5','♥'), Card('4','♥'),
        Card('7','♦'), Card('6','♦'), Card('5','♦'),
        Card('3','♣'), Card('2','♣'), Card('T','♣')
    ] # 9 HCP, 4 spades
    hand = Hand(cards)
    features = {
        'hand': hand, 'hand_features': {'hcp': 9, 'suit_lengths': hand.suit_lengths},
        'auction_features': {'opening_bid': '1NT', 'opener_relationship': 'Partner'},
        'auction_history': ['1NT', 'Pass']
    }
    specialist = StaymanConvention()
    result = specialist.evaluate(hand, features)
    assert result is not None and result[0] == "2♣"