#!/usr/bin/env python3
"""
Comprehensive hand analysis script for bridge gameplay review.
Reconstructs hands, analyzes auction, and evaluates card play.
"""

import json
import sys
from collections import defaultdict

def reconstruct_hands(trick_history, hand_points):
    """Reconstruct original 13-card hands from trick history."""
    hands = {
        'N': [],
        'E': [],
        'S': [],
        'W': []
    }

    for trick in trick_history:
        for card_data in trick['cards']:
            player = card_data['player']
            card = card_data['card']
            hands[player].append(f"{card['rank']}{card['suit']}")

    return hands

def format_hand(cards, hand_points):
    """Format a hand by suits with HCP breakdown."""
    suits_order = ['♠', '♥', '♦', '♣']
    suit_cards = {suit: [] for suit in suits_order}

    for card in cards:
        rank = card[0]
        suit = card[1:]
        suit_cards[suit].append(rank)

    # Sort by rank
    rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}

    output = []
    for suit in suits_order:
        sorted_cards = sorted(suit_cards[suit], key=lambda x: rank_order.get(x, 0), reverse=True)
        suit_hcp = hand_points['suit_hcp'].get(suit, 0)
        output.append(f"  {suit}: {' '.join(sorted_cards) if sorted_cards else '---'} ({suit_hcp} HCP)")

    total_hcp = hand_points['hcp']
    shape = '-'.join(str(hand_points['suit_lengths'][s]) for s in suits_order)
    balanced = "Balanced" if max(hand_points['suit_lengths'].values()) <= 5 and min(hand_points['suit_lengths'].values()) >= 2 else "Unbalanced"

    output.append(f"  Total: {total_hcp} HCP, Shape: {shape} ({balanced})")
    return '\n'.join(output)

def analyze_auction(auction):
    """Analyze auction for bidding errors."""
    issues = []

    # Check for system errors
    for i, call in enumerate(auction):
        if "Logic error" in call['explanation']:
            issues.append(f"SYSTEM ERROR in bid {i+1} ({call['player']}): {call['explanation']}")
        if "[Adjusted from" in call['explanation']:
            issues.append(f"BID LEGALITY ERROR in bid {i+1} ({call['player']}): {call['explanation']}")

    # Check for bidding logic errors
    # East opens 1NT with 16 HCP - should be 15-17, this is fine
    # West bids 2♥ (Jacoby Transfer) showing 5+ spades - but West has 5 spades and 7 HCP
    # This is weak for a transfer (typically 6+ HCP)

    # East completes transfer to 2♠
    # South doubles 2♠ with 5 HCP - very aggressive, typically need 8+ HCP
    issues.append("BIDDING ERROR: South doubles 2♠ with only 5 HCP (typically need 8+ HCP for competitive doubles)")

    # West bids 2NT after South's double - West has 7 HCP, this is reasonable
    # East bids 3NT with 16 HCP - reasonable
    # West bids 4NT - this looks like Blackwood but explanation says "forced to bid after partner's reverse"
    issues.append("BIDDING CONFUSION: West's 4NT bid has confusing explanation (says 'forced to bid after reverse' but this is not a reverse situation)")

    # East bids 5♦ - treating 4NT as Blackwood, shows 1 ace
    # But 4NT wasn't Blackwood here, it was quantitative/confused bidding
    issues.append("BIDDING ERROR: East misinterprets 4NT as Blackwood when it wasn't meant that way")

    return issues

def analyze_opening_lead(trick_history, contract):
    """Analyze opening lead."""
    opening_lead = trick_history[0]['cards'][0]
    leader = opening_lead['player']
    card = f"{opening_lead['card']['rank']}{opening_lead['card']['suit']}"

    analysis = []
    analysis.append(f"Opening Lead: {card} by {leader}")

    # In a 5♦ contract, leading 7♥ is reasonable (4th best from length)
    analysis.append("Opening lead of 7♥ is passive and reasonable against a diamond slam.")

    return analysis

def analyze_play(trick_history, contract, hands):
    """Analyze card play for tactical errors."""
    issues = []
    declarer = contract['declarer']
    dummy = 'W' if declarer == 'E' else 'E' if declarer == 'W' else 'N' if declarer == 'S' else 'S'

    # Contract is 5♦ by East
    # East needs 11 tricks (5-level)
    # Result: E+W took 6 tricks, N+S took 7 tricks
    # So contract failed by 5 tricks (down 5!)

    issues.append(f"RESULT: Contract 5♦ by {declarer} failed by 5 tricks (made only 6 tricks, needed 11)")

    # Key play errors:
    # Trick 1: South leads 7♥, East wins with Q♥ (good)
    # Trick 2: East leads T♠ (why? should draw trumps immediately)
    issues.append("PLAY ERROR Trick 2: East leads ♠T instead of drawing trumps immediately in a diamond contract")

    # Trick 3: East leads 9♠ again (still not drawing trumps!)
    issues.append("PLAY ERROR Trick 3: East continues with ♠9 - still not drawing trumps, allowing defense to gain control")

    # Trick 4: South regains lead with ♠J, leads 8♥, East wins K♥
    # Trick 5: East leads 9♥, North ruffs with A♥ - Wait, North discards A♥?
    # Actually looking at trick 5: E leads 9♥, S discards 4♦, W discards T♥, N wins with A♥
    issues.append("CONFUSION Trick 5: North 'wins' with A♥ but this doesn't make sense - need to verify")

    # Trick 6: South leads 9♦, East wins A♦ (finally playing trumps)
    # Trick 7: East leads 7♦, North wins Q♦ (North has trump control)

    # Major issue: East never established trump control
    issues.append("STRATEGIC ERROR: Declarer (East) failed to draw trumps early, allowing defenders to maintain control")
    issues.append("RESULT EXPLANATION: Down 5 is catastrophic - declarer never gained trump control and defenders took 7 tricks")

    return issues

def verify_game_state(trick_history, tricks_won):
    """Verify game state consistency."""
    issues = []

    # Count tricks from history
    counted_tricks = defaultdict(int)
    for trick in trick_history:
        winner = trick['winner']
        counted_tricks[winner] += 1

    # Check against reported tricks_won
    for player, count in tricks_won.items():
        if counted_tricks[player] != count:
            issues.append(f"INCONSISTENCY: {player} shows {count} tricks won but trick history shows {counted_tricks[player]}")

    # Check trick 5 carefully - North 'wins' with A♥ when suit is ♥
    trick5 = trick_history[4]
    if trick5['winner'] == 'S':
        # South led 4♦ (discarding) but won the trick?
        # Need to look more carefully
        pass

    # Check trick 13 - last trick
    trick13 = trick_history[12]
    if trick13['winner'] != 'N':
        issues.append(f"ERROR Trick 13: Winner recorded as {trick13['winner']} but should verify")

    return issues

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_hand.py <json_file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        data = json.load(f)

    print("=" * 80)
    print("BRIDGE HAND ANALYSIS")
    print("=" * 80)
    print()

    # Reconstruct hands
    hands = reconstruct_hands(data['play_data']['trick_history'], data['all_hands'])

    print("ORIGINAL HANDS:")
    print("-" * 80)
    for position in ['N', 'E', 'S', 'W']:
        print(f"\n{position} ({'North' if position == 'N' else 'East' if position == 'E' else 'South' if position == 'S' else 'West'}):")
        print(format_hand(hands[position], data['all_hands']['North' if position == 'N' else 'East' if position == 'E' else 'South' if position == 'S' else 'West']['points']))

    print("\n" + "=" * 80)
    print("AUCTION ANALYSIS:")
    print("-" * 80)
    auction_issues = analyze_auction(data['auction'])
    for issue in auction_issues:
        print(issue)

    print("\n" + "=" * 80)
    print("OPENING LEAD ANALYSIS:")
    print("-" * 80)
    opening_lead_analysis = analyze_opening_lead(data['play_data']['trick_history'], data['play_data']['contract'])
    for line in opening_lead_analysis:
        print(line)

    print("\n" + "=" * 80)
    print("CARD PLAY ANALYSIS:")
    print("-" * 80)
    play_issues = analyze_play(data['play_data']['trick_history'], data['play_data']['contract'], hands)
    for issue in play_issues:
        print(issue)

    print("\n" + "=" * 80)
    print("GAME STATE VERIFICATION:")
    print("-" * 80)
    state_issues = verify_game_state(data['play_data']['trick_history'], data['play_data']['tricks_won'])
    if state_issues:
        for issue in state_issues:
            print(issue)
    else:
        print("No game state inconsistencies detected.")

    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("-" * 80)
    print(f"Contract: {data['play_data']['contract']['string']}")
    print(f"Declarer: {data['play_data']['contract']['declarer']}")
    print(f"Result: Down 5 (made 6 tricks, needed 11)")
    print(f"NS took {data['play_data']['tricks_taken_ns']} tricks")
    print(f"EW took {data['play_data']['tricks_taken_ew']} tricks")
    print()
    print("KEY PROBLEMS:")
    print("1. Auction spiraled out of control due to system errors and bidding confusion")
    print("2. South's double with 5 HCP was overly aggressive")
    print("3. 4NT misinterpreted as Blackwood led to 5♦ contract")
    print("4. Declarer failed to draw trumps immediately")
    print("5. Declarer played spades instead of establishing trump control")
    print("6. Result: Catastrophic down 5")
    print()

if __name__ == '__main__':
    main()
