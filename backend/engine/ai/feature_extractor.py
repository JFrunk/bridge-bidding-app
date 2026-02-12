from engine.hand import Hand
from engine.ai.auction_context import analyze_auction_context
from engine.ai.bidding_state import BiddingStateBuilder
from typing import Dict

# Seat utilities - for partner/opponent calculations
# This file uses integer indices (0-3) for auction position tracking.
# We use seat_from_index for relative position calculations (partner = +2, LHO = +1, RHO = +3).
from utils.seats import seat_index, seat_from_index, SEATS

# Modulo-4 offsets for relative positions (used throughout this file)
# These match the seats utility: partner=+2, LHO=+1, RHO=+3
PARTNER_OFFSET = 2
LHO_OFFSET = 1
RHO_OFFSET = 3

# =============================================================================
# FUNDAMENTAL BRIDGE METRICS
# These are "first principles" calculations that expert players use instinctively.
# =============================================================================

def calculate_quick_tricks(hand: Hand) -> float:
    """Calculate Quick Tricks (AK=2, AQ=1.5, A=1, KQ=1, Kx=0.5)."""
    qt = 0.0
    for suit in ['♠', '♥', '♦', '♣']:
        suit_cards = [c.rank for c in hand.cards if c.suit == suit]
        length = len(suit_cards)
        has_ace = 'A' in suit_cards
        has_king = 'K' in suit_cards
        has_queen = 'Q' in suit_cards

        if has_ace and has_king:
            qt += 2.0
        elif has_ace and has_queen:
            qt += 1.5
        elif has_ace:
            qt += 1.0
        elif has_king and has_queen:
            qt += 1.0
        elif has_king and length >= 2:
            qt += 0.5
    return qt


def calculate_stoppers(hand: Hand) -> Dict[str, bool]:
    """Calculate which suits are stopped (A, Kx, Qxx, Jxxx, or xxxx length)."""
    stoppers = {}
    for suit in ['♠', '♥', '♦', '♣']:
        suit_cards = [c.rank for c in hand.cards if c.suit == suit]
        length = len(suit_cards)
        has_ace = 'A' in suit_cards
        has_king = 'K' in suit_cards
        has_queen = 'Q' in suit_cards
        has_jack = 'J' in suit_cards

        is_stopped = (
            has_ace or
            (has_king and length >= 2) or
            (has_queen and length >= 3) or
            (has_jack and length >= 4) or
            length >= 4
        )
        stoppers[suit] = is_stopped
    return stoppers


def calculate_stopper_quality(hand: Hand) -> Dict[str, str]:
    """Calculate stopper quality (double/solid/partial/length/none)."""
    quality = {}
    for suit in ['♠', '♥', '♦', '♣']:
        suit_cards = [c.rank for c in hand.cards if c.suit == suit]
        length = len(suit_cards)
        has_ace = 'A' in suit_cards
        has_king = 'K' in suit_cards
        has_queen = 'Q' in suit_cards
        has_jack = 'J' in suit_cards
        has_ten = 'T' in suit_cards

        if has_ace and has_king:
            quality[suit] = 'double'
        elif has_ace and has_queen and has_jack:
            quality[suit] = 'double'
        elif has_king and has_queen and has_jack:
            quality[suit] = 'double'
        elif has_ace:
            quality[suit] = 'solid'
        elif has_king and has_queen:
            quality[suit] = 'solid'
        elif has_king and has_jack and has_ten:
            quality[suit] = 'solid'
        elif has_king and length >= 2:
            quality[suit] = 'partial'
        elif has_queen and length >= 3:
            quality[suit] = 'partial'
        elif has_jack and length >= 4:
            quality[suit] = 'partial'
        elif length >= 4:
            quality[suit] = 'length'
        else:
            quality[suit] = 'none'
    return quality


def count_stoppers(hand: Hand) -> int:
    """Count how many suits are stopped."""
    stoppers = calculate_stoppers(hand)
    return sum(1 for stopped in stoppers.values() if stopped)


def calculate_support_points(hand: Hand, trump_suit: str = None, partner_trump_length: int = 5) -> int:
    """
    Calculate Support Points (HCP + shortness + trump length bonus).

    Based on the Law of Total Tricks:
    - Shortness points: void=5, singleton=3, doubleton=1
    - Trump length bonus: +1 for each trump beyond the 8th in partnership

    Args:
        hand: Hand object
        trump_suit: The agreed trump suit (None if no fit)
        partner_trump_length: Assumed length in partner's trump suit (default 5)

    Returns:
        Total support points
    """
    shortness_points = 0
    trump_length_bonus = 0

    for suit, length in hand.suit_lengths.items():
        if trump_suit and suit == trump_suit:
            # Calculate trump length bonus (Law of Total Tricks)
            # +1 for each trump beyond 8 in the partnership
            combined_trumps = length + partner_trump_length
            if combined_trumps > 8:
                trump_length_bonus = combined_trumps - 8
            continue
        # Shortness points in non-trump suits
        if length == 0:
            shortness_points += 5
        elif length == 1:
            shortness_points += 3
        elif length == 2:
            shortness_points += 1

    return hand.hcp + shortness_points + trump_length_bonus


def calculate_losing_trick_count(hand: Hand) -> int:
    """Calculate Losing Trick Count (LTC)."""
    ltc = 0
    for suit in ['♠', '♥', '♦', '♣']:
        suit_cards = [c.rank for c in hand.cards if c.suit == suit]
        length = len(suit_cards)
        if length == 0:
            continue
        cards_to_count = min(length, 3)
        has_ace = 'A' in suit_cards
        has_king = 'K' in suit_cards
        has_queen = 'Q' in suit_cards
        suit_losers = 0
        if cards_to_count >= 1 and not has_ace:
            suit_losers += 1
        if cards_to_count >= 2 and not has_king:
            suit_losers += 1
        if cards_to_count >= 3 and not has_queen:
            suit_losers += 1
        ltc += suit_losers
    return ltc


def calculate_playing_tricks(hand: Hand) -> float:
    """
    Calculate estimated Playing Tricks for evaluating strong opening hands.

    Playing tricks count the expected tricks when the hand is played with
    its longest suit as trumps. Used for Strong 2♣ opening decisions.

    Calculation per suit:
    - A = 1 trick
    - K in 2+ card suit = 1 trick
    - K singleton = 0.5 trick
    - Q in 3+ card suit = 1 trick
    - Q doubleton with another honor = 0.5 trick
    - Length tricks: cards beyond 3 in a suit with A or K = 1 trick each

    A hand needs 9+ playing tricks with 19-21 HCP for Strong 2♣.
    A hand with 22+ HCP automatically qualifies for Strong 2♣.

    Returns:
        Float representing estimated playing tricks (e.g., 9.5)
    """
    tricks = 0.0

    for suit in ['♠', '♥', '♦', '♣']:
        suit_cards = [c.rank for c in hand.cards if c.suit == suit]
        length = len(suit_cards)

        if length == 0:
            continue

        has_ace = 'A' in suit_cards
        has_king = 'K' in suit_cards
        has_queen = 'Q' in suit_cards
        has_jack = 'J' in suit_cards
        has_ten = 'T' in suit_cards

        # Honor tricks
        if has_ace:
            tricks += 1.0
        if has_king:
            if length >= 2:
                tricks += 1.0
            else:
                tricks += 0.5  # Singleton K
        if has_queen:
            if length >= 3:
                tricks += 1.0
            elif length == 2 and (has_ace or has_king or has_jack):
                tricks += 0.5  # Qx with another honor
        if has_jack:
            if length >= 4 and (has_queen or has_ten):
                tricks += 0.5  # Jxxx with Q or T

        # Length tricks (cards beyond 3 in a suit that has A or K)
        # These are "running tricks" once trumps are drawn
        if length > 3 and (has_ace or has_king):
            length_tricks = length - 3
            # Reduce value slightly if suit lacks solidity
            if not has_queen and not has_jack:
                length_tricks *= 0.75
            tricks += length_tricks

    return tricks


def get_suit_from_bid(bid: str) -> str:
    """Extract suit from a bid string.

    Handles both Unicode symbols (♠♥♦♣) and ASCII letters (SHDC).
    """
    if not bid or bid in ['Pass', 'X', 'XX'] or 'NT' in bid:
        return None
    if len(bid) >= 2:
        suit_char = bid[1]
        # Handle Unicode symbols directly
        if suit_char in '♠♥♦♣':
            return suit_char
        # Handle ASCII letters (convert to Unicode)
        ascii_to_unicode = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}
        if suit_char.upper() in ascii_to_unicode:
            return ascii_to_unicode[suit_char.upper()]
    return None


def get_bid_level(bid: str) -> int:
    """Extract level from a bid string. Returns 0 for Pass/X/XX."""
    if not bid or bid in ['Pass', 'X', 'XX']:
        return 0
    if len(bid) >= 1 and bid[0].isdigit():
        return int(bid[0])
    return 0


# =============================================================================
# FORCING SEQUENCE ANALYSIS
# Critical for SAYC bidding decisions - determines if auction is game-forcing,
# one-round forcing, or non-forcing.
# =============================================================================

GAME_FORCING_SEQUENCES = {
    # 2♣ opening is game forcing (unless 2♦ negative response followed by rebid)
    '2♣': 'game_forcing',
    # Jump shifts by responder (1♥-2♠, 1♦-2♥, etc.) are game forcing
    'jump_shift_response': 'game_forcing',
    # New suit by responder at 2-level after 1-level response is game forcing in 2/1
    '2_over_1': 'game_forcing',
    # Fourth suit forcing is game forcing
    'fourth_suit': 'game_forcing',
}

ONE_ROUND_FORCING_BIDS = {
    # New suit by responder is forcing one round
    'new_suit_response': 'one_round',
    # Opener's reverse is forcing one round
    'reverse': 'one_round',
    # Jump rebid by opener in new suit
    'jump_shift_rebid': 'one_round',
}


def analyze_forcing_status(auction_history: list, positions: list, my_index: int) -> dict:
    """
    Analyze the forcing status of the auction.

    Returns:
        dict with:
        - forcing_type: 'game_forcing', 'one_round_forcing', 'invitational', 'non_forcing'
        - forcing_source: What created the forcing status (e.g., '2♣ opening', 'reverse')
        - must_bid: Whether we MUST bid (can't pass)
        - minimum_level: Minimum level we must bid to (e.g., game level)
    """
    result = {
        'forcing_type': 'non_forcing',
        'forcing_source': None,
        'must_bid': False,
        'minimum_level': 0,
        'game_forcing_established': False,
    }

    if not auction_history:
        return result

    # Find opener and their suit
    opener_index = -1
    opening_bid = None
    for i, bid in enumerate(auction_history):
        if bid not in ['Pass', 'X', 'XX']:
            opener_index = i % 4
            opening_bid = bid
            break

    if opening_bid is None:
        return result

    # Check for 2♣ game-forcing opening
    # Only game-forcing for the partnership that opened 2♣, not opponents
    partner_index = (my_index + PARTNER_OFFSET) % 4
    if opening_bid == '2♣':
        if opener_index == my_index or opener_index == partner_index:
            result['forcing_type'] = 'game_forcing'
            result['forcing_source'] = '2♣ opening'
            result['game_forcing_established'] = True
            result['minimum_level'] = 4  # Must reach game

            # Check if we're past the 2♦ waiting bid
            non_pass_bids = [b for b in auction_history if b not in ['Pass', 'X', 'XX']]
            if len(non_pass_bids) >= 2:
                result['must_bid'] = True
            return result
        # Opponent opened 2♣ — not forcing for us
        return result

    # Track bids by partnership
    partner_index = (my_index + PARTNER_OFFSET) % 4

    # Collect partnership bids
    my_bids = []
    partner_bids = []
    opener_bids = []

    for i, bid in enumerate(auction_history):
        bidder = i % 4
        if bid not in ['Pass', 'X', 'XX']:
            if bidder == my_index:
                my_bids.append((i, bid))
            elif bidder == partner_index:
                partner_bids.append((i, bid))
            if bidder == opener_index:
                opener_bids.append((i, bid))

    # Check for reverse by opener (I am responder, partner opened)
    if opener_index == partner_index and len(opener_bids) >= 2:
        first_bid = opener_bids[0][1]
        second_bid = opener_bids[1][1]
        first_suit = get_suit_from_bid(first_bid)
        second_suit = get_suit_from_bid(second_bid)
        second_level = get_bid_level(second_bid)

        if first_suit and second_suit and second_level == 2:
            # Reverse: higher-ranking suit at 2-level
            suit_ranks = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
            if suit_ranks.get(second_suit, 0) > suit_ranks.get(first_suit, 0):
                result['forcing_type'] = 'one_round_forcing'
                result['forcing_source'] = 'opener_reverse'
                result['must_bid'] = True
                return result

    # Check for jump shift by responder (game forcing)
    if opener_index == partner_index and len(my_bids) >= 1:
        # My first response
        first_response = my_bids[0][1]
        first_response_level = get_bid_level(first_response)
        opening_level = get_bid_level(opening_bid)

        # Jump shift = skipping a level in a new suit
        if first_response_level >= opening_level + 2:
            response_suit = get_suit_from_bid(first_response)
            opening_suit = get_suit_from_bid(opening_bid)
            if response_suit and opening_suit and response_suit != opening_suit:
                result['forcing_type'] = 'game_forcing'
                result['forcing_source'] = 'jump_shift_response'
                result['game_forcing_established'] = True
                result['minimum_level'] = 4
                result['must_bid'] = True
                return result

    # Check for new suit by responder (one round forcing)
    if opener_index == partner_index and len(my_bids) >= 1:
        first_response = my_bids[0][1]
        response_suit = get_suit_from_bid(first_response)
        opening_suit = get_suit_from_bid(opening_bid)

        if response_suit and opening_suit and response_suit != opening_suit:
            # New suit response is forcing one round
            result['forcing_type'] = 'one_round_forcing'
            result['forcing_source'] = 'new_suit_response'
            # Only forcing if we haven't had a chance to pass
            if len(auction_history) % 4 == my_index:
                result['must_bid'] = False  # It's my turn, not partner's
            return result

    # Check if I opened and partner responded in a new suit (forcing me to bid)
    # This handles: 1♣ - Pass - 1♥ - Pass - ? (North must bid)
    if opener_index == my_index and len(my_bids) >= 1 and len(partner_bids) >= 1:
        my_opening_suit = get_suit_from_bid(my_bids[0][1])
        partner_response = partner_bids[0][1]
        partner_response_suit = get_suit_from_bid(partner_response)
        partner_response_level = get_bid_level(partner_response)

        # New suit response is forcing for one round in SAYC
        # 1-level new suit: forcing one round
        # 2-level new suit (2/1): game forcing
        if partner_response_suit and my_opening_suit and partner_response_suit != my_opening_suit:
            if partner_response_level == 2:
                # 2/1 game forcing response
                result['forcing_type'] = 'game_forcing'
                result['forcing_source'] = '2_over_1_response'
                result['game_forcing_established'] = True
                result['minimum_level'] = 4
                result['must_bid'] = True
                return result
            elif partner_response_level == 1:
                # 1-level new suit is forcing one round
                result['forcing_type'] = 'one_round_forcing'
                result['forcing_source'] = 'new_suit_response_by_partner'
                result['must_bid'] = True
                return result

    # Check if partner's last bid was a new suit (forcing on me)
    if partner_bids:
        last_partner_bid = partner_bids[-1][1]
        last_partner_suit = get_suit_from_bid(last_partner_bid)

        # Count unique suits partner has bid
        partner_suits = set()
        for _, bid in partner_bids:
            s = get_suit_from_bid(bid)
            if s:
                partner_suits.add(s)

        # If partner just bid a new suit, it's forcing
        if len(partner_suits) >= 2:
            previous_suits = set()
            for _, bid in partner_bids[:-1]:
                s = get_suit_from_bid(bid)
                if s:
                    previous_suits.add(s)

            if last_partner_suit and last_partner_suit not in previous_suits:
                result['forcing_type'] = 'one_round_forcing'
                result['forcing_source'] = 'new_suit_by_partner'
                result['must_bid'] = True

    return result


def detect_balancing_seat(auction_history: list, positions: list, my_index: int) -> dict:
    """
    Detect if player is in balancing (pass-out) seat.

    Balancing seat occurs when:
    1. Opponent opened
    2. Two passes followed
    3. My pass would end the auction

    In balancing seat, can bid with ~3 HCP less than normal.

    Returns:
        dict with:
        - is_balancing: True if in pass-out position
        - hcp_adjustment: How many HCP to subtract from requirements (-3 typical)
        - reason: Why this is/isn't balancing seat
    """
    result = {
        'is_balancing': False,
        'hcp_adjustment': 0,
        'reason': 'not_applicable',
    }

    if len(auction_history) < 3:
        result['reason'] = 'auction_too_short'
        return result

    # Check if last two bids were Pass
    if auction_history[-1] != 'Pass' or auction_history[-2] != 'Pass':
        result['reason'] = 'not_two_passes'
        return result

    # Find opener
    opener_index = -1
    for i, bid in enumerate(auction_history):
        if bid not in ['Pass', 'X', 'XX']:
            opener_index = i % 4
            break

    if opener_index == -1:
        result['reason'] = 'no_opener'
        return result

    # Check if opener is opponent
    partner_index = (my_index + PARTNER_OFFSET) % 4
    if opener_index == my_index or opener_index == partner_index:
        result['reason'] = 'partnership_opened'
        return result

    # Count non-pass bids from each side
    my_team_bids = 0
    opp_team_bids = 0
    for i, bid in enumerate(auction_history):
        if bid not in ['Pass', 'X', 'XX']:
            bidder = i % 4
            if bidder == my_index or bidder == partner_index:
                my_team_bids += 1
            else:
                opp_team_bids += 1

    # Classic balancing: opponents bid, we haven't, two passes
    if opp_team_bids >= 1 and my_team_bids == 0:
        result['is_balancing'] = True
        result['hcp_adjustment'] = -3  # Can bid with 3 fewer HCP
        result['reason'] = 'pass_out_seat_after_opponent_bid'
        return result

    # Also balancing if auction would die at low level
    # e.g., 1♥ - Pass - Pass - ? (direct balancing)
    if len(auction_history) == 3:
        if auction_history[1] == 'Pass' and auction_history[2] == 'Pass':
            result['is_balancing'] = True
            result['hcp_adjustment'] = -3
            result['reason'] = 'direct_balancing_seat'
            return result

    return result


def find_agreed_suit(auction_history: list, positions: list, my_index: int) -> dict:
    """
    Determine if partnership has agreed on a trump suit.

    Agreement occurs when:
    1. Partner raises my suit
    2. I raise partner's suit
    3. Both bid same suit
    4. Implicit agreement through certain conventions

    Returns:
        dict with:
        - agreed_suit: The agreed trump suit (or None)
        - agreement_level: Level at which suit was agreed
        - fit_known: True if we know we have 8+ card fit
        - fit_length: Combined length if known
    """
    result = {
        'agreed_suit': None,
        'agreement_level': 0,
        'fit_known': False,
        'fit_length': 0,
    }

    partner_index = (my_index + PARTNER_OFFSET) % 4

    my_suits = []
    partner_suits = []

    for i, bid in enumerate(auction_history):
        bidder = i % 4
        suit = get_suit_from_bid(bid)
        level = get_bid_level(bid)

        if suit:
            if bidder == my_index:
                my_suits.append((suit, level))
            elif bidder == partner_index:
                partner_suits.append((suit, level))

    # Check for explicit agreement (same suit bid by both)
    for my_suit, my_level in my_suits:
        for partner_suit, partner_level in partner_suits:
            if my_suit == partner_suit:
                result['agreed_suit'] = my_suit
                result['agreement_level'] = max(my_level, partner_level)
                result['fit_known'] = True
                # Assume 8-card fit minimum when suit is raised
                result['fit_length'] = 8
                return result

    # Check for raise (partner bids my suit or vice versa)
    if my_suits and partner_suits:
        my_first_suit = my_suits[0][0]
        for partner_suit, partner_level in partner_suits:
            if partner_suit == my_first_suit:
                result['agreed_suit'] = my_first_suit
                result['agreement_level'] = partner_level
                result['fit_known'] = True
                result['fit_length'] = 8
                return result

        partner_first_suit = partner_suits[0][0]
        for my_suit, my_level in my_suits:
            if my_suit == partner_first_suit:
                result['agreed_suit'] = partner_first_suit
                result['agreement_level'] = my_level
                result['fit_known'] = True
                result['fit_length'] = 8
                return result

    return result


def count_partnership_bids(auction_history: list, positions: list, my_index: int) -> dict:
    """
    Count bids made by each member of partnership.

    Returns:
        dict with:
        - my_bid_count: Number of non-pass bids I've made
        - partner_bid_count: Number of non-pass bids partner made
        - my_pass_count: Number of passes I've made
        - total_auction_rounds: How many complete rounds
    """
    partner_index = (my_index + PARTNER_OFFSET) % 4

    my_bids = 0
    my_passes = 0
    partner_bids = 0

    for i, bid in enumerate(auction_history):
        bidder = i % 4
        if bidder == my_index:
            if bid == 'Pass':
                my_passes += 1
            else:
                # Count all bids including X and XX (they're still actions)
                my_bids += 1
        elif bidder == partner_index:
            if bid != 'Pass':
                # Count all non-pass bids including X and XX
                partner_bids += 1

    return {
        'my_bid_count': my_bids,
        'partner_bid_count': partner_bids,
        'my_pass_count': my_passes,
        'total_auction_rounds': len(auction_history) // 4,
    }


def extract_features(hand: Hand, auction_history: list, my_position: str, vulnerability: str, dealer: str = 'North'):
    """Extract features from a hand and auction for bidding decision."""
    base_positions = ['North', 'East', 'South', 'West']
    # Handle None dealer (when frontend doesn't send it) - default to North
    if dealer is None:
        dealer = 'North'
    dealer_idx = base_positions.index(dealer)
    positions = [base_positions[(dealer_idx + i) % 4] for i in range(4)]
    my_index = positions.index(my_position)
    partner_position = positions[(my_index + PARTNER_OFFSET) % 4]

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

    interference = _detect_interference(auction_history, positions, my_index, opener_relationship, opener_index)
    auction_context = analyze_auction_context(auction_history, positions, my_index)
    bidding_state = BiddingStateBuilder().build(auction_history, dealer)

    # Calculate fundamental bridge metrics
    quick_tricks = calculate_quick_tricks(hand)
    stoppers = calculate_stoppers(hand)
    stopper_quality = calculate_stopper_quality(hand)
    stopper_count = count_stoppers(hand)
    losing_trick_count = calculate_losing_trick_count(hand)
    partner_suit = get_suit_from_bid(partner_last_bid) if partner_last_bid else None
    support_points = calculate_support_points(hand, partner_suit)

    # NEW: Calculate forcing status, balancing, agreed suit, bid counts
    forcing_status = analyze_forcing_status(auction_history, positions, my_index)
    balancing_info = detect_balancing_seat(auction_history, positions, my_index)
    agreed_suit_info = find_agreed_suit(auction_history, positions, my_index)
    bid_counts = count_partnership_bids(auction_history, positions, my_index)

    return {
        'hand_features': {
            'hcp': hand.hcp,
            'dist_points': hand.dist_points,
            'total_points': hand.total_points,
            'suit_lengths': hand.suit_lengths,
            'is_balanced': hand.is_balanced,
            'quick_tricks': quick_tricks,
            'stoppers': stoppers,
            'stopper_quality': stopper_quality,
            'stopper_count': stopper_count,
            'support_points': support_points,
            'losing_trick_count': losing_trick_count,
        },
        'auction_features': {
            'num_bids': len(auction_history),
            'opening_bid': opening_bid,
            'opener': opener,
            'opener_relationship': opener_relationship,
            'partner_bids': partner_bids,
            'partner_last_bid': partner_last_bid,
            'opener_last_bid': opener_last_bid,
            'opener_index': opener_index,
            'is_contested': is_contested,
            'vulnerability': vulnerability,
            'interference': interference,
            # NEW: Forcing sequence tracking
            'forcing_status': forcing_status,
            # NEW: Balancing seat detection
            'balancing': balancing_info,
            # NEW: Agreed suit tracking
            'agreed_suit': agreed_suit_info,
            # NEW: Partnership bid counts
            'bid_counts': bid_counts,
        },
        'auction_history': auction_history,
        'hand': hand,
        'my_index': my_index,
        'positions': positions,
        'auction_context': auction_context,
        'bidding_state': bidding_state
    }


def _detect_interference(auction_history, positions, my_index, opener_relationship, opener_index):
    """Detect if there was interference between partner's opening and my response."""
    interference = {
        'present': False,
        'bid': None,
        'level': None,
        'type': 'none',
        'position': None
    }

    if opener_relationship != 'Partner':
        return interference

    partner_index = opener_index
    lho_index = (partner_index + LHO_OFFSET) % 4
    rho_index = (partner_index + RHO_OFFSET) % 4

    for auction_idx in range(opener_index + 1, len(auction_history)):
        bidder_position = auction_idx % 4
        bid = auction_history[auction_idx]

        if bidder_position == lho_index or bidder_position == rho_index:
            if bid != 'Pass':
                interference['present'] = True
                interference['bid'] = bid
                interference['position'] = auction_idx

                if bid == 'X':
                    interference['type'] = 'double'
                    interference['level'] = 0
                elif bid == 'XX':
                    interference['type'] = 'redouble'
                    interference['level'] = 0
                elif 'NT' in bid:
                    interference['type'] = 'nt_overcall'
                    interference['level'] = int(bid[0])
                elif len(bid) >= 2 and bid[0].isdigit():
                    interference['type'] = 'suit_overcall'
                    interference['level'] = int(bid[0])

                return interference

        if bidder_position == my_index:
            break

    return interference
