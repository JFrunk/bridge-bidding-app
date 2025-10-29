#!/usr/bin/env python3
"""
Test script to debug why evaluate-bid isn't storing data
"""
import sys
import sqlite3

sys.path.insert(0, 'backend')

from engine.feedback.bidding_feedback import get_feedback_generator
from engine.hand import Hand, Card
from engine.ai.bid_explanation import BidExplanation

# Create a simple test hand
cards = [
    Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
    Card('A', '♥'), Card('K', '♥'),
    Card('A', '♦'), Card('K', '♦'),
    Card('A', '♣'), Card('K', '♣'), Card('Q', '♣'), Card('J', '♣'), Card('T', '♣'), Card('9', '♣')
]
hand = Hand(cards)

# Create feedback generator
print("Creating feedback generator...")
gen = get_feedback_generator('backend/bridge.db')
print(f"Database path: {gen.db_path}")

# Create auction context
auction_context = {
    'history': [],
    'current_player': 'South',
    'dealer': 'North',
    'vulnerability': 'None'
}

# Create optimal explanation
optimal_explanation = BidExplanation('2NT')
optimal_explanation.primary_reason = 'Balanced hand with 20-21 HCP'
optimal_explanation.convention_reference = 'opening_2nt'

# Test evaluate_and_store
print("\nEvaluating and storing bid...")
try:
    feedback = gen.evaluate_and_store(
        user_id=1,
        hand=hand,
        user_bid='2NT',
        auction_context=auction_context,
        optimal_bid='2NT',
        optimal_explanation=optimal_explanation,
        session_id='test_session_123'
    )

    print(f"✓ Feedback generated:")
    print(f"  - Correctness: {feedback.correctness.value}")
    print(f"  - Score: {feedback.score}")
    print(f"  - Impact: {feedback.impact.value}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Check database
print("\nChecking database...")
conn = sqlite3.connect('backend/bridge.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM bidding_decisions")
count = cursor.fetchone()[0]
print(f"Total bidding_decisions records: {count}")

if count > 0:
    cursor.execute("SELECT id, user_bid, optimal_bid, correctness, score FROM bidding_decisions ORDER BY id DESC LIMIT 3")
    print("\nLast 3 records:")
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {row[1]} (optimal: {row[2]}) - {row[3]} - score: {row[4]}")

conn.close()

print("\n✓ Test complete")
