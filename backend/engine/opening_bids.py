from engine.hand import Hand

def get_opening_bid(hand: Hand):
    """Determines the correct opening bid and provides an explanation."""

    # Rule 1: Check for very strong hands first.
    if hand.total_points >= 22:
        return ("2♣", "Strong and artificial. Shows 22+ total points, game forcing.")
    
    # Rule 2: Check for a 2NT opening.
    if 20 <= hand.hcp <= 21 and hand.is_balanced:
        return ("2NT", "Shows a balanced hand with 20-21 HCP.")
    
    # Rule 3: Check for a standard 1NT opening.
    if 15 <= hand.hcp <= 17 and hand.is_balanced:
        return ("1NT", "Shows 15-17 HCP and a balanced hand.")
    
    # Rule 4: Check for a one-level suit opening (12+ points).
    if hand.total_points >= 12:
        has_5_card_spades = hand.suit_lengths['♠'] >= 5
        has_5_card_hearts = hand.suit_lengths['♥'] >= 5
        
        if has_5_card_spades or has_5_card_hearts:
            if has_5_card_spades and (hand.suit_lengths['♠'] >= hand.suit_lengths['♥']):
                return ("1♠", "Shows 12+ points and a 5+ card spade suit.")
            return ("1♥", "Shows 12+ points and a 5+ card heart suit.")
        
        if hand.suit_lengths['♦'] > hand.suit_lengths['♣']:
            return ("1♦", "Shows 12+ points and no 5-card major. Diamonds is the longer minor.")
        return ("1♣", "Shows 12+ points and no 5-card major. Clubs is the longer or equal minor.")

    # Rule 5: If no other rule applies, pass.
    return ("Pass", "Less than 12 total points.")