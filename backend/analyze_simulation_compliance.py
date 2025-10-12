#!/usr/bin/env python3
"""
Analyze simulation results for convention compliance
"""
import json
from collections import defaultdict

def analyze_compliance(results_file='simulation_results.json'):
    with open(results_file, 'r') as f:
        data = json.load(f)

    print("=" * 80)
    print("BRIDGE BIDDING SIMULATION - COMPLIANCE ANALYSIS")
    print("=" * 80)
    print()

    total_hands = len(data['hands'])
    print(f"Total hands tested: {total_hands}")
    print(f"Timestamp: {data['metadata']['timestamp']}")
    print()

    # Track issues
    issues = []
    warnings = []

    # Convention tracking
    conventions_used = defaultdict(list)
    stayman_sequences = []
    jacoby_sequences = []
    blackwood_sequences = []
    preempt_sequences = []
    negative_double_sequences = []

    # Illegal bid tracking
    illegal_bid_pattern = 0

    for hand_idx, hand in enumerate(data['hands'], 1):
        hand_num = hand['hand_number']
        auction = hand['auction']
        hands = hand['hands']

        # Extract auction sequence
        bid_sequence = [entry['bid'] for entry in auction]
        explanations = [entry['explanation'] for entry in auction]

        # Check for Stayman sequences
        if '2♣' in bid_sequence:
            for i, bid in enumerate(bid_sequence):
                if bid == '2♣' and i > 0 and bid_sequence[i-1] == '1NT':
                    stayman_sequences.append({
                        'hand': hand_num,
                        'responder': auction[i]['player'],
                        'responder_hand': hands[auction[i]['player']],
                        'auction': bid_sequence[:i+5] if len(bid_sequence) > i+5 else bid_sequence,
                        'explanation': auction[i]['explanation']
                    })
                    conventions_used['Stayman'].append(hand_num)

                    # Validate Stayman requirements
                    responder_hand = hands[auction[i]['player']]
                    hcp = responder_hand['hcp']
                    suit_lengths = responder_hand['suit_lengths']

                    has_4_card_major = suit_lengths['♥'] >= 4 or suit_lengths['♠'] >= 4
                    has_both_majors = suit_lengths['♥'] >= 4 and suit_lengths['♠'] >= 4

                    if not has_4_card_major:
                        issues.append(f"Hand {hand_num}: Stayman without 4-card major (♥:{suit_lengths['♥']}, ♠:{suit_lengths['♠']})")

                    if hcp < 7:
                        issues.append(f"Hand {hand_num}: Stayman with only {hcp} HCP (need 7+)")
                    elif hcp == 7 and not has_both_majors:
                        issues.append(f"Hand {hand_num}: Stayman with 7 HCP but not 4-4 majors")

        # Check for Jacoby Transfers
        if '2♦' in bid_sequence or '2♥' in bid_sequence:
            for i, bid in enumerate(bid_sequence):
                if i > 0 and bid_sequence[i-1] == '1NT':
                    explanation = auction[i]['explanation'].lower()
                    if 'transfer' in explanation or 'jacoby' in explanation:
                        jacoby_sequences.append({
                            'hand': hand_num,
                            'transfer_bid': bid,
                            'auction': bid_sequence[:i+3] if len(bid_sequence) > i+3 else bid_sequence
                        })
                        conventions_used['Jacoby Transfer'].append(hand_num)

                        # Validate transfer requirements
                        responder_hand = hands[auction[i]['player']]
                        suit_lengths = responder_hand['suit_lengths']

                        # 2♦ transfers to hearts, 2♥ transfers to spades
                        if bid == '2♦' and suit_lengths['♥'] < 5:
                            issues.append(f"Hand {hand_num}: 2♦ Jacoby transfer without 5+ hearts (has {suit_lengths['♥']})")
                        elif bid == '2♥' and suit_lengths['♠'] < 5:
                            issues.append(f"Hand {hand_num}: 2♥ Jacoby transfer without 5+ spades (has {suit_lengths['♠']})")

        # Check for Blackwood
        if '4NT' in bid_sequence:
            for i, bid in enumerate(bid_sequence):
                if bid == '4NT':
                    explanation = auction[i]['explanation'].lower()
                    if 'blackwood' in explanation or 'ace' in explanation:
                        blackwood_sequences.append({
                            'hand': hand_num,
                            'auction': bid_sequence[:i+2] if len(bid_sequence) > i+2 else bid_sequence
                        })
                        conventions_used['Blackwood'].append(hand_num)

        # Check for Preempts
        for i, bid in enumerate(bid_sequence):
            if i == 0 or all(b == 'Pass' for b in bid_sequence[:i]):
                explanation = auction[i]['explanation'].lower()
                if 'preempt' in explanation or 'weak two' in explanation or 'weak 2' in explanation:
                    preempt_sequences.append({
                        'hand': hand_num,
                        'bid': bid,
                        'opener_hand': hands[auction[i]['player']]
                    })
                    conventions_used['Preempts'].append(hand_num)

                    # Validate preempt requirements
                    opener_hand = hands[auction[i]['player']]
                    hcp = opener_hand['hcp']
                    max_suit = max(opener_hand['suit_lengths'].values())

                    if bid.startswith('2') and bid[1] in ['♥', '♠', '♦']:
                        # Weak two: 6-10 HCP, 6-card suit
                        if hcp < 6 or hcp > 10:
                            warnings.append(f"Hand {hand_num}: Weak two with {hcp} HCP (expected 6-10)")
                        if max_suit < 6:
                            issues.append(f"Hand {hand_num}: Weak two without 6-card suit (longest: {max_suit})")

        # Check for Negative Doubles
        for i, bid in enumerate(bid_sequence):
            if bid == 'Double':
                explanation = auction[i]['explanation'].lower()
                if 'negative' in explanation:
                    negative_double_sequences.append({
                        'hand': hand_num,
                        'auction': bid_sequence[:i+1]
                    })
                    conventions_used['Negative Double'].append(hand_num)

        # Check for any Pass after partner's forcing bid
        for i in range(1, len(bid_sequence)):
            if bid_sequence[i] == 'Pass':
                prev_explanation = explanations[i-1].lower()
                if 'forcing' in prev_explanation and auction[i-1]['player'] != auction[i]['player']:
                    # Check if this is partner passing a forcing bid
                    warnings.append(f"Hand {hand_num}: Possible pass after forcing bid (bid {i+1})")

    # Print summary
    print("=" * 80)
    print("CONVENTION USAGE SUMMARY")
    print("=" * 80)
    for conv, hands in sorted(conventions_used.items()):
        print(f"\n{conv}: Used in {len(hands)} hands")
        print(f"  Hand numbers: {sorted(set(hands))[:10]}{'...' if len(hands) > 10 else ''}")

    print()
    print("=" * 80)
    print("COMPLIANCE CHECK RESULTS")
    print("=" * 80)
    print()

    if issues:
        print(f"ERRORS FOUND: {len(issues)}")
        print("-" * 80)
        for issue in issues[:20]:  # Show first 20
            print(f"  ❌ {issue}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more errors")
    else:
        print("✓ No convention compliance errors found!")

    print()

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        print("-" * 80)
        for warning in warnings[:10]:  # Show first 10
            print(f"  ⚠️  {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more warnings")
    else:
        print("✓ No warnings!")

    print()
    print("=" * 80)
    print("DETAILED CONVENTION ANALYSIS")
    print("=" * 80)

    # Stayman details
    if stayman_sequences:
        print(f"\nSTAYMAN USAGE: {len(stayman_sequences)} instances")
        print("-" * 80)
        for seq in stayman_sequences[:3]:
            hand_data = seq['responder_hand']
            print(f"  Hand {seq['hand']} - {seq['responder']}")
            print(f"    HCP: {hand_data['hcp']}, Distribution: {hand_data['suit_lengths']}")
            print(f"    Auction: {' - '.join(seq['auction'][:8])}")

    # Jacoby details
    if jacoby_sequences:
        print(f"\nJACOBY TRANSFER USAGE: {len(jacoby_sequences)} instances")
        print("-" * 80)
        for seq in jacoby_sequences[:3]:
            print(f"  Hand {seq['hand']}: {seq['transfer_bid']} transfer")
            print(f"    Auction: {' - '.join(seq['auction'][:6])}")

    # Preempts details
    if preempt_sequences:
        print(f"\nPREEMPT USAGE: {len(preempt_sequences)} instances")
        print("-" * 80)
        for seq in preempt_sequences[:3]:
            hand_data = seq['opener_hand']
            print(f"  Hand {seq['hand']}: {seq['bid']}")
            print(f"    HCP: {hand_data['hcp']}, Longest suit: {max(hand_data['suit_lengths'].values())} cards")

    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Total hands tested: {total_hands}")
    print(f"Conventions used: {len(conventions_used)} different types")
    print(f"Convention instances: {sum(len(v) for v in conventions_used.values())}")
    print(f"Compliance errors: {len(issues)}")
    print(f"Warnings: {len(warnings)}")
    print()

    if len(issues) == 0:
        print("✅ ALL 100 HANDS PASSED CONVENTION COMPLIANCE CHECKS!")
    else:
        error_rate = (len(issues) / total_hands) * 100
        print(f"⚠️  Compliance rate: {100 - error_rate:.1f}% ({total_hands - len(issues)}/{total_hands} hands)")

    print()
    return issues, warnings, conventions_used

if __name__ == "__main__":
    analyze_compliance()
