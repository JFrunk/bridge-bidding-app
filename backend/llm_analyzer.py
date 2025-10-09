"""
LLM-Powered Bidding Analysis Tool

This script analyzes simulation results using Claude API to evaluate
the quality and accuracy of bidding decisions according to SAYC conventions.
"""

import json
import os
from datetime import datetime
from anthropic import Anthropic

# Configuration
INPUT_JSON = "simulation_results.json"
OUTPUT_REPORT = "analysis_report.md"
OUTPUT_JSON = "analysis_results.json"
HANDS_TO_ANALYZE = None  # None = all hands, or set to a number like 5 for testing

# Claude API configuration
MODEL = "claude-3-5-sonnet-20241022"  # or "claude-3-opus-20240229" for highest quality

def load_simulation_results():
    """Load the simulation results JSON file."""
    try:
        with open(INPUT_JSON, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {INPUT_JSON} not found. Run simulation_enhanced.py first.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: {INPUT_JSON} is not valid JSON.")
        exit(1)

def format_hand_for_analysis(hand_data):
    """Format hand data for LLM analysis."""
    lines = []
    for suit in ['♠', '♥', '♦', '♣']:
        cards = [card['rank'] for card in hand_data['cards'] if card['suit'] == suit]
        lines.append(f"{suit}: {' '.join(cards) if cards else '--'}")

    lines.append(f"\nHCP: {hand_data['hcp']}")
    lines.append(f"Distribution Points: {hand_data['dist_points']}")
    lines.append(f"Total Points: {hand_data['total_points']}")
    lines.append(f"Balanced: {hand_data['is_balanced']}")
    lines.append(f"Suit Lengths: {' '.join([f'{k}:{v}' for k, v in hand_data['suit_lengths'].items()])}")

    return "\n".join(lines)

def format_auction_for_analysis(auction):
    """Format auction sequence for analysis."""
    lines = []
    for i, entry in enumerate(auction, 1):
        lines.append(f"{i}. {entry['player']}: {entry['bid']}")
        lines.append(f"   System explanation: {entry['explanation']}")
    return "\n".join(lines)

def create_analysis_prompt(hand_result):
    """Create the prompt for Claude to analyze a single hand."""
    hand_num = hand_result['hand_number']
    scenario = hand_result['scenario']
    vulnerability = hand_result['vulnerability']

    prompt = f"""You are an expert bridge player and teacher, analyzing bidding sequences according to Standard American Yellow Card (SAYC) conventions.

Please analyze the following bridge hand and bidding sequence:

**Hand #{hand_num} - Scenario: {scenario}**
**Vulnerability: {vulnerability}**

**HANDS:**

North:
{format_hand_for_analysis(hand_result['hands']['North'])}

East:
{format_hand_for_analysis(hand_result['hands']['East'])}

South:
{format_hand_for_analysis(hand_result['hands']['South'])}

West:
{format_hand_for_analysis(hand_result['hands']['West'])}

**BIDDING SEQUENCE:**
{format_auction_for_analysis(hand_result['auction'])}

---

Please provide a comprehensive analysis covering:

1. **Overall Assessment**: Rate the auction quality (Excellent/Good/Fair/Poor) and provide a 1-2 sentence summary.

2. **Bid-by-Bid Analysis**: For each bid in the sequence:
   - Is the bid correct according to SAYC?
   - If incorrect, what would be the correct bid and why?
   - Does the explanation provided by the system accurately describe the bid?

3. **Critical Issues**: Highlight any serious errors or concerning patterns (e.g., missed game, wrong strain, violation of conventions).

4. **Final Contract Evaluation**:
   - Is the final contract reasonable given the hands?
   - Could a better contract have been reached?
   - Would this contract likely make?

5. **Teaching Points**: What lessons or common mistakes are illustrated by this hand?

Please be specific and reference SAYC conventions by name when applicable (e.g., Stayman, Jacoby Transfer, Blackwood, etc.).

Format your response in clear markdown with headers."""

    return prompt

def analyze_hand_with_llm(client, hand_result, hand_index, total_hands):
    """Send a single hand to Claude for analysis."""
    print(f"  Analyzing hand {hand_index}/{total_hands}...", end=" ")

    prompt = create_analysis_prompt(hand_result)

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            temperature=0.3,  # Lower temperature for more consistent analysis
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        analysis = message.content[0].text
        print("✓")

        return {
            'hand_number': hand_result['hand_number'],
            'scenario': hand_result['scenario'],
            'analysis': analysis,
            'tokens_used': {
                'input': message.usage.input_tokens,
                'output': message.usage.output_tokens
            }
        }

    except Exception as e:
        print(f"✗ Error: {e}")
        return {
            'hand_number': hand_result['hand_number'],
            'scenario': hand_result['scenario'],
            'analysis': f"Error during analysis: {str(e)}",
            'error': str(e)
        }

def generate_summary_statistics(analyses):
    """Generate summary statistics from all analyses."""
    total_hands = len(analyses)
    total_input_tokens = sum(a.get('tokens_used', {}).get('input', 0) for a in analyses)
    total_output_tokens = sum(a.get('tokens_used', {}).get('output', 0) for a in analyses)
    errors = sum(1 for a in analyses if 'error' in a)

    return {
        'total_hands_analyzed': total_hands,
        'successful_analyses': total_hands - errors,
        'failed_analyses': errors,
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'total_tokens': total_input_tokens + total_output_tokens
    }

def create_markdown_report(simulation_data, analyses, statistics):
    """Generate a comprehensive markdown report."""
    lines = []

    lines.append("# Bridge Bidding Analysis Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Simulation Date:** {simulation_data['metadata']['timestamp']}")
    lines.append(f"**Model Used:** {MODEL}")
    lines.append("")

    lines.append("## Summary Statistics")
    lines.append("")
    lines.append(f"- **Total Hands Analyzed:** {statistics['total_hands_analyzed']}")
    lines.append(f"- **Successful Analyses:** {statistics['successful_analyses']}")
    lines.append(f"- **Failed Analyses:** {statistics['failed_analyses']}")
    lines.append(f"- **Total Tokens Used:** {statistics['total_tokens']:,} (Input: {statistics['total_input_tokens']:,}, Output: {statistics['total_output_tokens']:,})")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Individual hand analyses
    for analysis in analyses:
        lines.append(f"## Hand #{analysis['hand_number']} - {analysis['scenario']}")
        lines.append("")
        lines.append(analysis['analysis'])
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)

def main():
    """Main execution function."""
    print("=" * 60)
    print("LLM-Powered Bidding Analysis")
    print("=" * 60)
    print()

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key'")
        print()
        exit(1)

    # Load simulation results
    print(f"Loading simulation results from {INPUT_JSON}...")
    simulation_data = load_simulation_results()
    hands = simulation_data['hands']

    if HANDS_TO_ANALYZE:
        hands = hands[:HANDS_TO_ANALYZE]
        print(f"Analyzing first {HANDS_TO_ANALYZE} hands only (limited for testing)")
    else:
        print(f"Analyzing all {len(hands)} hands")

    print()

    # Initialize Claude client
    client = Anthropic(api_key=api_key)

    # Analyze each hand
    print("Running LLM analysis...")
    analyses = []
    for i, hand_result in enumerate(hands, 1):
        analysis = analyze_hand_with_llm(client, hand_result, i, len(hands))
        analyses.append(analysis)

    print()

    # Generate statistics
    statistics = generate_summary_statistics(analyses)

    # Create markdown report
    print(f"Generating markdown report...")
    report = create_markdown_report(simulation_data, analyses, statistics)

    with open(OUTPUT_REPORT, 'w') as f:
        f.write(report)
    print(f"✓ Report saved to {OUTPUT_REPORT}")

    # Save detailed JSON
    print(f"Saving detailed analysis JSON...")
    output_data = {
        'metadata': {
            'analysis_timestamp': datetime.now().isoformat(),
            'simulation_timestamp': simulation_data['metadata']['timestamp'],
            'model': MODEL
        },
        'statistics': statistics,
        'analyses': analyses
    }

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(output_data, f, indent=2)
    print(f"✓ Analysis data saved to {OUTPUT_JSON}")

    print()
    print("=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print()
    print(f"Summary:")
    print(f"  - Hands analyzed: {statistics['total_hands_analyzed']}")
    print(f"  - Success rate: {statistics['successful_analyses']}/{statistics['total_hands_analyzed']}")
    print(f"  - Total tokens: {statistics['total_tokens']:,}")
    print(f"  - Report: {OUTPUT_REPORT}")
    print()

if __name__ == "__main__":
    main()
