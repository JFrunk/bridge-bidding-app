from engine.ai.conventions import jacoby_transfers, stayman # NEW: import stayman

def select_bidding_module(features):
    auction_features = features['auction_features']

    # --- CONVENTIONAL BIDS (HIGHEST PRIORITY) ---
    
    # Check for responses to 1NT opening
    if auction_features['opening_bid'] == '1NT':
        # Check if the Jacoby specialist has a valid move
        jacoby_bid = jacoby_transfers.evaluate(features['hand'], features)
        if jacoby_bid:
            return ('convention_bid', jacoby_bid)
        
        # If not, check if the Stayman specialist has a valid move
        stayman_bid = stayman.evaluate(features['hand'], features)
        if stayman_bid:
            return ('convention_bid', stayman_bid)

    # --- NATURAL BIDS (LOWER PRIORITY) ---
    if not auction_features['opener']: return ('natural_bid', 'opening_bids')
    if auction_features['opener_relationship'] == 'Me' and len(auction_features['partner_bids']) == 1:
        return ('natural_bid', 'openers_rebid')
    if auction_features['opener_relationship'] == 'Opponent':
        non_pass_bids = [bid for bid in features['auction_history'] if bid != "Pass"]
        if len(non_pass_bids) == 1: return ('natural_bid', 'overcalls')
    if auction_features['opener_relationship'] == 'Partner':
        if len(auction_features['partner_bids']) == 1: return ('natural_bid', 'responses')
            
    return ('natural_bid', 'pass_by_default')