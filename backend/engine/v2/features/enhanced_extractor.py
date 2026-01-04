"""
Enhanced Feature Extractor for V2 Engine

Builds on the existing feature_extractor.py but adds PBN support
and flattens features for schema-based rule evaluation.
"""

from typing import Dict, Any, Optional, List
from engine.hand import Hand
from engine.ai.feature_extractor import (
    extract_features,
    calculate_quick_tricks,
    calculate_stoppers,
    calculate_stopper_quality,
    calculate_losing_trick_count,
    calculate_support_points,
    get_suit_from_bid,
    get_bid_level
)


def hand_to_pbn(hand: Hand) -> str:
    """
    Convert Hand object to PBN (Portable Bridge Notation) format.

    PBN format: S.H.D.C where each suit uses standard card symbols
    Example: "AKQ32.K87.J9.T65"

    Args:
        hand: Hand object with cards

    Returns:
        PBN string representation
    """
    suits = {'♠': [], '♥': [], '♦': [], '♣': []}

    # Sort cards into suits
    for card in hand.cards:
        suits[card.suit].append(card.rank)

    # Order ranks properly (A, K, Q, J, T, 9, 8, 7, 6, 5, 4, 3, 2)
    rank_order = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, 'T': 4,
                  '9': 5, '8': 6, '7': 7, '6': 8, '5': 9, '4': 10, '3': 11, '2': 12}

    suit_strings = []
    for suit in ['♠', '♥', '♦', '♣']:
        sorted_ranks = sorted(suits[suit], key=lambda r: rank_order.get(r, 13))
        suit_strings.append(''.join(sorted_ranks))

    return '.'.join(suit_strings)


def pbn_to_hand(pbn: str) -> Hand:
    """
    Convert PBN string to Hand object.

    Args:
        pbn: PBN string like "AKQ32.K87.J9.T65"

    Returns:
        Hand object
    """
    from engine.hand import Card

    parts = pbn.split('.')
    if len(parts) != 4:
        raise ValueError(f"Invalid PBN format: {pbn}")

    suits = ['♠', '♥', '♦', '♣']
    cards = []

    for i, suit_str in enumerate(parts):
        for rank in suit_str:
            cards.append(Card(rank, suits[i]))

    return Hand(cards)


def extract_flat_features(hand: Hand, auction_history: list, my_position: str,
                          vulnerability: str, dealer: str = 'North') -> Dict[str, Any]:
    """
    Extract features in a flat dictionary format suitable for schema matching.

    This wraps the existing extract_features() but flattens the nested structure
    and adds derived features useful for rule matching.

    Args:
        hand: Hand object
        auction_history: List of bids
        my_position: Player position
        vulnerability: Vulnerability string
        dealer: Dealer position

    Returns:
        Flat dictionary with all features
    """
    # Get existing features
    nested = extract_features(hand, auction_history, my_position, vulnerability, dealer)

    # Flatten into single dict
    flat = {}

    # Hand features
    hf = nested['hand_features']
    flat['hcp'] = hf['hcp']
    flat['dist_points'] = hf['dist_points']
    flat['total_points'] = hf['total_points']
    flat['is_balanced'] = hf['is_balanced']
    flat['quick_tricks'] = hf['quick_tricks']
    flat['stopper_count'] = hf['stopper_count']
    flat['losing_trick_count'] = hf['losing_trick_count']
    # NOTE: support_points is calculated later, after agreed_suit is determined

    # Suit lengths as individual keys
    for suit, length in hf['suit_lengths'].items():
        suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}[suit]
        flat[f'{suit_name}_length'] = length

    # Stoppers as individual keys
    for suit, has_stopper in hf['stoppers'].items():
        suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}[suit]
        flat[f'{suit_name}_stopped'] = has_stopper

    # Stopper quality
    for suit, quality in hf['stopper_quality'].items():
        suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}[suit]
        flat[f'{suit_name}_stopper_quality'] = quality

    # Auction features
    af = nested['auction_features']
    flat['num_bids'] = af['num_bids']
    flat['opening_bid'] = af['opening_bid']
    flat['opener_relationship'] = af['opener_relationship']
    flat['partner_last_bid'] = af['partner_last_bid']
    flat['is_contested'] = af['is_contested']
    flat['vulnerability'] = af['vulnerability']

    # Forcing status
    fs = af['forcing_status']
    flat['forcing_type'] = fs['forcing_type']
    flat['must_bid'] = fs['must_bid']
    flat['game_forcing'] = fs['game_forcing_established']

    # Balancing
    bal = af['balancing']
    flat['is_balancing'] = bal['is_balancing']
    flat['balancing_hcp_adjustment'] = bal['hcp_adjustment']

    # Agreed suit
    agreed = af['agreed_suit']
    flat['agreed_suit'] = agreed['agreed_suit']
    flat['fit_known'] = agreed['fit_known']
    flat['fit_length'] = agreed['fit_length']

    # CRITICAL: Recalculate support points when fit is confirmed
    # Support points = HCP + shortness points + trump length bonus (Law of Total Tricks)
    # Only add bonuses when we have a confirmed trump fit
    if agreed['fit_known'] and agreed['agreed_suit']:
        # Estimate partner's trump length from their bid
        # If partner opened a major, assume 5; if they raised, assume 3-4
        partner_trump_length = 5  # Default assumption for opener's suit
        if flat['partner_last_bid']:
            partner_bid = flat['partner_last_bid']
            # If partner raised our suit, they likely have 3-4
            # If partner bid their own suit, assume 5
            if partner_bid and partner_bid[0].isdigit():
                level = int(partner_bid[0])
                if level >= 2:  # Raise typically shows 3-4 card support
                    partner_trump_length = 4

        # Recalculate with confirmed trump suit and partner length
        flat['support_points'] = calculate_support_points(
            hand, agreed['agreed_suit'], partner_trump_length
        )
        flat['support_points_active'] = True  # Flag that bonuses are being counted
        flat['trump_length_bonus'] = max(0, hand.suit_lengths.get(agreed['agreed_suit'], 0) + partner_trump_length - 8)
    else:
        # Without confirmed fit, support points = HCP (no bonuses yet)
        flat['support_points'] = hf['hcp']
        flat['support_points_active'] = False
        flat['trump_length_bonus'] = 0

    # Bid counts
    bc = af['bid_counts']
    flat['my_bid_count'] = bc['my_bid_count']
    flat['partner_bid_count'] = bc['partner_bid_count']
    flat['my_pass_count'] = bc['my_pass_count']

    # Derived features for schema matching
    flat['is_opening'] = af['num_bids'] == 0 or all(b == 'Pass' for b in auction_history)
    flat['is_response'] = af['opener_relationship'] == 'Partner' and bc['my_bid_count'] == 0
    flat['is_rebid'] = af['opener_relationship'] == 'Me' and bc['my_bid_count'] >= 1
    flat['is_competitive_later'] = af['opener_relationship'] == 'Opponent' and bc['my_bid_count'] >= 1
    flat['is_responder_rebid'] = af['opener_relationship'] == 'Partner' and bc['my_bid_count'] >= 1

    # Advancer detection: partner made a competitive action over opponent's opening
    # This includes overcalls, takeout doubles, and suit bids
    partner_bids_temp = _get_partner_bids(auction_history, my_position, dealer)
    partner_made_competitive_action = False
    for bid in partner_bids_temp:
        if bid not in ['Pass', 'XX'] and bid != '':
            partner_made_competitive_action = True
            break

    # is_advancer: opponent opened, partner made competitive action, I haven't bid yet
    flat['is_advancer'] = (af['opener_relationship'] == 'Opponent' and
                           partner_made_competitive_action and
                           bc['my_bid_count'] == 0)

    # is_overcall: opponent opened, partner hasn't acted competitively, I haven't bid
    flat['is_overcall'] = (af['opener_relationship'] == 'Opponent' and
                           not partner_made_competitive_action and
                           bc['my_bid_count'] == 0)

    # is_doubler_rebid: I doubled (takeout), partner responded, now I'm rebidding
    # Key: my_bid_count >= 1, my last bid was X, and partner has bid something
    my_bids_temp = _get_my_bids(auction_history, my_position, dealer)
    i_doubled = 'X' in my_bids_temp
    partner_responded_to_double = (i_doubled and
                                   partner_made_competitive_action and
                                   flat['partner_last_bid'] not in ['Pass', 'X', 'XX', None])
    flat['is_doubler_rebid'] = (af['opener_relationship'] == 'Opponent' and
                                 i_doubled and
                                 partner_responded_to_double and
                                 bc['my_bid_count'] >= 1)

    # Longest suit info
    suit_lengths = hf['suit_lengths']
    longest_length = max(suit_lengths.values())
    longest_suits = [s for s, l in suit_lengths.items() if l == longest_length]
    flat['longest_suit_length'] = longest_length
    flat['longest_suit'] = longest_suits[0] if longest_suits else None
    flat['has_4_card_major'] = suit_lengths.get('♠', 0) >= 4 or suit_lengths.get('♥', 0) >= 4
    flat['has_5_card_major'] = suit_lengths.get('♠', 0) >= 5 or suit_lengths.get('♥', 0) >= 5
    flat['has_6_card_suit'] = longest_length >= 6
    flat['has_7_card_suit'] = longest_length >= 7

    # Longest major suit (for responding to takeout doubles)
    spades_len = suit_lengths.get('♠', 0)
    hearts_len = suit_lengths.get('♥', 0)
    if spades_len >= hearts_len and spades_len >= 4:
        flat['longest_major'] = '♠'
        flat['longest_major_length'] = spades_len
    elif hearts_len >= 4:
        flat['longest_major'] = '♥'
        flat['longest_major_length'] = hearts_len
    else:
        flat['longest_major'] = None
        flat['longest_major_length'] = 0

    # Major/minor suit lengths
    flat['spades_length'] = suit_lengths.get('♠', 0)
    flat['hearts_length'] = suit_lengths.get('♥', 0)
    flat['diamonds_length'] = suit_lengths.get('♦', 0)
    flat['clubs_length'] = suit_lengths.get('♣', 0)

    # Overcall-specific features
    # Find the best suit for overcalling (longest 5+ card suit with best quality)
    suit_ranking = {'♣': 0, '♦': 1, '♥': 2, '♠': 3}
    best_overcall_suit = None
    best_overcall_length = 0
    best_overcall_quality = 'poor'
    quality_order = {'poor': 0, 'fair': 1, 'good': 2, 'excellent': 3}

    for suit in ['♠', '♥', '♦', '♣']:  # Check in rank order for tie-breaking
        length = suit_lengths.get(suit, 0)
        if length >= 5:
            quality = evaluate_suit_quality(hand, suit)
            # Prefer longer suits, then better quality, then higher ranking
            if (length > best_overcall_length or
                (length == best_overcall_length and quality_order.get(quality, 0) > quality_order.get(best_overcall_quality, 0)) or
                (length == best_overcall_length and quality == best_overcall_quality and suit_ranking.get(suit, 0) > suit_ranking.get(best_overcall_suit, 0))):
                best_overcall_suit = suit
                best_overcall_length = length
                best_overcall_quality = quality

    flat['suit_length'] = best_overcall_length  # Length of best overcall suit
    flat['suit_quality'] = best_overcall_quality  # Quality of best overcall suit
    flat['best_suit'] = best_overcall_suit  # The suit itself

    # Check if we can overcall at 1-level (suit outranks opponent's suit)
    opening_bid = flat.get('opening_bid', '')
    opponent_suit = get_suit_from_bid(opening_bid) if opening_bid else None
    flat['bid_higher_than_opening'] = False
    if best_overcall_suit and opponent_suit:
        flat['bid_higher_than_opening'] = suit_ranking.get(best_overcall_suit, 0) > suit_ranking.get(opponent_suit, 0)

    # Minimum bid level needed (1 if we can bid higher at same level, 2 otherwise)
    if opening_bid and opening_bid.startswith('1') and flat['bid_higher_than_opening']:
        flat['bid_level'] = 1
    elif opening_bid and opening_bid.startswith('1'):
        flat['bid_level'] = 2
    else:
        flat['bid_level'] = 2  # Default to 2-level for non-1-level openings

    # Support for partner's suit
    if flat['partner_last_bid']:
        partner_suit = get_suit_from_bid(flat['partner_last_bid'])
        if partner_suit:
            flat['support_for_partner'] = suit_lengths.get(partner_suit, 0)
        else:
            flat['support_for_partner'] = 0
    else:
        flat['support_for_partner'] = 0

    # Partner's first suit (for preference bids)
    # Scan partner's bids to find their first natural suit bid
    flat['partner_first_suit'] = None
    flat['partner_second_suit'] = None
    flat['support_for_partner_first'] = 0
    flat['support_for_partner_second'] = 0
    partner_bids = _get_partner_bids(auction_history, my_position, dealer)
    partner_suits_found = []
    for bid in partner_bids:
        suit = get_suit_from_bid(bid)
        if suit and suit not in partner_suits_found:
            partner_suits_found.append(suit)

    if len(partner_suits_found) >= 1:
        flat['partner_first_suit'] = partner_suits_found[0]
        flat['support_for_partner_first'] = suit_lengths.get(partner_suits_found[0], 0)
    if len(partner_suits_found) >= 2:
        flat['partner_second_suit'] = partner_suits_found[1]
        flat['support_for_partner_second'] = suit_lengths.get(partner_suits_found[1], 0)

    # Suit preference delta: positive means prefer first suit, negative means prefer second
    # Used for "preference" bids when partner has shown two suits
    flat['suit_preference_delta'] = flat['support_for_partner_first'] - flat['support_for_partner_second']
    flat['prefer_partner_first_suit'] = flat['suit_preference_delta'] >= 0 and flat['partner_first_suit'] is not None
    flat['prefer_partner_second_suit'] = flat['suit_preference_delta'] < 0 and flat['partner_second_suit'] is not None
    flat['partner_showed_two_suits'] = flat['partner_second_suit'] is not None

    # My first suit (the suit I bid first)
    flat['my_suit'] = None
    flat['my_last_bid'] = None
    flat['first_suit'] = None  # Alias for schema rules
    flat['first_suit_length'] = None  # Length of first suit I bid
    my_bids = _get_my_bids(auction_history, my_position, dealer)

    # Get my last bid (for transfer completion rules)
    if my_bids:
        flat['my_last_bid'] = my_bids[-1]

    # RHO's last bid (for redouble after takeout double, etc.)
    rho_bids = _get_rho_bids(auction_history, my_position, dealer)
    flat['rho_last_bid'] = rho_bids[-1] if rho_bids else None

    # Get my first natural suit bid
    for bid in my_bids:
        suit = get_suit_from_bid(bid)
        if suit:
            flat['my_suit'] = suit
            flat['first_suit'] = suit  # Alias for opener rebid rules
            flat['first_suit_length'] = suit_lengths.get(suit, 0)  # Length in that suit
            break

    # Second suit features (for Barrier Principle - reverses)
    # Find if I have a second 4+ card suit
    flat['second_suit'] = None
    flat['second_suit_length'] = 0
    flat['second_suit_higher'] = False
    flat['second_suit_lower'] = False

    if flat['my_suit']:
        my_first_suit = flat['my_suit']
        # Find second longest suit that's 4+ cards
        suit_ranking = {'♣': 0, '♦': 1, '♥': 2, '♠': 3}
        for suit, length in sorted(suit_lengths.items(), key=lambda x: -x[1]):
            if suit != my_first_suit and length >= 4:
                flat['second_suit'] = suit
                flat['second_suit_length'] = length
                flat['second_suit_higher'] = suit_ranking.get(suit, 0) > suit_ranking.get(my_first_suit, 0)
                flat['second_suit_lower'] = suit_ranking.get(suit, 0) < suit_ranking.get(my_first_suit, 0)
                break

    # Partner raised my suit (vs bid a new suit)
    # True when partner's first suit bid is the same as my first suit bid
    flat['partner_raised_my_suit'] = (
        flat['my_suit'] is not None and
        flat['partner_first_suit'] is not None and
        flat['partner_first_suit'] == flat['my_suit']
    )

    # Partner bid new suit (not a raise)
    flat['partner_bid_new_suit'] = (
        flat['partner_first_suit'] is not None and
        flat['my_suit'] is not None and
        flat['partner_first_suit'] != flat['my_suit']
    )

    # Stopper in opponent's suit (for NT overcalls/rebids)
    flat['stopper_in_opponent_suit'] = False
    opening_bid = flat.get('opening_bid', '')
    if opening_bid and af['opener_relationship'] in ['Opponent', 'RHO', 'LHO']:
        opponent_suit = get_suit_from_bid(opening_bid)
        if opponent_suit:
            suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}.get(opponent_suit)
            if suit_name:
                flat['stopper_in_opponent_suit'] = flat.get(f'{suit_name}_stopped', False)

    # Unbid suit support count (for takeout doubles)
    # Count how many unbid suits we have 3+ card support in
    bid_suits = set()
    for bid in auction_history:
        suit = get_suit_from_bid(bid)
        if suit:
            bid_suits.add(suit)
    unbid_suits = {'♠', '♥', '♦', '♣'} - bid_suits
    flat['unbid_suit_support'] = sum(1 for s in unbid_suits if suit_lengths.get(s, 0) >= 3)

    # support_all_unbid: True if we have 3+ cards in ALL unbid suits
    # This is key for takeout double evaluation
    flat['support_all_unbid'] = all(suit_lengths.get(s, 0) >= 3 for s in unbid_suits) if unbid_suits else False

    # For takeout doubles, also check support for unbid majors specifically
    unbid_majors = {'♠', '♥'} - bid_suits
    flat['support_unbid_major'] = any(suit_lengths.get(s, 0) >= 4 for s in unbid_majors) if unbid_majors else False
    flat['support_both_majors'] = all(suit_lengths.get(s, 0) >= 4 for s in unbid_majors) if len(unbid_majors) == 2 else False

    # Enhanced takeout double shape detection
    # "Perfect shape" = 3+ in all unbid suits AND short in opponent's suit
    opponent_suit = None
    if opening_bid:
        opponent_suit = get_suit_from_bid(opening_bid)

    flat['short_in_opponent_suit'] = False
    flat['opponent_suit_length'] = 0
    if opponent_suit:
        opponent_length = suit_lengths.get(opponent_suit, 0)
        flat['short_in_opponent_suit'] = opponent_length <= 2
        flat['opponent_suit_length'] = opponent_length

    # Perfect takeout shape: 4+ in all unbid majors, 3+ in all unbid minors, short in their suit
    flat['perfect_takeout_shape'] = False
    if opponent_suit and flat['short_in_opponent_suit']:
        unbid_majors = [s for s in ['♠', '♥'] if s != opponent_suit]
        unbid_minors = [s for s in ['♣', '♦'] if s != opponent_suit]
        major_support = all(suit_lengths.get(s, 0) >= 4 for s in unbid_majors)
        minor_support = all(suit_lengths.get(s, 0) >= 3 for s in unbid_minors)
        flat['perfect_takeout_shape'] = major_support and minor_support

    # Other major length (for Michaels)
    flat['other_major_length'] = 0
    if opponent_suit == '♥':
        flat['other_major_length'] = suit_lengths.get('♠', 0)
    elif opponent_suit == '♠':
        flat['other_major_length'] = suit_lengths.get('♥', 0)

    # Any minor length (for Michaels over major)
    flat['any_minor_length'] = max(suit_lengths.get('♣', 0), suit_lengths.get('♦', 0))

    # Shortness detection (for Splinters and Jacoby rebids)
    flat['has_void'] = any(l == 0 for l in suit_lengths.values())
    flat['has_singleton'] = any(l == 1 for l in suit_lengths.values())
    flat['has_doubleton'] = any(l == 2 for l in suit_lengths.values())

    # Find the short suit (void or singleton)
    flat['short_suit'] = None
    flat['short_suit_length'] = 13
    for suit in ['♠', '♥', '♦', '♣']:
        length = suit_lengths.get(suit, 0)
        if length < flat['short_suit_length']:
            flat['short_suit_length'] = length
            flat['short_suit'] = suit

    # Fourth Suit Forcing detection
    # Track which suits have been bid naturally
    all_suits = {'♠', '♥', '♦', '♣'}
    bid_suits_natural = set()
    for bid in auction_history:
        suit = get_suit_from_bid(bid)
        if suit:
            bid_suits_natural.add(suit)

    unbid_suits_remaining = all_suits - bid_suits_natural
    flat['is_fourth_suit'] = len(unbid_suits_remaining) == 1
    flat['fourth_suit'] = list(unbid_suits_remaining)[0] if flat['is_fourth_suit'] else None

    # FSF trigger detection: Did partner bid the fourth suit?
    # This means three suits were bid before partner's last suit bid, and partner bid the fourth
    flat['partner_bid_fsf'] = False
    flat['fsf_suit'] = None
    if flat['partner_last_bid'] and len(bid_suits_natural) == 4:
        # Check if partner's last bid introduced the fourth suit
        partner_bid_suit = get_suit_from_bid(flat['partner_last_bid'])
        if partner_bid_suit:
            # Find the index of partner's last suit bid in the auction
            partner_fsf_index = None
            for i in range(len(auction_history) - 1, -1, -1):
                if auction_history[i] == flat['partner_last_bid']:
                    partner_fsf_index = i
                    break

            if partner_fsf_index is not None:
                # Count suits bid BEFORE partner's FSF bid
                suits_before_partner = set()
                for i in range(partner_fsf_index):
                    s = get_suit_from_bid(auction_history[i])
                    if s:
                        suits_before_partner.add(s)
                if len(suits_before_partner) == 3 and partner_bid_suit not in suits_before_partner:
                    flat['partner_bid_fsf'] = True
                    flat['fsf_suit'] = partner_bid_suit

    # Did I bid FSF on my last bid?
    flat['i_bid_fsf'] = False
    if flat['my_last_bid'] and len(bid_suits_natural) == 4:
        my_bid_suit = get_suit_from_bid(flat['my_last_bid'])
        if my_bid_suit:
            # Count suits bid BEFORE my last bid
            suits_before_me = set()
            for i, bid in enumerate(auction_history):
                if _bid_index_is_mine(i, my_position, dealer) and bid == flat['my_last_bid']:
                    break
                s = get_suit_from_bid(bid)
                if s:
                    suits_before_me.add(s)
            if len(suits_before_me) == 3 and my_bid_suit not in suits_before_me:
                flat['i_bid_fsf'] = True

    # Stopper in fourth suit (for NT decisions after FSF)
    flat['has_stopper_in_fourth_suit'] = False
    if flat['fourth_suit']:
        suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}.get(flat['fourth_suit'])
        if suit_name:
            flat['has_stopper_in_fourth_suit'] = flat.get(f'{suit_name}_stopped', False)

    # Stopper in FSF suit (when partner bid FSF, do we have stopper?)
    flat['has_stopper_in_fsf_suit'] = False
    if flat['fsf_suit']:
        suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}.get(flat['fsf_suit'])
        if suit_name:
            flat['has_stopper_in_fsf_suit'] = flat.get(f'{suit_name}_stopped', False)

    # LHO's last bid (for balancing checks)
    lho_bids = _get_lho_bids(auction_history, my_position, dealer)
    flat['lho_last_bid'] = lho_bids[-1] if lho_bids else None

    # PBN representation
    flat['pbn'] = hand_to_pbn(hand)

    # Limit bid detection and partner HCP range inference
    # When partner makes a limit bid, we know both their floor AND ceiling
    flat['partner_showed_limit'] = False
    flat['partner_min_hcp'] = 0
    flat['partner_max_hcp'] = 40  # No ceiling until limit bid

    # Infer partner's HCP range from their bids
    if flat['partner_last_bid']:
        partner_bid = flat['partner_last_bid']

        # Common limit bid HCP ranges in SAYC
        limit_bid_ranges = {
            # Responses to 1-level openings
            '1NT': (6, 10),      # 1NT response = 6-10 HCP
            '2NT': (11, 12),     # 2NT invitational = 11-12 HCP
            '3NT': (13, 15),     # 3NT = 13-15 HCP balanced

            # Single raises
            '2♠': (6, 10),       # Single raise = 6-10 support points
            '2♥': (6, 10),
            '2♦': (6, 10),
            '2♣': (10, 12),      # 2♣ over 1NT = Stayman (different)

            # Limit raises
            '3♠': (10, 12),      # Limit raise = 10-12 support points
            '3♥': (10, 12),
            '3♦': (10, 12),
            '3♣': (10, 12),
        }

        # Check if partner's bid is a known limit bid
        if partner_bid in limit_bid_ranges:
            min_hcp, max_hcp = limit_bid_ranges[partner_bid]
            flat['partner_showed_limit'] = True
            flat['partner_min_hcp'] = min_hcp
            flat['partner_max_hcp'] = max_hcp

        # Opening bids also define ranges
        if af['opener_relationship'] == 'Partner':
            opening = af['opening_bid']
            if opening == '1NT':
                flat['partner_min_hcp'] = 15
                flat['partner_max_hcp'] = 17
                flat['partner_showed_limit'] = True
            elif opening == '2NT':
                flat['partner_min_hcp'] = 20
                flat['partner_max_hcp'] = 21
                flat['partner_showed_limit'] = True
            elif opening in ['1♣', '1♦', '1♥', '1♠']:
                flat['partner_min_hcp'] = 12
                flat['partner_max_hcp'] = 21  # Could be any strength until rebid

    # Key cards for RKCB (Roman Key Card Blackwood)
    # Key cards = 4 aces + trump King (if trump suit is known)
    # Count aces held
    aces_held = sum(1 for c in hand.cards if c.rank == 'A')
    flat['aces_held'] = aces_held

    # Key cards depend on agreed trump suit
    trump_king = 0
    if agreed['agreed_suit']:
        trump_suit = agreed['agreed_suit']
        trump_king = 1 if any(c.rank == 'K' and c.suit == trump_suit for c in hand.cards) else 0

    flat['key_cards'] = aces_held + trump_king
    flat['has_trump_queen'] = False
    if agreed['agreed_suit']:
        flat['has_trump_queen'] = any(c.rank == 'Q' and c.suit == agreed['agreed_suit'] for c in hand.cards)

    # RKCB 1430 response booleans (for schema matching)
    kc = flat['key_cards']
    flat['key_card_count_is_1_or_4'] = kc in [1, 4]
    flat['key_card_count_is_0_or_3'] = kc in [0, 3]
    flat['key_card_count_is_2'] = kc == 2
    flat['key_card_count_is_5'] = kc == 5

    # Partner's keycard count from RKCB response (for slam decisions)
    partner_kc = _infer_partner_keycards(auction_history, flat['partner_last_bid'])
    flat['partner_keycards_min'] = partner_kc['min']
    flat['partner_keycards_max'] = partner_kc['max']
    flat['total_keycards_min'] = kc + partner_kc['min']
    flat['total_keycards_max'] = kc + partner_kc['max']
    flat['have_all_keycards'] = flat['total_keycards_min'] >= 4
    flat['missing_two_keycards'] = flat['total_keycards_max'] <= 3

    # Suits bid count (for Fourth Suit Forcing detection)
    flat['suits_bid_count'] = len(bid_suits_natural)
    flat['is_fourth_suit_scenario'] = len(bid_suits_natural) == 3

    # Control Bidding Features (for slam exploration)
    # Control level: 1 = first-round (Ace/Void), 2 = second-round (King/Singleton)
    for suit in ['♠', '♥', '♦', '♣']:
        suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}[suit]
        flat[f'{suit_name}_control'] = _get_suit_control_level(hand, suit)

    # Major fit confirmed at game force level
    # True if we have an agreed major at 3+ level in a GF auction
    flat['major_fit_gf'] = False
    flat['in_slam_zone'] = False
    if agreed['agreed_suit'] in ['♠', '♥'] and agreed['fit_known']:
        # Check if we're in a game force
        if fs['game_forcing_established'] or flat['hcp'] >= 13:
            flat['major_fit_gf'] = True
            # Check current bidding level
            current_level = _get_current_auction_level(auction_history)
            if current_level >= 3:
                flat['in_slam_zone'] = True

    # Control bidding: lowest unbid control
    # Find the cheapest suit where we have a control that hasn't been bid yet
    flat['lowest_control_suit'] = None
    flat['has_unbid_control'] = False
    suit_order = ['♣', '♦', '♥', '♠']

    if flat['in_slam_zone'] and agreed['agreed_suit']:
        trump_suit = agreed['agreed_suit']
        suit_name_map = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
        for suit in suit_order:
            if suit == trump_suit:
                continue  # Skip trump suit
            if suit not in bid_suits_natural:  # Suit hasn't been bid
                suit_name = suit_name_map[suit]
                control_level = flat.get(f'{suit_name}_control', 0)
                if control_level > 0:
                    flat['lowest_control_suit'] = suit
                    flat['has_unbid_control'] = True
                    break

    # Denied control detection (for slam safety)
    # True if there's an unbid suit below the trump suit where we have NO control
    flat['has_denied_control'] = False
    flat['denied_control_suit'] = None

    if flat['in_slam_zone'] and agreed['agreed_suit']:
        trump_suit = agreed['agreed_suit']
        trump_idx = suit_order.index(trump_suit) if trump_suit in suit_order else 4

        for suit in suit_order[:trump_idx]:  # All suits below trump
            if suit not in bid_suits_natural:  # Unbid suit
                suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}[suit]
                if flat.get(f'{suit_name}_control', 0) == 0:
                    flat['has_denied_control'] = True
                    flat['denied_control_suit'] = suit
                    break  # Found a hole

    # Combined partnership HCP estimate (for slam decisions)
    flat['partnership_hcp_min'] = flat['hcp'] + flat['partner_min_hcp']
    flat['partnership_hcp_max'] = flat['hcp'] + flat['partner_max_hcp']
    flat['partnership_has_slam_values'] = flat['partnership_hcp_min'] >= 31

    # Gambling 3NT features (solid minor with no outside strength)
    _add_gambling_features(flat, hand)

    # Keep reference to original structures
    flat['_hand'] = hand
    flat['_auction_history'] = auction_history
    flat['_nested_features'] = nested

    return flat


def get_suit_hcp(hand: Hand, suit: str) -> int:
    """Get HCP in a specific suit."""
    hcp_values = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
    return sum(hcp_values.get(c.rank, 0) for c in hand.cards if c.suit == suit)


def get_suit_honors(hand: Hand, suit: str) -> List[str]:
    """Get list of honors (A, K, Q, J, T) in a suit."""
    honors = ['A', 'K', 'Q', 'J', 'T']
    return [c.rank for c in hand.cards if c.suit == suit and c.rank in honors]


def evaluate_suit_quality(hand: Hand, suit: str) -> str:
    """
    Evaluate suit quality for overcalls/preempts.

    Returns: 'excellent', 'good', 'fair', 'poor'
    """
    cards = [c for c in hand.cards if c.suit == suit]
    length = len(cards)
    honors = get_suit_honors(hand, suit)

    if length < 4:
        return 'poor'

    # Count top honors
    top_honors = sum(1 for h in honors if h in ['A', 'K', 'Q'])

    if 'A' in honors and 'K' in honors:
        return 'excellent'
    if top_honors >= 2 and length >= 5:
        return 'excellent'
    if top_honors >= 2:
        return 'good'
    if top_honors >= 1 and length >= 5:
        return 'good'
    if 'J' in honors and 'T' in honors:
        return 'fair'
    if top_honors >= 1:
        return 'fair'

    return 'poor'


def _get_partner_bids(auction_history: List[str], my_position: str, dealer: str = 'North') -> List[str]:
    """
    Extract partner's bids from the auction history.

    Args:
        auction_history: List of bids in order
        my_position: My position (North, East, South, West)
        dealer: Dealer position (determines bid indexing)

    Returns:
        List of partner's bids in order
    """
    positions = ['North', 'East', 'South', 'West']
    my_idx = positions.index(my_position) if my_position in positions else 0
    dealer_idx = positions.index(dealer) if dealer in positions else 0
    partner_idx = (my_idx + 2) % 4  # Partner is across the table

    partner_bids = []
    for i, bid in enumerate(auction_history):
        # Position of bid i = (dealer_idx + i) % 4
        bid_position_idx = (dealer_idx + i) % 4
        if bid_position_idx == partner_idx:
            partner_bids.append(bid)

    return partner_bids


def _get_my_bids(auction_history: List[str], my_position: str, dealer: str = 'North') -> List[str]:
    """
    Extract my bids from the auction history.

    Args:
        auction_history: List of bids in order
        my_position: My position (North, East, South, West)
        dealer: Dealer position (determines bid indexing)

    Returns:
        List of my bids in order
    """
    positions = ['North', 'East', 'South', 'West']
    my_idx = positions.index(my_position) if my_position in positions else 0
    dealer_idx = positions.index(dealer) if dealer in positions else 0

    my_bids = []
    for i, bid in enumerate(auction_history):
        # Position of bid i = (dealer_idx + i) % 4
        bid_position_idx = (dealer_idx + i) % 4
        if bid_position_idx == my_idx:
            my_bids.append(bid)

    return my_bids


def _get_rho_bids(auction_history: List[str], my_position: str, dealer: str = 'North') -> List[str]:
    """
    Extract Right Hand Opponent's bids from the auction history.

    Args:
        auction_history: List of bids in order
        my_position: My position (North, East, South, West)
        dealer: Dealer position (determines bid indexing)

    Returns:
        List of RHO's bids in order
    """
    positions = ['North', 'East', 'South', 'West']
    my_idx = positions.index(my_position) if my_position in positions else 0
    dealer_idx = positions.index(dealer) if dealer in positions else 0
    rho_idx = (my_idx - 1) % 4  # RHO is to my right (bid just before me)

    rho_bids = []
    for i, bid in enumerate(auction_history):
        # Position of bid i = (dealer_idx + i) % 4
        bid_position_idx = (dealer_idx + i) % 4
        if bid_position_idx == rho_idx:
            rho_bids.append(bid)

    return rho_bids


def _get_suit_control_level(hand: Hand, suit: str) -> int:
    """
    Get the control level for a suit.

    Control levels for slam bidding:
    - 1 = First-round control (Ace or Void)
    - 2 = Second-round control (King or Singleton)
    - 0 = No control

    Args:
        hand: Hand object
        suit: Suit symbol (♠, ♥, ♦, ♣)

    Returns:
        Control level (0, 1, or 2)
    """
    suit_cards = [c for c in hand.cards if c.suit == suit]
    suit_length = len(suit_cards)

    # Void = first-round control
    if suit_length == 0:
        return 1

    # Ace = first-round control
    if any(c.rank == 'A' for c in suit_cards):
        return 1

    # Singleton = second-round control (opponent can cash one trick max)
    if suit_length == 1:
        return 2

    # King = second-round control
    if any(c.rank == 'K' for c in suit_cards):
        return 2

    return 0


def _get_current_auction_level(auction_history: List[str]) -> int:
    """
    Get the current bidding level from the auction history.

    Args:
        auction_history: List of bids

    Returns:
        Current level (1-7) or 0 if no bids made
    """
    for bid in reversed(auction_history):
        if bid and bid[0].isdigit():
            return int(bid[0])
    return 0


def _bid_index_is_mine(bid_index: int, my_position: str, dealer: str = 'North') -> bool:
    """
    Check if a bid at a given index was made by me.

    Args:
        bid_index: Index of the bid in auction history
        my_position: My position (North, East, South, West)
        dealer: Dealer position

    Returns:
        True if this bid was made by me
    """
    positions = ['North', 'East', 'South', 'West']
    my_idx = positions.index(my_position) if my_position in positions else 0
    dealer_idx = positions.index(dealer) if dealer in positions else 0
    bid_position_idx = (dealer_idx + bid_index) % 4
    return bid_position_idx == my_idx


def _get_lho_bids(auction_history: List[str], my_position: str, dealer: str = 'North') -> List[str]:
    """
    Extract Left Hand Opponent's bids from the auction history.

    Args:
        auction_history: List of bids in order
        my_position: My position (North, East, South, West)
        dealer: Dealer position (determines bid indexing)

    Returns:
        List of LHO's bids in order
    """
    positions = ['North', 'East', 'South', 'West']
    my_idx = positions.index(my_position) if my_position in positions else 0
    dealer_idx = positions.index(dealer) if dealer in positions else 0
    lho_idx = (my_idx + 1) % 4  # LHO is to my left (bids after me)

    lho_bids = []
    for i, bid in enumerate(auction_history):
        # Position of bid i = (dealer_idx + i) % 4
        bid_position_idx = (dealer_idx + i) % 4
        if bid_position_idx == lho_idx:
            lho_bids.append(bid)

    return lho_bids


def _is_solid_suit(hand: Hand, suit: str) -> bool:
    """
    Check if a suit is solid (7+ cards headed by AKQ).

    A solid suit runs without losing a trick to opponents.

    Args:
        hand: Hand object
        suit: Suit symbol (♣, ♦, ♥, ♠)

    Returns:
        True if suit is solid (7+ with AKQ)
    """
    suit_cards = [c for c in hand.cards if c.suit == suit]
    if len(suit_cards) < 7:
        return False

    ranks = {c.rank for c in suit_cards}
    return 'A' in ranks and 'K' in ranks and 'Q' in ranks


def _count_outside_stoppers(hand: Hand, long_suit: str) -> int:
    """
    Count stoppers (A or K) in suits other than the long suit.

    For Gambling 3NT, we need to know if hand has outside stoppers.

    Args:
        hand: Hand object
        long_suit: The solid suit to exclude

    Returns:
        Count of A and K in other suits
    """
    count = 0
    for card in hand.cards:
        if card.suit != long_suit and card.rank in ['A', 'K']:
            count += 1
    return count


def _add_gambling_features(flat: Dict[str, Any], hand: Hand) -> None:
    """
    Add Gambling 3NT detection features to the flat features dict.

    Gambling 3NT shows a solid 7+ card minor with no outside A or K.

    Args:
        flat: Flat features dictionary to update
        hand: Hand object
    """
    # Check for solid minor
    flat['is_solid_clubs'] = _is_solid_suit(hand, '♣')
    flat['is_solid_diamonds'] = _is_solid_suit(hand, '♦')
    flat['is_solid_minor'] = flat['is_solid_clubs'] or flat['is_solid_diamonds']

    # Count outside stoppers (A or K in side suits)
    if flat['is_solid_clubs']:
        flat['outside_stopper_count'] = _count_outside_stoppers(hand, '♣')
    elif flat['is_solid_diamonds']:
        flat['outside_stopper_count'] = _count_outside_stoppers(hand, '♦')
    else:
        flat['outside_stopper_count'] = 0

    # Classic Gambling 3NT: solid minor with NO outside A/K
    flat['is_gambling_3nt_hand'] = flat['is_solid_minor'] and flat['outside_stopper_count'] == 0


def _infer_partner_keycards(auction_history: List[str], partner_last_bid: str) -> Dict[str, int]:
    """
    Infer partner's keycard count from their RKCB response.

    Uses 1430 responses:
    - 5♣ = 1 or 4 keycards
    - 5♦ = 0 or 3 keycards
    - 5♥ = 2 keycards, no trump Queen
    - 5♠ = 2 keycards, with trump Queen
    - 5NT = 5 keycards (all of them)

    Returns dict with 'min' and 'max' keycard count.
    """
    # Check if we asked 4NT and partner responded
    if not partner_last_bid:
        return {'min': 0, 'max': 0}

    # Only infer if partner's last bid was an RKCB response
    if partner_last_bid == '5♣':
        return {'min': 1, 'max': 4}  # 1 or 4 keycards
    elif partner_last_bid == '5♦':
        return {'min': 0, 'max': 3}  # 0 or 3 keycards
    elif partner_last_bid == '5♥':
        return {'min': 2, 'max': 2}  # 2 keycards, no Queen
    elif partner_last_bid == '5♠':
        return {'min': 2, 'max': 2}  # 2 keycards, with Queen
    elif partner_last_bid == '5NT':
        return {'min': 5, 'max': 5}  # All 5 keycards

    return {'min': 0, 'max': 0}
