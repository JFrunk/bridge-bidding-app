from engine.hand import Hand

def _get_quick_tricks(hand: Hand) -> float:
    """Calculates quick tricks based on Goren's definition."""
    quick_tricks = 0
    for suit in ['♠', '♥', '♦', '♣']:
        honors = {card.rank for card in hand.cards if card.suit == suit}
        if 'A' in honors and 'K' in honors: quick_tricks += 2
        elif 'A' in honors: quick_tricks += 1
        elif 'K' in honors and 'Q' in honors: quick_tricks += 1
        elif 'K' in honors and hand.suit_lengths[suit] > 1: quick_tricks += 0.5
    return quick_tricks

def get_opening_bid(hand: Hand):
    """
    Determines the opening bid based on the provided flowchart logic, with corrected priority.
    """
    adjusted_points = hand.total_points
    is_4333 = sorted(hand.suit_lengths.values()) == [3, 3, 3, 4]
    has_ace = any(card.rank == 'A' for card in hand.cards)
    if is_4333 or not has_ace:
        adjusted_points -= 1

    if adjusted_points < 13 or (adjusted_points == 13 and _get_quick_tricks(hand) < 2.0):
        return ("Pass", "Less than 13-14 points or insufficient quick tricks.")

    if hand.is_balanced:
        if 20 <= hand.hcp <= 21:
            return ("2NT", "Shows a balanced hand with 20-21 HCP.")
        if 15 <= hand.hcp <= 17:
            return ("1NT", "Shows 15-17 HCP and a balanced hand.")
    
    if adjusted_points >= 22:
        return ("2♣", "Strong and artificial. Shows 22+ points.")

    longest_suit_len = max(hand.suit_lengths.values())

    if longest_suit_len >= 6:
        long_suits = [s for s, l in hand.suit_lengths.items() if l >= longest_suit_len]
        long_suit = max(long_suits, key=lambda s: {'♠': 4, '♥': 3, '♦': 2, '♣': 1}.get(s, 0))
        bid_level = ""
        if longest_suit_len == 6: bid_level = "2"
        if longest_suit_len == 7: bid_level = "3"
        if longest_suit_len >= 8: bid_level = "4"
        
        if bid_level and long_suit in ['♠', '♥', '♦']:
             return (f"{bid_level}{long_suit}", f"Opening a strong {longest_suit_len}-card {long_suit} suit.")

    if longest_suit_len >= 5:
        if hand.suit_lengths['♠'] >= 5:
            return ("1♠", f"Shows {adjusted_points} total points and a 5+ card spade suit.")
        if hand.suit_lengths['♥'] >= 5:
            return ("1♥", f"Shows {adjusted_points} total points and a 5+ card heart suit.")
        if hand.suit_lengths['♦'] >= 5 and hand.suit_lengths['♦'] >= hand.suit_lengths['♣']:
             return ("1♦", f"Shows {adjusted_points} total points and a 5+ card diamond suit.")
        if hand.suit_lengths['♣'] >= 5:
             return ("1♣", f"Shows {adjusted_points} total points and a 5+ card club suit.")

    if hand.suit_lengths['♦'] > hand.suit_lengths['♣']:
        return ("1♦", "Shows 12+ points, no 5-card suit. Diamonds is the longer minor.")
    else:
        return ("1♣", "Shows 12+ points, no 5-card suit. Clubs is the longer or equal minor.")