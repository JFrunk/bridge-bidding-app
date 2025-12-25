from engine.hand import Hand
from engine.ai.auction_context import analyze_auction_context

def extract_features(hand: Hand, auction_history: list, my_position: str, vulnerability: str, dealer: str = 'North'):
    """
    Extract features from a hand and auction for bidding decision.

    Args:
        hand: The player's hand
        auction_history: List of bids in order (starting from dealer)
        my_position: Position of player making the bid (North/East/South/West)
        vulnerability: Vulnerability status
        dealer: Who dealt (default 'North' for backward compatibility)
               IMPORTANT: The auction_history is ordered starting from dealer!
               So auction_history[0] is dealer's bid, auction_history[1] is dealer+1's bid, etc.
    """
    # Standard position order - but we need to rotate based on dealer
    base_positions = ['North', 'East', 'South', 'West']
    dealer_idx = base_positions.index(dealer)

    # Create positions list starting from dealer
    # This means positions[i] gives us who made auction_history[i]
    positions = [base_positions[(dealer_idx + i) % 4] for i in range(4)]

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

    # Expert-level auction context with range tracking
    auction_context = analyze_auction_context(auction_history, positions, my_index)

    return {
        'hand_features': { 'hcp': hand.hcp, 'dist_points': hand.dist_points, 'total_points': hand.total_points, 'suit_lengths': hand.suit_lengths, 'is_balanced': hand.is_balanced },
        'auction_features': { 'num_bids': len(auction_history), 'opening_bid': opening_bid, 'opener': opener, 'opener_relationship': opener_relationship, 'partner_bids': partner_bids, 'partner_last_bid': partner_last_bid, 'opener_last_bid': opener_last_bid, 'opener_index': opener_index, 'is_contested': is_contested, 'vulnerability': vulnerability, 'interference': interference },
        'auction_history': auction_history, 'hand': hand, 'my_index': my_index, 'positions': positions,
        'auction_context': auction_context
    }

def _detect_interference(auction_history, positions, my_index, opener_relationship, opener_index):
    """
    Detect if there was interference (opponent's bid) between partner's opening and my first response.

    Returns dict with:
        - present: bool (True if opponent made a bid)
        - bid: str (the interference bid, e.g., '2♦')
        - level: int (bid level, e.g., 2)
        - type: str ('double', 'suit_overcall', 'nt_overcall', 'none')
        - position: int (auction index where interference occurred)
    """
    interference = {
        'present': False,
        'bid': None,
        'level': None,
        'type': 'none',
        'position': None
    }

    # Only check for interference if partner opened (not opponent, not me)
    if opener_relationship != 'Partner':
        return interference

    # Determine partner's position (opener)
    partner_index = opener_index

    # Determine opponent positions (LHO and RHO)
    lho_index = (partner_index + 1) % 4  # Left-hand opponent
    rho_index = (partner_index + 3) % 4  # Right-hand opponent (or my_index - 1)

    # Search through auction after opening for any opponent bid (not Pass)
    # We check all bids after the opening until we reach our position in the auction
    for auction_idx in range(opener_index + 1, len(auction_history)):
        bidder_position = auction_idx % 4
        bid = auction_history[auction_idx]

        # Check if this bidder is an opponent (LHO or RHO)
        if bidder_position == lho_index or bidder_position == rho_index:
            if bid != 'Pass':
                # Found interference!
                interference['present'] = True
                interference['bid'] = bid
                interference['position'] = auction_idx

                # Classify the interference
                if bid == 'X':
                    interference['type'] = 'double'
                    interference['level'] = 0  # Special case for double
                elif bid == 'XX':
                    interference['type'] = 'redouble'
                    interference['level'] = 0
                elif 'NT' in bid:
                    interference['type'] = 'nt_overcall'
                    interference['level'] = int(bid[0])
                elif len(bid) >= 2 and bid[0].isdigit():
                    interference['type'] = 'suit_overcall'
                    interference['level'] = int(bid[0])

                # Return on first interference found
                return interference

        # Stop if we've reached our position in the auction
        if bidder_position == my_index:
            break

    return interference