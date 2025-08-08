from engine.ai.conventions.jacoby_transfers import get_jacoby_transfer_bid

def select_bidding_module(features):
    """
    Looks at the features and decides which bidding logic to use, with corrected priority.
    """
    
    hand = features['hand']
    hand_features = features['hand_features']
    auction_features = features['auction_features']
    
    # Rule 1: Is this an opening bid?
    if not auction_features['opener']:
        return 'opening_bids'
    
    # Rule 2: Am I the opener? Check for rebids, starting with the MOST SPECIFIC cases first.
    if auction_features['opener_relationship'] == 'Me':
        # HIGHEST PRIORITY: Check for transfer completion after a 1NT opening.
        if auction_features['opening_bid'] == '1NT':
            partner_last_bid = auction_features['partner_last_bid']
            if partner_last_bid in ['2♦', '2♥']:
                return 'transfer_completion'
        
        # NEXT PRIORITY: Is this a general rebid after partner's first response?
        if len(auction_features['partner_bids']) == 1:
            return 'openers_rebid'

    # Rule 3: Is my partner the opener? Check for responses.
    if auction_features['opener_relationship'] == 'Partner':
        # Did partner open 1NT? Check for conventions.
        if auction_features['opening_bid'] == '1NT':
            transfer_bid = get_jacoby_transfer_bid(hand)
            if transfer_bid: return 'jacoby_transfers'
            if hand_features['hcp'] >= 8 and (hand_features['suit_lengths']['♥'] >= 4 or hand_features['suit_lengths']['♠'] >= 4):
                return 'stayman_response'

        # Is this a simple response to a suit opening?
        if len(auction_features['partner_bids']) == 1:
            return 'responses'
    
    # Rule 4: Is this an overcall situation?
    if auction_features['opener_relationship'] == 'Opponent':
        non_pass_bids = [bid for bid in features['auction_history'] if bid != "Pass"]
        if len(non_pass_bids) == 1: return 'overcalls'
            
    return 'pass_by_default'