#!/usr/bin/env python3
"""
Comprehensive Bidding AI Analysis
Analyzes the 100-hand simulation to identify specific bidding issues and patterns
"""
import json
import re
from collections import defaultdict, Counter

def analyze_illegal_bids(results_file='simulation_results.json'):
    """Analyze patterns in illegal bid suggestions"""
    with open(results_file, 'r') as f:
        data = json.load(f)

    print("=" * 80)
    print("COMPREHENSIVE BIDDING AI ANALYSIS")
    print("=" * 80)
    print()

    total_hands = len(data['hands'])
    print(f"Total hands tested: {total_hands}")
    print(f"Timestamp: {data['metadata']['timestamp']}")
    print()

    # Track illegal bid patterns
    illegal_bid_by_module = defaultdict(list)
    illegal_bid_types = Counter()
    hands_with_illegal_bids = set()
    total_illegal_bids = 0

    # Track auction characteristics
    auction_stats = {
        'all_pass': 0,
        'game_contracts': 0,
        'part_scores': 0,
        'slam_contracts': 0,
        'passed_out': 0,
        'competitive': 0,
        'total_bids': 0
    }

    # Track bidding module usage
    module_usage = Counter()

    # Track specific bidding issues
    rebid_issues = []
    response_issues = []
    opener_issues = []
    advancer_issues = []

    for hand_idx, hand in enumerate(data['hands'], 1):
        hand_num = hand['hand_number']
        auction = hand['auction']

        # Count bids
        bid_sequence = [entry['bid'] for entry in auction]
        auction_stats['total_bids'] += len(bid_sequence)

        # Check for all-pass
        if all(bid == 'Pass' for bid in bid_sequence):
            auction_stats['all_pass'] += 1
            auction_stats['passed_out'] += 1
            continue

        # Find final contract
        non_pass_bids = [bid for bid in bid_sequence if bid not in ['Pass', 'Double', 'Redouble']]
        if non_pass_bids:
            final_bid = non_pass_bids[-1]
            level = int(final_bid[0]) if final_bid[0].isdigit() else 0

            if level >= 6:
                auction_stats['slam_contracts'] += 1
            elif level >= 3:
                auction_stats['game_contracts'] += 1
            else:
                auction_stats['part_scores'] += 1
        else:
            auction_stats['passed_out'] += 1

        # Check for competitive auctions (both sides bid)
        positions = [entry['player'] for i, entry in enumerate(auction)
                    if entry['bid'] not in ['Pass', 'Double', 'Redouble']]
        ns_bid = any(p in ['North', 'South'] for p in positions)
        ew_bid = any(p in ['East', 'West'] for p in positions)
        if ns_bid and ew_bid:
            auction_stats['competitive'] += 1

        # Analyze explanations for illegal bids and module usage
        for i, entry in enumerate(auction):
            explanation = entry['explanation']

            # Check for illegal bid warnings
            if 'illegal bid' in explanation.lower() or 'overriding to pass' in explanation.lower():
                # Extract module name and illegal bid
                module_match = re.search(r"AI module '(\w+)'", explanation)
                bid_match = re.search(r"illegal bid '([^']+)'", explanation)

                if module_match and bid_match:
                    module = module_match.group(1)
                    illegal_bid = bid_match.group(1)

                    illegal_bid_by_module[module].append({
                        'hand': hand_num,
                        'bid': illegal_bid,
                        'position': entry['player'],
                        'auction_position': i + 1,
                        'full_auction': bid_sequence[:i]
                    })

                    illegal_bid_types[illegal_bid] += 1
                    hands_with_illegal_bids.add(hand_num)
                    total_illegal_bids += 1

                    # Categorize by module type
                    if module == 'openers_rebid':
                        rebid_issues.append({
                            'hand': hand_num,
                            'illegal_bid': illegal_bid,
                            'context': bid_sequence[:i]
                        })
                    elif module == 'responses':
                        response_issues.append({
                            'hand': hand_num,
                            'illegal_bid': illegal_bid,
                            'context': bid_sequence[:i]
                        })
                    elif module == 'advancer_bids':
                        advancer_issues.append({
                            'hand': hand_num,
                            'illegal_bid': illegal_bid,
                            'context': bid_sequence[:i]
                        })

            # Track module usage from explanations
            if 'module:' in explanation.lower() or any(mod in explanation.lower()
                    for mod in ['opening', 'response', 'rebid', 'overcall', 'stayman', 'jacoby']):
                for module in ['openers_rebid', 'responses', 'advancer_bids', 'opening_bids']:
                    if module in explanation.lower():
                        module_usage[module] += 1

    # Print detailed analysis
    print("=" * 80)
    print("ILLEGAL BID ANALYSIS")
    print("=" * 80)
    print()
    print(f"Total illegal bids detected: {total_illegal_bids}")
    print(f"Hands with illegal bids: {len(hands_with_illegal_bids)}/{total_hands} ({len(hands_with_illegal_bids)/total_hands*100:.1f}%)")
    print(f"Hands without issues: {total_hands - len(hands_with_illegal_bids)} ({(total_hands - len(hands_with_illegal_bids))/total_hands*100:.1f}%)")
    print()

    print("ILLEGAL BIDS BY MODULE:")
    print("-" * 80)
    for module, occurrences in sorted(illegal_bid_by_module.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{module}: {len(occurrences)} illegal bids")

        # Show first 3 examples
        for idx, example in enumerate(occurrences[:3], 1):
            print(f"  {idx}. Hand {example['hand']}, Position {example['auction_position']}")
            print(f"     Tried to bid: {example['bid']}")
            print(f"     After: {' - '.join(example['full_auction'][-5:]) if example['full_auction'] else 'Opening'}")

    print()
    print("=" * 80)
    print("TOP 10 ILLEGAL BID TYPES")
    print("=" * 80)
    for bid, count in illegal_bid_types.most_common(10):
        print(f"  {bid}: {count} times")

    print()
    print("=" * 80)
    print("AUCTION STATISTICS")
    print("=" * 80)
    print(f"Total bids made: {auction_stats['total_bids']}")
    print(f"Average bids per hand: {auction_stats['total_bids']/total_hands:.1f}")
    print(f"\nContract Distribution:")
    print(f"  Slam contracts (6+ level): {auction_stats['slam_contracts']} ({auction_stats['slam_contracts']/total_hands*100:.1f}%)")
    print(f"  Game contracts (3-5 level): {auction_stats['game_contracts']} ({auction_stats['game_contracts']/total_hands*100:.1f}%)")
    print(f"  Part scores (1-2 level): {auction_stats['part_scores']} ({auction_stats['part_scores']/total_hands*100:.1f}%)")
    print(f"  Passed out (all pass): {auction_stats['passed_out']} ({auction_stats['passed_out']/total_hands*100:.1f}%)")
    print(f"\nCompetitive auctions: {auction_stats['competitive']} ({auction_stats['competitive']/total_hands*100:.1f}%)")

    print()
    print("=" * 80)
    print("DETAILED ISSUE BREAKDOWN")
    print("=" * 80)

    print(f"\nOPENER'S REBID ISSUES: {len(rebid_issues)}")
    if rebid_issues:
        print("Sample issues:")
        for issue in rebid_issues[:3]:
            print(f"  Hand {issue['hand']}: Tried {issue['illegal_bid']} after {' - '.join(issue['context'][-3:])}")

    print(f"\nRESPONSE ISSUES: {len(response_issues)}")
    if response_issues:
        print("Sample issues:")
        for issue in response_issues[:3]:
            print(f"  Hand {issue['hand']}: Tried {issue['illegal_bid']} after {' - '.join(issue['context'][-3:])}")

    print(f"\nADVANCER ISSUES: {len(advancer_issues)}")
    if advancer_issues:
        print("Sample issues:")
        for issue in advancer_issues[:3]:
            print(f"  Hand {issue['hand']}: Tried {issue['illegal_bid']} after {' - '.join(issue['context'][-3:])}")

    print()
    print("=" * 80)
    print("KEY FINDINGS & RECOMMENDATIONS")
    print("=" * 80)
    print()

    # Calculate issue rate
    issue_rate = (len(hands_with_illegal_bids) / total_hands) * 100

    if issue_rate > 50:
        severity = "CRITICAL"
    elif issue_rate > 30:
        severity = "HIGH"
    elif issue_rate > 10:
        severity = "MODERATE"
    else:
        severity = "LOW"

    print(f"Overall Issue Severity: {severity}")
    print(f"Issue Rate: {issue_rate:.1f}% of hands had illegal bid attempts")
    print()

    print("TOP ISSUES IDENTIFIED:")
    print()

    issues_ranked = sorted(illegal_bid_by_module.items(), key=lambda x: len(x[1]), reverse=True)

    for rank, (module, occurrences) in enumerate(issues_ranked[:3], 1):
        print(f"{rank}. {module.upper()} MODULE")
        print(f"   - {len(occurrences)} illegal bids across {len(set(o['hand'] for o in occurrences))} hands")

        # Analyze patterns
        bid_types = Counter(o['bid'] for o in occurrences)
        print(f"   - Most common illegal bids: {', '.join(f'{bid} ({count})' for bid, count in bid_types.most_common(3))}")
        print()

    print()
    print("RECOMMENDATIONS FOR IMPROVEMENT:")
    print()

    recommendations = []

    if len(rebid_issues) > 10:
        recommendations.append({
            'priority': 'HIGH',
            'module': 'openers_rebid',
            'issue': f'{len(rebid_issues)} illegal rebid attempts',
            'action': 'Review opener rebid logic to ensure bids respect auction level and legality constraints'
        })

    if len(response_issues) > 10:
        recommendations.append({
            'priority': 'HIGH',
            'module': 'responses',
            'issue': f'{len(response_issues)} illegal response attempts',
            'action': 'Review responder logic to ensure responses are legal given opening bid'
        })

    if len(advancer_issues) > 5:
        recommendations.append({
            'priority': 'MEDIUM',
            'module': 'advancer_bids',
            'issue': f'{len(advancer_issues)} illegal advancer attempts',
            'action': 'Review advancer (partner of overcaller) logic for competitive auctions'
        })

    # Add general recommendations
    recommendations.append({
        'priority': 'HIGH',
        'module': 'all',
        'issue': 'Illegal bid detection happening at runtime',
        'action': 'Add pre-validation in each module before returning bids to catch issues earlier'
    })

    recommendations.append({
        'priority': 'MEDIUM',
        'module': 'all',
        'issue': 'Fallback to Pass may be too conservative',
        'action': 'Consider implementing smarter fallback logic that finds the next-best legal bid'
    })

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. [{rec['priority']}] {rec['module'].upper()}")
        print(f"   Issue: {rec['issue']}")
        print(f"   Action: {rec['action']}")
        print()

    print()
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()

    if issue_rate < 10:
        print("✅ GOOD: The bidding AI is performing well with few illegal bid attempts.")
        print("   Minor refinements recommended to reach production quality.")
    elif issue_rate < 30:
        print("⚠️  MODERATE: The bidding AI has noticeable issues that should be addressed.")
        print("   Focus on the top 2-3 problematic modules identified above.")
    else:
        print("❌ NEEDS WORK: The bidding AI has significant issues with illegal bids.")
        print("   Systematic review of bidding logic is strongly recommended.")

    print()
    print(f"Clean hands: {total_hands - len(hands_with_illegal_bids)}/{total_hands}")
    print(f"Success rate: {((total_hands - len(hands_with_illegal_bids))/total_hands*100):.1f}%")
    print()

    return {
        'total_hands': total_hands,
        'hands_with_issues': len(hands_with_illegal_bids),
        'total_illegal_bids': total_illegal_bids,
        'issue_rate': issue_rate,
        'severity': severity,
        'recommendations': recommendations,
        'module_breakdown': {module: len(occurrences) for module, occurrences in illegal_bid_by_module.items()}
    }

if __name__ == "__main__":
    results = analyze_illegal_bids()
