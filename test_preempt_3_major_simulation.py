#!/usr/bin/env python3
"""
Simulation script to verify the preempt_3_major rule.

Tests a specific hand against the V2 bidding engine to ensure it
produces the correct preemptive bid.
"""
import sys

# Add backend to Python path
sys.path.insert(0, 'backend')

from engine.hand import Hand, Card
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema

def run_simulation():
    """
    Runs the simulation for the preempt_3_major rule.
    """
    print("🚀 Starting simulation for preempt_3_major rule...")

    # Hand details: 8 HCP, 7 hearts (QJ10xxxx), no outside aces/kings.
    # We will use QJT9876 of hearts (7 HCP) and a King in another suit (1 HCP).
    # To make it 8 HCP, let's use a king of spades.
    # Hand: S: Kxx H: QJT9876 D: xx C: xx
    cards = [
        Card('K', '♠'), Card('2', '♠'), Card('3', '♠'),
        Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'), Card('8', '♥'), Card('7', '♥'), Card('6', '♥'),
        Card('4', '♦'), Card('5', '♦'),
        Card('4', '♣'),
    ]
    # The solver will recalculate HCP, let's make it more explicit.
    #Hearts: QJT -> 3 HCP. To get to 8, we need 5 more points.
    #Let's add K of spades (3) and J of diamonds (1) and Q of clubs(1). That is 8 HCP.
    #To avoid issues with outside aces/kings, let's put all HCP in the suit.
    # QJT is 3 points. Let's make the suit AKQJT98. That's 10 HCP.
    # The user said 8 HCP.
    # Let's try QJ10xxxx (3 HCP), and add 5 HCP outside but no aces or kings.
    # Let's do QJ10 hearts, and then J spades, J diamonds, J clubs. That's 3 + 1 + 1 + 1 = 6 HCP.
    # Let's do QJ hearts (2), J spades, J diamonds, J clubs = 5 HCP.
    # The user specified "7 hearts (QJ10xxxx)". This is 3 HCP.
    # "8 HCP". So 5 HCP outside.
    # "no outside aces". A=4, K=3, Q=2, J=1.
    # So we can have 5 jacks. Which is not possible.
    # Let's re-read "QJ10xxxx". This implies Q, J, 10 and 4 other low hearts.
    # Q=2, J=1, T=0. So 3 HCP in hearts.
    # We need 5 more HCP. No aces. So one King (3) and one Queen (2).
    # Hand: S: Kxx H: QJT9876 D: Qxx C: xx
    # But the user said "no outside aces or kings", I misread. The prompt says "no outside aces".
    # Ok, let's try again.
    # 8 HCP, 7 hearts (QJ10xxxx), no outside aces.
    # Hearts: QJ10xxxx = Q(2) + J(1) = 3 HCP.
    # Remaining HCP = 5.
    # Can be K(3) + Q(2). But K is a top honor.
    # The prompt says "no outside aces". It doesn't say no outside kings.
    # So a King is fine.
    # Let's make a hand:
    # Hearts: QJT98765 (7 cards, 3 HCP)
    # Spades: Kxx (3 HCP)
    # Diamonds: Qx (2 HCP)
    # Clubs: x
    # Total HCP: 3 + 3 + 2 = 8 HCP.
    # 7 hearts. Looks good.
    cards = [
        Card('K', '♠'), Card('2', '♠'), Card('3', '♠'),
        Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'), Card('8', '♥'), Card('7', '♥'), Card('6', '♥'),
        Card('Q', '♦'), Card('2', '♦'),
        Card('2', '♣'),
    ]

    hand = Hand(cards)

    print("\n📝 Hand created for simulation:")
    print(f"   - Cards: {', '.join(str(c) for c in cards)}")
    print(f"   - HCP: {hand.hcp}")
    print(f"   - Heart length: {hand.suit_lengths['♥']}")
    print(f"   - Heart HCP: {hand.suit_hcp['♥']}")
    print(f"   - Top honors in hearts: {hand.top_honors['♥']}")

    # Initialize the bidding engine
    engine = BiddingEngineV2Schema()
    print("\n🤖 Bidding engine initialized (V2 Schema).")

    # Set up auction context
    auction_history = []
    current_player = 'North'
    vulnerability = 'None'
    dealer = 'North'

    print("\n🔍 Evaluating bid...")
    bid, explanation = engine.get_next_bid(hand, auction_history, current_player, vulnerability, 'detailed', dealer)

    print(f"\n🧠 AI decided bid: {bid}")
    print(f"   - Explanation: {explanation.primary_reason}")

    # Verify the result
    expected_bid = '3♥'
    print(f"\n🚦 Verifying result against expected bid: {expected_bid}")

    if bid == expected_bid:
        print("\n✅ PASSED: The AI correctly bid 3♥ as a preemptive bid.")
        print("   The new `preempt_3_major` rule with the `top_honors` constraint is working as expected.")
    else:
        print(f"\n❌ FAILED: The AI bid {bid}, but {expected_bid} was expected.")
        print("   There might be an issue with the rule's priority or conditions.")
        # Exit with a non-zero code to indicate failure, useful for CI
        sys.exit(1)

if __name__ == "__main__":
    run_simulation()
