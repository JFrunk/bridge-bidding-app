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

    # Compute vulnerability booleans for rule conditions
    # my_position is 'North', 'East', 'South', or 'West'
    # NS are vulnerable if vulnerability is 'NS' or 'Both'
    # EW are vulnerable if vulnerability is 'EW' or 'Both'
    vuln = af['vulnerability']
    is_ns = my_position in ['North', 'South']
    flat['we_are_vulnerable'] = (vuln in ['NS', 'Both'] and is_ns) or (vuln in ['EW', 'Both'] and not is_ns)
    flat['they_are_vulnerable'] = (vuln in ['EW', 'Both'] and is_ns) or (vuln in ['NS', 'Both'] and not is_ns)
    flat['favorable_vulnerability'] = flat['they_are_vulnerable'] and not flat['we_are_vulnerable']
    flat['unfavorable_vulnerability'] = flat['we_are_vulnerable'] and not flat['they_are_vulnerable']

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

    # CRITICAL: Calculate support points in two scenarios:
    # 1. When fit is confirmed (both partners agree on a suit)
    # 2. When responding with support to partner's suit (we have 3+ cards)
    #
    # Support points = HCP + shortness points (void=5, singleton=3, doubleton=1)
    # These bonuses only apply when we have a fit!

    # First, calculate support_for_partner since we need it for the check
    # (This gets recalculated later, but we need it now for support_points)
    partner_suit = None
    if flat['partner_last_bid']:
        partner_suit = get_suit_from_bid(flat['partner_last_bid'])

    support_for_partner_temp = 0
    if partner_suit:
        support_for_partner_temp = hand.suit_lengths.get(partner_suit, 0)

    # Check if we should calculate support points
    should_calc_support = False
    trump_suit = None
    partner_trump_length = 5  # Default assumption for opener's suit

    if agreed['fit_known'] and agreed['agreed_suit']:
        # Case 1: Fit is already confirmed
        should_calc_support = True
        trump_suit = agreed['agreed_suit']
        if flat['partner_last_bid']:
            partner_bid = flat['partner_last_bid']
            # If partner raised our suit, they likely have 3-4
            if partner_bid and partner_bid[0].isdigit():
                level = int(partner_bid[0])
                if level >= 2:  # Raise typically shows 3-4 card support
                    partner_trump_length = 4

    elif support_for_partner_temp >= 3 and partner_suit:
        # Case 2: We're about to raise with support - calculate support points
        # This is critical for limit raises and game raises
        should_calc_support = True
        trump_suit = partner_suit
        # Partner opened a suit, assume they have 5 (or 4 for minors)
        if partner_suit in ['♥', '♠']:
            partner_trump_length = 5
        else:
            partner_trump_length = 4  # Minors could be only 4

    if should_calc_support and trump_suit:
        # Calculate support points with shortness bonuses
        flat['support_points'] = calculate_support_points(
            hand, trump_suit, partner_trump_length
        )
        flat['support_points_active'] = True
        flat['trump_length_bonus'] = max(0, hand.suit_lengths.get(trump_suit, 0) + partner_trump_length - 8)
    else:
        # Without a fit, support points = HCP (no bonuses)
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

    # Reverse detection (Barrier Principle)
    # A reverse is when opener bids a HIGHER-ranking suit at the 2-level
    # after opening at the 1-level. Requires 16+ points.
    # Example: 1♦ - 1♠ - 2♥ is a reverse (hearts higher than diamonds)
    # The "barrier" is rebidding your first suit at 2-level (e.g., 2♦)
    # Going ABOVE the barrier (2♥ or 2♠) is a reverse
    flat['is_reverse'] = False
    flat['can_bid_reverse'] = False  # Has the hand strength for a reverse

    if flat.get('is_rebid', False) and flat.get('first_suit'):
        first_suit = flat['first_suit']
        suit_ranking = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
        first_suit_rank = suit_ranking.get(first_suit, 0)

        # Check if we have a second suit that would be a reverse
        if flat.get('second_suit'):
            second_suit = flat['second_suit']
            second_suit_rank = suit_ranking.get(second_suit, 0)

            # Reverse: second suit ranks higher than first suit
            # E.g., opened 1♦, rebidding 2♥ is a reverse
            if second_suit_rank > first_suit_rank:
                flat['is_reverse'] = True

        # Can we afford to reverse? Need 16+ HCP
        flat['can_bid_reverse'] = flat.get('hcp', 0) >= 16

    # Michaels and Unusual 2NT detection
    # Detect if partner made a Michaels cuebid or Unusual 2NT
    flat['partner_bid_michaels'] = False
    flat['partner_bid_unusual_2nt'] = False
    flat['michaels_shows_majors'] = False  # Michaels over minor shows both majors
    flat['michaels_shows_major_minor'] = False  # Michaels over major shows other major + minor
    flat['prefer_clubs'] = False
    flat['prefer_diamonds'] = False

    # Check partner's bids for Michaels/Unusual 2NT patterns
    if partner_bids and len(partner_bids) >= 1:
        partner_first_bid = partner_bids[0] if partner_bids else None

        # Check for Unusual 2NT (partner bid 2NT directly over opponent's opening)
        if partner_first_bid == '2NT' and opening_bid:
            opp_suit = get_suit_from_bid(opening_bid)
            # Unusual 2NT shows two lowest unbid suits (typically minors)
            if opp_suit in ['♥', '♠']:
                flat['partner_bid_unusual_2nt'] = True
                flat['prefer_clubs'] = suit_lengths.get('♣', 0) >= suit_lengths.get('♦', 0)
                flat['prefer_diamonds'] = suit_lengths.get('♦', 0) > suit_lengths.get('♣', 0)

        # Check for Michaels cuebid (partner cuebid opponent's suit at 2-level)
        if partner_first_bid and opening_bid:
            partner_suit = get_suit_from_bid(partner_first_bid)
            opp_suit = get_suit_from_bid(opening_bid)
            partner_level = get_bid_level(partner_first_bid)

            # Michaels: 2♥ over 1♥, 2♠ over 1♠, 2♣ over 1♣, 2♦ over 1♦
            if partner_suit == opp_suit and partner_level == 2:
                flat['partner_bid_michaels'] = True
                if opp_suit in ['♣', '♦']:
                    # Michaels over minor shows both majors
                    flat['michaels_shows_majors'] = True
                else:
                    # Michaels over major shows other major + unspecified minor
                    flat['michaels_shows_major_minor'] = True
                    flat['prefer_clubs'] = suit_lengths.get('♣', 0) >= suit_lengths.get('♦', 0)
                    flat['prefer_diamonds'] = suit_lengths.get('♦', 0) > suit_lengths.get('♣', 0)

    # Support for other major (used for Michaels over major responses)
    # When partner bids Michaels over a major, they show the OTHER major
    flat['support_for_other_major'] = 0
    flat['other_major'] = None
    if flat.get('michaels_shows_major_minor'):
        # Michaels over 1H shows spades + minor; over 1S shows hearts + minor
        if opening_bid:
            opp_suit = get_suit_from_bid(opening_bid)
            if opp_suit == '♥':
                flat['other_major'] = '♠'
                flat['support_for_other_major'] = suit_lengths.get('♠', 0)
            elif opp_suit == '♠':
                flat['other_major'] = '♥'
                flat['support_for_other_major'] = suit_lengths.get('♥', 0)

    # Detect if I made a Michaels cuebid (for rebid after partner's 2NT ask)
    flat['i_made_michaels'] = False
    flat['i_made_michaels_over_major'] = False
    flat['partner_asked_for_minor'] = False
    my_bids = _get_my_bids(auction_history, my_position, dealer)
    if my_bids and opening_bid:
        my_first_bid = my_bids[0]
        my_suit = get_suit_from_bid(my_first_bid)
        opp_suit = get_suit_from_bid(opening_bid)
        my_level = get_bid_level(my_first_bid)

        # Check if I made a Michaels cuebid (cuebid of opponent's suit at 2-level)
        if my_suit == opp_suit and my_level == 2:
            flat['i_made_michaels'] = True
            if opp_suit in ['♥', '♠']:
                flat['i_made_michaels_over_major'] = True
                # Check if partner asked for my minor with 2NT or 3C
                # 2NT = Standard ask for minor
                # 3C = Artificial ask for minor (when 2NT not available or passed)
                partner_last = flat.get('partner_last_bid')
                if partner_last == '2NT' or partner_last == '3♣' or partner_last == '3C':
                    flat['partner_asked_for_minor'] = True

    # Jacoby 2NT detection (responder's game-forcing raise of opener's major)
    # Partner responds 2NT to opener's 1H or 1S, showing 4+ card support and GF values
    flat['partner_bid_jacoby_2nt'] = False
    flat['my_opening_suit'] = None
    my_bids = _get_my_bids(auction_history, my_position, dealer)
    if my_bids and len(my_bids) >= 1:
        my_first_bid = my_bids[0]
        my_first_suit = get_suit_from_bid(my_first_bid)
        my_first_level = get_bid_level(my_first_bid)

        # Check if I opened 1H or 1S
        if my_first_level == 1 and my_first_suit in ['♥', '♠']:
            flat['my_opening_suit'] = my_first_suit

            # Check if partner responded 2NT (Jacoby 2NT)
            if partner_bids and len(partner_bids) >= 1:
                partner_first_bid = partner_bids[0]
                if partner_first_bid == '2NT':
                    # Verify partner's 2NT was in response to my opening (not overcall situation)
                    # Partner's 2NT should be immediately after my 1M opening
                    flat['partner_bid_jacoby_2nt'] = True

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

    # Partner showed extra values detection (beyond minimum opening)
    # Extras = values beyond minimum (typically 16+ HCP)
    flat['partner_showed_extras'] = False

    if partner_bids:
        opening = af.get('opening_bid', '')

        # Case 1: Partner opened 1NT (15-17 HCP) - extras by definition
        if af.get('opener_relationship') == 'Partner' and opening == '1NT':
            flat['partner_showed_extras'] = True

        # Case 2: Partner made a reverse (17+ HCP)
        # A reverse is when opener bids a higher-ranking suit at the 2-level
        if len(partner_bids) >= 2 and af.get('opener_relationship') == 'Partner':
            first_bid = partner_bids[0]
            second_bid = partner_bids[1]
            first_suit = None
            second_suit = None

            # Extract suits from bids
            for s in ['♠', '♥', '♦', '♣']:
                if s in first_bid:
                    first_suit = s
                if s in second_bid:
                    second_suit = s

            if first_suit and second_suit:
                suit_rank = {'♣': 0, '♦': 1, '♥': 2, '♠': 3}
                # Check if second suit is higher ranking and at 2-level
                if suit_rank.get(second_suit, 0) > suit_rank.get(first_suit, 0):
                    if len(second_bid) >= 2 and second_bid[0] == '2':
                        flat['partner_showed_extras'] = True

        # Case 3: Partner rebid 2NT (18-19) or 3NT (20-21) after opening 1-suit
        partner_last = flat.get('partner_last_bid', '')
        if af.get('opener_relationship') == 'Partner':
            if partner_last in ['2NT', '3NT'] and opening in ['1♣', '1♦', '1♥', '1♠']:
                flat['partner_showed_extras'] = True

        # Case 4: Partner jumped in a new suit (shows extra values)
        if len(partner_bids) >= 2 and af.get('opener_relationship') == 'Partner':
            first_level = int(partner_bids[0][0]) if partner_bids[0][0].isdigit() else 0
            second_level = int(partner_bids[1][0]) if partner_bids[1][0].isdigit() else 0
            if first_level and second_level and second_level >= first_level + 2:
                flat['partner_showed_extras'] = True

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

    # Preempt detection: Did partner preempt?
    # Weak 2s: 2D, 2H, 2S with 5-10 HCP and 6+ cards
    # 3-level preempts: 3C, 3D, 3H, 3S with 5-10 HCP and 7+ cards
    flat['partner_preempted'] = False
    flat['partner_suit'] = None
    preempt_bids = ['2♦', '2♥', '2♠', '3♣', '3♦', '3♥', '3♠', '4♥', '4♠']
    if partner_bids and partner_bids[0] in preempt_bids:
        # Partner's first bid was a preempt (assuming they opened with it)
        flat['partner_preempted'] = True
        flat['partner_suit'] = get_suit_from_bid(partner_bids[0])
    elif flat.get('partner_last_bid') in preempt_bids and flat.get('opener_relationship') == 'Partner':
        # Partner opened with a preempt
        opening = flat.get('opening_bid')
        if opening in preempt_bids:
            flat['partner_preempted'] = True
            flat['partner_suit'] = get_suit_from_bid(opening)

    # RHO doubled? (needed for pass_weak_after_preempt_doubled)
    flat['rho_doubled'] = False
    rho_bids = _get_rho_bids(auction_history, my_position, dealer)
    if rho_bids and rho_bids[-1] == 'X':
        flat['rho_doubled'] = True

    # Partner transferred? (for no_blackwood_after_transfer_signoff)
    flat['partner_transferred'] = False
    jacoby_transfers = ['2♦', '2♥']  # 2D->hearts, 2H->spades
    if partner_bids:
        for pb in partner_bids:
            if pb in jacoby_transfers:
                flat['partner_transferred'] = True
                break

    # 1NT opener detection (for Smolen guards)
    flat['opener_opened_1nt'] = False
    my_bids_for_1nt = _get_my_bids(auction_history, my_position, dealer)
    if my_bids_for_1nt and my_bids_for_1nt[0] == '1NT':
        flat['opener_opened_1nt'] = True

    # Smolen detection: Partner bid 3H or 3S after we denied a major with 2D
    flat['partner_bid_smolen'] = False
    if flat['opener_opened_1nt'] and len(my_bids_for_1nt) >= 2:
        # Check if we responded 2D to Stayman (denying a major)
        if my_bids_for_1nt[1] == '2♦':
            # Check if partner then bid 3H or 3S (Smolen)
            smolen_bids = ['3♥', '3♠']
            partner_last = flat.get('partner_last_bid')
            if partner_last in smolen_bids:
                flat['partner_bid_smolen'] = True

    # Asked Blackwood (for slam bidding decisions)
    flat['asked_blackwood'] = False
    for mb in my_bids_for_1nt:
        if mb == '4NT':
            flat['asked_blackwood'] = True
            break

    # Gambling 3NT features (solid minor with no outside strength)
    _add_gambling_features(flat, hand)

    # Law of Total Tricks (LoTT) features for competitive auction safety
    # LoTT states: Total tricks available = Our fit + Their fit
    # Safe bidding level = Our fit length - 6 (at equal vulnerability)
    lott_features = _calculate_lott_features(
        hand, flat, partner_bids, auction_history, my_position, dealer
    )
    flat.update(lott_features)

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
    # For 6+ card suits, J alone is considered fair (adequate for weak 2)
    if 'J' in honors and length >= 6:
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


def _calculate_lott_features(hand: Hand, flat: Dict[str, Any], partner_bids: List[str],
                             auction_history: List[str], my_position: str, dealer: str) -> Dict[str, Any]:
    """
    Calculate Law of Total Tricks (LoTT) features for competitive auction safety.

    The Law of Total Tricks states that the total number of tricks available
    on a deal equals the sum of both sides' best fits. This guides competitive
    bidding decisions:
    - Safe level = Our best fit - 6
    - Volatile boards (high total tricks) favor aggressive bidding
    - Low total tricks favor defense

    Args:
        hand: Hand object
        flat: Flat features dict (for agreed_suit, fit_length, support_for_partner)
        partner_bids: List of partner's bids
        auction_history: Full auction history
        my_position: My position
        dealer: Dealer position

    Returns:
        Dict with LoTT features:
        - our_best_fit: Maximum combined fit length (our cards + partner's inferred)
        - lott_safe_level: Safe level to bid (our_best_fit - 6)
        - their_best_fit: Estimated opponent fit length
        - total_tricks_index: our_best_fit + their_best_fit
        - is_volatile_board: True if total_tricks_index >= 18
        - lott_above_safe: True if current auction level exceeds lott_safe_level
    """
    result = {
        'our_best_fit': 0,
        'lott_safe_level': 2,
        'their_best_fit': 8,  # Default assumption: 8-card fit
        'total_tricks_index': 16,
        'is_volatile_board': False,
        'lott_above_safe': False,
    }

    # Get our suit lengths
    suit_lengths = {
        '♠': flat.get('spades_length', 0),
        '♥': flat.get('hearts_length', 0),
        '♦': flat.get('diamonds_length', 0),
        '♣': flat.get('clubs_length', 0),
    }

    # Infer partner's suit lengths from their bids
    partner_inferred_suits = _infer_partner_suit_lengths(partner_bids)

    # Calculate our fit length for each suit
    our_fit_lengths = {}
    for suit in ['♠', '♥', '♦', '♣']:
        our_fit_lengths[suit] = suit_lengths[suit] + partner_inferred_suits.get(suit, 0)

    # If we have an agreed suit, use that fit
    if flat.get('fit_known') and flat.get('agreed_suit'):
        agreed_suit = flat['agreed_suit']
        fit_length = flat.get('fit_length', 0)
        if fit_length > 0:
            our_fit_lengths[agreed_suit] = fit_length

    # If partner bid a suit and we have support, estimate fit
    partner_suit = flat.get('partner_suit')  # From preempts or partner_first_suit
    if not partner_suit:
        partner_suit = flat.get('partner_first_suit')
    if partner_suit:
        support = flat.get('support_for_partner', 0)
        # Partner's suit bid implies minimum length
        partner_min_length = partner_inferred_suits.get(partner_suit, 5)
        estimated_fit = support + partner_min_length
        our_fit_lengths[partner_suit] = max(our_fit_lengths.get(partner_suit, 0), estimated_fit)

    # Our best fit is the maximum
    result['our_best_fit'] = max(our_fit_lengths.values()) if our_fit_lengths else 0

    # LoTT safe level = Our best fit - 6
    # Minimum safe level is 2 (can't bid below 2-level in competition)
    result['lott_safe_level'] = max(2, result['our_best_fit'] - 6)

    # Infer opponent's fit length from their bids
    opponent_inferred_suits = _infer_opponent_suit_lengths(
        auction_history, my_position, dealer, flat.get('opening_bid', '')
    )
    result['their_best_fit'] = max(opponent_inferred_suits.values()) if opponent_inferred_suits else 8

    # Total tricks index = sum of both sides' best fits
    result['total_tricks_index'] = result['our_best_fit'] + result['their_best_fit']

    # Volatile boards (high total tricks) favor aggressive bidding
    # 18+ total tricks means both sides have good fits
    result['is_volatile_board'] = result['total_tricks_index'] >= 18

    # Check if current auction level exceeds our safe level
    current_level = _get_current_auction_level(auction_history)
    result['lott_above_safe'] = current_level > result['lott_safe_level']

    # Strength-Based Override: HCP should override LoTT when game values exist
    # If combined partnership HCP >= 25, we have game values and LoTT ceiling
    # should not prevent us from bidding game
    partnership_min_hcp = flat.get('partnership_hcp_min', flat.get('hcp', 0))
    result['hcp_overrides_lott'] = partnership_min_hcp >= 25

    # Misfit detection: When fit is 6 or less, we have a misfit
    # Even with HCP, misfits are dangerous - LoTT still applies
    result['is_misfit'] = result['our_best_fit'] <= 6

    # Combined decision: Should we compete based on LoTT?
    # Yes if: (above safe level AND vulnerable AND not game values) OR misfit
    result['lott_says_pass'] = (
        (result['lott_above_safe'] and flat.get('we_are_vulnerable', False) and not result['hcp_overrides_lott'])
        or result['is_misfit']
    )

    # Should we bid game despite LoTT ceiling?
    # Yes if: game values AND fit exists (not misfit)
    result['strength_overrides_lott'] = result['hcp_overrides_lott'] and not result['is_misfit']

    # Suit Quality Score (SQS) for the trump suit
    # SQS = Length + Number of Top 3 Honors (A, K, Q)
    # An SQS of 10+ is "Safe" for 3-level, 8 or less is "Fragile"
    trump_suit = flat.get('agreed_suit') or flat.get('partner_first_suit')
    if trump_suit:
        trump_sqs = _calculate_suit_quality_score(hand, trump_suit, partner_inferred_suits.get(trump_suit, 0))
        result['trump_suit_quality_score'] = trump_sqs['sqs']
        result['trump_suit_honors'] = trump_sqs['honors']
        result['trump_quality_safe'] = trump_sqs['sqs'] >= 10
        result['trump_quality_fragile'] = trump_sqs['sqs'] <= 8
    else:
        result['trump_suit_quality_score'] = 0
        result['trump_suit_honors'] = 0
        result['trump_quality_safe'] = False
        result['trump_quality_fragile'] = True

    # Honor-adjusted LoTT: If trumps are fragile AND vulnerable, reduce safe level
    if result['trump_quality_fragile'] and flat.get('we_are_vulnerable', False):
        result['honor_adjusted_safe_level'] = max(2, result['lott_safe_level'] - 1)
    else:
        result['honor_adjusted_safe_level'] = result['lott_safe_level']

    # Working HCP vs Wasteful HCP
    # Working HCP = honors in our long suits (offensive power)
    # Wasteful HCP = honors in short suits or opponent's suits (defensive power)
    working_hcp, wasteful_hcp, wasted_in_opp_suits = _calculate_working_hcp(
        hand, suit_lengths, trump_suit, opponent_inferred_suits
    )
    result['working_hcp'] = working_hcp
    result['wasteful_hcp'] = wasteful_hcp
    result['wasted_in_opponent_suits'] = wasted_in_opp_suits

    # Working HCP Ratio - key metric for positional value
    total_hcp = flat.get('hcp', 0)
    result['working_hcp_ratio'] = working_hcp / max(1, total_hcp)
    result['hcp_efficiency'] = result['working_hcp_ratio']  # Alias

    # Adjusted HCP: Reduce value of wasted points
    # Q/J in short suits bid by opponents are worth ~50% of face value
    result['adjusted_hcp'] = total_hcp - (wasted_in_opp_suits * 0.5)

    # Misfit-heavy detection: High HCP but low working ratio
    # These hands should pass or double, not declare
    result['is_misfit_heavy'] = (
        result['working_hcp_ratio'] < 0.5 and
        total_hcp >= 12 and
        result['our_best_fit'] <= 7
    )

    # Distributional Value (Dummy Points) - only applies with a fit
    # Adds value for shortness when supporting partner
    if trump_suit and result['our_best_fit'] >= 8:
        raw_dummy_points = _calculate_dummy_points(hand, suit_lengths, trump_suit)

        # Ruffing Control Check: Scale dummy points by trump quality
        # A void with hollow trumps (2,3,4,5) is nearly worthless - you'll be over-ruffed
        ruff_control = _calculate_ruffing_control(hand, trump_suit, raw_dummy_points)
        result['raw_dummy_points'] = raw_dummy_points
        result['dummy_points'] = ruff_control['adjusted_ssp']
        result['control_multiplier'] = ruff_control['control_multiplier']
        result['is_fragile_ruff'] = ruff_control['is_fragile_ruff']

        # Total playing strength with controlled dummy points
        result['total_playing_strength'] = total_hcp + result['dummy_points']

        # "Thin game" detection: Low HCP but high playing strength
        result['is_thin_game_candidate'] = (
            total_hcp >= 10 and total_hcp <= 14 and
            result['total_playing_strength'] >= 14 and
            result['our_best_fit'] >= 9 and
            not result['is_fragile_ruff']
        )
    else:
        result['raw_dummy_points'] = 0
        result['dummy_points'] = 0
        result['control_multiplier'] = 1.0
        result['is_fragile_ruff'] = False
        result['total_playing_strength'] = total_hcp
        result['is_thin_game_candidate'] = False

    # Composite Strength: The final evaluation formula
    # Final Strength = (Raw HCP - Wasted Points) + (SSP × Control Multiplier)
    result['composite_strength'] = (
        result['adjusted_hcp'] + result['dummy_points']
    )

    # Preemptive Aggression Score - for tactical obstruction
    # For preempts, use honors in our longest suit (not partner's suit)
    longest_suit = flat.get('longest_suit')
    if longest_suit:
        preempt_honors = sum(1 for c in hand.cards if c.suit == longest_suit and c.rank in ['A', 'K', 'Q'])
    else:
        preempt_honors = result['trump_suit_honors']

    preempt_data = _calculate_preemptive_aggression(
        suit_lengths, flat.get('we_are_vulnerable', False),
        flat.get('they_are_vulnerable', False), preempt_honors
    )
    result['aggression_score'] = preempt_data['aggression_score']
    result['is_prime_preempt_target'] = preempt_data['is_prime_preempt_target']
    result['safety_margin'] = preempt_data['safety_margin']
    result['preempt_suit_honors'] = preempt_honors

    # Defensive Value Calculator - determines when to double vs bid
    # Uses quick_tricks from base features and is_misfit computed above
    quick_tricks = flat.get('quick_tricks', 0)
    defensive_data = _calculate_defensive_value(hand, quick_tricks, result['is_misfit'])
    result['is_defensive_powerhouse'] = defensive_data['is_defensive_powerhouse']
    result['offense_to_defense_ratio'] = defensive_data['offense_to_defense_ratio']
    result['defensive_penalty_candidate'] = defensive_data['defensive_penalty_candidate']

    # Doubled Auction Survival (DAS) - determines rescue actions when doubled
    # Detect if we are doubled - check BOTH RHO and LHO for doubles
    # Penalty doubles can come from either opponent
    rho_doubled = flat.get('rho_doubled', False)

    # Also check if LHO doubled
    lho_bids = _get_lho_bids(auction_history, my_position, dealer)
    lho_doubled = lho_bids and lho_bids[-1] == 'X'

    # We're doubled if either opponent doubled (and it wasn't redoubled away)
    is_doubled = rho_doubled or lho_doubled

    partner_sos_redouble = False

    # Check if partner issued an SOS redouble (XX after we were doubled)
    if partner_bids and partner_bids[-1] == 'XX':
        partner_sos_redouble = True

    # Determine what suit we're doubled in
    doubled_suit = None
    if is_doubled:
        # Find our side's last suit bid (could be ours or partner's)
        my_bids = _get_my_bids(auction_history, my_position, dealer)
        for bid in reversed(my_bids):
            suit = get_suit_from_bid(bid)
            if suit:
                doubled_suit = suit
                break
        # If we haven't bid a suit, check partner's bids
        if not doubled_suit and partner_bids:
            for bid in reversed(partner_bids):
                suit = get_suit_from_bid(bid)
                if suit:
                    doubled_suit = suit
                    break

    result['is_doubled'] = is_doubled
    result['partner_sos_redouble'] = partner_sos_redouble
    result['doubled_suit'] = doubled_suit

    # Detect "Last Chance to Rescue" scenario
    # This is when: Double → Pass → Pass → (we're now the last to act)
    # The auction pattern is: [X, Pass, Pass] as the last 3 bids before us
    is_last_chance_to_rescue = False
    if is_doubled and len(auction_history) >= 3:
        # Check if the last 3 bids before our turn are: X, Pass, Pass
        # This means partner passed after the double, and RHO also passed
        last_three = auction_history[-3:]
        if last_three == ['X', 'Pass', 'Pass']:
            is_last_chance_to_rescue = True
        # Also check for pattern where we bid, got doubled, partner passed, RHO passed
        # Pattern: [our_bid, X, Pass, Pass] where we're now to act again
        elif len(auction_history) >= 4:
            last_four = auction_history[-4:]
            if last_four[1] == 'X' and last_four[2] == 'Pass' and last_four[3] == 'Pass':
                # Our bid was doubled, then two passes - we're the "last chance"
                is_last_chance_to_rescue = True

    result['is_last_chance_to_rescue'] = is_last_chance_to_rescue

    # Calculate DAS features
    das_data = _calculate_doubled_status(
        hand, suit_lengths, doubled_suit,
        result['working_hcp_ratio'], flat.get('we_are_vulnerable', False),
        flat.get('hcp', 0)
    )
    result['panic_index'] = das_data['panic_index']
    result['should_rescue'] = das_data['should_rescue']
    result['can_punish_with_redouble'] = das_data['can_punish_with_redouble']
    result['rescue_suit'] = das_data['rescue_suit']
    result['rescue_action'] = das_data['rescue_action']
    result['multiple_rescue_suits'] = das_data['multiple_rescue_suits']
    result['rescue_candidates'] = das_data.get('rescue_candidates', 0)

    # Partner rescue response (when partner needs to respond to our SOS)
    if partner_sos_redouble:
        rescue_response = _calculate_partner_rescue_response(hand, suit_lengths, doubled_suit)
        result['rescue_response_suit'] = rescue_response['rescue_response_suit']
        result['rescue_response_action'] = rescue_response['rescue_response_action']
    else:
        result['rescue_response_suit'] = None
        result['rescue_response_action'] = None

    return result


def _calculate_suit_quality_score(hand: Hand, suit: str, partner_inferred_length: int) -> Dict[str, Any]:
    """
    Calculate Suit Quality Score (SQS) for competitive bidding decisions.

    SQS = Combined Length + Number of Top 3 Honors (A, K, Q) we hold

    The SQS determines if the trump suit is "safe" for competitive bidding:
    - SQS 10+ = Safe for 3-level
    - SQS 8-9 = Marginal
    - SQS ≤ 7 = Fragile (avoid competing vulnerable)

    Args:
        hand: Hand object
        suit: Trump suit symbol
        partner_inferred_length: Partner's inferred length in this suit

    Returns:
        Dict with 'sqs' (score), 'honors' (count of A/K/Q), 'length' (our length)
    """
    suit_cards = [c for c in hand.cards if c.suit == suit]
    our_length = len(suit_cards)

    # Count top 3 honors (A, K, Q)
    top_honors = sum(1 for c in suit_cards if c.rank in ['A', 'K', 'Q'])

    # Combined fit length
    combined_length = our_length + partner_inferred_length

    # SQS = Combined length + our top honors
    sqs = combined_length + top_honors

    return {
        'sqs': sqs,
        'honors': top_honors,
        'length': our_length,
        'combined_length': combined_length
    }


def _calculate_working_hcp(hand: Hand, suit_lengths: Dict[str, int], trump_suit: str,
                           opponent_suits: Dict[str, int] = None) -> tuple:
    """
    Calculate Working HCP vs Wasteful HCP for positional evaluation.

    Working HCP = honors in our long suits (4+ cards) - these generate tricks
    Wasteful HCP = honors in short suits (≤2 cards) - often captured or wasted
    Wasted in Opponent Suits = Q/J in short suits where opponents have length

    This distinction is critical in competitive auctions where:
    - Working HCP supports offensive bidding
    - Wasteful HCP suggests defensive potential (pass/double)
    - Wasted in opponent suits = likely captured, worst case

    Args:
        hand: Hand object
        suit_lengths: Dict of suit lengths {suit: length}
        trump_suit: The agreed/potential trump suit
        opponent_suits: Dict of opponent's inferred suit lengths

    Returns:
        Tuple of (working_hcp, wasteful_hcp, wasted_in_opponent_suits)
    """
    hcp_values = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
    working_hcp = 0
    wasteful_hcp = 0
    wasted_in_opp = 0

    if opponent_suits is None:
        opponent_suits = {}

    for suit in ['♠', '♥', '♦', '♣']:
        length = suit_lengths.get(suit, 0)
        suit_cards = [c for c in hand.cards if c.suit == suit]
        suit_hcp = sum(hcp_values.get(c.rank, 0) for c in suit_cards)

        # Check if this is an opponent's suit (they bid it)
        is_opponent_suit = suit in opponent_suits and opponent_suits[suit] >= 5

        if length >= 4 or suit == trump_suit:
            # Long suits and trump suit = working HCP
            working_hcp += suit_hcp
        elif length <= 2:
            # Short suits = wasteful HCP (honors may be captured)
            wasteful_hcp += suit_hcp

            # Extra penalty: Q/J in short suits where opponents have length
            # These are almost certainly going to be captured
            if is_opponent_suit:
                qj_waste = sum(hcp_values.get(c.rank, 0) for c in suit_cards if c.rank in ['Q', 'J'])
                wasted_in_opp += qj_waste
        else:
            # 3-card suits: split the difference
            working_hcp += suit_hcp // 2
            wasteful_hcp += suit_hcp - (suit_hcp // 2)

    return working_hcp, wasteful_hcp, wasted_in_opp


def _calculate_dummy_points(hand: Hand, suit_lengths: Dict[str, int], trump_suit: str) -> int:
    """
    Calculate Dummy Points (distributional value) for supporting partner.

    Dummy Points add value for shortness when we're raising partner's suit:
    - Void: +5 points (can ruff from the start)
    - Singleton: +3 points (can ruff after one round)
    - Doubleton: +1 point (can ruff after two rounds)

    These points are ONLY valid when:
    1. We have a fit (8+ cards combined)
    2. The shortness is NOT in the trump suit
    3. We have adequate trumps to ruff (3+ in support)

    Args:
        hand: Hand object
        suit_lengths: Dict of suit lengths {suit: length}
        trump_suit: The agreed trump suit

    Returns:
        Dummy points to add to hand evaluation
    """
    dummy_pts = 0
    trump_length = suit_lengths.get(trump_suit, 0)

    # Need at least 3 trumps to count dummy points
    if trump_length < 3:
        return 0

    for suit in ['♠', '♥', '♦', '♣']:
        if suit == trump_suit:
            continue  # Don't count shortness in trump suit

        length = suit_lengths.get(suit, 0)

        if length == 0:
            dummy_pts += 5  # Void
        elif length == 1:
            dummy_pts += 3  # Singleton
        elif length == 2:
            dummy_pts += 1  # Doubleton

    return dummy_pts


def _calculate_ruffing_control(hand: Hand, trump_suit: str, raw_ssp: int) -> Dict[str, Any]:
    """
    Adjust Short Suit Points (SSP) based on trump quality.

    The physics: A void is only valuable if your trumps are high enough
    to prevent over-ruffs. Ruffing with the 2 when opponent has the 9
    gives them the trick.

    Trump Quality Scale:
    - 2+ honors (A,K,Q): Full control (multiplier 1.0)
    - 1 honor: Partial control (multiplier 0.7)
    - 0 honors: Weak control (multiplier 0.3)

    Args:
        hand: Hand object
        trump_suit: The trump suit symbol
        raw_ssp: Raw short suit points before adjustment

    Returns:
        Dict with adjusted_ssp, control_multiplier, is_fragile_ruff
    """
    trump_cards = [c for c in hand.cards if c.suit == trump_suit]
    honors = sum(1 for c in trump_cards if c.rank in ['A', 'K', 'Q'])

    if honors >= 2:
        multiplier = 1.0  # Full control
    elif honors == 1:
        multiplier = 0.7  # Partial control
    else:
        multiplier = 0.3  # Weak control - ruffs will likely be over-ruffed

    adjusted_ssp = raw_ssp * multiplier

    return {
        'adjusted_ssp': adjusted_ssp,
        'control_multiplier': multiplier,
        'is_fragile_ruff': multiplier < 0.7 and raw_ssp > 0
    }


def _calculate_preemptive_aggression(suit_lengths: Dict[str, int], we_vul: bool,
                                      they_vul: bool, trump_honors: int) -> Dict[str, Any]:
    """
    Calculate aggression score for preemptive bidding opportunities.

    The physics of preemption is the Vulnerability Delta:
    - Favorable (They V, We NV): -500 is a "win" vs their +620 game
    - Unfavorable (We V, They NV): -500 is disaster vs their +420 game

    The Rule of 2-3-4:
    - NV vs NV: Overbid by 3 (down 3 undoubled = -150)
    - NV vs V: Overbid by 4 (favorable, maximum obstruction)
    - V vs V: Overbid by 2 (conservative)
    - V vs NV: Overbid by 2 (unfavorable, cautious)

    Args:
        suit_lengths: Dict of suit lengths
        we_vul: Are we vulnerable?
        they_vul: Are they vulnerable?
        trump_honors: Number of A/K/Q in our long suit

    Returns:
        Dict with aggression_score, is_prime_preempt_target, safety_margin
    """
    max_length = max(suit_lengths.values()) if suit_lengths else 0

    # Vulnerability modifier
    if not we_vul and they_vul:
        vul_modifier = 2.0  # Favorable: Maximum aggression
        safety_margin = 4  # Rule of 4
    elif not we_vul and not they_vul:
        vul_modifier = 1.0  # Equal: Moderate aggression
        safety_margin = 3  # Rule of 3
    elif we_vul and they_vul:
        vul_modifier = 0.7  # Both V: Conservative
        safety_margin = 2  # Rule of 2
    else:
        vul_modifier = 0.4  # Unfavorable: Extreme caution
        safety_margin = 2  # Rule of 2

    # Trump quality modifier: Don't preempt with hollow suits
    if trump_honors >= 2:
        quality_modifier = 1.0
    elif trump_honors == 1:
        quality_modifier = 0.8
    else:
        quality_modifier = 0.5  # Dangerous to preempt with Jxxxx or worse

    # Aggression score: Weighted by length squared, adjusted by vulnerability and quality
    aggression_score = (max_length ** 2) * vul_modifier * quality_modifier

    # Prime preempt target: High aggression, long suit, decent quality
    is_prime_target = (
        aggression_score > 30 and
        max_length >= 7 and
        trump_honors >= 1
    )

    return {
        'aggression_score': aggression_score,
        'is_prime_preempt_target': is_prime_target,
        'safety_margin': safety_margin
    }


def _calculate_defensive_value(hand: Hand, quick_tricks: float, is_misfit: bool) -> Dict[str, Any]:
    """
    Calculate defensive value to determine when to double vs bid.

    The Dual Nature of High Cards: An Ace can be a "Trick Taker" (Offense)
    or an "Entry Stopper" (Defense). This calculator identifies when your
    strength is better utilized by defending rather than declaring.

    Quick Trick Reference:
        A-K in a suit: 2.0 QT (guaranteed two defensive stops)
        A-Q in a suit: 1.5 QT (likely one and a half stops)
        Ace or K-Q:    1.0 QT (one stop)
        King-x:        0.5 QT (fragile; requires Ace position)

    First Principle of Defense: If hand contains 3.0+ Quick Tricks but
    no fit with partner, Offensive Potential is low but Defensive Potential
    is massive. Bidding is a "Logic Failure"; doubling is the correct move.

    Args:
        hand: Hand object
        quick_tricks: Pre-calculated quick tricks value
        is_misfit: Whether we have a misfit with partner

    Returns:
        Dict with:
        - is_defensive_powerhouse: True if 3.0+ QT (should double, not bid)
        - offense_to_defense_ratio: Lower = more defensive (< 0.6 means defend)
        - defensive_penalty_candidate: True if should consider penalty double
    """
    hcp = hand.hcp

    # Defensive powerhouse: 3.0+ quick tricks is massive defensive strength
    is_defensive_powerhouse = quick_tricks >= 3.0

    # Offense to defense ratio: HCP / (QT * 4)
    # Lower ratio means honors are concentrated (defensive)
    # Higher ratio means scattered HCP (less defensive)
    if quick_tricks > 0:
        offense_to_defense_ratio = hcp / (quick_tricks * 4)
    else:
        offense_to_defense_ratio = float('inf')  # All HCP with no QT (very unusual)

    # Penalty double candidate: High QT, misfit, or low offense ratio
    # This triggers when we should stop competing and start defending
    defensive_penalty_candidate = (
        (is_defensive_powerhouse and is_misfit) or  # QT + no fit = defend
        (quick_tricks >= 2.5 and offense_to_defense_ratio < 0.6) or  # Concentrated honors
        (is_misfit and quick_tricks >= 2.0 and hcp >= 10)  # Decent values, no fit
    )

    return {
        'is_defensive_powerhouse': is_defensive_powerhouse,
        'offense_to_defense_ratio': round(offense_to_defense_ratio, 2) if offense_to_defense_ratio != float('inf') else 99.0,
        'defensive_penalty_candidate': defensive_penalty_candidate
    }


def _calculate_doubled_status(hand: Hand, suit_lengths: Dict[str, int],
                               doubled_suit: str, working_hcp_ratio: float,
                               we_vulnerable: bool, hcp: int) -> Dict[str, Any]:
    """
    Calculate Doubled Auction Survival (DAS) status.

    When doubled for penalty, determines if we're in a "Penalty Trap" or
    if we can "Hold" the contract. Also identifies rescue options.

    Physics of Being Doubled:
    - Panic Index increases with: short trumps, wasted HCP, vulnerability
    - Rescue needed when panic_index >= 50
    - Strength redouble when working_hcp_ratio > 0.8 and hcp > 15

    Args:
        hand: Hand object
        suit_lengths: Dict of suit lengths
        doubled_suit: The suit we're doubled in (or None)
        working_hcp_ratio: Ratio of working to total HCP
        we_vulnerable: Vulnerability status
        hcp: Total HCP

    Returns:
        Dict with panic_index, should_rescue, can_punish_with_redouble,
        rescue_suit, rescue_action, multiple_rescue_suits
    """
    if not doubled_suit:
        return {
            'panic_index': 0,
            'should_rescue': False,
            'can_punish_with_redouble': False,
            'rescue_suit': None,
            'rescue_action': 'HOLD',
            'multiple_rescue_suits': False
        }

    # Calculate panic index based on trump length and HCP quality
    trump_length = suit_lengths.get(doubled_suit, 0)
    panic_index = 0

    # Physics: Short trumps = high panic
    if trump_length <= 1:
        panic_index += 50
    elif trump_length == 2:
        panic_index += 30
    elif trump_length == 3:
        panic_index += 10

    # Physics: Wasted HCP = higher panic
    if working_hcp_ratio < 0.4:
        panic_index += 30
    elif working_hcp_ratio < 0.5:
        panic_index += 15

    # Physics: Vulnerability increases penalty
    if we_vulnerable:
        panic_index += 20

    # Find rescue suits (4+ cards, not the doubled suit)
    rescue_candidates = []
    for suit in ['♣', '♦', '♥', '♠']:
        if suit != doubled_suit and suit_lengths.get(suit, 0) >= 4:
            rescue_candidates.append((suit, suit_lengths.get(suit, 0)))

    # Sort by length (descending), then by rank (ascending for cheapest)
    rescue_candidates.sort(key=lambda x: (-x[1], ['♣', '♦', '♥', '♠'].index(x[0])))

    # Determine rescue action
    multiple_rescue_suits = len(rescue_candidates) >= 2
    should_rescue = panic_index >= 50

    if len(rescue_candidates) == 0:
        rescue_action = 'PASS'  # No safe harbor
        rescue_suit = None
    elif multiple_rescue_suits and should_rescue:
        rescue_action = 'REDOUBLE'  # SOS: Partner picks cheapest 4-card suit
        rescue_suit = None
    elif len(rescue_candidates) >= 1 and should_rescue:
        rescue_action = 'BID'  # Direct rescue to longest suit
        rescue_suit = rescue_candidates[0][0]
    else:
        rescue_action = 'HOLD'  # Panic not high enough
        rescue_suit = rescue_candidates[0][0] if rescue_candidates else None

    # Strength redouble: Good working HCP and strong hand
    can_punish = working_hcp_ratio > 0.8 and hcp >= 15 and trump_length >= 3

    return {
        'panic_index': panic_index,
        'should_rescue': should_rescue,
        'can_punish_with_redouble': can_punish,
        'rescue_suit': rescue_suit,
        'rescue_action': rescue_action,
        'multiple_rescue_suits': multiple_rescue_suits,
        'rescue_candidates': len(rescue_candidates)
    }


def _calculate_partner_rescue_response(hand: Hand, suit_lengths: Dict[str, int],
                                        doubled_suit: str) -> Dict[str, Any]:
    """
    Partner's response logic after an SOS Redouble.

    The partner must bid their cheapest 4-card suit to find a safe harbor.
    This is a command, not an invitation.

    Priority:
    1. Cheapest 4-card suit (excluding doubled suit)
    2. Best 3-card suit if no 4-card suit
    3. Lowest rank available if flat

    Args:
        hand: Partner's hand
        suit_lengths: Partner's suit lengths
        doubled_suit: The suit the partnership is doubled in

    Returns:
        Dict with rescue_response_suit, rescue_response_action
    """
    suits_order = ['♣', '♦', '♥', '♠']  # Cheapest first

    # Priority 1: Find cheapest 4-card suit
    for suit in suits_order:
        if suit != doubled_suit and suit_lengths.get(suit, 0) >= 4:
            return {
                'rescue_response_suit': suit,
                'rescue_response_action': 'BID',
                'rescue_response_reason': 'SOS_RESCUE_RESPONSE'
            }

    # Priority 2: Find any 3-card suit
    for suit in suits_order:
        if suit != doubled_suit and suit_lengths.get(suit, 0) >= 3:
            return {
                'rescue_response_suit': suit,
                'rescue_response_action': 'BID',
                'rescue_response_reason': 'EMERGENCY_EXIT'
            }

    # Priority 3: No escape possible
    return {
        'rescue_response_suit': None,
        'rescue_response_action': 'PASS',
        'rescue_response_reason': 'NO_ESCAPE_POSSIBLE'
    }


def interpret_redouble(hand: Hand, auction_history: List[str],
                       suit_lengths: Dict[str, int], hcp: int,
                       doubled_suit: str, panic_index: int) -> Dict[str, Any]:
    """
    Interpret partner's redouble as either Power (Sit) or SOS (Pull).

    At low levels (1-2), a redouble is usually SOS if there's a misfit.
    At high levels (3+), it's usually Power (we can make it).
    With 12+ HCP, partner may convert SOS to Power.

    Args:
        hand: Our hand
        auction_history: Current auction
        suit_lengths: Our suit lengths
        hcp: Our HCP
        doubled_suit: Suit we're doubled in
        panic_index: Current panic level

    Returns:
        Dict with interpretation mode and expected action
    """
    # Get current auction level
    current_level = 1
    for bid in reversed(auction_history):
        if bid not in ['Pass', 'X', 'XX'] and len(bid) >= 2:
            try:
                current_level = int(bid[0])
                break
            except ValueError:
                continue

    # At low levels, assume SOS if panic is high
    if current_level <= 2:
        if panic_index >= 60:
            # Check if we can convert to Power with strong defense
            defensive_hcp = sum(1 for card in hand.cards if card.rank in ['A', 'K', 'Q', 'J'])
            if hcp >= 12 and defensive_hcp >= 4:
                return {
                    'interpretation_mode': 'POWER_CONVERSION',
                    'action': 'PASS',
                    'reason': 'Converting SOS to Power with strong defense',
                    'expected_response': None
                }
            # SOS - must pull to cheapest 4-card suit
            rescue = _calculate_partner_rescue_response(hand, suit_lengths, doubled_suit)
            return {
                'interpretation_mode': 'SOS_PULL',
                'action': 'BID',
                'reason': f'Low level ({current_level}-level) and high panic ({panic_index})',
                'expected_response': rescue['rescue_response_suit']
            }

    # At high levels (3+), assume Power - stay put
    return {
        'interpretation_mode': 'POWER_EXPECTATION',
        'action': 'PASS',
        'reason': f'High level ({current_level}-level) implies strength',
        'expected_response': None
    }


def _infer_partner_suit_lengths(partner_bids: List[str]) -> Dict[str, int]:
    """
    Infer partner's suit lengths from their bids.

    Bridge bidding rules imply minimum suit lengths:
    - 1-level major opening: 5+ cards
    - 1-level minor opening: 3+ cards (could be only 3)
    - 2-level weak bid: 6+ cards
    - 3-level preempt: 7+ cards
    - 4-level preempt: 8+ cards
    - Overcall: 5+ cards
    - Raise of partner's suit: 3+ cards
    - New suit at 2-level: 4+ cards

    Args:
        partner_bids: List of partner's bids

    Returns:
        Dict mapping suit symbols to minimum inferred lengths
    """
    inferred = {}

    for bid in partner_bids:
        if not bid or bid in ['Pass', 'X', 'XX']:
            continue

        suit = get_suit_from_bid(bid)
        level = get_bid_level(bid)

        if not suit or not level:
            continue

        # Infer minimum length based on bid
        min_length = 0

        if level == 1:
            # 1-level openings
            if suit in ['♥', '♠']:
                min_length = 5  # 5-card majors
            else:
                min_length = 3  # 3+ card minors
        elif level == 2:
            # Could be weak 2 (6+ cards) or 2-over-1 (4+ cards)
            # Assume weak 2 for preemptive suits
            if suit in ['♥', '♠', '♦']:
                min_length = 6  # Weak 2
            else:
                min_length = 4
        elif level == 3:
            min_length = 7  # 3-level preempt
        elif level == 4:
            min_length = 8  # 4-level preempt
        elif level >= 5:
            min_length = 8  # Very distributional

        # Update if this implies longer suit
        if suit and min_length > inferred.get(suit, 0):
            inferred[suit] = min_length

    return inferred


def _infer_opponent_suit_lengths(auction_history: List[str], my_position: str,
                                  dealer: str, opening_bid: str) -> Dict[str, int]:
    """
    Infer opponent's suit lengths from their bids.

    This helps estimate their best fit for LoTT calculations.

    Args:
        auction_history: Full auction history
        my_position: My position
        dealer: Dealer position
        opening_bid: The opening bid (if any)

    Returns:
        Dict mapping suit symbols to minimum inferred opponent fit lengths
    """
    inferred = {}

    # Get opponent bids (LHO and RHO)
    lho_bids = _get_lho_bids(auction_history, my_position, dealer)
    rho_bids = _get_rho_bids(auction_history, my_position, dealer)

    # Combine to infer opponent suit distribution
    for bid in lho_bids + rho_bids:
        if not bid or bid in ['Pass', 'X', 'XX']:
            continue

        suit = get_suit_from_bid(bid)
        level = get_bid_level(bid)

        if not suit or not level:
            continue

        # Infer minimum length
        min_length = 0
        if level == 1:
            if suit in ['♥', '♠']:
                min_length = 5
            else:
                min_length = 3
        elif level == 2:
            min_length = 6
        elif level >= 3:
            min_length = 7

        if suit and min_length > inferred.get(suit, 0):
            inferred[suit] = min_length

    # Check if opponents found a fit (both bid same suit)
    for suit in ['♠', '♥', '♦', '♣']:
        lho_bid_suit = any(get_suit_from_bid(b) == suit for b in lho_bids if b not in ['Pass', 'X', 'XX'])
        rho_bid_suit = any(get_suit_from_bid(b) == suit for b in rho_bids if b not in ['Pass', 'X', 'XX'])

        # If both opponents bid the same suit, they likely have a fit
        if lho_bid_suit and rho_bid_suit:
            # Assume at least 8-card fit when both bid
            inferred[suit] = max(inferred.get(suit, 0), 8)

    # Default: assume opponents have 8-card fit in their best suit if they bid at all
    if not inferred and (lho_bids or rho_bids):
        inferred['?'] = 8  # Unknown but assume 8-card fit

    return inferred


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
