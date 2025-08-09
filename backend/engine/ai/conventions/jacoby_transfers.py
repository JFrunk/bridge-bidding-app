from engine.hand import Hand

def evaluate(hand: Hand, features: dict):
    """
    Master function for the Jacoby Transfer convention.
    Handles both initiating and completing the transfer.
    """
    auction_features = features['auction_features']
    auction_history = features['auction_history']

    # --- LOGIC FOR COMPLETING a transfer ---
    if auction_features['opener_relationship'] == 'Me' and auction_features['opening_bid'] == '1NT':
        partner_last_bid = auction_features['partner_last_bid']
        
        # Partner transferred to Hearts (bid 2 Diamonds)
        if partner_last_bid == "2♦":
            # With a maximum hand (17-18 pts) and only 2 hearts, bid 2NT
            if hand.hcp >= 17 and hand.suit_lengths['♥'] == 2:
                return ("2NT", "Maximum 1NT opening (17-18 HCP) with no fit for Hearts.")
            # Otherwise, complete the transfer normally
            return ("2♥", "Completing the transfer to Hearts.")

        # Partner transferred to Spades (bid 2 Hearts)
        if partner_last_bid == "2♥":
            # With a maximum hand (17-18 pts) and only 2 spades, bid 2NT
            if hand.hcp >= 17 and hand.suit_lengths['♠'] == 2:
                return ("2NT", "Maximum 1NT opening (17-18 HCP) with no fit for Spades.")
            # Otherwise, complete the transfer normally
            return ("2♠", "Completing the transfer to Spades.")

    # --- LOGIC FOR INITIATING a transfer ---
    if auction_features['opening_bid'] == '1NT' and auction_features['opener_relationship'] == 'Partner':
        non_pass_bids = [bid for bid in auction_history if bid != 'Pass']
        if len(non_pass_bids) == 1:
            if hand.suit_lengths['♥'] >= 5:
                return ("2♦", "Jacoby Transfer showing 5+ Hearts.")
            if hand.suit_lengths['♠'] >= 5:
                return ("2♥", "Jacoby Transfer showing 5+ Spades.")

    return None # Convention is not applicable