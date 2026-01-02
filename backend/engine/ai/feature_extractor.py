from engine.hand import Hand
from engine.ai.auction_context import analyze_auction_context
from typing import Dict

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


def calculate_support_points(hand: Hand, trump_suit: str = None) -> int:
    """Calculate Support Points (HCP + shortness when raising partner)."""
    shortness_points = 0
    for suit, length in hand.suit_lengths.items():
        if trump_suit and suit == trump_suit:
            continue
        if length == 0:
            shortness_points += 5
        elif length == 1:
            shortness_points += 3
        elif length == 2:
            shortness_points += 1
    return hand.hcp + shortness_points


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


def get_suit_from_bid(bid: str) -> str:
    """Extract suit from a bid string."""
    if not bid or bid in ['Pass', 'X', 'XX'] or 'NT' in bid:
        return None
    if len(bid) >= 2 and bid[1] in '♠♥♦♣':
        return bid[1]
    return None


def extract_features(hand: Hand, auction_history: list, my_position: str, vulnerability: str, dealer: str = 'North'):
    """Extract features from a hand and auction for bidding decision."""
    base_positions = ['North', 'East', 'South', 'West']
    dealer_idx = base_positions.index(dealer)
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

    interference = _detect_interference(auction_history, positions, my_index, opener_relationship, opener_index)
    auction_context = analyze_auction_context(auction_history, positions, my_index)

    # Calculate fundamental bridge metrics
    quick_tricks = calculate_quick_tricks(hand)
    stoppers = calculate_stoppers(hand)
    stopper_quality = calculate_stopper_quality(hand)
    stopper_count = count_stoppers(hand)
    losing_trick_count = calculate_losing_trick_count(hand)
    partner_suit = get_suit_from_bid(partner_last_bid) if partner_last_bid else None
    support_points = calculate_support_points(hand, partner_suit)

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
            'interference': interference
        },
        'auction_history': auction_history,
        'hand': hand,
        'my_index': my_index,
        'positions': positions,
        'auction_context': auction_context
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
    lho_index = (partner_index + 1) % 4
    rho_index = (partner_index + 3) % 4

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
