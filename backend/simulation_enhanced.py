"""
Enhanced Bidding Simulation with Detailed Logging

This script runs automated bidding simulations and exports results in JSON format
for later analysis by an LLM. It provides comprehensive data about hands, auctions,
and player decisions.
"""

import random
import json
from datetime import datetime
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.hand_constructor import generate_hand_for_convention
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.blackwood import BlackwoodConvention

# Configuration
DEAL_COUNT = 100  # Number of hands to simulate
SCENARIO_COUNT = 10  # Number of scenario-based hands
OUTPUT_JSON = "simulation_results.json"
OUTPUT_TEXT = "simulation_results.txt"

CONVENTION_MAP = {
    "Preempt": PreemptConvention(),
    "JacobyTransfer": JacobyConvention(),
    "Stayman": StaymanConvention(),
    "Blackwood": BlackwoodConvention()
}

def deal_random_hand():
    """Generate a random deal with 4 hands."""
    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)
    return {
        'North': Hand(deck[0:13]),
        'East': Hand(deck[13:26]),
        'South': Hand(deck[26:39]),
        'West': Hand(deck[39:52])
    }

def deal_scenario_hand(scenario, deck):
    """Generate a hand based on a scenario definition."""
    deal = {}
    remaining_deck = list(deck)

    for setup_rule in scenario.get('setup', []):
        position = setup_rule.get('position')
        convention_name = setup_rule.get('generate_for_convention')

        if position and convention_name:
            specialist = CONVENTION_MAP.get(convention_name)
            if specialist:
                hand, remaining_deck = generate_hand_for_convention(specialist, remaining_deck)
                deal[position] = hand

    random.shuffle(remaining_deck)
    for position in ['North', 'East', 'South', 'West']:
        if position not in deal:
            deal[position] = Hand(remaining_deck[:13])
            remaining_deck = remaining_deck[13:]

    return deal

def run_bidding_simulation(engine, deal, vulnerability):
    """
    Run a complete bidding auction until completion.
    Returns auction history with explanations.
    """
    auction_history = []
    players = ['North', 'East', 'South', 'West']
    current_bidder_index = 0

    while True:
        # Check for auction completion (3 consecutive passes after at least one bid)
        if len(auction_history) >= 4:
            non_pass_bids = [entry for entry in auction_history if entry['bid'] != 'Pass']
            if non_pass_bids and all(entry['bid'] == 'Pass' for entry in auction_history[-3:]):
                break

        # Check for all-pass opening (4 consecutive passes)
        if len(auction_history) >= 4 and all(entry['bid'] == 'Pass' for entry in auction_history):
            break

        # Safety break for infinite loops
        if len(auction_history) > 30:
            break

        player_name = players[current_bidder_index]
        hand = deal[player_name]
        bid, explanation = engine.get_next_bid(hand, [entry['bid'] for entry in auction_history], player_name, vulnerability)

        auction_history.append({
            'player': player_name,
            'bid': bid,
            'explanation': explanation
        })

        current_bidder_index = (current_bidder_index + 1) % 4

    return auction_history

def hand_to_dict(hand):
    """Convert a Hand object to a dictionary for JSON export."""
    return {
        'cards': [{'rank': card.rank, 'suit': card.suit} for card in hand.cards],
        'hcp': hand.hcp,
        'dist_points': hand.dist_points,
        'total_points': hand.total_points,
        'suit_lengths': hand.suit_lengths,
        'suit_hcp': hand.suit_hcp,
        'is_balanced': hand.is_balanced
    }

def format_hand_for_text(hand, position):
    """Format a hand as readable text."""
    suits_text = []
    for suit in ['♠', '♥', '♦', '♣']:
        cards = [card.rank for card in hand.cards if card.suit == suit]
        suits_text.append(f"  {suit}: {' '.join(cards) if cards else '--'}")

    return f"{position} (HCP: {hand.hcp}, Total: {hand.total_points}, Balanced: {hand.is_balanced})\n" + "\n".join(suits_text)

def format_auction_for_text(auction):
    """Format auction as a readable table."""
    lines = []
    lines.append("Auction:")
    lines.append("North      East       South      West")
    lines.append("-" * 42)

    for i in range(0, len(auction), 4):
        row = []
        for j in range(4):
            if i + j < len(auction):
                entry = auction[i + j]
                row.append(f"{entry['bid']:<10}")
            else:
                row.append(" " * 10)
        lines.append(" ".join(row))

    return "\n".join(lines)

def format_auction_with_explanations(auction):
    """Format auction with detailed explanations."""
    lines = []
    lines.append("\nDetailed Bidding Sequence:")
    for i, entry in enumerate(auction, 1):
        lines.append(f"{i}. {entry['player']}: {entry['bid']}")
        lines.append(f"   Explanation: {entry['explanation']}")
    return "\n".join(lines)

def main():
    """Run the enhanced simulation."""
    print(f"=" * 60)
    print(f"Enhanced Bridge Bidding Simulation")
    print(f"=" * 60)
    print(f"Configuration:")
    print(f"  - Total hands: {DEAL_COUNT}")
    print(f"  - Scenario hands: {SCENARIO_COUNT}")
    print(f"  - Random hands: {DEAL_COUNT - SCENARIO_COUNT}")
    print(f"  - Output JSON: {OUTPUT_JSON}")
    print(f"  - Output Text: {OUTPUT_TEXT}")
    print(f"=" * 60)
    print()

    engine = BiddingEngine()

    # Load scenarios
    try:
        with open('scenarios.json', 'r') as f:
            scenarios = json.load(f)
    except (IOError, json.JSONDecodeError):
        scenarios = []
        print("Warning: scenarios.json not found. Running random hands only.")

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_hands': DEAL_COUNT,
            'scenario_hands': SCENARIO_COUNT,
            'random_hands': DEAL_COUNT - SCENARIO_COUNT
        },
        'hands': []
    }

    text_output = []
    text_output.append("=" * 60)
    text_output.append("Bridge Bidding Simulation Results")
    text_output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    text_output.append("=" * 60)
    text_output.append("")

    # Run simulations
    for i in range(1, DEAL_COUNT + 1):
        deal = None
        scenario_name = "Random"
        vulnerability = "None"  # Could be randomized: random.choice(["None", "NS", "EW", "Both"])

        # Generate scenario-based hand for first SCENARIO_COUNT deals
        if i <= SCENARIO_COUNT and scenarios:
            scenario = random.choice([s for s in scenarios if s.get("setup")])
            if scenario:
                scenario_name = scenario['name']
                deck = [Card(r, s) for r in '23456789TJQKA' for s in ['♠', '♥', '♦', '♣']]
                deal = deal_scenario_hand(scenario, deck)

        # Generate random hand if no scenario used
        if not deal:
            deal = deal_random_hand()

        print(f"Simulating hand {i}/{DEAL_COUNT} (Scenario: {scenario_name})...", end=" ")

        # Run the auction
        auction = run_bidding_simulation(engine, deal, vulnerability)

        # Store results
        hand_result = {
            'hand_number': i,
            'scenario': scenario_name,
            'vulnerability': vulnerability,
            'hands': {
                position: hand_to_dict(hand)
                for position, hand in deal.items()
            },
            'auction': auction
        }
        results['hands'].append(hand_result)

        # Format text output
        text_output.append(f"\n{'=' * 60}")
        text_output.append(f"Hand #{i} - Scenario: {scenario_name} - Vulnerability: {vulnerability}")
        text_output.append(f"{'=' * 60}")
        text_output.append("")

        for position in ['North', 'East', 'South', 'West']:
            text_output.append(format_hand_for_text(deal[position], position))
            text_output.append("")

        text_output.append(format_auction_for_text(auction))
        text_output.append(format_auction_with_explanations(auction))
        text_output.append("")

        print("✓")

    # Save JSON results
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ JSON results saved to {OUTPUT_JSON}")

    # Save text results
    with open(OUTPUT_TEXT, 'w') as f:
        f.write("\n".join(text_output))
    print(f"✓ Text results saved to {OUTPUT_TEXT}")

    print(f"\n{'=' * 60}")
    print(f"Simulation Complete!")
    print(f"{'=' * 60}")
    print(f"\nNext steps:")
    print(f"1. Review text output: {OUTPUT_TEXT}")
    print(f"2. Run LLM analysis: python llm_analyzer.py")
    print()

if __name__ == "__main__":
    main()
