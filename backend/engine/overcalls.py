from engine.hand import Hand

def get_overcall(hand: Hand, auction_history: list):
    if not (8 <= hand.hcp <= 16):
        return ("Pass", "Points are outside the 8-16 HCP range for a simple overcall.")
    best_suit_to_bid = None
    for suit in ['♠', '♥', '♦', '♣']:
        if hand.suit_lengths[suit] >= 5:
            honors = {'A', 'K', 'Q', 'J', 'T'}
            suit_cards = [card.rank for card in hand.cards if card.suit == suit]
            honor_count = sum(1 for rank in suit_cards if rank in honors)
            if honor_count >= 2:
                best_suit_to_bid = suit
                break
    if not best_suit_to_bid:
        return ("Pass", "No suitable 5+ card suit to overcall with.")
    opponent_bid = auction_history[-1]
    opponent_level = int(opponent_bid[0])
    if opponent_level == 1:
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
        opponent_suit = opponent_bid[1]
        if opponent_suit in suit_rank and suit_rank[best_suit_to_bid] > suit_rank[opponent_suit]:
            suit_name = {'♠': 'Spade', '♥': 'Heart', '♦': 'Diamond', '♣': 'Club'}[best_suit_to_bid]
            return (f"1{best_suit_to_bid}", f"Overcall. Shows 8-16 HCP and a good 5+ card {suit_name} suit.")
    return ("Pass", "No legal or suitable overcall available.")