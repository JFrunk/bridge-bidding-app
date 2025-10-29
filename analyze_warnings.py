#!/usr/bin/env python3
"""
Analyze the WARNING messages from the simulation run
Parse the console output to identify illegal bid patterns
"""
import re
from collections import defaultdict, Counter

# Console output from the simulation
console_output = """
Simulating hand 5/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '4♣'. Overriding to Pass.
Simulating hand 6/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '3♣'. Overriding to Pass.
Simulating hand 7/100 (Scenario: Random)... WARNING: AI module 'advancer_bids' suggested illegal bid '1NT'. Overriding to Pass.
Simulating hand 8/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '3NT'. Overriding to Pass.
Simulating hand 10/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 11/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '1♠'. Overriding to Pass.
Simulating hand 13/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '4♠'. Overriding to Pass.
Simulating hand 14/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '3♦'. Overriding to Pass.
Simulating hand 15/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '3♠'. Overriding to Pass.
Simulating hand 16/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 17/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '2♣'. Overriding to Pass.
Simulating hand 20/100 (Scenario: Random)... WARNING: AI module 'advancer_bids' suggested illegal bid '3♥'. Overriding to Pass.
Simulating hand 21/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 25/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 27/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '3♣'. Overriding to Pass.
Simulating hand 31/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '3♥'. Overriding to Pass.
Simulating hand 33/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '1♠'. Overriding to Pass.
Simulating hand 34/100 (Scenario: Random)... WARNING: AI module 'michaels_cuebid' suggested illegal bid '2♠'. Overriding to Pass.
Simulating hand 36/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '3♠'. Overriding to Pass.
Simulating hand 37/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 38/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '3♥'. Overriding to Pass.
Simulating hand 39/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '1NT'. Overriding to Pass.
Simulating hand 44/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 46/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '3♣'. Overriding to Pass.
Simulating hand 47/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 51/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 63/100 (Scenario: Random)... WARNING: AI module 'advancer_bids' suggested illegal bid '3♣'. Overriding to Pass.
Simulating hand 71/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '2♣'. Overriding to Pass.
Simulating hand 72/100 (Scenario: Random)... WARNING: AI module 'advancer_bids' suggested illegal bid '3♠'. Overriding to Pass.
WARNING: AI module 'advancer_bids' suggested illegal bid '3♠'. Overriding to Pass.
WARNING: AI module 'responses' suggested illegal bid '4♣'. Overriding to Pass.
WARNING: AI module 'advancer_bids' suggested illegal bid '3♠'. Overriding to Pass.
Simulating hand 73/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '1♠'. Overriding to Pass.
Simulating hand 74/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '3NT'. Overriding to Pass.
Simulating hand 76/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '4♦'. Overriding to Pass.
Simulating hand 77/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 83/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '2♦'. Overriding to Pass.
WARNING: AI module 'responses' suggested illegal bid '3NT'. Overriding to Pass.
WARNING: AI module 'advancer_bids' suggested illegal bid '4♦'. Overriding to Pass.
Simulating hand 85/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '2♦'. Overriding to Pass.
Simulating hand 86/100 (Scenario: Random)... WARNING: AI module 'openers_rebid' suggested illegal bid '2NT'. Overriding to Pass.
Simulating hand 87/100 (Scenario: Random)... WARNING: AI module 'responses' suggested illegal bid '2NT'. Overriding to Pass.
"""

def analyze_warnings():
    """Analyze the warning patterns"""
    print("=" * 80)
    print("ILLEGAL BID WARNING ANALYSIS")
    print("=" * 80)
    print()

    # Parse warnings
    warnings = []
    for line in console_output.strip().split('\n'):
        if 'WARNING' in line:
            # Extract hand number
            hand_match = re.search(r'hand (\d+)/', line)
            hand_num = int(hand_match.group(1)) if hand_match else None

            # Extract module
            module_match = re.search(r"module '(\w+)'", line)
            module = module_match.group(1) if module_match else 'unknown'

            # Extract illegal bid
            bid_match = re.search(r"illegal bid '([^']+)'", line)
            illegal_bid = bid_match.group(1) if bid_match else 'unknown'

            warnings.append({
                'hand': hand_num,
                'module': module,
                'bid': illegal_bid
            })

    total_warnings = len(warnings)
    unique_hands = len(set(w['hand'] for w in warnings if w['hand']))

    print(f"Total illegal bid warnings: {total_warnings}")
    print(f"Hands affected: {unique_hands}/100 ({unique_hands}%)")
    print(f"Clean hands: {100 - unique_hands}/100 ({100 - unique_hands}%)")
    print()

    # Analyze by module
    by_module = defaultdict(list)
    for w in warnings:
        by_module[w['module']].append(w)

    print("=" * 80)
    print("ILLEGAL BIDS BY MODULE")
    print("=" * 80)
    print()
    for module, items in sorted(by_module.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{module}: {len(items)} warnings ({len(items)/total_warnings*100:.1f}%)")
        bid_counts = Counter(w['bid'] for w in items)
        print(f"  Most common: {', '.join(f'{bid} ({count})' for bid, count in bid_counts.most_common(3))}")
        print()

    # Analyze by bid type
    by_bid = Counter(w['bid'] for w in warnings)
    print("=" * 80)
    print("MOST COMMON ILLEGAL BIDS")
    print("=" * 80)
    print()
    for bid, count in by_bid.most_common(10):
        print(f"  {bid}: {count} times ({count/total_warnings*100:.1f}%)")
    print()

    # Analyze bid patterns
    print("=" * 80)
    print("BID PATTERN ANALYSIS")
    print("=" * 80)
    print()

    # Categorize bids
    nt_bids = [w for w in warnings if 'NT' in w['bid']]
    suit_bids = [w for w in warnings if any(s in w['bid'] for s in ['♣', '♦', '♥', '♠'])]

    print(f"No Trump bids: {len(nt_bids)} ({len(nt_bids)/total_warnings*100:.1f}%)")
    print(f"Suit bids: {len(suit_bids)} ({len(suit_bids)/total_warnings*100:.1f}%)")
    print()

    # Level analysis
    print("By Level:")
    for level in ['1', '2', '3', '4', '5', '6', '7']:
        level_bids = [w for w in warnings if w['bid'].startswith(level)]
        if level_bids:
            print(f"  Level {level}: {len(level_bids)} bids")
    print()

    # Severity assessment
    print("=" * 80)
    print("SEVERITY ASSESSMENT")
    print("=" * 80)
    print()

    issue_rate = unique_hands
    if issue_rate > 50:
        severity = "CRITICAL"
        color = "🔴"
    elif issue_rate > 30:
        severity = "HIGH"
        color = "🟠"
    elif issue_rate > 10:
        severity = "MODERATE"
        color = "🟡"
    else:
        severity = "LOW"
        color = "🟢"

    print(f"{color} Overall Severity: {severity}")
    print(f"   Issue Rate: {issue_rate}% of hands")
    print()

    # Recommendations
    print("=" * 80)
    print("DETAILED RECOMMENDATIONS")
    print("=" * 80)
    print()

    recs = []

    if by_module.get('openers_rebid', []):
        count = len(by_module['openers_rebid'])
        recs.append({
            'priority': 'HIGH' if count > 10 else 'MEDIUM',
            'module': 'openers_rebid',
            'count': count,
            'issue': f"Opener making {count} illegal rebids",
            'likely_cause': "Rebid logic not checking if bid level is legal given opponent intervention",
            'fix': "Add validation to ensure rebid is higher than last bid in auction"
        })

    if by_module.get('responses', []):
        count = len(by_module['responses'])
        recs.append({
            'priority': 'HIGH' if count > 10 else 'MEDIUM',
            'module': 'responses',
            'count': count,
            'issue': f"Responder making {count} illegal responses",
            'likely_cause': "Response logic not accounting for intervening bids",
            'fix': "Update response calculations to consider minimum legal bid level"
        })

    if by_module.get('advancer_bids', []):
        count = len(by_module['advancer_bids'])
        recs.append({
            'priority': 'MEDIUM',
            'module': 'advancer_bids',
            'count': count,
            'issue': f"Advancer (partner of overcaller) making {count} illegal bids",
            'likely_cause': "Advancer logic not properly tracking auction level",
            'fix': "Review advancer bid selection to ensure legal level"
        })

    # Sort by count
    recs.sort(key=lambda x: x['count'], reverse=True)

    for i, rec in enumerate(recs, 1):
        print(f"{i}. [{rec['priority']}] {rec['module'].upper()}")
        print(f"   Count: {rec['count']} occurrences")
        print(f"   Issue: {rec['issue']}")
        print(f"   Likely Cause: {rec['likely_cause']}")
        print(f"   Recommended Fix: {rec['fix']}")
        print()

    # General recommendations
    print("GENERAL IMPROVEMENTS:")
    print()
    print("1. [HIGH] Add Bid Validation Helper")
    print("   - Create a centralized is_legal_bid(bid, auction) function")
    print("   - All modules should call this before returning a bid")
    print("   - This catches issues before runtime")
    print()

    print("2. [HIGH] Improve Fallback Logic")
    print("   - Instead of always falling back to Pass")
    print("   - Try to find the next legal bid that's similar")
    print("   - For example, if 2NT is illegal, try 3NT or Pass")
    print()

    print("3. [MEDIUM] Add Unit Tests for Illegal Bid Scenarios")
    print("   - Test each module with competitive auctions")
    print("   - Ensure modules respect auction level constraints")
    print("   - Add regression tests for fixed issues")
    print()

    print("4. [MEDIUM] Improve Auction Context Awareness")
    print("   - Modules need better understanding of minimum legal bid")
    print("   - Consider creating an AuctionState helper class")
    print("   - Track current level, strain, and minimum next bid")
    print()

    print("5. [LOW] Add Logging for Near-Misses")
    print("   - Log when a bid is just barely illegal")
    print("   - This helps identify systemic issues in bid calculation")
    print()

    # Summary
    print("=" * 80)
    print("EXECUTIVE SUMMARY")
    print("=" * 80)
    print()

    if issue_rate < 20:
        status = "✅ ACCEPTABLE"
        message = "The bidding AI has some issues but overall performs reasonably well. Focus on fixing the top 2-3 modules with the most issues."
    elif issue_rate < 40:
        status = "⚠️  NEEDS ATTENTION"
        message = "The bidding AI has noticeable quality issues. A systematic review of the problematic modules is recommended."
    else:
        status = "❌ NEEDS SIGNIFICANT WORK"
        message = "The bidding AI has major issues with bid legality. This requires immediate attention before production use."

    print(f"Status: {status}")
    print()
    print(message)
    print()
    print(f"Statistics:")
    print(f"  - Clean hands: {100 - unique_hands}/100 ({100 - unique_hands}%)")
    print(f"  - Hands with issues: {unique_hands}/100 ({unique_hands}%)")
    print(f"  - Total illegal bid attempts: {total_warnings}")
    print(f"  - Average issues per problem hand: {total_warnings/unique_hands:.1f}")
    print()

    print("Next Steps:")
    print("  1. Fix the top module identified above (likely openers_rebid)")
    print("  2. Implement centralized bid validation")
    print("  3. Re-run this 100-hand test")
    print("  4. Iterate until issue rate is < 5%")
    print()

if __name__ == "__main__":
    analyze_warnings()
