
"""
Simulation test to verify the preempt_3_major rule.
"""
import sys
import pytest

# Add backend to Python path
sys.path.insert(0, 'backend')

from engine.hand import Hand, Card
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema

def test_preempt_3_major_simulation():
    """
    Tests that a hand with 8 HCP and a 7-card heart suit with 2 top honors
    correctly bids 3 Hearts as a preemptive bid.
    """
    # Hand details: 8 HCP, 7 hearts (QJ10xxxx), no outside aces.
    # This hand has 2 top honors in hearts (Q, J) and satisfies the "Rule of 2 & 3".
    # After the refactoring, this should now pass the `preempt_3_major` rule.
    cards = [
        Card('K', '♠'), Card('2', '♠'), Card('3', '♠'),
        Card('Q', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'), Card('8', '♥'), Card('7', '♥'), Card('6', '♥'),
        Card('Q', '♦'), Card('2', '♦'),
        Card('2', '♣'),
    ]
    hand = Hand(cards)

    # Initialize the bidding engine
    engine = BiddingEngineV2Schema()

    # Set up auction context
    auction_history = []
    current_player = 'North'
    vulnerability = 'None'
    dealer = 'North'

    # Get the bid from the engine
    bid, explanation = engine.get_next_bid(hand, auction_history, current_player, vulnerability, 'detailed', dealer)

    # Verify the result
    expected_bid = '3♥'
    assert bid == expected_bid, f"AI bid {bid} but expected {expected_bid}. Explanation: {explanation.primary_reason}"

