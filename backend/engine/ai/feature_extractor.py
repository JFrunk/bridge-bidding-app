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

    # Detect interference (RHO's bid between partner's opening and my response)
    interference = _detect_interference(auction_history, positions, my_index, opener_relationship, opener_index)

    return {
        'hand_features': { 'hcp': hand.hcp, 'dist_points': hand.dist_points, 'total_points': hand.total_points, 'suit_lengths': hand.suit_lengths, 'is_balanced': hand.is_balanced },
        'auction_features': { 'num_bids': len(auction_history), 'opening_bid': opening_bid, 'opener': opener, 'opener_relationship': opener_relationship, 'partner_bids': partner_bids, 'partner_last_bid': partner_last_bid, 'opener_last_bid': opener_last_bid, 'opener_index': opener_index, 'is_contested': is_contested, 'vulnerability': vulnerability, 'interference': interference },
        'auction_history': auction_history, 'hand': hand, 'my_index': my_index, 'positions': positions
    }

def _detect_interference(auction_history, positions, my_index, opener_relationship, opener_index):
    """
    Detect if there was interference (opponent's bid) between partner's opening and my first response.

    Returns dict with:
        - present: bool (True if RHO made a bid)
        - bid: str (the interference bid, e.g., '2♦')
        - level: int (bid level, e.g., 2)
        - type: str ('double', 'suit_overcall', 'nt_overcall', 'none')
    """
    interference = {
        'present': False,
        'bid': None,
        'level': None,
        'type': 'none'
    }

    # Only check for interference if partner opened (not opponent, not me)
    if opener_relationship != 'Partner':
        return interference

    # My RHO (right-hand opponent) is the player immediately after the opener
    rho_index = (opener_index + 1) % 4

    # Check if RHO made a bid (not Pass) after the opening
    if len(auction_history) > opener_index + 1:
        rho_bid = auction_history[opener_index + 1]

        if rho_bid != 'Pass':
            interference['present'] = True
            interference['bid'] = rho_bid

            # Classify the interference
            if rho_bid == 'X':
                interference['type'] = 'double'
                interference['level'] = 0  # Special case for double
            elif rho_bid == 'XX':
                interference['type'] = 'redouble'
                interference['level'] = 0
            elif 'NT' in rho_bid:
                interference['type'] = 'nt_overcall'
                interference['level'] = int(rho_bid[0])
            elif len(rho_bid) >= 2 and rho_bid[0].isdigit():
                interference['type'] = 'suit_overcall'
                interference['level'] = int(rho_bid[0])

    return interference