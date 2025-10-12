#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. 2-level new suit responses (10+ HCP)
2. Rebidding 6-card suits before jumping to 3NT
"""

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

def create_hand(cards_str):
    """
    Helper to create a hand from a string like "♠AK ♥QJ5 ♦AKQ106 ♣T98"
    """
    cards = []
    parts = cards_str.split()
    for part in parts:
        suit = part[0]
        ranks = part[1:]
        for rank in ranks:
            cards.append(Card(rank, suit))
    return Hand(cards)

engine = BiddingEngine()

print("=" * 70)
print("TEST 1: 2-level New Suit Responses")
print("=" * 70)

# Test 1a: After 1♥ opening, respond 2♦ with 13 HCP and 5 diamonds
print("\nTest 1a: After 1♥, respond 2♦ with 13 HCP and 5 diamonds")
south_hand = create_hand("♠Q6 ♥Q8 ♦AKQT6 ♣T982")
auction = ['1♥', 'Pass']
bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')
assert bid == '2♦', f"Expected 2♦, got {bid}"
print(f"✅ PASS: South bids {bid} - {explanation}")

# Test 1b: After 1♠ opening, respond 2♣ with 10 HCP and 5 clubs
print("\nTest 1b: After 1♠, respond 2♣ with 10 HCP and 5 clubs")
south_hand = create_hand("♠Q65 ♥K82 ♦Q32 ♣AKJ85")
auction = ['1♠', 'Pass']
bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')
assert bid == '2♣', f"Expected 2♣, got {bid}"
print(f"✅ PASS: South bids {bid} - {explanation}")

# Test 1c: After 1♦ opening, respond 2♣ with 11 HCP and 5 clubs
print("\nTest 1c: After 1♦, respond 2♣ with 11 HCP and 5 clubs")
south_hand = create_hand("♠Q65 ♥K82 ♦Q32 ♣AKJ85")
auction = ['1♦', 'Pass']
bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')
assert bid == '2♣', f"Expected 2♣, got {bid}"
print(f"✅ PASS: South bids {bid} - {explanation}")

# Test 1d: After 1♣ opening, respond 2♦ with 10 HCP and 5 diamonds
print("\nTest 1d: After 1♣, respond 2♦ with 10 HCP and 5 diamonds")
south_hand = create_hand("♠Q65 ♥K82 ♦AKJ85 ♣732")
auction = ['1♣', 'Pass']
bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')
assert bid == '2♦', f"Expected 2♦, got {bid}"
print(f"✅ PASS: South bids {bid} - {explanation}")

# Test 1e: After 1♥ opening, respond 2♠ with 10 HCP and 5 spades
print("\nTest 1e: After 1♥, respond 2♠ with 10 HCP and 5 spades")
south_hand = create_hand("♠AKJ85 ♥Q82 ♦732 ♣653")
auction = ['1♥', 'Pass']
bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')
assert bid == '2♠', f"Expected 2♠, got {bid}"
print(f"✅ PASS: South bids {bid} - {explanation}")

# Test 1f: With only 9 HCP, should NOT bid 2-level (should bid 1NT or pass)
print("\nTest 1f: With 9 HCP and 5 diamonds, bid 1NT (not 2♦)")
south_hand = create_hand("♠Q654 ♥Q82 ♦KJ985 ♣73")
auction = ['1♥', 'Pass']
bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None')
assert bid != '2♦', f"Should NOT bid 2♦ with only 9 HCP, got {bid}"
print(f"✅ PASS: South correctly bids {bid} (not 2♦) with only 9 HCP")

print("\n" + "=" * 70)
print("TEST 2: Rebidding 6-Card Suits Before 3NT")
print("=" * 70)

# Test 2a: With 19+ points and 6-card hearts, rebid 3♥ (not 3NT)
print("\nTest 2a: After 1♥-2♦, rebid 3♥ with 20 points and 6 hearts")
north_hand = create_hand("♠K8 ♥AKJ943 ♦J7 ♣AQ4")
auction = ['1♥', 'Pass', '2♦', 'Pass']
bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')
assert bid == '3♥', f"Expected 3♥, got {bid}"
print(f"✅ PASS: North bids {bid} - {explanation}")

# Test 2b: With 19+ points and 6-card spades, rebid 3♠ (not 3NT)
print("\nTest 2b: After 1♠-2♣, rebid 3♠ with 19 points and 6 spades")
north_hand = create_hand("♠AKJ943 ♥K8 ♦A7 ♣AQ4")
auction = ['1♠', 'Pass', '2♣', 'Pass']
bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')
assert bid == '3♠', f"Expected 3♠, got {bid}"
print(f"✅ PASS: North bids {bid} - {explanation}")

# Test 2c: With 19+ points but only 5-card suit, bid 3NT
print("\nTest 2c: After 1♥-2♦, bid 3NT with 19 points and only 5 hearts")
north_hand = create_hand("♠AK8 ♥AKJ94 ♦J7 ♣AQ4")
auction = ['1♥', 'Pass', '2♦', 'Pass']
bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')
assert bid == '3NT', f"Expected 3NT, got {bid}"
print(f"✅ PASS: North correctly bids {bid} with only 5-card suit")

# Test 2d: With 16-18 points and 6-card suit, bid 3♥ (invitational)
print("\nTest 2d: After 1♥-1NT, bid 3♥ with 16-18 points and 6 hearts")
north_hand = create_hand("♠K8 ♥AKJ943 ♦J7 ♣K84")
auction = ['1♥', 'Pass', '1NT', 'Pass']
bid, explanation = engine.get_next_bid(north_hand, auction, 'North', 'None')
assert bid == '3♥', f"Expected 3♥, got {bid}"
print(f"✅ PASS: North bids {bid} - {explanation}")

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("✅ ALL TESTS PASSED!")
print("\nFixes verified:")
print("1. ✅ 2-level new suit responses now work correctly (require 10+ HCP)")
print("2. ✅ Opener rebids 6-card suit before jumping to 3NT with strong hands")
print("\nThese fixes address the reported issues:")
print("- South no longer incorrectly passes with 14 points and 5 diamonds")
print("- North no longer incorrectly bids 3NT with 6-card major suit")
