from engine.hand import Hand

def get_openers_rebid(hand: Hand, auction_history: list):
    """
    Determines the opener's rebid with corrected logic for strong hands.
    """
    partner_response = next((bid for bid in reversed(auction_history[1::2]) if bid != 'Pass'), None)
    my_opening_bid = next((bid for bid in auction_history[::2] if bid != 'Pass'), None)

    if not partner_response or not my_opening_bid:
        return ("Pass", "Cannot determine auction context for rebid.")
        
    # --- LOGIC FOR REBIDS AFTER A 2 CLUB OPENING ---
    if my_opening_bid == '2♣':
        if partner_response == '2♦':
            if 22 <= hand.hcp <= 24 and hand.is_balanced:
                return ("2NT", "Shows a balanced hand with 22-24 HCP.")
            best_suit = max(hand.suit_lengths, key=hand.suit_lengths.get)
            if hand.suit_lengths[best_suit] >= 5:
                bid_level = '3' if best_suit in ['♣', '♦'] else '2'
                return (f"{bid_level}{best_suit}", f"Shows a strong hand with a long {best_suit} suit.")
        if partner_response == '2NT':
            best_suit = max(hand.suit_lengths, key=hand.suit_lengths.get)
            if hand.suit_lengths[best_suit] >= 5:
                return (f"3{best_suit}", f"Showing my long {best_suit} suit.")

    # --- LOGIC FOR REBIDS AFTER A 1-LEVEL OPENING ---
    # Minimum Hand: 13-15 total points
    if 13 <= hand.total_points <= 15:
        if partner_response.endswith(my_opening_bid[1]):
            return ("Pass", "Minimum hand (13-15 pts), passing partner's simple raise.")
        if partner_response == "1NT":
            second_suits = [s for s, l in hand.suit_lengths.items() if l >= 4 and s != my_opening_bid[1]]
            if second_suits:
                return (f"2{second_suits[0]}", f"Minimum hand (13-15 pts) showing a second suit.")
            if hand.suit_lengths.get(my_opening_bid[1], 0) >= 6:
                return (f"2{my_opening_bid[1]}", f"Minimum hand (13-15 pts) rebidding a 6+ card suit.")
            return (f"2{my_opening_bid[1]}", f"Minimum hand (13-15 pts) rebidding a 5-card suit.")
        if partner_response[0] == '1' and len(partner_response) == 2:
            partner_suit = partner_response[1]
            if hand.suit_lengths.get(partner_suit, 0) >= 4:
                return (f"2{partner_suit}", f"Minimum hand (13-15 pts) showing 4+ card support.")
            if hand.is_balanced:
                return ("1NT", "Minimum hand (12-14 HCP), balanced, no fit for partner's suit.")

    # Medium Hand: 16-18 total points
    elif 16 <= hand.total_points <= 18:
        if partner_response.endswith(my_opening_bid[1]):
            return (f"3{my_opening_bid[1]}", "Invitational (16-18 pts), raising partner's simple raise.")
        if partner_response[0] == '1' and len(partner_response) == 2:
            partner_suit = partner_response[1]
            if hand.suit_lengths.get(partner_suit, 0) >= 4:
                return (f"3{partner_suit}", f"Invitational (16-18 pts) jump raise showing 4+ card support.")
        if hand.suit_lengths.get(my_opening_bid[1], 0) >= 6:
            return (f"3{my_opening_bid[1]}", f"Invitational (16-18 pts) jump rebid of a 6+ card suit.")
        return ("2NT", "Shows a strong hand (16-18 pts) with no obvious fit.")

    # Strong Hand: 19+ total points
    elif hand.total_points >= 19:
        # CORRECTED LOGIC: First, check if partner has raised our suit
        if partner_response.endswith(my_opening_bid[1]):
            partner_suit = my_opening_bid[1]
            if partner_suit in ['♥', '♠']:
                return (f"4{partner_suit}", f"Strong hand ({hand.total_points} pts), bidding game after partner's raise.")
        
        # If partner bid a new suit and we have a fit
        if len(partner_response) == 2:
            partner_suit = partner_response[1]
            if partner_suit in ['♥', '♠'] and hand.suit_lengths.get(partner_suit, 0) >= 4:
                return (f"4{partner_suit}", f"Strong hand ({hand.total_points} pts), bidding game with a fit.")
        
        # Default for strong hands is to bid game in NT
        return ("3NT", f"Strong hand ({hand.total_points} pts), bidding game in No-Trump.")

    return ("Pass", "No clear rebid available.")