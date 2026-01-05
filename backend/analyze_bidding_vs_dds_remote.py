#!/usr/bin/env python3
"""
Analyze bidding engine quality by comparing final contracts to DDS trick potential.

This script uses a hybrid approach:
- LOCAL: Generate hands, run bidding with V2 Schema Engine
- REMOTE (Production): Calculate DDS trick potential on Linux server
- LOCAL: Compare results and compute delta analysis

This works around the macOS DDS instability issue.

Usage:
    python analyze_bidding_vs_dds_remote.py --hands 100
    python analyze_bidding_vs_dds_remote.py --hands 500 --output results.json
"""
import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
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
    parts = []
    for pos in ['North', 'East', 'South', 'West']:
        hand = hands[pos]
        suits = []
        for suit in ['♠', '♥', '♦', '♣']:
            suit_cards = ''.join([c.rank for c in hand.cards if c.suit == suit])
            suits.append(suit_cards)
        parts.append('.'.join(suits))
    return 'N:' + ' '.join(parts)


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


def run_bidding_locally(num_hands: int, verbose: bool = False) -> List[dict]:
    """Run bidding locally and return hand data for DDS analysis."""
    engine = BiddingEngine()
    hand_data = []

    print(f"Running bidding for {num_hands} hands using {ENGINE_NAME} engine...")

    for i in range(num_hands):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{num_hands}")

        hands = create_random_deal()
        auction = run_auction(hands, engine)
        final_contract, declarer = get_final_contract(auction)

        # Store hand data
        data = {
            'hand_id': i,
            'pbn': hands_to_pbn(hands),
            'north_pbn': str(hands['North']),
            'south_pbn': str(hands['South']),
            'east_pbn': str(hands['East']),
            'west_pbn': str(hands['West']),
            'ns_hcp': hands['North'].hcp + hands['South'].hcp,
            'ew_hcp': hands['East'].hcp + hands['West'].hcp,
            'auction': auction,
            'final_contract': final_contract,
            'declarer': declarer,
            'tricks_needed': (contract_to_level(final_contract) + 6) if final_contract else 0,
            'suit': get_suit_from_contract(final_contract) if final_contract else None
        }
        hand_data.append(data)

    return hand_data


def run_dds_on_production(hand_data: List[dict]) -> List[dict]:
    """
    Run DDS analysis on production server.

    Sends hand data to production, runs DDS there, and returns results.
    """
    print(f"\nSending {len(hand_data)} hands to production for DDS analysis...")

    # Create a script to run on production
    dds_script = '''
import json
import sys

try:
    from endplay.types import Deal
    from endplay.dds import calc_dd_table
    DDS_AVAILABLE = True
except ImportError:
    DDS_AVAILABLE = False
    print("ERROR: DDS not available on production", file=sys.stderr)
    sys.exit(1)

# Read hand data from stdin
hand_data = json.loads(sys.stdin.read())

# Suit and player index maps
suit_index_map = {'♣': 0, '♦': 1, '♥': 2, '♠': 3, 'NT': 4}
player_index_map = {'North': 0, 'East': 1, 'South': 2, 'West': 3}

results = []
for hand in hand_data:
    if not hand.get('final_contract') or not hand.get('declarer') or not hand.get('suit'):
        results.append({'hand_id': hand['hand_id'], 'dds_tricks': None})
        continue

    try:
        pbn = hand['pbn']
        deal = Deal(pbn)
        dd_table = calc_dd_table(deal)
        data = dd_table.to_list()

        suit_idx = suit_index_map.get(hand['suit'])
        player_idx = player_index_map.get(hand['declarer'])

        if suit_idx is not None and player_idx is not None:
            dds_tricks = data[suit_idx][player_idx]
        else:
            dds_tricks = None

        results.append({'hand_id': hand['hand_id'], 'dds_tricks': dds_tricks})
    except Exception as e:
        results.append({'hand_id': hand['hand_id'], 'dds_tricks': None, 'error': str(e)})

print(json.dumps(results))
'''

    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(dds_script)
        script_path = f.name

    try:
        # Prepare hand data JSON
        hand_json = json.dumps(hand_data)

        # Run on production via SSH
        cmd = f'''ssh oracle-bridge "cd /opt/bridge-bidding-app/backend && source venv/bin/activate && python3 -c '{dds_script}'"'''

        # Use subprocess with input
        result = subprocess.run(
            ['ssh', 'oracle-bridge',
             f'cd /opt/bridge-bidding-app/backend && source venv/bin/activate && python3 -'],
            input=f'{dds_script}\n__DATA__\n{hand_json}',
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            print(f"Error from production: {result.stderr}")
            # Fall back to sending data separately
            return run_dds_on_production_fallback(hand_data)

        # Parse results
        dds_results = json.loads(result.stdout)
        return dds_results

    except subprocess.TimeoutExpired:
        print("Timeout waiting for DDS results from production")
        return []
    except json.JSONDecodeError as e:
        print(f"Failed to parse DDS results: {e}")
        print(f"Raw output: {result.stdout[:500]}")
        return run_dds_on_production_fallback(hand_data)
    except Exception as e:
        print(f"Error running DDS on production: {e}")
        return run_dds_on_production_fallback(hand_data)
    finally:
        os.unlink(script_path)


def run_dds_on_production_fallback(hand_data: List[dict]) -> List[dict]:
    """Fallback: Upload data file, run script, download results."""
    print("Using fallback method: file transfer...")

    # Write hand data to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(hand_data, f)
        local_data_path = f.name

    remote_data_path = '/tmp/dds_hand_data.json'
    remote_result_path = '/tmp/dds_results.json'

    try:
        # Upload hand data
        subprocess.run(['scp', local_data_path, f'oracle-bridge:{remote_data_path}'],
                      check=True, capture_output=True)

        # Run DDS analysis on production
        dds_cmd = f'''
cd /opt/bridge-bidding-app/backend && source venv/bin/activate && python3 << 'SCRIPT'
import json
from endplay.types import Deal
from endplay.dds import calc_dd_table

with open('{remote_data_path}') as f:
    hand_data = json.load(f)

suit_index_map = {{'♣': 0, '♦': 1, '♥': 2, '♠': 3, 'NT': 4}}
player_index_map = {{'North': 0, 'East': 1, 'South': 2, 'West': 3}}

results = []
total = len(hand_data)
for i, hand in enumerate(hand_data):
    if (i + 1) % 10 == 0:
        print(f"  DDS Progress: {{i + 1}}/{{total}}", flush=True)

    if not hand.get('final_contract') or not hand.get('declarer') or not hand.get('suit'):
        results.append({{'hand_id': hand['hand_id'], 'dds_tricks': None}})
        continue

    try:
        pbn = hand['pbn']
        deal = Deal(pbn)
        dd_table = calc_dd_table(deal)
        data = dd_table.to_list()

        suit_idx = suit_index_map.get(hand['suit'])
        player_idx = player_index_map.get(hand['declarer'])

        if suit_idx is not None and player_idx is not None:
            dds_tricks = data[suit_idx][player_idx]
        else:
            dds_tricks = None

        results.append({{'hand_id': hand['hand_id'], 'dds_tricks': dds_tricks}})
    except Exception as e:
        results.append({{'hand_id': hand['hand_id'], 'dds_tricks': None, 'error': str(e)}})

with open('{remote_result_path}', 'w') as f:
    json.dump(results, f)

print(f"DDS analysis complete: {{len(results)}} hands processed")
SCRIPT
'''

        result = subprocess.run(['ssh', 'oracle-bridge', dds_cmd],
                               capture_output=True, text=True, timeout=300)
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}")

        # Download results
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            local_result_path = f.name

        subprocess.run(['scp', f'oracle-bridge:{remote_result_path}', local_result_path],
                      check=True, capture_output=True)

        with open(local_result_path) as f:
            dds_results = json.load(f)

        os.unlink(local_result_path)
        return dds_results

    except subprocess.TimeoutExpired:
        print("Timeout waiting for DDS results")
        return []
    except Exception as e:
        print(f"Error in fallback DDS analysis: {e}")
        return []
    finally:
        os.unlink(local_data_path)
        # Clean up remote files
        subprocess.run(['ssh', 'oracle-bridge', f'rm -f {remote_data_path} {remote_result_path}'],
                      capture_output=True)


def merge_results(hand_data: List[dict], dds_results: List[dict]) -> List[HandResult]:
    """Merge local bidding data with remote DDS results."""
    # Create lookup for DDS results
    dds_lookup = {r['hand_id']: r.get('dds_tricks') for r in dds_results}

    results = []
    for hand in hand_data:
        hand_id = hand['hand_id']
        dds_tricks = dds_lookup.get(hand_id)

        if hand['final_contract'] and dds_tricks is not None:
            delta = dds_tricks - hand['tricks_needed']
        else:
            delta = 0

        result = HandResult(
            hand_id=hand_id,
            north_pbn=hand['north_pbn'],
            south_pbn=hand['south_pbn'],
            east_pbn=hand['east_pbn'],
            west_pbn=hand['west_pbn'],
            ns_hcp=hand['ns_hcp'],
            ew_hcp=hand['ew_hcp'],
            auction=hand['auction'],
            final_contract=hand['final_contract'],
            declarer=hand['declarer'],
            tricks_needed=hand['tricks_needed'],
            dds_tricks=dds_tricks,
            delta=delta,
            overbid_severity=classify_overbid(delta)
        )
        results.append(result)

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
    parser = argparse.ArgumentParser(description='Analyze bidding vs DDS (remote DDS)')
    parser.add_argument('--hands', type=int, default=100, help='Number of hands to analyze')
    parser.add_argument('--output', type=str, help='Output file for JSON results')
    parser.add_argument('--verbose', action='store_true', help='Show progress details')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--local-only', action='store_true', help='Skip DDS (bidding analysis only)')

    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)

    # Step 1: Run bidding locally
    hand_data = run_bidding_locally(args.hands, args.verbose)

    if args.local_only:
        print("\n--local-only specified, skipping DDS analysis")
        # Just print basic stats
        contracted = [h for h in hand_data if h['final_contract']]
        print(f"\nBasic Stats:")
        print(f"  Total hands: {len(hand_data)}")
        print(f"  With contracts: {len(contracted)}")
        print(f"  Passed out: {len(hand_data) - len(contracted)}")
        return

    # Step 2: Run DDS on production
    dds_results = run_dds_on_production_fallback(hand_data)

    if not dds_results:
        print("\nFailed to get DDS results from production")
        print("Make sure you can SSH to oracle-bridge and DDS is installed")
        return

    # Step 3: Merge results
    results = merge_results(hand_data, dds_results)

    # Step 4: Print summary
    print_summary(results)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()
