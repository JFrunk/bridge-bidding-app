#!/usr/bin/env python3
"""
Debug script to reproduce the bidding from hand_2025-10-10_08-20-12.json
"""

import json
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

# Load the hand data
with open('review_requests/hand_2025-10-10_08-20-12.json', 'r') as f:
    hand_data = json.load(f)

# Reconstruct hands
def create_hand_from_cards(cards_data):
    cards = [Card(c['rank'], c['suit']) for c in cards_data]
    return Hand(cards)

north_hand = create_hand_from_cards(hand_data['all_hands']['North']['cards'])
east_hand = create_hand_from_cards(hand_data['all_hands']['East']['cards'])
south_hand = create_hand_from_cards(hand_data['all_hands']['South']['cards'])
west_hand = create_hand_from_cards(hand_data['all_hands']['West']['cards'])

print("=" * 70)
print("HAND ANALYSIS")
print("=" * 70)
print(f"\nNorth: {north_hand}")
print(f"  HCP: {north_hand.hcp}, Total: {north_hand.total_points}")
print(f"  Distribution: ♠{north_hand.suit_lengths['♠']} ♥{north_hand.suit_lengths['♥']} ♦{north_hand.suit_lengths['♦']} ♣{north_hand.suit_lengths['♣']}")

print(f"\nSouth (You): {south_hand}")
print(f"  HCP: {south_hand.hcp}, Total: {south_hand.total_points}")
print(f"  Distribution: ♠{south_hand.suit_lengths['♠']} ♥{south_hand.suit_lengths['♥']} ♦{south_hand.suit_lengths['♦']} ♣{south_hand.suit_lengths['♣']}")

print("\n" + "=" * 70)
print("BIDDING SIMULATION")
print("=" * 70)

engine = BiddingEngine()
vulnerability = hand_data['vulnerability']

# Simulate the auction
auction = []

# Bid 1: North opens
print("\n--- Bid 1: North to bid ---")
print(f"Auction so far: {[b['bid'] for b in auction]}")
bid, explanation = engine.get_next_bid(north_hand, [b['bid'] for b in auction], 'North', vulnerability)
print(f"North bids: {bid}")
print(f"Explanation: {explanation}")
auction.append({'bid': bid, 'explanation': explanation})

# Bid 2: East responds
print("\n--- Bid 2: East to bid ---")
print(f"Auction so far: {[b['bid'] for b in auction]}")
bid, explanation = engine.get_next_bid(east_hand, [b['bid'] for b in auction], 'East', vulnerability)
print(f"East bids: {bid}")
print(f"Explanation: {explanation}")
auction.append({'bid': bid, 'explanation': explanation})

# Bid 3: South responds - THIS IS THE KEY ONE
print("\n--- Bid 3: South (YOU) to bid ---")
print(f"Auction so far: {[b['bid'] for b in auction]}")
print(f"South hand: ♠Q6 ♥Q8 ♦AKQ106 ♣T982")
print(f"South HCP: {south_hand.hcp}, Total points: {south_hand.total_points}")
bid, explanation = engine.get_next_bid(south_hand, [b['bid'] for b in auction], 'South', vulnerability)
print(f"\n🔍 AI RECOMMENDS: {bid}")
print(f"Explanation: {explanation}")
print(f"\n❓ QUESTION: With 13 HCP and 5 diamonds, should South pass?")
auction.append({'bid': bid, 'explanation': explanation})

# Bid 4: West responds
print("\n--- Bid 4: West to bid ---")
print(f"Auction so far: {[b['bid'] for b in auction]}")
bid, explanation = engine.get_next_bid(west_hand, [b['bid'] for b in auction], 'West', vulnerability)
print(f"West bids: {bid}")
print(f"Explanation: {explanation}")
auction.append({'bid': bid, 'explanation': explanation})

# Bid 5: North rebids - THIS IS THE SECOND KEY ONE
print("\n--- Bid 5: North to rebid ---")
print(f"Auction so far: {[b['bid'] for b in auction]}")
print(f"North hand: ♠K8 ♥AKJ943 ♦J7 ♣AQ4")
print(f"North has 6-card hearts, 18 HCP")
bid, explanation = engine.get_next_bid(north_hand, [b['bid'] for b in auction], 'North', vulnerability)
print(f"\n🔍 AI RECOMMENDS: {bid}")
print(f"Explanation: {explanation}")
print(f"\n❓ QUESTION: Should North bid 3♥ (showing 6+ hearts) instead of 3NT?")
auction.append({'bid': bid, 'explanation': explanation})

print("\n" + "=" * 70)
print("FINAL AUCTION")
print("=" * 70)
for i, bid_obj in enumerate(auction):
    player = ['North', 'East', 'South', 'West'][i % 4]
    print(f"{player}: {bid_obj['bid']} - {bid_obj['explanation']}")
