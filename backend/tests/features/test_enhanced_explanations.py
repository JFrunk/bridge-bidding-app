"""
Test script demonstrating the enhanced explanation features.

This shows:
1. Three explanation levels (simple, detailed, expert)
2. SAYC rule references with URLs
3. JSON API for structured data
"""

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
import json


def test_explanation_levels():
    """Test all three explanation levels."""
    print("=" * 80)
    print("TEST 1: EXPLANATION LEVELS")
    print("=" * 80)

    # Create a 16 HCP balanced hand
    cards = [
        Card('A', '♠'), Card('K', '♠'), Card('5', '♠'),
        Card('Q', '♥'), Card('5', '♥'), Card('3', '♥'),
        Card('A', '♦'), Card('K', '♦'), Card('3', '♦'),
        Card('7', '♣'), Card('6', '♣'), Card('4', '♣'), Card('2', '♣')
    ]
    hand = Hand(cards)

    print(f"\nHand: {hand.hcp} HCP, Distribution: {hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
    print(f"Balanced: {hand.is_balanced}\n")

    engine = BiddingEngine()

    for level in ['simple', 'detailed', 'expert']:
        print(f"\n{'─' * 80}")
        print(f"LEVEL: {level.upper()}")
        print('─' * 80)
        bid, explanation = engine.get_next_bid(hand, [], 'North', 'None', level)
        print(f"Bid: {bid}\n")
        print(explanation)


def test_structured_json():
    """Test the JSON API endpoint."""
    print("\n\n" + "=" * 80)
    print("TEST 2: STRUCTURED JSON OUTPUT")
    print("=" * 80)

    # Same hand as above
    cards = [
        Card('A', '♠'), Card('K', '♠'), Card('5', '♠'),
        Card('Q', '♥'), Card('5', '♥'), Card('3', '♥'),
        Card('A', '♦'), Card('K', '♦'), Card('3', '♦'),
        Card('7', '♣'), Card('6', '♣'), Card('4', '♣'), Card('2', '♣')
    ]
    hand = Hand(cards)

    engine = BiddingEngine()
    bid, explanation_dict = engine.get_next_bid_structured(hand, [], 'North', 'None')

    print(f"\nBid: {bid}\n")
    print("Structured Explanation (JSON):")
    print(json.dumps(explanation_dict, indent=2))


def test_response_with_support():
    """Test response bids with support points calculation."""
    print("\n\n" + "=" * 80)
    print("TEST 3: RESPONSE WITH SUPPORT (EXPERT LEVEL)")
    print("=" * 80)

    # Hand with 4-card heart support and 13 HCP
    cards = [
        Card('K', '♠'), Card('8', '♠'),
        Card('Q', '♥'), Card('J', '♥'), Card('9', '♥'), Card('7', '♥'),
        Card('A', '♦'), Card('6', '♦'), Card('4', '♦'),
        Card('K', '♣'), Card('5', '♣'), Card('3', '♣'), Card('2', '♣')
    ]
    hand = Hand(cards)

    print(f"\nHand: {hand.hcp} HCP, Distribution: {hand.suit_lengths['♠']}-{hand.suit_lengths['♥']}-{hand.suit_lengths['♦']}-{hand.suit_lengths['♣']}")
    print("Auction: 1♥ - Pass - Pass")
    print("(Partner opened 1♥, you're responding)\n")

    engine = BiddingEngine()
    auction = ['1♥', 'Pass', 'Pass']  # North opened 1♥, East passed, South to bid
    bid, explanation = engine.get_next_bid(hand, auction, 'South', 'None', 'expert')

    print(f"Bid: {bid}\n")
    print(explanation)


def test_sayc_rules():
    """Show SAYC rule in action."""
    print("\n\n" + "=" * 80)
    print("TEST 4: SAYC RULE REFERENCE")
    print("=" * 80)

    from engine.ai.sayc_rules import get_rule, SAYC_RULES

    print("\nSample SAYC Rules in Database:\n")

    for rule_id in ['1nt_opening', 'simple_raise', 'stayman', 'blackwood']:
        rule = get_rule(rule_id)
        if rule:
            print(f"• {rule.name} ({rule.category})")
            print(f"  {rule.description}")
            print(f"  📚 {rule.url}")
            print()

    print(f"Total rules in database: {len(SAYC_RULES)}")


if __name__ == "__main__":
    test_explanation_levels()
    test_structured_json()
    test_response_with_support()
    test_sayc_rules()

    print("\n\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nFeatures demonstrated:")
    print("  ✓ Three explanation levels (simple, detailed, expert)")
    print("  ✓ SAYC rule references with URLs")
    print("  ✓ Structured JSON API output")
    print("  ✓ Hand value analysis")
    print("  ✓ Alternative bid consideration")
    print("  ✓ Support points calculation")
    print("\nNext steps:")
    print("  • Add explanation level selector in frontend")
    print("  • Make SAYC URLs clickable")
    print("  • Build custom explanation UI from JSON data")
