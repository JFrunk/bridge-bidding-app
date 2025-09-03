from engine.hand import Hand

def extract_features(hand: Hand, auction_history: list, my_position: str, vulnerability: str):
    positions = ['North', 'East', 'South', 'West']
    my_index = positions.index(my_position)
    partner_position = positions[(my_index + 2) % 4]
    
    opening_bid, opener, opener_relationship = None, None, None
    opener_index = -1
    partner_bids, opener_bids = [], []
    is_contested = False
    
    north_south_bids, east_west_bids = False, False
    for i, bid in enumerate(auction_history):
        bidder = positions[i % 4]
        if bid != 'Pass':
            if bidder in ['North', 'South']: north_south_bids = True
            if bidder in ['East', 'West']: east_west_bids = True
        if bid != 'Pass' and not opening_bid:
            opening_bid, opener, opener_index = bid, bidder, i % 4
        if bidder == partner_position: partner_bids.append(bid)
        if bidder == opener: opener_bids.append(bid)
    
    if north_south_bids and east_west_bids: is_contested = True

    if opener:
        if opener == partner_position: opener_relationship = 'Partner'
        elif opener == my_position: opener_relationship = 'Me'
        else: opener_relationship = 'Opponent'

    partner_last_bid = next((bid for bid in reversed(partner_bids) if bid != 'Pass'), None)
    opener_last_bid = next((bid for bid in reversed(opener_bids) if bid != 'Pass'), None)

    return {
        'hand_features': { 'hcp': hand.hcp, 'dist_points': hand.dist_points, 'total_points': hand.total_points, 'suit_lengths': hand.suit_lengths, 'is_balanced': hand.is_balanced },
        'auction_features': { 'num_bids': len(auction_history), 'opening_bid': opening_bid, 'opener': opener, 'opener_relationship': opener_relationship, 'partner_bids': partner_bids, 'partner_last_bid': partner_last_bid, 'opener_last_bid': opener_last_bid, 'opener_index': opener_index, 'is_contested': is_contested, 'vulnerability': vulnerability },
        'auction_history': auction_history, 'hand': hand, 'my_index': my_index, 'positions': positions
    }