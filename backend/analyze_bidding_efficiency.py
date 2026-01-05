#!/usr/bin/env python3
"""
Comprehensive Bidding Efficiency Analysis.

This script performs a full analysis of bidding engine performance by:
1. Generating random hands and running bidding locally (V2 Schema Engine)
2. Tracking which schema rule was used for each bid
3. Running DDS analysis on production server
4. Computing efficiency gaps and generating visualizations
5. Creating falsification reports to identify problematic rules

The Bidding Efficiency Gap is defined as:
  Gap = Tricks_Required_By_Contract - DDS_Max_Tricks

- Positive Gap (Gap > 0): Overbid - logic failure
- Negative Gap (Gap < 0): Underbid - missed opportunity
- Zero Gap (Gap = 0): Optimal efficiency

Usage:
    python analyze_bidding_efficiency.py --hands 200
    python analyze_bidding_efficiency.py --hands 500 --output report.json --chart efficiency.png
"""
import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any
import warnings

# Suppress matplotlib warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.hand import Hand

# Check if V2 schema engine should be used
USE_V2 = os.environ.get('USE_V2_SCHEMA_ENGINE', 'false').lower() == 'true'
# Check if V1 fallback should be disabled (pure V2 mode)
DISABLE_V1_FALLBACK = os.environ.get('DISABLE_V1_FALLBACK', 'false').lower() == 'true'

if USE_V2:
    from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
    ENGINE_NAME = "V2 Schema" + (" (pure V2)" if DISABLE_V1_FALLBACK else " (with V1 fallback)")

    def BiddingEngine():
        return BiddingEngineV2Schema(use_v1_fallback=not DISABLE_V1_FALLBACK)
else:
    from engine.bidding_engine import BiddingEngine
    ENGINE_NAME = "V1 Legacy"


@dataclass
class BidTrace:
    """Trace of a single bid decision."""
    position: str
    bid: str
    explanation: str
    rule_id: Optional[str] = None
    schema_file: Optional[str] = None
    priority: Optional[int] = None
    hcp: int = 0
    distribution: str = ""


@dataclass
class HandResult:
    """Complete analysis result for one hand."""
    hand_id: int
    hands_pbn: Dict[str, str]
    ns_hcp: int
    ew_hcp: int
    auction: List[str]
    bid_traces: List[BidTrace]
    final_contract: Optional[str]
    declarer: Optional[str]
    tricks_required: int
    dds_tricks: Optional[int]
    gap: int  # positive = overbid, negative = underbid
    is_critical_overbid: bool
    final_rule_id: Optional[str] = None
    final_schema: Optional[str] = None


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
        pbn = []
        for suit in ['♠', '♥', '♦', '♣']:
            suit_cards = [c[0] for c in hand_cards if c[1] == suit]
            pbn.append(''.join(suit_cards))
        hands[pos] = Hand.from_pbn('.'.join(pbn))

    return hands


def get_distribution_string(hand: Hand) -> str:
    """Get distribution pattern like '5-4-3-1'."""
    lengths = []
    for suit in ['♠', '♥', '♦', '♣']:
        length = len([c for c in hand.cards if c.suit == suit])
        lengths.append(length)
    lengths.sort(reverse=True)
    return '-'.join(str(l) for l in lengths)


def run_auction_with_trace(hands: Dict[str, Hand], engine: BiddingEngine, dealer: str = 'North') -> Tuple[List[str], List[BidTrace]]:
    """Run a full auction and return bid sequence with trace information."""
    positions = ['North', 'East', 'South', 'West']
    dealer_idx = positions.index(dealer)

    auction = []
    traces = []
    consecutive_passes = 0
    current_player = dealer_idx

    for _ in range(52):  # Safety limit
        pos = positions[current_player]
        hand = hands[pos]

        try:
            # Get bid with explanation
            bid, explanation = engine.get_next_bid(
                hand=hand,
                auction_history=auction,
                my_position=pos,
                vulnerability='None',
                dealer=dealer
            )

            # Try to extract rule info from V2 engine
            rule_id = None
            schema_file = None
            priority = None

            # V2 engine stores last used rule info
            if hasattr(engine, '_last_rule_id'):
                rule_id = engine._last_rule_id
            if hasattr(engine, '_last_schema_file'):
                schema_file = engine._last_schema_file
            if hasattr(engine, '_last_priority'):
                priority = engine._last_priority

            trace = BidTrace(
                position=pos,
                bid=bid,
                explanation=explanation,
                rule_id=rule_id,
                schema_file=schema_file,
                priority=priority,
                hcp=hand.hcp,
                distribution=get_distribution_string(hand)
            )
            traces.append(trace)

        except Exception as e:
            bid = 'Pass'
            trace = BidTrace(
                position=pos,
                bid=bid,
                explanation=f"Error: {str(e)}",
                hcp=hand.hcp,
                distribution=get_distribution_string(hand)
            )
            traces.append(trace)

        auction.append(bid)

        if bid == 'Pass':
            consecutive_passes += 1
        else:
            consecutive_passes = 0

        if consecutive_passes >= 3 and len([b for b in auction if b != 'Pass']) > 0:
            break
        if len(auction) == 4 and all(b == 'Pass' for b in auction):
            break

        current_player = (current_player + 1) % 4

    return auction, traces


def get_final_contract(auction: List[str]) -> Tuple[Optional[str], Optional[str], int]:
    """Extract final contract, declarer, and bid index from auction."""
    if all(b == 'Pass' for b in auction):
        return None, None, -1

    positions = ['North', 'East', 'South', 'West']

    final_contract = None
    final_idx = -1
    for i, bid in enumerate(auction):
        if bid not in ['Pass', 'X', 'XX']:
            final_contract = bid
            final_idx = i

    if final_contract is None:
        return None, None, -1

    suit = get_suit_from_contract(final_contract)
    declarer_side = positions[final_idx % 4]

    if declarer_side in ['North', 'South']:
        possible_declarers = ['North', 'South']
    else:
        possible_declarers = ['East', 'West']

    for i, bid in enumerate(auction):
        if bid not in ['Pass', 'X', 'XX']:
            if positions[i % 4] in possible_declarers:
                if get_suit_from_contract(bid) == suit:
                    return final_contract, positions[i % 4], final_idx

    return final_contract, declarer_side, final_idx


def contract_to_tricks(contract: str) -> int:
    """Convert contract to tricks required."""
    if not contract or contract == 'Pass':
        return 0
    try:
        return int(contract[0]) + 6
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


def run_dds_on_production(hands_data: List[Dict]) -> Dict[int, Dict]:
    """Run DDS analysis on production server via SSH."""
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(hands_data, f)
        input_file = f.name

    output_file = tempfile.mktemp(suffix='.json')

    # Create remote script
    remote_script = '''
import json
import sys
from endplay.dds import calc_dd_table
from endplay.types import Deal

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file) as f:
    hands_data = json.load(f)

results = {}
for i, h in enumerate(hands_data):
    if (i + 1) % 10 == 0:
        print(f"  DDS Progress: {i + 1}/{len(hands_data)}", file=sys.stderr)

    try:
        pbn = h["pbn"]
        declarer = h["declarer"]
        suit = h["suit"]

        # Map suit and declarer to indices
        suit_map = {"♣": 0, "♦": 1, "♥": 2, "♠": 3, "NT": 4}
        player_map = {"North": 0, "East": 1, "South": 2, "West": 3}

        suit_idx = suit_map.get(suit)
        player_idx = player_map.get(declarer)

        if suit_idx is not None and player_idx is not None:
            deal = Deal(pbn)
            dd_table = calc_dd_table(deal)
            data = dd_table.to_list()
            tricks = data[suit_idx][player_idx]
            results[h["hand_id"]] = {"dds_tricks": tricks}
        else:
            results[h["hand_id"]] = {"dds_tricks": None, "error": "Invalid suit/declarer"}
    except Exception as e:
        results[h["hand_id"]] = {"dds_tricks": None, "error": str(e)}

with open(output_file, 'w') as f:
    json.dump(results, f)

print(f"DDS analysis complete: {len(results)} hands processed", file=sys.stderr)
'''

    try:
        # Upload input file
        remote_input = '/tmp/dds_input.json'
        remote_output = '/tmp/dds_output.json'
        remote_script_path = '/tmp/dds_runner.py'

        subprocess.run(
            ['scp', '-q', input_file, f'oracle-bridge:{remote_input}'],
            check=True, capture_output=True
        )

        # Create and upload script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(remote_script)
            local_script = f.name

        subprocess.run(
            ['scp', '-q', local_script, f'oracle-bridge:{remote_script_path}'],
            check=True, capture_output=True
        )

        # Run on production
        result = subprocess.run(
            ['ssh', 'oracle-bridge', f'cd /opt/bridge-bidding-app/backend && source venv/bin/activate && python3 {remote_script_path} {remote_input} {remote_output}'],
            check=True, capture_output=True, text=True
        )
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Download results
        subprocess.run(
            ['scp', '-q', f'oracle-bridge:{remote_output}', output_file],
            check=True, capture_output=True
        )

        # Read results
        with open(output_file) as f:
            dds_results = json.load(f)

        # Convert string keys to int
        return {int(k): v for k, v in dds_results.items()}

    finally:
        # Cleanup
        for f in [input_file, output_file, local_script]:
            try:
                os.unlink(f)
            except:
                pass


def analyze_hands(num_hands: int, verbose: bool = False) -> List[HandResult]:
    """Analyze N random hands with full tracing."""
    engine = BiddingEngine()
    results = []
    hands_for_dds = []

    print(f"Analyzing {num_hands} hands using {ENGINE_NAME} engine...")
    print()

    # Phase 1: Run bidding locally
    print("Phase 1: Running bidding locally...")
    intermediate_results = []

    for i in range(num_hands):
        if (i + 1) % 20 == 0:
            print(f"  Bidding Progress: {i + 1}/{num_hands}")

        hands = create_random_deal()
        auction, traces = run_auction_with_trace(hands, engine)
        final_contract, declarer, final_bid_idx = get_final_contract(auction)

        hands_pbn = {pos: str(hands[pos]) for pos in hands}

        intermediate_results.append({
            'hand_id': i,
            'hands': hands,
            'hands_pbn': hands_pbn,
            'auction': auction,
            'traces': traces,
            'final_contract': final_contract,
            'declarer': declarer,
            'final_bid_idx': final_bid_idx,
            'ns_hcp': hands['North'].hcp + hands['South'].hcp,
            'ew_hcp': hands['East'].hcp + hands['West'].hcp
        })

        # Prepare DDS request if there's a contract
        if final_contract and declarer:
            suit = get_suit_from_contract(final_contract)
            hands_for_dds.append({
                'hand_id': i,
                'pbn': hands_to_pbn(hands),
                'declarer': declarer,
                'suit': suit
            })

    # Phase 2: Run DDS on production
    print(f"\nPhase 2: Running DDS analysis on {len(hands_for_dds)} hands...")
    dds_results = run_dds_on_production(hands_for_dds) if hands_for_dds else {}

    # Phase 3: Compute gaps and build results
    print("\nPhase 3: Computing efficiency gaps...")
    for r in intermediate_results:
        hand_id = r['hand_id']
        final_contract = r['final_contract']

        if final_contract is None:
            # Passed out
            result = HandResult(
                hand_id=hand_id,
                hands_pbn=r['hands_pbn'],
                ns_hcp=r['ns_hcp'],
                ew_hcp=r['ew_hcp'],
                auction=r['auction'],
                bid_traces=r['traces'],
                final_contract=None,
                declarer=None,
                tricks_required=0,
                dds_tricks=None,
                gap=0,
                is_critical_overbid=False
            )
        else:
            tricks_required = contract_to_tricks(final_contract)
            dds_info = dds_results.get(hand_id, {})
            dds_tricks = dds_info.get('dds_tricks')

            if dds_tricks is not None:
                gap = tricks_required - dds_tricks
            else:
                gap = 0

            # Get rule info from the final contract bid
            final_rule_id = None
            final_schema = None
            if r['final_bid_idx'] >= 0 and r['final_bid_idx'] < len(r['traces']):
                final_trace = r['traces'][r['final_bid_idx']]
                final_rule_id = final_trace.rule_id
                final_schema = final_trace.schema_file

            result = HandResult(
                hand_id=hand_id,
                hands_pbn=r['hands_pbn'],
                ns_hcp=r['ns_hcp'],
                ew_hcp=r['ew_hcp'],
                auction=r['auction'],
                bid_traces=r['traces'],
                final_contract=final_contract,
                declarer=r['declarer'],
                tricks_required=tricks_required,
                dds_tricks=dds_tricks,
                gap=gap,
                is_critical_overbid=(gap >= 3),
                final_rule_id=final_rule_id,
                final_schema=final_schema
            )

        results.append(result)

    return results


def generate_efficiency_chart(results: List[HandResult], output_file: str = 'bidding_efficiency.png'):
    """Generate efficiency visualization chart."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib not available - skipping chart generation")
        return None

    # Filter to hands with contracts and DDS data
    data_points = [(r.dds_tricks, r.tricks_required, r.gap)
                   for r in results
                   if r.dds_tricks is not None and r.tricks_required > 0]

    if not data_points:
        print("No data points for chart")
        return None

    dds_tricks = [d[0] for d in data_points]
    engine_tricks = [d[1] for d in data_points]
    gaps = [d[2] for d in data_points]

    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(12, 8))

    # Add jitter
    np.random.seed(42)
    jitter_x = np.random.normal(0, 0.15, size=len(dds_tricks))
    jitter_y = np.random.normal(0, 0.15, size=len(engine_tricks))

    # Scatter plot with gap coloring
    scatter = ax.scatter(
        np.array(dds_tricks) + jitter_x,
        np.array(engine_tricks) + jitter_y,
        alpha=0.6,
        c=gaps,
        cmap='RdYlGn_r',
        s=50,
        edgecolors='white',
        linewidth=0.5
    )

    # Optimal efficiency line
    ax.plot([0, 13], [0, 13], color='black', linestyle='--',
            alpha=0.5, linewidth=2, label='Optimal Efficiency (Gap = 0)')

    # Overbid threshold lines
    ax.plot([0, 10], [3, 13], color='red', linestyle=':',
            alpha=0.3, linewidth=1, label='Critical Overbid (+3)')

    ax.set_xlabel('DDS Potential (Max Tricks Available)', fontsize=12)
    ax.set_ylabel('Contract Requirement (Tricks Needed)', fontsize=12)
    ax.set_title(f'{ENGINE_NAME} Engine Bidding Efficiency Analysis\n'
                 f'({len(data_points)} contracts analyzed)', fontsize=14)

    # Color bar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Gap (+ = Overbid, - = Underbid)', fontsize=10)

    ax.legend(loc='upper left')
    ax.set_xlim(-0.5, 13.5)
    ax.set_ylim(5.5, 13.5)
    ax.set_xticks(range(14))
    ax.set_yticks(range(6, 14))
    ax.grid(True, alpha=0.3)

    # Add quadrant labels
    ax.text(2, 12, 'OVERBID\n(Aggression)', fontsize=10,
            color='red', alpha=0.7, ha='center')
    ax.text(11, 7, 'UNDERBID\n(Missed Potential)', fontsize=10,
            color='green', alpha=0.7, ha='center')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nChart saved to: {output_file}")
    return output_file


def generate_falsification_report(results: List[HandResult]) -> Dict:
    """Generate report identifying problematic rules."""
    # Count failures by rule
    rule_failures = Counter()
    rule_total = Counter()
    rule_gaps = defaultdict(list)

    for r in results:
        if r.final_contract and r.dds_tricks is not None:
            rule_id = r.final_rule_id or 'unknown'
            rule_total[rule_id] += 1
            rule_gaps[rule_id].append(r.gap)

            if r.gap >= 2:  # Critical overbid
                rule_failures[rule_id] += 1

    # Calculate statistics per rule
    rule_stats = {}
    for rule_id in rule_total:
        gaps = rule_gaps[rule_id]
        rule_stats[rule_id] = {
            'total_uses': rule_total[rule_id],
            'critical_overbids': rule_failures[rule_id],
            'failure_rate': rule_failures[rule_id] / rule_total[rule_id] if rule_total[rule_id] > 0 else 0,
            'mean_gap': sum(gaps) / len(gaps) if gaps else 0,
            'max_gap': max(gaps) if gaps else 0
        }

    # Sort by failure rate
    sorted_rules = sorted(rule_stats.items(),
                          key=lambda x: x[1]['critical_overbids'],
                          reverse=True)

    return {
        'rules': dict(sorted_rules),
        'summary': {
            'total_contracts': sum(rule_total.values()),
            'total_critical_overbids': sum(rule_failures.values()),
            'rules_with_failures': len([r for r in rule_failures if rule_failures[r] > 0])
        }
    }


def print_summary(results: List[HandResult]):
    """Print comprehensive summary statistics."""
    print("\n" + "="*70)
    print("BIDDING EFFICIENCY ANALYSIS SUMMARY")
    print("="*70)

    contracted = [r for r in results if r.final_contract]
    passed_out = len(results) - len(contracted)
    with_dds = [r for r in contracted if r.dds_tricks is not None]

    print(f"\nTotal hands: {len(results)}")
    print(f"Passed out: {passed_out}")
    print(f"With contracts: {len(contracted)}")
    print(f"With DDS data: {len(with_dds)}")

    if not with_dds:
        return

    gaps = [r.gap for r in with_dds]
    avg_gap = sum(gaps) / len(gaps)

    print(f"\n{'='*40}")
    print("EFFICIENCY METRICS")
    print(f"{'='*40}")
    print(f"Mean Gap: {avg_gap:+.2f} tricks")
    print(f"Min Gap: {min(gaps)} (best underbid)")
    print(f"Max Gap: {max(gaps)} (worst overbid)")

    # Gap distribution
    accurate = len([g for g in gaps if g == 0])
    mild_over = len([g for g in gaps if g == 1])
    moderate_over = len([g for g in gaps if g == 2])
    severe_over = len([g for g in gaps if g >= 3])
    mild_under = len([g for g in gaps if g == -1])
    moderate_under = len([g for g in gaps if g == -2])
    severe_under = len([g for g in gaps if g <= -3])

    print(f"\n{'='*40}")
    print("GAP DISTRIBUTION")
    print(f"{'='*40}")
    print(f"Severe Underbid (≤-3): {severe_under:4d} ({100*severe_under/len(gaps):5.1f}%)")
    print(f"Moderate Underbid (-2): {moderate_under:4d} ({100*moderate_under/len(gaps):5.1f}%)")
    print(f"Mild Underbid (-1):     {mild_under:4d} ({100*mild_under/len(gaps):5.1f}%)")
    print(f"Accurate (0):           {accurate:4d} ({100*accurate/len(gaps):5.1f}%)")
    print(f"Mild Overbid (+1):      {mild_over:4d} ({100*mild_over/len(gaps):5.1f}%)")
    print(f"Moderate Overbid (+2):  {moderate_over:4d} ({100*moderate_over/len(gaps):5.1f}%)")
    print(f"Severe Overbid (≥+3):   {severe_over:4d} ({100*severe_over/len(gaps):5.1f}%) ⚠️")

    # Calculate key metrics
    accuracy_rate = accurate / len(gaps)
    overbid_rate = (mild_over + moderate_over + severe_over) / len(gaps)
    underbid_rate = (mild_under + moderate_under + severe_under) / len(gaps)
    critical_failures = severe_over

    print(f"\n{'='*40}")
    print("KEY METRICS")
    print(f"{'='*40}")
    print(f"Accuracy Rate (Gap=0):      {100*accuracy_rate:.1f}%")
    print(f"Overbid Rate (Gap>0):       {100*overbid_rate:.1f}%")
    print(f"Underbid Rate (Gap<0):      {100*underbid_rate:.1f}%")
    print(f"Critical Failures (Gap≥3):  {critical_failures}")

    # Falsification report
    print(f"\n{'='*40}")
    print("RULE FALSIFICATION AUDIT")
    print(f"{'='*40}")

    report = generate_falsification_report(results)

    print(f"\nRules with Critical Overbids (Gap ≥ 2):")
    print("-" * 60)
    print(f"{'Rule ID':<35} {'Uses':>6} {'Fails':>6} {'Rate':>8} {'Mean Gap':>9}")
    print("-" * 60)

    for rule_id, stats in list(report['rules'].items())[:15]:
        if stats['critical_overbids'] > 0:
            print(f"{rule_id:<35} {stats['total_uses']:>6} {stats['critical_overbids']:>6} "
                  f"{100*stats['failure_rate']:>7.1f}% {stats['mean_gap']:>+8.2f}")

    # Top 10 worst overbids
    print(f"\n{'='*70}")
    print("TOP 10 WORST OVERBIDS")
    print("="*70)

    worst = sorted([r for r in with_dds if r.gap > 0], key=lambda r: -r.gap)[:10]

    for r in worst:
        print(f"\nHand {r.hand_id}: {r.final_contract} by {r.declarer}")
        print(f"  Gap: +{r.gap} (required {r.tricks_required}, can make {r.dds_tricks})")
        print(f"  Rule: {r.final_rule_id or 'unknown'}")
        print(f"  Auction: {' - '.join(r.auction)}")
        print(f"  N: {r.hands_pbn['North']} | S: {r.hands_pbn['South']}")


def main():
    parser = argparse.ArgumentParser(description='Comprehensive Bidding Efficiency Analysis')
    parser.add_argument('--hands', type=int, default=100, help='Number of hands to analyze')
    parser.add_argument('--output', type=str, help='Output file for JSON results')
    parser.add_argument('--chart', type=str, default='bidding_efficiency.png', help='Output file for chart')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')

    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)

    results = analyze_hands(args.hands, args.verbose)
    print_summary(results)

    # Generate chart
    generate_efficiency_chart(results, args.chart)

    # Generate JSON report
    if args.output:
        report = {
            'engine': ENGINE_NAME,
            'hands_analyzed': len(results),
            'results': [asdict(r) for r in results],
            'falsification_report': generate_falsification_report(results)
        }
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nFull report saved to: {args.output}")


if __name__ == '__main__':
    main()
