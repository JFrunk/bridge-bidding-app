#!/usr/bin/env python3
"""
Test Seed Generator for Penalty Trap Scenarios

Generates hands specifically designed to trigger Doubled Auction Survival (DAS) rules.
These hands create situations where:
1. One side opens/overcalls
2. Gets doubled by opponents
3. Must decide whether to rescue, redouble, or accept

Usage:
    python3 test_seed_generator.py                    # Generate 100 penalty trap hands
    python3 test_seed_generator.py --hands 50        # Generate 50 hands
    python3 test_seed_generator.py --output file.json # Save to specific file
    python3 test_seed_generator.py --analyze          # Run full efficiency analysis
"""

import argparse
import json
import random
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from engine.hand import Hand, Card


@dataclass
class PenaltyTrapScenario:
    """A scenario designed to trigger DAS rules."""
    name: str
    description: str
    south_constraints: Dict[str, Any]
    north_constraints: Dict[str, Any]
    auction_setup: List[str]  # Bids before South's decision
    expected_rule: str  # Which DAS rule should trigger


# Define specific penalty trap scenarios
#
# DAS (Doubled Auction Survival) triggers when:
# 1. Our side bid a contract
# 2. Opponents doubled it (penalty double, not takeout)
# 3. We need to decide: accept, rescue, or redouble
#
# For testing, we need auctions where:
# - RHO just doubled (rho_doubled = True)
# - The double was on a contract WE bid
#
# Dealer is North. Positions by auction index:
# 0=North, 1=East, 2=South, 3=West, 4=North, 5=East, 6=South...
#
# Example: North opens 1♥, East doubles (takeout) - this is NOT a penalty double scenario
# Example: North opens 1♥, East passes, South bids 2♥, West doubles - THIS is penalty!
PENALTY_TRAP_SCENARIOS = [
    PenaltyTrapScenario(
        name="doubled_2h_desperate_rescue",
        description="South raised 1H with singleton trump - EMERGENCY rescue needed",
        south_constraints={
            "hearts": (1, 1),  # SINGLETON trump - adds 50 to panic, triggers rescue
            "hcp": (6, 8),
            "clubs": (5, 6),  # Single clear escape suit (not multiple, so BID not XX)
        },
        north_constraints={
            "hearts": (5, 6),
            "hcp": (12, 14)
        },
        # North=1♥, East=Pass, South=2♥, West=X, North=Pass, East=Pass → South to bid
        # With singleton trump, panic >= 50 → should_rescue = True
        # With only one 4+ card suit (clubs), rescue_action = BID (not REDOUBLE)
        auction_setup=["1♥", "Pass", "2♥", "X", "Pass", "Pass"],
        expected_rule="emergency_suit_rescue"
    ),
    PenaltyTrapScenario(
        name="doubled_2s_sos_needed",
        description="South raised 1S but only singleton trump, needs SOS with 2 escape suits",
        south_constraints={
            "spades": (1, 1),  # SINGLETON trump - adds 50 to panic!
            "hcp": (6, 8),
            "clubs": (4, 5),  # Escape suit 1
            "diamonds": (4, 5),  # Escape suit 2
        },
        north_constraints={
            "spades": (5, 6),
            "hcp": (12, 14)
        },
        # Singleton trump + multiple escape suits → SOS Redouble
        auction_setup=["1♠", "Pass", "2♠", "X", "Pass", "Pass"],
        expected_rule="sos_redouble_force"
    ),
    PenaltyTrapScenario(
        name="strength_redouble_penalty",
        description="South bid 2H, doubled, but South has strong hand",
        south_constraints={
            "hcp": (14, 16),
            "hearts": (4, 5),  # Good support
        },
        north_constraints={
            "hcp": (12, 14),
            "hearts": (5, 6)
        },
        # North=1♥, East=Pass, South=2♥, West=X, North=Pass, East=Pass → South to bid
        auction_setup=["1♥", "Pass", "2♥", "X", "Pass", "Pass"],
        expected_rule="strength_redouble_power"
    ),
    PenaltyTrapScenario(
        name="accept_doubled_good_fit",
        description="South raised 2S doubled but has good fit - accept it",
        south_constraints={
            "hcp": (8, 10),
            "spades": (4, 5),  # Good support
        },
        north_constraints={
            "hcp": (12, 14),
            "spades": (5, 6)
        },
        # North=1♠, East=Pass, South=2♠, West=X, North=Pass, East=Pass → South to bid
        auction_setup=["1♠", "Pass", "2♠", "X", "Pass", "Pass"],
        expected_rule="accept_doubled_contract"
    ),
    PenaltyTrapScenario(
        name="partner_sos_redoubled",
        description="Partner SOS redoubled, South finds cheapest 4-card suit",
        south_constraints={
            "clubs": (4, 5),  # Escape suit
            "hearts": (2, 3),  # Poor hearts
            "hcp": (6, 10)
        },
        north_constraints={
            "hearts": (4, 5),  # Some hearts but misfit after XX
            "hcp": (8, 11)
        },
        # North=1♥, East=Pass, South=2♥, West=X, North=XX (SOS!), East=Pass → South to bid
        # North's XX says "I don't want to play here doubled"
        auction_setup=["1♥", "Pass", "2♥", "X", "XX", "Pass"],
        expected_rule="partner_sos_response"
    )
]


def generate_hand_with_constraints(constraints: Dict[str, Any],
                                    available_cards: List[Card]) -> Tuple[Hand, List[Card]]:
    """Generate a hand matching constraints from available cards."""
    suits = ['♠', '♥', '♦', '♣']
    # Use T for 10 (PBN format)
    ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']

    selected = []
    remaining = available_cards.copy()

    # Group available cards by suit
    by_suit = {suit: [c for c in remaining if c.suit == suit] for suit in suits}

    # Handle specific suit length constraints
    suit_map = {'spades': '♠', 'hearts': '♥', 'diamonds': '♦', 'clubs': '♣'}

    for suit_name, suit_symbol in suit_map.items():
        if suit_name in constraints:
            min_len, max_len = constraints[suit_name]
            target = random.randint(min_len, max_len)
            suit_cards = by_suit[suit_symbol]

            if len(suit_cards) >= target:
                chosen = random.sample(suit_cards, target)
                selected.extend(chosen)
                for c in chosen:
                    remaining.remove(c)
                    by_suit[suit_symbol].remove(c)

    # Fill to 13 cards
    needed = 13 - len(selected)
    if needed > 0 and len(remaining) >= needed:
        fill = random.sample(remaining, needed)
        selected.extend(fill)
        for c in fill:
            remaining.remove(c)

    # Check HCP constraint (using .hcp attribute)
    if 'hcp' in constraints:
        min_hcp, max_hcp = constraints['hcp']
        hand = Hand(selected)
        # Simple retry if HCP out of range (limited attempts)
        attempts = 0
        while (hand.hcp < min_hcp or hand.hcp > max_hcp) and attempts < 10:
            # Swap a high card for a low card or vice versa
            if hand.hcp < min_hcp:
                # Need more HCP - swap low card for high card from remaining
                high_remaining = [c for c in remaining if c.rank in ['A', 'K', 'Q', 'J']]
                low_selected = [c for c in selected if c.rank not in ['A', 'K', 'Q', 'J']]
                if high_remaining and low_selected:
                    swap_out = random.choice(low_selected)
                    swap_in = random.choice(high_remaining)
                    selected.remove(swap_out)
                    selected.append(swap_in)
                    remaining.append(swap_out)
                    remaining.remove(swap_in)
            else:
                # Too much HCP - swap high for low
                low_remaining = [c for c in remaining if c.rank not in ['A', 'K', 'Q', 'J']]
                high_selected = [c for c in selected if c.rank in ['A', 'K', 'Q', 'J']]
                if low_remaining and high_selected:
                    swap_out = random.choice(high_selected)
                    swap_in = random.choice(low_remaining)
                    selected.remove(swap_out)
                    selected.append(swap_in)
                    remaining.append(swap_out)
                    remaining.remove(swap_in)

            hand = Hand(selected)
            attempts += 1

    return Hand(selected), remaining


def create_full_deck() -> List[Card]:
    """Create a standard 52-card deck."""
    suits = ['♠', '♥', '♦', '♣']
    # Use T for 10 (PBN format)
    ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    return [Card(rank, suit) for suit in suits for rank in ranks]


def generate_penalty_trap_deal(scenario: PenaltyTrapScenario, seed: int) -> Dict[str, Any]:
    """Generate a full deal for a penalty trap scenario."""
    random.seed(seed)

    deck = create_full_deck()
    random.shuffle(deck)

    # Generate South hand first (our hero)
    south_hand, remaining = generate_hand_with_constraints(scenario.south_constraints, deck)

    # Generate North hand
    north_hand, remaining = generate_hand_with_constraints(scenario.north_constraints, remaining)

    # Generate East and West from remaining cards
    random.shuffle(remaining)
    east_cards = remaining[:13]
    west_cards = remaining[13:26]

    east_hand = Hand(east_cards)
    west_hand = Hand(west_cards)

    return {
        'seed': seed,
        'scenario': scenario.name,
        'expected_rule': scenario.expected_rule,
        'description': scenario.description,
        'auction_setup': scenario.auction_setup,
        'hands': {
            'north': [f"{c.rank}{c.suit}" for c in north_hand.cards],
            'east': [f"{c.rank}{c.suit}" for c in east_hand.cards],
            'south': [f"{c.rank}{c.suit}" for c in south_hand.cards],
            'west': [f"{c.rank}{c.suit}" for c in west_hand.cards]
        },
        'hcp': {
            'north': north_hand.hcp,
            'east': east_hand.hcp,
            'south': south_hand.hcp,
            'west': west_hand.hcp
        }
    }


def generate_penalty_trap_hands(num_hands: int = 100, base_seed: int = 1000) -> List[Dict[str, Any]]:
    """Generate multiple penalty trap hands across all scenarios."""
    hands = []
    hands_per_scenario = num_hands // len(PENALTY_TRAP_SCENARIOS)

    for i, scenario in enumerate(PENALTY_TRAP_SCENARIOS):
        for j in range(hands_per_scenario):
            seed = base_seed + (i * hands_per_scenario) + j
            deal = generate_penalty_trap_deal(scenario, seed)
            hands.append(deal)

    # Fill remaining hands with random scenario selection
    remaining = num_hands - (hands_per_scenario * len(PENALTY_TRAP_SCENARIOS))
    for k in range(remaining):
        scenario = random.choice(PENALTY_TRAP_SCENARIOS)
        seed = base_seed + num_hands + k
        deal = generate_penalty_trap_deal(scenario, seed)
        hands.append(deal)

    return hands


def analyze_with_das_rules(hands: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze generated hands with the DAS feature extractor."""
    from engine.v2.features.enhanced_extractor import extract_flat_features
    from engine.hand import Hand, Card

    results = {
        'total_hands': len(hands),
        'rules_triggered': {},
        'panic_index_distribution': [],
        'rescue_actions': {'PASS': 0, 'BID': 0, 'REDOUBLE': 0, 'HOLD': 0},
        'expected_vs_actual': []
    }

    for deal in hands:
        # Reconstruct south hand
        south_cards = []
        for card_str in deal['hands']['south']:
            rank = card_str[:-1]
            suit = card_str[-1]
            south_cards.append(Card(rank, suit))
        south_hand = Hand(south_cards)

        # Build auction history from setup
        auction = deal['auction_setup']

        # Determine dealer (North opens typically)
        dealer = 'North'
        my_position = 'South'

        # Extract features using the flat feature extractor
        features = extract_flat_features(
            hand=south_hand,
            auction_history=auction,
            my_position=my_position,
            vulnerability={'ns': False, 'ew': False},
            dealer=dealer
        )

        # Record panic index
        panic_index = features.get('panic_index', 0)
        results['panic_index_distribution'].append(panic_index)

        # Record rescue action
        rescue_action = features.get('rescue_action', 'HOLD')
        results['rescue_actions'][rescue_action] = results['rescue_actions'].get(rescue_action, 0) + 1

        # Track which rules should trigger
        expected = deal['expected_rule']

        # Check if conditions match expected rule
        triggered = None
        if features.get('should_rescue') and features.get('multiple_rescue_suits'):
            triggered = 'sos_redouble_force'
        elif features.get('should_rescue') and features.get('rescue_action') == 'BID':
            triggered = 'emergency_suit_rescue'
        elif features.get('partner_sos_redouble') and features.get('rescue_response_action') == 'BID':
            triggered = 'partner_sos_response'
        elif features.get('can_punish_with_redouble'):
            triggered = 'strength_redouble_power'
        elif features.get('is_doubled') and not features.get('should_rescue'):
            triggered = 'accept_doubled_contract'

        results['expected_vs_actual'].append({
            'scenario': deal['scenario'],
            'expected': expected,
            'triggered': triggered,
            'match': expected == triggered,
            'panic_index': panic_index
        })

        # Count rule triggers
        if triggered:
            results['rules_triggered'][triggered] = results['rules_triggered'].get(triggered, 0) + 1

    # Calculate match rate
    matches = sum(1 for r in results['expected_vs_actual'] if r['match'])
    results['match_rate'] = matches / len(hands) if hands else 0

    return results


def print_analysis_report(results: Dict[str, Any]):
    """Print a formatted analysis report."""
    print("\n" + "=" * 70)
    print("PENALTY TRAP SCENARIO ANALYSIS")
    print("=" * 70)

    print(f"\nTotal hands analyzed: {results['total_hands']}")
    print(f"Rule match rate: {results['match_rate']:.1%}")

    print("\n" + "-" * 40)
    print("RESCUE ACTIONS DISTRIBUTION")
    print("-" * 40)
    for action, count in results['rescue_actions'].items():
        pct = count / results['total_hands'] * 100 if results['total_hands'] else 0
        print(f"  {action:12s}: {count:4d} ({pct:5.1f}%)")

    print("\n" + "-" * 40)
    print("RULES TRIGGERED")
    print("-" * 40)
    for rule, count in sorted(results['rules_triggered'].items(), key=lambda x: -x[1]):
        pct = count / results['total_hands'] * 100 if results['total_hands'] else 0
        print(f"  {rule:30s}: {count:4d} ({pct:5.1f}%)")

    print("\n" + "-" * 40)
    print("PANIC INDEX DISTRIBUTION")
    print("-" * 40)
    panic = results['panic_index_distribution']
    if panic:
        print(f"  Min:     {min(panic):3d}")
        print(f"  Max:     {max(panic):3d}")
        print(f"  Average: {sum(panic)/len(panic):5.1f}")

        # Buckets
        buckets = {'0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}
        for p in panic:
            if p <= 20: buckets['0-20'] += 1
            elif p <= 40: buckets['21-40'] += 1
            elif p <= 60: buckets['41-60'] += 1
            elif p <= 80: buckets['61-80'] += 1
            else: buckets['81-100'] += 1

        print("\n  Panic Index Buckets:")
        for bucket, count in buckets.items():
            pct = count / len(panic) * 100
            bar = '█' * int(pct / 2)
            print(f"    {bucket:8s}: {count:4d} ({pct:5.1f}%) {bar}")

    # Show mismatches
    mismatches = [r for r in results['expected_vs_actual'] if not r['match']]
    if mismatches:
        print("\n" + "-" * 40)
        print(f"MISMATCHES ({len(mismatches)} total)")
        print("-" * 40)
        for m in mismatches[:10]:  # Show first 10
            print(f"  Scenario: {m['scenario']}")
            print(f"    Expected: {m['expected']}")
            print(f"    Triggered: {m['triggered']}")
            print(f"    Panic: {m['panic_index']}")
            print()


def main():
    parser = argparse.ArgumentParser(description='Generate penalty trap test hands')
    parser.add_argument('--hands', type=int, default=100, help='Number of hands to generate')
    parser.add_argument('--seed', type=int, default=1000, help='Base seed for generation')
    parser.add_argument('--output', type=str, default='penalty_trap_hands.json', help='Output file')
    parser.add_argument('--analyze', action='store_true', help='Run DAS analysis on generated hands')
    args = parser.parse_args()

    print(f"Generating {args.hands} penalty trap hands...")
    hands = generate_penalty_trap_hands(args.hands, args.seed)

    # Save to file
    with open(args.output, 'w') as f:
        json.dump(hands, f, indent=2)
    print(f"Saved to {args.output}")

    if args.analyze:
        print("\nAnalyzing with DAS rules...")
        results = analyze_with_das_rules(hands)
        print_analysis_report(results)

        # Save analysis
        analysis_file = args.output.replace('.json', '_analysis.json')
        with open(analysis_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nAnalysis saved to {analysis_file}")


if __name__ == '__main__':
    main()
