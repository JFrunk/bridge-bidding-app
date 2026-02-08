#!/usr/bin/env python3
"""
Interactive Bridge Bidding Test Script

Usage:
    python play_bridge.py                  # Random hands, AI bids all
    python play_bridge.py --interactive    # You bid as South, AI bids others
    python play_bridge.py --dealer N       # Set dealer (N/E/S/W)
    python play_bridge.py --vuln NS        # Set vulnerability (None/NS/EW/Both)
    python play_bridge.py --hand-file X    # Load hands from JSON file
    python play_bridge.py --seed 42        # Reproducible random hands
"""

import argparse
import json
import os
import random
import sys
from typing import Dict, List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

# Enable V2 schema engine
os.environ['USE_V2_SCHEMA_ENGINE'] = 'true'


POSITIONS = ['North', 'East', 'South', 'West']
POSITION_MAP = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}


def deal_random_hands(seed: Optional[int] = None) -> Dict[str, Hand]:
    """Deal four random hands from a shuffled deck."""
    if seed is not None:
        random.seed(seed)

    # Create full 52-card deck
    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)

    # Deal 13 cards to each position
    return {
        'North': Hand(deck[0:13]),
        'East': Hand(deck[13:26]),
        'South': Hand(deck[26:39]),
        'West': Hand(deck[39:52])
    }


def load_hands_from_file(filepath: str) -> Dict[str, Hand]:
    """Load hands from a JSON file (review request format)."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    hands = {}
    for position in POSITIONS:
        if 'all_hands' in data and position in data['all_hands']:
            cards_data = data['all_hands'][position]['cards']
            cards = [Card(c['rank'], c['suit']) for c in cards_data]
            hands[position] = Hand(cards)
        elif position.lower() in data:
            # Alternative format
            cards_data = data[position.lower()]
            cards = [Card(c['rank'], c['suit']) for c in cards_data]
            hands[position] = Hand(cards)

    return hands


def display_hand(hand: Hand, position: str, show_details: bool = True) -> None:
    """Display a hand with its analysis."""
    suits_display = []
    for suit in ['♠', '♥', '♦', '♣']:
        suit_cards = [c for c in hand.cards if c.suit == suit]
        ranks = ''.join(c.rank for c in sorted(suit_cards, key=lambda x: "AKQJT98765432".index(x.rank)))
        suits_display.append(f"{suit}{ranks if ranks else '-'}")

    print(f"\n{position}: {' '.join(suits_display)}")

    if show_details:
        print(f"  HCP: {hand.hcp}, Total: {hand.total_points}")
        dist = f"♠{hand.suit_lengths['♠']} ♥{hand.suit_lengths['♥']} ♦{hand.suit_lengths['♦']} ♣{hand.suit_lengths['♣']}"
        print(f"  Distribution: {dist}")
        print(f"  Balanced: {hand.is_balanced}")


def display_all_hands(hands: Dict[str, Hand], show_hidden: bool = True) -> None:
    """Display all hands in a clear format."""
    print("\n" + "=" * 70)
    print("HANDS")
    print("=" * 70)

    for position in POSITIONS:
        if position in hands:
            display_hand(hands[position], position, show_details=show_hidden)


def display_auction_table(auction: List[Dict], dealer: str) -> None:
    """Display the auction in table format."""
    dealer_idx = POSITIONS.index(dealer)

    print("\n" + "-" * 50)
    print("│ {:^10} │ {:^10} │ {:^10} │ {:^10} │".format(*POSITIONS))
    print("-" * 50)

    # Add initial passes for positions before dealer
    row = [''] * 4
    bid_idx = 0

    for i, bid_obj in enumerate(auction):
        pos_idx = (dealer_idx + i) % 4
        row[pos_idx] = bid_obj['bid']

        if pos_idx == 3 or i == len(auction) - 1:
            print("│ {:^10} │ {:^10} │ {:^10} │ {:^10} │".format(*row))
            row = [''] * 4

    print("-" * 50)


def get_user_bid(hand: Hand, auction: List[str], legal_bids: List[str]) -> str:
    """Get a bid from the user."""
    print("\nYour hand:")
    display_hand(hand, "You (South)", show_details=True)

    print(f"\nAuction so far: {auction}")
    print(f"\nLegal bids: {', '.join(legal_bids[:20])}...")

    while True:
        user_input = input("\nEnter your bid (or 'ai' for AI suggestion, 'q' to quit): ").strip().upper()

        if user_input == 'Q':
            sys.exit(0)

        if user_input == 'AI':
            return None  # Signal to use AI

        # Normalize bid format
        bid = user_input.replace('S', '♠').replace('H', '♥').replace('D', '♦').replace('C', '♣')
        bid = bid.replace('NT', 'NT').replace('PASS', 'Pass').replace('X', 'X').replace('XX', 'XX')

        # Handle special cases
        if bid.upper() == 'PASS' or bid.upper() == 'P':
            bid = 'Pass'

        if bid in legal_bids or bid == 'Pass':
            return bid

        # Try to find a match
        for legal in legal_bids:
            if legal.replace('♠', 'S').replace('♥', 'H').replace('♦', 'D').replace('♣', 'C').upper() == user_input:
                return legal

        print(f"Invalid bid. Please enter a legal bid from: {', '.join(legal_bids[:10])}...")


def run_auction(
    hands: Dict[str, Hand],
    engine: BiddingEngine,
    dealer: str = 'North',
    vulnerability: str = 'None',
    interactive: bool = False,
    user_position: str = 'South'
) -> List[Dict]:
    """Run a complete auction."""
    auction = []
    auction_bids = []
    dealer_idx = POSITIONS.index(dealer)
    consecutive_passes = 0

    print("\n" + "=" * 70)
    print(f"BIDDING (Dealer: {dealer}, Vulnerability: {vulnerability})")
    print("=" * 70)

    max_rounds = 20  # Safety limit
    bid_count = 0

    while bid_count < max_rounds * 4:
        current_pos_idx = (dealer_idx + bid_count) % 4
        current_player = POSITIONS[current_pos_idx]
        current_hand = hands[current_player]

        print(f"\n--- {current_player} to bid ---")
        print(f"Auction: {auction_bids}")

        # Check if interactive and user's turn
        if interactive and current_player == user_position:
            # Get legal bids for user
            legal_bids = engine.get_legal_bids(auction_bids)
            user_bid = get_user_bid(current_hand, auction_bids, legal_bids)

            if user_bid is None:
                # User wants AI suggestion
                bid, explanation = engine.get_next_bid(current_hand, auction_bids, current_player, vulnerability)
                print(f"\n🤖 AI suggests: {bid}")
                print(f"   Explanation: {explanation}")
                confirm = input("Use this bid? (y/n): ").strip().lower()
                if confirm == 'y':
                    pass  # Use the AI bid
                else:
                    user_bid = get_user_bid(current_hand, auction_bids, legal_bids)
                    bid = user_bid
                    explanation = "User's choice"
            else:
                bid = user_bid
                explanation = "User's choice"
        else:
            # AI bids
            bid, explanation = engine.get_next_bid(current_hand, auction_bids, current_player, vulnerability)

        print(f"  {current_player} bids: {bid}")
        print(f"  Explanation: {explanation}")

        auction.append({
            'player': current_player,
            'bid': bid,
            'explanation': explanation
        })
        auction_bids.append(bid)
        bid_count += 1

        # Check for end of auction
        if bid == 'Pass':
            consecutive_passes += 1
        else:
            consecutive_passes = 0

        # Auction ends after 3 consecutive passes (if there was a bid) or 4 passes (if no bid)
        if consecutive_passes >= 3 and len(auction_bids) > 3:
            # Check if there was a real bid
            non_pass_bids = [b for b in auction_bids if b != 'Pass']
            if non_pass_bids:
                break

        if consecutive_passes >= 4:
            break

    return auction


def determine_contract(auction: List[Dict]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Determine the final contract from the auction."""
    # Find the last non-pass bid
    last_real_bid = None
    declarer = None
    doubled = ""

    bids_only = [a['bid'] for a in auction]

    for i in range(len(auction) - 1, -1, -1):
        bid = auction[i]['bid']
        if bid not in ['Pass', 'X', 'XX']:
            last_real_bid = bid
            break
        elif bid == 'XX':
            doubled = "XX"
        elif bid == 'X' and doubled != "XX":
            doubled = "X"

    if last_real_bid is None:
        return None, None, None  # All pass

    # Find declarer: first player of winning side to bid the strain
    strain = last_real_bid[-1] if 'NT' not in last_real_bid else 'NT'
    if 'NT' in last_real_bid:
        strain = 'NT'

    # Find the side that won (the partnership that made the last real bid)
    for i in range(len(auction) - 1, -1, -1):
        if auction[i]['bid'] == last_real_bid:
            winning_player = auction[i]['player']
            break

    ns_players = ['North', 'South']
    ew_players = ['East', 'West']

    winning_side = ns_players if winning_player in ns_players else ew_players

    # Find first player of winning side to bid this strain
    for a in auction:
        if a['player'] in winning_side:
            bid = a['bid']
            if bid not in ['Pass', 'X', 'XX']:
                bid_strain = bid[-1] if 'NT' not in bid else 'NT'
                if 'NT' in bid:
                    bid_strain = 'NT'
                if bid_strain == strain:
                    declarer = a['player']
                    break

    contract = last_real_bid + doubled

    return contract, declarer, doubled


def main():
    parser = argparse.ArgumentParser(description='Interactive Bridge Bidding Test Script')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive mode - you bid as South')
    parser.add_argument('--dealer', '-d', type=str, default='N',
                        help='Dealer position (N/E/S/W)')
    parser.add_argument('--vuln', '-v', type=str, default='None',
                        help='Vulnerability (None/NS/EW/Both)')
    parser.add_argument('--hand-file', '-f', type=str,
                        help='Load hands from JSON file')
    parser.add_argument('--seed', '-s', type=int,
                        help='Random seed for reproducible hands')
    parser.add_argument('--show-all', action='store_true', default=True,
                        help='Show all hands (default: True)')
    parser.add_argument('--user-position', '-p', type=str, default='S',
                        help='Your position in interactive mode (N/E/S/W)')

    args = parser.parse_args()

    # Normalize dealer
    dealer = POSITION_MAP.get(args.dealer.upper(), 'North')
    user_position = POSITION_MAP.get(args.user_position.upper(), 'South')

    # Get hands
    if args.hand_file:
        print(f"Loading hands from: {args.hand_file}")
        hands = load_hands_from_file(args.hand_file)
    else:
        print(f"Dealing random hands (seed: {args.seed})")
        hands = deal_random_hands(args.seed)

    # Display hands
    display_all_hands(hands, show_hidden=args.show_all)

    # Create engine
    engine = BiddingEngine()

    # Run auction
    auction = run_auction(
        hands=hands,
        engine=engine,
        dealer=dealer,
        vulnerability=args.vuln,
        interactive=args.interactive,
        user_position=user_position
    )

    # Display final auction
    print("\n" + "=" * 70)
    print("FINAL AUCTION")
    print("=" * 70)
    display_auction_table(auction, dealer)

    # Determine contract
    contract, declarer, doubled = determine_contract(auction)

    if contract:
        print(f"\nContract: {contract} by {declarer}")
    else:
        print("\nResult: All Pass")

    # Display auction with explanations
    print("\n" + "=" * 70)
    print("AUCTION DETAIL")
    print("=" * 70)
    for a in auction:
        print(f"{a['player']:6} : {a['bid']:4} - {a['explanation']}")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
