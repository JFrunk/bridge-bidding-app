"""
Bridgebots-to-MBB Mapping Layer

Translates bridgebots Deal/PlayerHand objects into MyBridgeBuddy engine inputs
(Hand objects, auction histories, vulnerability strings). This is the "state
normalization" layer that ensures the QA harness feeds identical inputs to both
the MBB engine and the external oracle.

Supports two modes:
1. bridgebots-based: Parse PBN files via bridgebots library (requires `pip install bridgebots`)
2. Raw PBN: Parse PBN files directly without bridgebots dependency
"""

import re
from typing import Dict, List, Optional, Tuple
from engine.hand import Hand
from utils.seats import SEATS, SEAT_NAMES

# Direction constants from shared utility
DIRECTIONS = SEATS
DIRECTION_FULL = SEAT_NAMES

# PBN bid notation → MBB bid notation
BID_TRANSLATION = {
    'P': 'Pass', 'Pass': 'Pass',
    'D': 'X', 'X': 'X', 'Dbl': 'X',
    'R': 'XX', 'XX': 'XX', 'Rdbl': 'XX',
}

# Suit letter → Unicode symbol (for bid conversion)
SUIT_ASCII_TO_UNICODE = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}


def translate_bid(pbn_bid: str) -> str:
    """
    Convert a PBN-format bid to MBB internal format.

    PBN uses: 1S, 2H, 3NT, P, D, R
    MBB uses: 1♠, 2♥, 3NT, Pass, X, XX
    """
    pbn_bid = pbn_bid.strip()
    if pbn_bid in BID_TRANSLATION:
        return BID_TRANSLATION[pbn_bid]

    # Handle suit bids: "1S" → "1♠", "3H" → "3♥"
    if len(pbn_bid) >= 2 and pbn_bid[0].isdigit():
        level = pbn_bid[0]
        denomination = pbn_bid[1:].upper()
        if denomination == 'NT':
            return f'{level}NT'
        if denomination in SUIT_ASCII_TO_UNICODE:
            return f'{level}{SUIT_ASCII_TO_UNICODE[denomination]}'

    # Already in MBB format (has Unicode suits)
    if any(c in pbn_bid for c in '♠♥♦♣'):
        return pbn_bid

    raise ValueError(f"Cannot translate PBN bid: '{pbn_bid}'")


def parse_pbn_deal_string(deal_string: str) -> Dict[str, Hand]:
    """
    Parse a PBN [Deal] tag value into four Hand objects.

    PBN Deal format: "N:AKQJ.T987.654.32 T98.AKQ.JT9.8765 765.J6.AK873.QJT 432.5432.Q2.AK94"
    First character is the direction of the first hand, followed by hands
    separated by spaces, in clockwise order (N→E→S→W from that starting direction).

    Returns:
        Dict mapping 'North'/'East'/'South'/'West' to Hand objects.
    """
    deal_string = deal_string.strip()

    # Extract starting direction
    if len(deal_string) >= 2 and deal_string[1] == ':':
        start_dir = deal_string[0].upper()
        hands_str = deal_string[2:].strip()
    else:
        start_dir = 'N'
        hands_str = deal_string

    hand_parts = hands_str.split()
    if len(hand_parts) != 4:
        raise ValueError(
            f"PBN deal must have exactly 4 hands, got {len(hand_parts)}: '{deal_string}'"
        )

    # Map starting direction to rotation offset using seats utility
    from utils.seats import seat_index, seat_from_index
    start_idx = seat_index(start_dir)
    result = {}
    for i, pbn_hand in enumerate(hand_parts):
        direction_letter = seat_from_index(start_idx + i)
        direction_name = DIRECTION_FULL[direction_letter]
        result[direction_name] = Hand.from_pbn(pbn_hand)

    return result


def parse_pbn_vulnerability(vul_string: str) -> str:
    """
    Convert PBN vulnerability tag to MBB format.

    PBN: 'None', 'NS', 'EW', 'Both', 'Love', 'All'
    MBB: 'None', 'NS', 'EW', 'Both'
    """
    vul = vul_string.strip()
    vul_map = {
        'None': 'None', 'Love': 'None', '-': 'None',
        'NS': 'NS', 'N-S': 'NS',
        'EW': 'EW', 'E-W': 'EW',
        'Both': 'Both', 'All': 'Both',
    }
    result = vul_map.get(vul)
    if result is None:
        raise ValueError(f"Unknown vulnerability: '{vul_string}'")
    return result


def parse_pbn_auction(auction_lines: List[str], dealer: str) -> List[str]:
    """
    Parse PBN auction section into MBB bid list.

    PBN auction format (one bid per entry or space-separated):
    "1S Pass 2H Pass 4S Pass Pass Pass"

    Handles: alerts (stripped), notes (stripped), AP (all pass shorthand).
    """
    bids = []
    done = False
    for line in auction_lines:
        if done:
            break
        line = line.strip()
        if not line or line.startswith(';'):
            continue

        # Split by whitespace, handle inline comments and AP
        tokens = line.split()
        in_comment = False
        for token in tokens:
            # Handle inline comments: { ... }
            if token.startswith('{'):
                in_comment = True
            if in_comment:
                if '}' in token:
                    in_comment = False
                continue

            # All Pass shorthand — each remaining player passes
            if token == 'AP':
                # AP means all remaining players pass to end the auction
                # Need to add passes until 3 consecutive passes after a non-pass bid
                remaining = (4 - (len(bids) % 4)) % 4
                if remaining == 0:
                    remaining = 4
                # Actually: AP = each remaining player in the round passes,
                # then add passes to complete 3 consecutive
                passes_needed = 0
                # Count trailing passes
                trailing = 0
                for b in reversed(bids):
                    if b == 'Pass':
                        trailing += 1
                    else:
                        break
                passes_needed = 3 - trailing
                for _ in range(max(passes_needed, 0)):
                    bids.append('Pass')
                done = True
                break

            # Strip alert markers and annotations
            token = re.sub(r'[!\?\*]', '', token)
            token = re.sub(r'\$\d+', '', token)  # NAG annotations
            if not token or token.startswith('['):
                continue
            try:
                bids.append(translate_bid(token))
            except ValueError:
                continue  # Skip unparseable tokens (notes, comments)

    return bids


class PBNRecord:
    """A single deal record parsed from a PBN file."""

    def __init__(self):
        self.event: str = ''
        self.site: str = ''
        self.board: int = 0
        self.dealer: str = 'North'
        self.vulnerability: str = 'None'
        self.hands: Dict[str, Hand] = {}
        self.auction: List[str] = []  # MBB-format bids
        self.declarer: str = ''
        self.contract: str = ''
        self.result: str = ''
        self.raw_tags: Dict[str, str] = {}

    def __repr__(self):
        return (
            f"PBNRecord(board={self.board}, dealer={self.dealer}, "
            f"vul={self.vulnerability}, auction_len={len(self.auction)})"
        )


def parse_pbn_file(filepath: str) -> List[PBNRecord]:
    """
    Parse a PBN file into a list of PBNRecord objects.

    Handles standard PBN tags: [Event], [Board], [Dealer], [Vulnerable],
    [Deal], [Auction], [Declarer], [Contract], [Result].
    """
    records = []
    current = None
    in_auction = False
    auction_lines = []
    auction_dealer = 'North'

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip('\n\r')

            # Tag line: [TagName "Value"]
            tag_match = re.match(r'\[(\w+)\s+"(.*)"\]', line)
            if tag_match:
                tag_name = tag_match.group(1)
                tag_value = tag_match.group(2)

                # Finalize previous auction section
                if in_auction and auction_lines and current:
                    current.auction = parse_pbn_auction(auction_lines, auction_dealer)
                    in_auction = False
                    auction_lines = []

                # New record starts at Event or Board tag (whichever comes first)
                if tag_name in ('Event', 'Board') and (current is None or current.hands):
                    if current is not None:
                        records.append(current)
                    current = PBNRecord()

                if current is None:
                    current = PBNRecord()

                current.raw_tags[tag_name] = tag_value

                if tag_name == 'Event':
                    current.event = tag_value
                elif tag_name == 'Board':
                    try:
                        current.board = int(tag_value)
                    except ValueError:
                        current.board = 0
                elif tag_name == 'Dealer':
                    current.dealer = DIRECTION_FULL.get(tag_value[0].upper(), 'North')
                elif tag_name in ('Vulnerable', 'Vulnerability'):
                    current.vulnerability = parse_pbn_vulnerability(tag_value)
                elif tag_name == 'Deal':
                    try:
                        current.hands = parse_pbn_deal_string(tag_value)
                    except (ValueError, IndexError) as e:
                        current.hands = {}  # Skip malformed deals
                elif tag_name == 'Declarer':
                    current.declarer = DIRECTION_FULL.get(tag_value[0].upper(), '')
                elif tag_name == 'Contract':
                    current.contract = tag_value
                elif tag_name == 'Result':
                    current.result = tag_value
                elif tag_name == 'Auction':
                    in_auction = True
                    auction_dealer = DIRECTION_FULL.get(tag_value[0].upper(), 'North')
                    auction_lines = []
                continue

            # Non-tag line while in auction section
            if in_auction:
                if line.strip() == '' or line.startswith('['):
                    # End of auction block
                    if current and auction_lines:
                        current.auction = parse_pbn_auction(auction_lines, auction_dealer)
                    in_auction = False
                    auction_lines = []
                else:
                    auction_lines.append(line)

    # Finalize last record
    if in_auction and auction_lines and current:
        current.auction = parse_pbn_auction(auction_lines, auction_dealer)
    if current is not None and (current.hands or current.auction):
        records.append(current)

    return records


def pbn_record_to_engine_inputs(
    record: PBNRecord,
    seat: str
) -> Dict:
    """
    Convert a PBNRecord into the inputs needed by BiddingEngineV2Schema.get_next_bid().

    Args:
        record: Parsed PBN record
        seat: Which seat to get the bid for ('North', 'East', 'South', 'West')

    Returns:
        Dict with keys: hand, auction_history, my_position, vulnerability, dealer
    """
    if seat not in record.hands:
        raise ValueError(f"Seat '{seat}' not found in record hands: {list(record.hands.keys())}")

    return {
        'hand': record.hands[seat],
        'my_position': seat,
        'vulnerability': record.vulnerability,
        'dealer': record.dealer,
    }


def calculate_feature_vector(hand: Hand) -> Dict:
    """
    Calculate the standardized feature vector for a hand.

    Used for discrepancy debugging: when MBB and oracle disagree,
    compare feature vectors to determine if the disagreement is due to
    feature calculation differences or logic differences.
    """
    from engine.ai.feature_extractor import (
        calculate_quick_tricks,
        calculate_losing_trick_count,
        calculate_stoppers,
    )

    controls = 0
    for card in hand.cards:
        if card.rank == 'A':
            controls += 2
        elif card.rank == 'K':
            controls += 1

    return {
        'hcp': hand.hcp,
        'shape': hand.suit_lengths,
        'total_points': hand.total_points,
        'is_balanced': hand.is_balanced,
        'controls': controls,
        'quick_tricks': calculate_quick_tricks(hand),
        'losing_trick_count': calculate_losing_trick_count(hand),
        'stoppers': calculate_stoppers(hand),
    }
