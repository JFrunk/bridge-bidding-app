#!/usr/bin/env python3
"""
Analyze bidding engine quality by comparing final contracts to DDS trick potential.

This identifies hands where the bidding went most wrong:
- Overbid: Contract level > trick potential (dangerous - going down)
- Underbid: Contract level < trick potential (missed opportunities)

Usage:
    python analyze_bidding_vs_dds.py --hands 100
    python analyze_bidding_vs_dds.py --hands 500 --output results.json
"""
import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.hand import Hand

# Check if V2 schema engine should be used
USE_V2 = os.environ.get('USE_V2_SCHEMA_ENGINE', 'false').lower() == 'true'

if USE_V2:
    from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema as BiddingEngine
    ENGINE_NAME = "V2 Schema"
else:
    from engine.bidding_engine import BiddingEngine
    ENGINE_NAME = "V1 Legacy"

# Check platform - DDS only works reliably on Linux
import platform
PLATFORM_ALLOWS_DDS = platform.system() == 'Linux'

# Try to import DDS
try:
    from endplay.dds import calc_dd_table
    from endplay.types import Deal, Player, Denom
    DDS_IMPORT_OK = True
except ImportError:
    DDS_IMPORT_OK = False

# DDS is only truly available on Linux
DDS_AVAILABLE = DDS_IMPORT_OK and PLATFORM_ALLOWS_DDS

if not DDS_AVAILABLE:
    if not PLATFORM_ALLOWS_DDS:
        print(f"⚠️ DDS disabled on {platform.system()} (only reliable on Linux)")
    else:
        print("⚠️ DDS not available - install endplay")
    print("   Using HCP-based estimation instead")


@dataclass
class HandResult:
    """Result of analyzing one hand."""
    hand_id: int
    north_pbn: str
    south_pbn: str
    east_pbn: str
    west_pbn: str
    ns_hcp: int
    ew_hcp: int
    auction: List[str]
    final_contract: Optional[str]
    declarer: Optional[str]
    tricks_needed: int
    dds_tricks: Optional[int]  # Max tricks available in the contract strain
    delta: int  # dds_tricks - tricks_needed (negative = overbid)
    overbid_severity: str  # "none", "mild", "moderate", "severe"


def create_random_deal() -> Dict[str, Hand]:
    """Create 4 random hands."""
    cards = []
    for suit in ['♠', '♥', '♦', '♣']:
        for rank in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']:
            cards.append((rank, suit))

    random.shuffle(cards)

    hands = {}
    positions = ['North', 'East', 'South', 'West']
    for i, pos in enumerate(positions):
        hand_cards = cards[i*13:(i+1)*13]
        # Convert to PBN format
        pbn = []
        for suit in ['♠', '♥', '♦', '♣']:
            suit_cards = [c[0] for c in hand_cards if c[1] == suit]
            pbn.append(''.join(suit_cards))
        hands[pos] = Hand.from_pbn('.'.join(pbn))

    return hands


def run_auction(hands: Dict[str, Hand], engine: BiddingEngine, dealer: str = 'North') -> List[str]:
    """Run a full auction and return the bid sequence."""
    positions = ['North', 'East', 'South', 'West']
    dealer_idx = positions.index(dealer)

    auction = []
    consecutive_passes = 0
    current_player = dealer_idx

    for _ in range(52):  # Safety limit
        pos = positions[current_player]
        hand = hands[pos]

        try:
            bid, explanation = engine.get_next_bid(
                hand=hand,
                auction_history=auction,
                my_position=pos,
                vulnerability='None',
                dealer=dealer
            )
        except Exception as e:
            bid = 'Pass'

        auction.append(bid)

        if bid == 'Pass':
            consecutive_passes += 1
        else:
            consecutive_passes = 0

        # Auction ends
        if consecutive_passes >= 3 and len([b for b in auction if b != 'Pass']) > 0:
            break
        if len(auction) == 4 and all(b == 'Pass' for b in auction):
            break

        current_player = (current_player + 1) % 4

    return auction


def get_final_contract(auction: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """Extract final contract and declarer from auction."""
    if all(b == 'Pass' for b in auction):
        return None, None

    positions = ['North', 'East', 'South', 'West']

    # Find last non-pass, non-double bid
    final_contract = None
    final_idx = -1
    for i, bid in enumerate(auction):
        if bid not in ['Pass', 'X', 'XX']:
            final_contract = bid
            final_idx = i

    if final_contract is None:
        return None, None

    # Find declarer (first player on that side to bid the strain)
    suit = get_suit_from_contract(final_contract)
    declarer_side = positions[final_idx % 4]

    # Partners are N-S or E-W
    if declarer_side in ['North', 'South']:
        possible_declarers = ['North', 'South']
    else:
        possible_declarers = ['East', 'West']

    # First player on that side to bid the strain is declarer
    for i, bid in enumerate(auction):
        if bid not in ['Pass', 'X', 'XX']:
            if positions[i % 4] in possible_declarers:
                if get_suit_from_contract(bid) == suit:
                    return final_contract, positions[i % 4]

    return final_contract, declarer_side


def contract_to_level(contract: str) -> int:
    """Extract level from contract string."""
    if not contract or contract == 'Pass':
        return 0
    try:
        return int(contract[0])
    except (ValueError, IndexError):
        return 0


def get_suit_from_contract(contract: str) -> Optional[str]:
    """Extract suit from contract."""
    if not contract or contract == 'Pass':
        return None
    if 'NT' in contract:
        return 'NT'
    for suit in ['♠', '♥', '♦', '♣']:
        if suit in contract:
            return suit
    return None


def hands_to_pbn(hands: Dict[str, Hand]) -> str:
    """Convert 4 hands to PBN deal string format for DDS."""
    # Format: N:spades.hearts.diamonds.clubs spades.hearts.diamonds.clubs ...
    parts = []
    for pos in ['North', 'East', 'South', 'West']:
        hand = hands[pos]
        # Get cards by suit
        suits = []
        for suit in ['♠', '♥', '♦', '♣']:
            suit_cards = ''.join([c.rank for c in hand.cards if c.suit == suit])
            suits.append(suit_cards)
        parts.append('.'.join(suits))
    return 'N:' + ' '.join(parts)


def get_dds_tricks(hands: Dict[str, Hand], declarer: str, suit: str) -> Optional[int]:
    """Use DDS to calculate max tricks in the given strain from declarer's perspective."""
    if not DDS_AVAILABLE:
        # Fallback: estimate from HCP
        if declarer in ['North', 'South']:
            hcp = hands['North'].hcp + hands['South'].hcp
        else:
            hcp = hands['East'].hcp + hands['West'].hcp

        # Rough estimate: 6 + (hcp - 20) / 3
        estimated = 6 + max(0, (hcp - 20)) // 3
        return min(13, max(6, estimated))

    try:
        # Convert suit to Denom index for to_list()
        # to_list() returns [clubs, diamonds, hearts, spades, nt]
        suit_index_map = {
            '♣': 0,
            '♦': 1,
            '♥': 2,
            '♠': 3,
            'NT': 4
        }
        suit_idx = suit_index_map.get(suit)
        if suit_idx is None:
            return None

        # Player index for to_list(): [N, E, S, W]
        player_index_map = {
            'North': 0,
            'East': 1,
            'South': 2,
            'West': 3
        }
        player_idx = player_index_map.get(declarer)
        if player_idx is None:
            return None

        # Convert hands to Deal
        pbn = hands_to_pbn(hands)
        deal = Deal(pbn)

        # Calculate DD table
        dd_table = calc_dd_table(deal)

        # Get tricks using to_list()
        data = dd_table.to_list()
        return data[suit_idx][player_idx]

    except Exception as e:
        print(f"DDS error: {e}")
        return None


def classify_overbid(delta: int) -> str:
    """Classify overbid severity based on delta."""
    if delta >= 0:
        return "none"
    elif delta == -1:
        return "mild"
    elif delta == -2:
        return "moderate"
    else:
        return "severe"


def analyze_hands(num_hands: int, verbose: bool = False) -> List[HandResult]:
    """Analyze N random hands."""
    engine = BiddingEngine()
    results = []

    print(f"Analyzing {num_hands} hands using {ENGINE_NAME} engine...")
    print(f"DDS available: {DDS_AVAILABLE}")
    print()

    for i in range(num_hands):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{num_hands}")

        hands = create_random_deal()
        auction = run_auction(hands, engine)

        final_contract, declarer = get_final_contract(auction)

        if final_contract is None:
            # Passed out
            result = HandResult(
                hand_id=i,
                north_pbn=str(hands['North']),
                south_pbn=str(hands['South']),
                east_pbn=str(hands['East']),
                west_pbn=str(hands['West']),
                ns_hcp=hands['North'].hcp + hands['South'].hcp,
                ew_hcp=hands['East'].hcp + hands['West'].hcp,
                auction=auction,
                final_contract=None,
                declarer=None,
                tricks_needed=0,
                dds_tricks=None,
                delta=0,
                overbid_severity="none"
            )
        else:
            level = contract_to_level(final_contract)
            suit = get_suit_from_contract(final_contract)
            tricks_needed = level + 6

            dds_tricks = get_dds_tricks(hands, declarer, suit)

            if dds_tricks is not None:
                delta = dds_tricks - tricks_needed
            else:
                delta = 0

            result = HandResult(
                hand_id=i,
                north_pbn=str(hands['North']),
                south_pbn=str(hands['South']),
                east_pbn=str(hands['East']),
                west_pbn=str(hands['West']),
                ns_hcp=hands['North'].hcp + hands['South'].hcp,
                ew_hcp=hands['East'].hcp + hands['West'].hcp,
                auction=auction,
                final_contract=final_contract,
                declarer=declarer,
                tricks_needed=tricks_needed,
                dds_tricks=dds_tricks,
                delta=delta,
                overbid_severity=classify_overbid(delta)
            )

        results.append(result)

        if verbose and final_contract and delta < -1:
            print(f"  Hand {i}: {final_contract} by {declarer} (delta: {delta})")

    return results


def print_summary(results: List[HandResult]):
    """Print summary statistics."""
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    # Filter to hands with contracts
    contracted = [r for r in results if r.final_contract]
    passed_out = len(results) - len(contracted)

    print(f"Total hands: {len(results)}")
    print(f"Passed out: {passed_out}")
    print(f"With contracts: {len(contracted)}")

    if not contracted:
        return

    # Delta statistics
    deltas = [r.delta for r in contracted if r.dds_tricks is not None]
    if deltas:
        avg_delta = sum(deltas) / len(deltas)
        print(f"\nDelta Statistics (DDS tricks - tricks needed):")
        print(f"  Mean delta: {avg_delta:.2f}")
        print(f"  Min delta: {min(deltas)} (worst overbid)")
        print(f"  Max delta: {max(deltas)} (biggest underbid)")

        # Overbid counts
        severe = len([d for d in deltas if d <= -3])
        moderate = len([d for d in deltas if d == -2])
        mild = len([d for d in deltas if d == -1])
        good = len([d for d in deltas if 0 <= d <= 2])
        underbid = len([d for d in deltas if d >= 3])

        print(f"\nOverbid Severity Distribution:")
        print(f"  Severe (delta <= -3):  {severe} ({100*severe/len(deltas):.1f}%)")
        print(f"  Moderate (delta = -2): {moderate} ({100*moderate/len(deltas):.1f}%)")
        print(f"  Mild (delta = -1):     {mild} ({100*mild/len(deltas):.1f}%)")
        print(f"  Good (delta 0-2):      {good} ({100*good/len(deltas):.1f}%)")
        print(f"  Underbid (delta >= 3): {underbid} ({100*underbid/len(deltas):.1f}%)")

    # Show worst overbids
    worst = sorted(contracted, key=lambda r: r.delta)[:10]
    print("\n" + "="*60)
    print("TOP 10 WORST OVERBIDS (lowest delta)")
    print("="*60)

    for r in worst:
        if r.dds_tricks is not None:
            print(f"\nHand {r.hand_id}: {r.final_contract} by {r.declarer}")
            print(f"  Delta: {r.delta} (needed {r.tricks_needed}, can make {r.dds_tricks})")
            print(f"  Auction: {' - '.join(r.auction)}")
            print(f"  N: {r.north_pbn} ({r.ns_hcp} HCP)")
            print(f"  S: {r.south_pbn}")

    # Show biggest underbids
    print("\n" + "="*60)
    print("TOP 10 BIGGEST UNDERBIDS (highest delta)")
    print("="*60)

    underbids = sorted(contracted, key=lambda r: -r.delta)[:10]
    for r in underbids:
        if r.dds_tricks is not None:
            print(f"\nHand {r.hand_id}: {r.final_contract} by {r.declarer}")
            print(f"  Delta: {r.delta} (needed {r.tricks_needed}, can make {r.dds_tricks})")
            print(f"  Auction: {' - '.join(r.auction)}")
            print(f"  N: {r.north_pbn} ({r.ns_hcp} HCP)")
            print(f"  S: {r.south_pbn}")


def main():
    parser = argparse.ArgumentParser(description='Analyze bidding vs DDS trick potential')
    parser.add_argument('--hands', type=int, default=100, help='Number of hands to analyze')
    parser.add_argument('--output', type=str, help='Output file for JSON results')
    parser.add_argument('--verbose', action='store_true', help='Show progress details')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')

    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)

    results = analyze_hands(args.hands, args.verbose)
    print_summary(results)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()
