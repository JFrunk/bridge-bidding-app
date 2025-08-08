from engine.hand import Hand

def get_response_bid(responder_hand: Hand, opening_bid: str):
    """Determines the response to a partner's opening bid and explains it."""

    # --- NEW LOGIC FOR STRONG OPENINGS ---
    # Rule for responding to a 2 Club opening
    if opening_bid == "2♣":
        # Any hand with fewer than 8 points makes a "waiting" bid.
        # (A hand with 8+ HCP would have a different, positive response)
        if responder_hand.hcp < 8:
            return ("2♦", "Artificial. A waiting or 'negative' response to 2♣, showing less than 8 HCP.")

    # Rule for responding to a 2NT opening (placeholder for now)
    if opening_bid == "2NT":
        # The system for responding to 2NT is complex (e.g., 3-level Stayman).
        # For now, we will pass to prevent errors, but this can be a future feature.
        return ("Pass", "System is not yet equipped for 2NT responses.")

    # --- EXISTING LOGIC FOR ONE-LEVEL OPENINGS ---
    if opening_bid in ["1♥", "1♠"]:
        opening_suit = opening_bid[1]
        suit_name = {'♠': 'Spade', '♥': 'Heart'}[opening_suit]
        if responder_hand.suit_lengths[opening_suit] >= 3:
            if 6 <= responder_hand.total_points <= 10:
                return (f"2{opening_suit}", f"Shows 6-10 points and 3+ card support for {suit_name}s.")
            if 11 <= responder_hand.total_points <= 12:
                return (f"3{opening_suit}", f"Invitational. Shows 11-12 points and 3+ card support for {suit_name}s.")
        if 6 <= responder_hand.total_points and responder_hand.suit_lengths['♠'] >= 4 and opening_bid == "1♥":
            return ("1♠", "Shows 6+ points and a 4+ card spade suit.")
        return ("Pass", "Not enough strength or fit to respond.")
    
    if opening_bid == "1NT":
        if responder_hand.hcp >= 8 and (responder_hand.suit_lengths['♥'] >= 4 or responder_hand.suit_lengths['♠'] >= 4):
            return ("2♣", "Stayman. Asks partner for a 4-card major.")
        return ("Pass", "Less than 8 points. Not enough to respond to 1NT.")
    
    return ("Pass", "No suitable response.")