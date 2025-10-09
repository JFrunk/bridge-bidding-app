"""
Claude Code Integrated Analysis

This script runs simulations and formats the results so you can ask Claude Code
to analyze them directly in your conversation. No API key needed!

Usage:
    python analyze_with_claude_code.py [number_of_hands]

Examples:
    python analyze_with_claude_code.py           # Analyzes 5 hands (default)
    python analyze_with_claude_code.py 10        # Analyzes 10 hands
"""

import sys
import json
from datetime import datetime
from simulation_enhanced import (
    deal_random_hand,
    deal_scenario_hand,
    run_bidding_simulation,
    hand_to_dict,
    BiddingEngine,
    CONVENTION_MAP,
    Card
)

def format_hand_compact(hand_data):
    """Format hand data in a compact, readable format."""
    lines = []
    for suit in ['♠', '♥', '♦', '♣']:
        cards = [card['rank'] for card in hand_data['cards'] if card['suit'] == suit]
        lines.append(f"{suit}: {' '.join(cards) if cards else '--'}")
    lines.append(f"HCP: {hand_data['hcp']}, Total: {hand_data['total_points']}, Balanced: {hand_data['is_balanced']}")
    return "\n".join(lines)

def format_auction_compact(auction):
    """Format auction in a table."""
    lines = ["Auction:"]
    lines.append("N          E          S          W")
    lines.append("-" * 44)

    for i in range(0, len(auction), 4):
        row = []
        for j in range(4):
            if i + j < len(auction):
                bid = auction[i + j]['bid']
                row.append(f"{bid:<10}")
            else:
                row.append(" " * 10)
        lines.append(" ".join(row))

    lines.append("\nBid Explanations:")
    for i, entry in enumerate(auction, 1):
        lines.append(f"{i}. {entry['player']}: {entry['bid']} - {entry['explanation']}")

    return "\n".join(lines)

def main():
    # Get number of hands from command line or default to 5
    num_hands = 5
    if len(sys.argv) > 1:
        try:
            num_hands = int(sys.argv[1])
            if num_hands < 1 or num_hands > 50:
                print("Please specify between 1 and 50 hands")
                return
        except ValueError:
            print("Usage: python analyze_with_claude_code.py [number_of_hands]")
            return

    print("=" * 70)
    print(f"Claude Code Analysis - Generating {num_hands} hands")
    print("=" * 70)
    print()

    engine = BiddingEngine()

    # Load scenarios
    try:
        with open('scenarios.json', 'r') as f:
            scenarios = json.load(f)
    except (IOError, json.JSONDecodeError):
        scenarios = []

    # Generate output
    output_lines = []
    output_lines.append("=" * 70)
    output_lines.append(f"BRIDGE BIDDING ANALYSIS - {num_hands} HANDS")
    output_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append("=" * 70)
    output_lines.append("")
    output_lines.append("Please analyze the following bridge hands and bidding sequences.")
    output_lines.append("For each hand, evaluate:")
    output_lines.append("1. Is each bid correct according to SAYC?")
    output_lines.append("2. What errors or issues do you see?")
    output_lines.append("3. What would be the correct bidding sequence?")
    output_lines.append("4. Rate the overall quality (Excellent/Good/Fair/Poor)")
    output_lines.append("")
    output_lines.append("=" * 70)
    output_lines.append("")

    results = []

    # Generate hands
    scenario_hands = min(2, num_hands)  # Use at most 2 scenarios
    for i in range(1, num_hands + 1):
        deal = None
        scenario_name = "Random"
        vulnerability = "None"

        # Use scenario for first few hands
        if i <= scenario_hands and scenarios:
            scenario = scenarios[i - 1] if i <= len(scenarios) else scenarios[0]
            if scenario and scenario.get('setup'):
                scenario_name = scenario['name']
                deck = [Card(r, s) for r in '23456789TJQKA' for s in ['♠', '♥', '♦', '♣']]
                deal = deal_scenario_hand(scenario, deck)

        if not deal:
            deal = deal_random_hand()

        print(f"Generating hand {i}/{num_hands}...", end=" ")

        # Run auction
        auction = run_bidding_simulation(engine, deal, vulnerability)

        # Store result
        hand_result = {
            'hand_number': i,
            'scenario': scenario_name,
            'vulnerability': vulnerability,
            'hands': {pos: hand_to_dict(hand) for pos, hand in deal.items()},
            'auction': auction
        }
        results.append(hand_result)

        # Format for output
        output_lines.append(f"HAND #{i} - {scenario_name} (Vulnerability: {vulnerability})")
        output_lines.append("=" * 70)
        output_lines.append("")

        for position in ['North', 'East', 'South', 'West']:
            output_lines.append(f"**{position}:**")
            output_lines.append(format_hand_compact(hand_result['hands'][position]))
            output_lines.append("")

        output_lines.append(format_auction_compact(auction))
        output_lines.append("")
        output_lines.append("-" * 70)
        output_lines.append("")

        print("✓")

    # Save to file
    output_file = "claude_code_analysis_input.txt"
    with open(output_file, 'w') as f:
        f.write("\n".join(output_lines))

    # Save JSON for reference
    json_file = "claude_code_analysis_data.json"
    with open(json_file, 'w') as f:
        json.dump({
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'num_hands': num_hands
            },
            'hands': results
        }, f, indent=2)

    print()
    print("=" * 70)
    print("✓ Analysis Ready!")
    print("=" * 70)
    print()
    print(f"Files created:")
    print(f"  - {output_file} (for review)")
    print(f"  - {json_file} (structured data)")
    print()
    print("=" * 70)
    print("NEXT STEP:")
    print("=" * 70)
    print()
    print("Copy and paste the content of the file into your Claude Code chat:")
    print()
    print(f"    cat {output_file}")
    print()
    print("Or simply ask Claude Code:")
    print()
    print(f'    "Please read and analyze {output_file}"')
    print()
    print("Claude Code will then analyze all the hands and provide detailed feedback!")
    print()

if __name__ == "__main__":
    main()
