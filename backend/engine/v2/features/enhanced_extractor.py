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
    flat['support_points'] = hf['support_points']

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

    # Bid counts
    bc = af['bid_counts']
    flat['my_bid_count'] = bc['my_bid_count']
    flat['partner_bid_count'] = bc['partner_bid_count']
    flat['my_pass_count'] = bc['my_pass_count']

    # Derived features for schema matching
    flat['is_opening'] = af['num_bids'] == 0 or all(b == 'Pass' for b in auction_history)
    flat['is_response'] = af['opener_relationship'] == 'Partner' and bc['my_bid_count'] == 0
    flat['is_rebid'] = af['opener_relationship'] == 'Me' and bc['my_bid_count'] >= 1
    flat['is_overcall'] = af['opener_relationship'] == 'Opponent' and bc['my_bid_count'] == 0

    # Longest suit info
    suit_lengths = hf['suit_lengths']
    longest_length = max(suit_lengths.values())
    longest_suits = [s for s, l in suit_lengths.items() if l == longest_length]
    flat['longest_suit_length'] = longest_length
    flat['longest_suit'] = longest_suits[0] if longest_suits else None
    flat['has_5_card_major'] = suit_lengths.get('♠', 0) >= 5 or suit_lengths.get('♥', 0) >= 5
    flat['has_6_card_suit'] = longest_length >= 6
    flat['has_7_card_suit'] = longest_length >= 7

    # Major/minor suit lengths
    flat['spades_length'] = suit_lengths.get('♠', 0)
    flat['hearts_length'] = suit_lengths.get('♥', 0)
    flat['diamonds_length'] = suit_lengths.get('♦', 0)
    flat['clubs_length'] = suit_lengths.get('♣', 0)

    # Support for partner's suit
    if flat['partner_last_bid']:
        partner_suit = get_suit_from_bid(flat['partner_last_bid'])
        if partner_suit:
            flat['support_for_partner'] = suit_lengths.get(partner_suit, 0)
        else:
            flat['support_for_partner'] = 0
    else:
        flat['support_for_partner'] = 0

    # PBN representation
    flat['pbn'] = hand_to_pbn(hand)

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
