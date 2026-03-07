"""
Vetting Script: Compare Learning Skill Generators vs BiddingEngine

For each skill generator, generates sample hands and compares:
  - Generator's get_expected_response() bid
  - BiddingEngine.get_next_bid() bid (the "real" answer)

Reports all divergences with full hand details for analysis.

Usage:
    python3 vet_learning_hands.py                    # All skills, 50 hands each
    python3 vet_learning_hands.py --hands 100        # More hands
    python3 vet_learning_hands.py --skill single_raise  # Single skill
    python3 vet_learning_hands.py --output results.json  # Save results
"""

import argparse
import json
import sys
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from engine.bidding_engine import BiddingEngine
from engine.hand import Hand
from engine.learning.skill_hand_generators import (
    SKILL_GENERATORS, create_deck, calculate_support_points
)


# Skills that involve bidding decisions (exclude HCP counting, suit quality, etc.)
BIDDING_SKILLS = {
    # Opening skills
    'when_to_open': {'auction': [], 'position': 'South', 'dealer': 'South'},
    'opening_one_major': {'auction': [], 'position': 'South', 'dealer': 'South'},
    'opening_one_minor': {'auction': [], 'position': 'South', 'dealer': 'South'},
    'opening_one_suit': {'auction': [], 'position': 'South', 'dealer': 'South'},
    'opening_1nt': {'auction': [], 'position': 'South', 'dealer': 'South'},
    'opening_2c_strong': {'auction': [], 'position': 'South', 'dealer': 'South'},
    'opening_2nt': {'auction': [], 'position': 'South', 'dealer': 'South'},

    # Response skills (partner opened, two passes, we respond)
    'single_raise': None,  # Dynamic - depends on partner_opened
    'limit_raise': None,
    'game_raise': None,
    'new_suit_response': None,
    'dustbin_1nt_response': None,
    'two_over_one_response': None,

    # Comprehensive response skills
    'responding_to_major': None,
    'responding_to_minor': None,
    'responding_to_1nt': None,
    'responding_to_2c': None,
    'responding_to_2nt': None,
}


def build_response_auction(generator) -> Tuple[List[str], str, str]:
    """Build the auction context for a response skill.

    Partner opens, opponents pass, we respond.
    Returns (auction_history, position, dealer).
    """
    partner_bid = None

    # Try various attribute names for the partner's opening
    for attr in ['partner_opened', 'opening_bid']:
        partner_bid = getattr(generator, attr, None)
        if partner_bid:
            break

    if not partner_bid:
        return None, None, None

    # Partner is North (opened), East passes, South (us) responds
    auction = [partner_bid, 'Pass']
    return auction, 'South', 'North'


def format_hand(hand: Hand) -> str:
    """Format hand for display."""
    suits = []
    for suit in ['♠', '♥', '♦', '♣']:
        cards = [c.rank for c in hand.cards if c.suit == suit]
        cards_str = ''.join(cards) if cards else '-'
        suits.append(f'{suit}{cards_str}')
    return ' '.join(suits)


def vet_skill(skill_id: str, engine: BiddingEngine, num_hands: int) -> Dict:
    """Vet a single skill's hands against the BiddingEngine.

    Returns dict with results summary and divergence details.
    """
    if skill_id not in SKILL_GENERATORS:
        return {'skill_id': skill_id, 'error': 'No generator found', 'divergences': []}

    gen_class = SKILL_GENERATORS[skill_id]
    results = {
        'skill_id': skill_id,
        'hands_tested': 0,
        'agreements': 0,
        'divergences': [],
        'errors': [],
        'skipped': 0,
    }

    for i in range(num_hands):
        try:
            generator = gen_class()
            deck = create_deck()
            hand, remaining = generator.generate(deck)

            if hand is None:
                results['errors'].append(f'Hand {i}: generation failed')
                continue

            # Get generator's expected response
            expected = generator.get_expected_response(hand)
            gen_bid = expected.get('bid')

            if gen_bid is None:
                results['skipped'] += 1
                continue

            # Build auction context
            if skill_id in BIDDING_SKILLS and BIDDING_SKILLS[skill_id] is not None:
                ctx = BIDDING_SKILLS[skill_id]
                auction = list(ctx['auction'])
                position = ctx['position']
                dealer = ctx['dealer']
            else:
                auction, position, dealer = build_response_auction(generator)
                if auction is None:
                    results['skipped'] += 1
                    continue

            # Get BiddingEngine's answer
            try:
                engine_bid, engine_explanation = engine.get_next_bid(
                    hand, auction, position, 'None', dealer=dealer
                )
            except Exception as e:
                results['errors'].append(f'Hand {i}: engine error: {str(e)[:100]}')
                continue

            results['hands_tested'] += 1

            # Normalize bids for comparison
            gen_bid_norm = gen_bid.strip().upper().replace('PASS', 'Pass')
            engine_bid_norm = engine_bid.strip().upper().replace('PASS', 'Pass')

            if gen_bid_norm == engine_bid_norm:
                results['agreements'] += 1
            else:
                # Calculate support points if trump suit is known
                trump = None
                for attr in ['partner_opened', 'opening_bid']:
                    po = getattr(generator, attr, None)
                    if po and len(po) >= 2 and po[-1] in '♠♥♦♣':
                        trump = po[-1]
                        break

                sp = calculate_support_points(hand, trump) if trump else None

                divergence = {
                    'hand_num': i,
                    'hand': format_hand(hand),
                    'hcp': hand.hcp,
                    'support_points': sp,
                    'balanced': hand.is_balanced,
                    'suit_lengths': dict(hand.suit_lengths),
                    'variant': getattr(generator, 'variant', None),
                    'auction': auction,
                    'generator_bid': gen_bid,
                    'generator_explanation': expected.get('explanation', ''),
                    'engine_bid': engine_bid,
                    'engine_explanation': str(engine_explanation)[:200],
                }
                results['divergences'].append(divergence)

        except Exception as e:
            results['errors'].append(f'Hand {i}: unexpected error: {str(e)[:100]}')

    return results


def print_results(all_results: List[Dict]):
    """Print formatted results to console."""
    total_tested = 0
    total_agreed = 0
    total_diverged = 0

    print('\n' + '=' * 80)
    print('LEARNING SYSTEM vs BIDDING ENGINE: VETTING REPORT')
    print('=' * 80)

    # Summary first
    for r in all_results:
        if r.get('error'):
            continue
        tested = r['hands_tested']
        agreed = r['agreements']
        diverged = len(r['divergences'])
        total_tested += tested
        total_agreed += agreed
        total_diverged += diverged

        pct = (agreed / tested * 100) if tested > 0 else 0
        status = 'MATCH' if diverged == 0 else f'{diverged} DIVERGENCES'
        print(f'  {r["skill_id"]:<30} {agreed}/{tested} agree ({pct:.0f}%)  {status}')

    print(f'\n  TOTAL: {total_agreed}/{total_tested} agree '
          f'({total_agreed/total_tested*100:.1f}%), '
          f'{total_diverged} divergences')

    # Detailed divergences
    for r in all_results:
        divergences = r.get('divergences', [])
        if not divergences:
            continue

        print(f'\n{"─" * 80}')
        print(f'DIVERGENCES: {r["skill_id"]} ({len(divergences)} cases)')
        print(f'{"─" * 80}')

        # Group by (generator_bid, engine_bid) pattern
        patterns = defaultdict(list)
        for d in divergences:
            key = (d['generator_bid'], d['engine_bid'])
            patterns[key].append(d)

        for (gen_bid, eng_bid), cases in sorted(patterns.items(), key=lambda x: -len(x[1])):
            print(f'\n  Pattern: Generator says "{gen_bid}" but Engine says "{eng_bid}" ({len(cases)} cases)')
            # Show up to 3 examples per pattern
            for d in cases[:3]:
                print(f'    Hand: {d["hand"]}  (HCP={d["hcp"]}, '
                      f'SP={d["support_points"] or "n/a"}, '
                      f'balanced={d["balanced"]})')
                print(f'      Variant: {d["variant"]}')
                print(f'      Auction: {d["auction"]}')
                print(f'      Generator: {d["generator_bid"]} - {d["generator_explanation"][:80]}')
                print(f'      Engine:    {d["engine_bid"]} - {d["engine_explanation"][:80]}')

        errors = r.get('errors', [])
        if errors:
            print(f'\n  Errors ({len(errors)}):')
            for e in errors[:5]:
                print(f'    {e}')


def main():
    parser = argparse.ArgumentParser(description='Vet learning skill generators against BiddingEngine')
    parser.add_argument('--hands', type=int, default=50, help='Hands per skill (default: 50)')
    parser.add_argument('--skill', type=str, help='Test single skill ID')
    parser.add_argument('--output', type=str, help='Save results to JSON file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    args = parser.parse_args()

    random.seed(args.seed)

    print(f'Initializing BiddingEngine...')
    engine = BiddingEngine()

    skills_to_test = [args.skill] if args.skill else list(BIDDING_SKILLS.keys())

    print(f'Vetting {len(skills_to_test)} skills, {args.hands} hands each...\n')

    all_results = []
    for skill_id in skills_to_test:
        result = vet_skill(skill_id, engine, args.hands)
        all_results.append(result)
        # Progress indicator
        tested = result['hands_tested']
        diverged = len(result['divergences'])
        sys.stdout.write(f'  {skill_id}: {tested} tested, {diverged} divergences\n')
        sys.stdout.flush()

    print_results(all_results)

    if args.output:
        # Serialize results to JSON
        with open(args.output, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f'\nResults saved to {args.output}')


if __name__ == '__main__':
    main()
