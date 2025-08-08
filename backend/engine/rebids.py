from engine.hand import Hand

def get_openers_rebid(hand: Hand, auction_history: list):
    """
    Determines the opener's rebid, now with logic for a 2 Club opening.
    """
    partner_response = next((bid for bid in reversed(auction_history[1::2]) if bid != 'Pass'), None)
    my_opening_bid = next((bid for bid in auction_history[::2] if bid != 'Pass'), None)

    if not partner_response or not my_opening_bid:
        return ("Pass", "Cannot determine auction context for rebid.")

    # --- NEW LOGIC FOR 2 CLUB REBID ---
    if my_opening_bid == '2♣' and partner_response == '2♦':
        # After the waiting response, describe the strong hand.
        if 22 <= hand.hcp <= 24 and hand.is_balanced:
            return ("2NT", "Shows a balanced hand with 22-24 HCP.")
        
        # Find the best 5+ card suit to show.
        best_suit = None
        best_length = 4
        for suit, length in hand.suit_lengths.items():
            if length > best_length:
                best_length = length
                best_suit = suit
        if best_suit:
            # A simple rebid of the long suit.
            return (f"2{best_suit}", f"Shows a strong hand with a long {best_suit} suit.")

    # --- EXISTING LOGIC FOR OTHER REBIDS ---
    try:
        response_level = int(partner_response[0])
        response_suit = partner_response[1]
    except (ValueError, IndexError):
        return ("Pass", "Partner's response was not a standard suit bid.")
    
    my_opening_suit = my_opening_bid[1]
    
    if response_suit == my_opening_suit and my_opening_suit in ['♥', '♠']:
        partner_points_min = 0
        if response_level == 2: partner_points_min = 6
        if response_level == 3: partner_points_min = 10

        if hand.total_points + partner_points_min >= 25:
            game_bid = f"4{my_opening_suit}"
            return (game_bid, f"Accepting the invitation to game with {hand.total_points} points.")
        
        if hand.total_points + partner_points_min >= 23:
            invitational_bid = f"3{my_opening_suit}"
            return (invitational_bid, f"Inviting to game with a strong hand ({hand.total_points} points).")
        
        return ("Pass", f"With a minimum hand ({hand.total_points} points), I will not bid further.")

    if partner_response in ['1♥', '1♠']:
        suit_of_response = partner_response[1]
        if hand.suit_lengths[suit_of_response] >= 4:
            if 12 <= hand.total_points <= 15:
                return (f"2{suit_of_response}", f"Shows 12-15 points and 4+ card support for partner's major.")
            if 16 <= hand.total_points <= 18:
                return (f"3{suit_of_response}", f"Invitational. Shows 16-18 points and 4+ card support.")

    for suit, length in hand.suit_lengths.items():
        if length >= 6:
            if 12 <= hand.total_points <= 15:
                 return (f"2{suit}", f"Shows a minimum opening hand with a 6+ card suit.")
            if 16 <= hand.total_points <= 18:
                 return (f"3{suit}", f"Invitational. Shows 16-18 points with a 6+ card suit.")
    
    return ("Pass", "No clear rebid available.")