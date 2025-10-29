#!/usr/bin/env python3
"""
Analyze the bidding in hand_2025-10-28_21-46-15.json
"""

import json

# Load the hand
with open('backend/review_requests/hand_2025-10-28_21-46-15.json', 'r') as f:
    hand_data = json.load(f)

print("=" * 80)
print("BIDDING ANALYSIS FOR HAND 2025-10-28 21:46:15")
print("=" * 80)
print()

# Display the hands
print("HANDS:")
print("-" * 80)
for player in ['North', 'South', 'East', 'West']:
    hand_info = hand_data['all_hands'][player]
    cards_by_suit = {'♠': [], '♥': [], '♦': [], '♣': []}

    for card in hand_info['cards']:
        cards_by_suit[card['suit']].append(card['rank'])

    # Sort cards within each suit
    rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10, '9': 9, '8': 8,
                  '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}

    hand_str = ""
    for suit in ['♠', '♥', '♦', '♣']:
        sorted_cards = sorted(cards_by_suit[suit], key=lambda r: rank_order.get(r, 0), reverse=True)
        hand_str += f"{suit}: {' '.join(sorted_cards) if sorted_cards else '-':<15}"

    points = hand_info['points']
    print(f"{player:6} ({points['hcp']:2} HCP, {points['total_points']:2} total): {hand_str}")

print()
print("=" * 80)
print("AUCTION ANALYSIS:")
print("=" * 80)
print()

# Analyze each bid
auction = hand_data['auction']
auction_bids = []

for i, bid_entry in enumerate(auction, 1):
    player = bid_entry['player']
    bid = bid_entry['bid']
    explanation = bid_entry['explanation']

    auction_bids.append(bid)

    print(f"Bid #{i}: {player} bids {bid}")
    print(f"  Explanation: {explanation}")

    # Check for legality issues
    if "[Adjusted from" in explanation:
        print(f"  ⚠️  BID WAS ADJUSTED FOR LEGALITY")
        # Extract original bid
        import re
        match = re.search(r'\[Adjusted from (.*?) to', explanation)
        if match:
            original = match.group(1)
            print(f"  ⚠️  Original intended bid: {original}")

    # Analyze specific problematic bids
    if i == 4 and player == "West":
        # West's 3♣ bid
        print()
        print("  ANALYSIS OF WEST'S 3♣ BID:")
        print(f"  - West has: {hand_data['all_hands']['West']['points']['hcp']} HCP")
        print(f"  - West has: {hand_data['all_hands']['West']['points']['suit_lengths']['♣']} clubs")
        print(f"  - Auction before West: {auction_bids[:-1]}")
        print(f"  - South bid 2♣, so minimum legal bid is 3♣")
        print(f"  - West wants to bid 2♣ (partner support) but it's illegal")
        print(f"  - System auto-raised to 3♣")
        print()
        print("  ❌ PROBLEM: West has only 8 HCP with 5-card suit")
        print("     - A new suit at 3-level by unpassed hand shows:")
        print("       * Constructive values (10+ HCP) in competitive auctions")
        print("       * Or preemptive jump (weak with long suit)")
        print("     - West's hand doesn't fit either profile!")
        print("     - 8 HCP is too weak for constructive 3♣")
        print("     - CORRECT BID: Pass (hand is too weak)")

    elif i == 7 and player == "South":
        # South's double
        print()
        print("  ANALYSIS OF SOUTH'S DOUBLE:")
        print(f"  - South has: {hand_data['all_hands']['South']['points']['hcp']} HCP")
        suits = hand_data['all_hands']['South']['points']['suit_lengths']
        print(f"  - South shape: ♠{suits['♠']} ♥{suits['♥']} ♦{suits['♦']} ♣{suits['♣']}")
        print(f"  - Auction: 1♥ - 1♠ - 2♣ - 3♣ - P - P - X")
        print()
        print("  CONTEXT: This is supposed to be a negative double")
        print("  - South already bid 2♣ (new suit = forcing)")
        print("  - After three passes, South doubles 3♣")
        print()
        print("  ❌ PROBLEM: This is NOT a negative double!")
        print("     - Negative doubles happen directly after opponent's overcall")
        print("     - South already made a positive bid (2♣)")
        print("     - This double is PENALTY or RESPONSIVE")
        print("     - With 6 clubs, South is doubling for penalty")
        print("     - But it's questionable after showing clubs!")

    elif i == 9 and player == "North":
        # North's 3♠ bid
        print()
        print("  ANALYSIS OF NORTH'S 3♠ BID:")
        print(f"  - North has: {hand_data['all_hands']['North']['points']['hcp']} HCP")
        suits = hand_data['all_hands']['North']['points']['suit_lengths']
        print(f"  - North shape: ♠{suits['♠']} ♥{suits['♥']} ♦{suits['♦']} ♣{suits['♣']}")
        print(f"  - North has only {suits['♠']} spades!")
        print()
        print("  ❌ PROBLEM: North is 'supporting partner's negative double'")
        print("     - But South's double was NOT a negative double")
        print("     - South already bid 2♣ naturally")
        print("     - North has only 3 spades (not a fit)")
        print("     - Original bid was 1♠ (illegal - East already bid 1♠)")
        print("     - System auto-raised to 3♠")
        print()
        print("  ❌ MAJOR ERROR: This makes no sense!")
        print("     - North is bidding a 3-card suit at the 3-level")
        print("     - North is treating a penalty double as negative")
        print("     - With 6 hearts and opening values, North should:")
        print("       * Bid 3♥ (showing extras with 6+ hearts)")
        print("       * Or Pass and defend 3♣X")
        print("     - CORRECT BID: 3♥ or Pass")

    print()

print("=" * 80)
print("SUMMARY OF PROBLEMS:")
print("=" * 80)
print()
print("1. WEST'S 3♣ BID (Bid #4):")
print("   - Intended 2♣, auto-raised to 3♣ for legality")
print("   - 8 HCP is too weak for constructive 3♣")
print("   - Should have PASSED")
print()
print("2. SOUTH'S DOUBLE (Bid #7):")
print("   - System treats this as 'negative double'")
print("   - But South already bid 2♣ (can't be negative)")
print("   - This is a penalty double (South has 6 clubs)")
print("   - Questionable tactical choice")
print()
print("3. NORTH'S 3♠ BID (Bid #9):")
print("   - Intended 1♠, auto-raised to 3♠ for legality")
print("   - North only has 3 spades!")
print("   - North misinterprets South's double as 'negative'")
print("   - Should bid 3♥ (6-card suit, extras) or Pass")
print()
print("FUNDAMENTAL ISSUE:")
print("-" * 80)
print("The auto-raise mechanism doesn't check if the RAISED bid is appropriate!")
print()
print("When a bid is illegal and gets auto-raised:")
print("  ✓ The raised bid IS legal (satisfies auction requirements)")
print("  ✗ The raised bid may be INAPPROPRIATE for the hand strength/shape")
print()
print("Examples from this hand:")
print("  - West wants 2♣ (8 HCP), raised to 3♣")
print("    * 3♣ requires ~10 HCP constructive values")
print("    * West doesn't have it → should decline the bid")
print()
print("  - North wants 1♠ (3-card suit), raised to 3♠")
print("    * 3♠ requires 4+ spades and competitive values")
print("    * North has neither → should pick different bid")
print()
print("RECOMMENDATION:")
print("-" * 80)
print("When auto-raise would create an inappropriate bid:")
print("  1. Check if raised bid still meets convention requirements")
print("  2. If not, reject that bid option entirely")
print("  3. Force AI to choose a different bid (e.g., Pass, different suit)")
print()
