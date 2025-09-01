from engine.hand import Hand

def _calculate_support_points(hand: Hand, trump_suit: str) -> int:
    """Calculates total points including short-suit points for a fit."""
    points = hand.hcp
    for suit, length in hand.suit_lengths.items():
        if suit != trump_suit:
            if length == 1: points += 3 # Singleton
            if length == 0: points += 5 # Void
    return points

def _find_best_new_suit_to_bid(hand: Hand, opening_bid: str):
    """Finds the best new suit to bid, prioritizing majors."""
    if opening_bid in ['1♣', '1♦']:
        if hand.suit_lengths['♥'] >= 4: return "1♥"
        if hand.suit_lengths['♠'] >= 4: return "1♠"
    elif opening_bid == '1♥' and hand.suit_lengths['♠'] >= 4:
        return "1♠"
    if hand.total_points >= 10:
        if hand.suit_lengths['♦'] >= 4 and opening_bid not in ['1♦']: return "2♦"
        if hand.suit_lengths['♣'] >= 4 and opening_bid not in ['1♣']: return "2♣"
    return None

def get_response_bid(responder_hand: Hand, opening_bid: str):
    """Handles the responder's FIRST bid based on all provided flowcharts."""
    try:
        opening_level = int(opening_bid[0])
        if opening_bid == "2♣":
            if responder_hand.hcp >= 8:
                for suit in ['♠', '♥', '♦', '♣']: 
                    if responder_hand.suit_lengths[suit] >= 5:
                        bid_level = '2' if suit in ['♥', '♠'] else '3'
                        return (f"{bid_level}{suit}", "Positive response to 2♣ with a 5+ card suit.")
                return ("2NT", "Positive response to 2♣ showing 8+ HCP, balanced.")
            else:
                return ("2♦", "Artificial. A waiting or 'negative' response to 2♣.")
        if opening_bid in ["2♦", "2♥", "2♠"]:
            if responder_hand.total_points >= 15:
                return ("2NT", "Ogust Convention. Inquiry about preempt strength.")
            preempt_suit = opening_bid[1]
            if responder_hand.suit_lengths[preempt_suit] >= 3 and responder_hand.total_points >= 11:
                return (f"3{preempt_suit}", "Constructive raise of preempt.")
        if opening_level >= 3:
            return ("Pass", "Partner has preempted at the 3+ level. Passing.")
    except (ValueError, IndexError):
        pass

    if responder_hand.total_points < 6:
        return ("Pass", "Less than 6 total points.")
        
    opening_suit = opening_bid[1]
    
    if responder_hand.suit_lengths[opening_suit] >= 3:
        support_points = _calculate_support_points(responder_hand, opening_suit)
        has_singleton_or_void = 1 in responder_hand.suit_lengths.values() or 0 in responder_hand.suit_lengths.values()
        if support_points >= 12 and has_singleton_or_void:
             return (f"4{opening_suit}", "Splinter. Jumping to game with excellent support and a short suit.")
        if 10 <= support_points <= 11:
            return (f"3{opening_suit}", f"Invitational raise showing 10-11 support points.")
        return (f"2{opening_suit}", f"Simple raise showing 6-9 support points.")

    best_new_suit = _find_best_new_suit_to_bid(responder_hand, opening_bid)
    if best_new_suit:
        return (best_new_suit, "Showing a new suit.")

    if responder_hand.is_balanced:
        if 16 <= responder_hand.hcp <= 18: return ("3NT", "Shows a balanced 16-18 HCP and no fit.")
        if 13 <= responder_hand.hcp <= 15: return ("2NT", "Shows a balanced 13-15 HCP and no fit.")
        if 6 <= responder_hand.hcp <= 9: return ("1NT", "Shows 6-9 HCP, balanced, and no 4-card major.")
    
    return ("Pass", "No clear response available.")

def get_responder_rebid(hand: Hand, features: dict):
    """Handles the responder's SECOND bid, based on the flowchart."""
    auction_features = features['auction_features']
    
    if 6 <= hand.total_points <= 9:
        if auction_features.get('opener_last_bid') == '1NT':
            return ("Pass", "Minimum hand (6-9 pts), passing opener's 1NT rebid.")
        return ("Pass", "Minimum hand (6-9 pts), no reason to bid further.")
    elif 10 <= hand.total_points <= 11:
        opener_first_suit = auction_features.get('opening_bid')[1]
        if hand.suit_lengths[opener_first_suit] >= 3:
            return (f"3{opener_first_suit}", "Invitational raise (10-11 pts) with trump support.")
        return ("2NT", "Invitational (10-11 pts), suggesting a 3NT contract.")
    elif hand.total_points >= 12:
        opener_first_suit = auction_features.get('opening_bid')[1]
        if hand.suit_lengths[opener_first_suit] >= 3:
            return (f"4{opener_first_suit}", "Game-forcing (12+ pts) with a fit.")
        return ("3NT", "Game-forcing (12+ pts), bidding game in No-Trump.")
    return ("Pass", "No clear rebid for responder.")