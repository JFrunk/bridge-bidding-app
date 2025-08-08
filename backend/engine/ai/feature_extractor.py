from engine.hand import Hand

def extract_features(hand: Hand, auction_history: list, my_position: str):
    positions = ['North', 'East', 'South', 'West']
    my_index = positions.index(my_position)
    partner_position = positions[(my_index + 2) % 4]
    
    opening_bid, opener, opener_relationship = None, None, None
    partner_bids = []
    
    for i, bid in enumerate(auction_history):
        if bid != 'Pass' and not opening_bid:
            opening_bid = bid
            opener = positions[i % 4]
        if positions[i % 4] == partner_position:
            partner_bids.append(bid)

    if opener:
        if opener == partner_position: opener_relationship = 'Partner'
        elif opener == my_position: opener_relationship = 'Me'
        else: opener_relationship = 'Opponent'

    partner_last_bid = next((bid for bid in reversed(partner_bids) if bid != 'Pass'), None)

    return {
        'hand_features': { 'hcp': hand.hcp, 'dist_points': hand.dist_points, 'total_points': hand.total_points, 'suit_lengths': hand.suit_lengths, 'is_balanced': hand.is_balanced },
        'auction_features': { 'num_bids': len(auction_history), 'opening_bid': opening_bid, 'opener': opener, 'opener_relationship': opener_relationship, 'partner_bids': partner_bids, 'partner_last_bid': partner_last_bid },
        'auction_history': auction_history,
        'hand': hand 
    }