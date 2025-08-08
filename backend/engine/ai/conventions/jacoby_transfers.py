from engine.hand import Hand

def get_jacoby_transfer_bid(hand: Hand):
    if hand.suit_lengths['♥'] >= 5:
        return ("2♦", "Jacoby Transfer showing 5+ Hearts.")
    if hand.suit_lengths['♠'] >= 5:
        return ("2♥", "Jacoby Transfer showing 5+ Spades.")
    return None