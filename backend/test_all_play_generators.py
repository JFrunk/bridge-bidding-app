#!/usr/bin/env python3
"""
Test all play skill hand generators to ensure they produce valid hands.
"""

import sys
sys.path.insert(0, '/Users/simonroy/Desktop/Bridge-Bidding-Program/backend')

from engine.learning.play_skill_hand_generators import (
    get_play_skill_hand_generator,
    get_available_play_skills
)

def test_generator(skill_id: str) -> bool:
    """Test a single generator."""
    try:
        generator = get_play_skill_hand_generator(skill_id)
        if generator is None:
            print(f"  ❌ {skill_id}: Generator not found")
            return False

        # Generate 3 hands to catch intermittent issues
        for i in range(3):
            deal, situation = generator.generate()

            # Validate all hands have exactly 13 cards
            if len(deal.declarer_hand.cards) != 13:
                print(f"  ❌ {skill_id} (test {i+1}): Declarer has {len(deal.declarer_hand.cards)} cards")
                return False
            if len(deal.dummy_hand.cards) != 13:
                print(f"  ❌ {skill_id} (test {i+1}): Dummy has {len(deal.dummy_hand.cards)} cards")
                return False
            if len(deal.lho_hand.cards) != 13:
                print(f"  ❌ {skill_id} (test {i+1}): LHO has {len(deal.lho_hand.cards)} cards")
                return False
            if len(deal.rho_hand.cards) != 13:
                print(f"  ❌ {skill_id} (test {i+1}): RHO has {len(deal.rho_hand.cards)} cards")
                return False

            # Validate total cards = 52
            all_cards = (deal.declarer_hand.cards + deal.dummy_hand.cards +
                        deal.lho_hand.cards + deal.rho_hand.cards)
            if len(all_cards) != 52:
                print(f"  ❌ {skill_id} (test {i+1}): Total cards = {len(all_cards)}")
                return False

            # Validate no duplicate cards
            card_set = set(all_cards)
            if len(card_set) != 52:
                print(f"  ❌ {skill_id} (test {i+1}): Duplicate cards detected")
                return False

        print(f"  ✅ {skill_id}")
        return True

    except Exception as e:
        print(f"  ❌ {skill_id}: {str(e)}")
        return False


def main():
    """Test all generators organized by level."""

    levels = {
        'Level 0 - Foundations': [
            'counting_winners',
            'counting_losers',
            'analyzing_the_lead',
        ],
        'Level 1 - Basic Techniques': [
            'leading_to_tricks',
            'second_hand_low',
            'third_hand_high',
            'winning_cheaply',
        ],
        'Level 2 - Finessing': [
            'simple_finesse',
            'double_finesse',
            'two_way_finesse',
            'finesse_or_drop',
        ],
        'Level 3 - Suit Establishment': [
            'establishing_long_suits',
            'ducking_plays',
            'hold_up_plays',
            'which_suit_to_establish',
        ],
        'Level 4 - Trump Management': [
            'drawing_trumps',
            'ruffing_losers',
            'trump_control',
            'crossruff',
        ],
        'Level 5 - Entry Management': [
            'preserving_entries',
            'unblocking',
            'creating_entries',
            'entry_killing_plays',
        ],
        'Level 6 - Card Combinations': [
            'aq_combinations',
            'kj_combinations',
            'safety_plays',
            'percentage_plays',
        ],
        'Level 7 - Timing & Planning': [
            'planning_nt_contracts',
            'planning_suit_contracts',
            'timing_decisions',
            'danger_hand',
        ],
        'Level 8 - Advanced Techniques': [
            'elimination_play',
            'endplays',
            'simple_squeeze',
            'avoidance_plays',
            'deceptive_plays',
        ],
    }

    print("Testing all play skill hand generators...\n")

    total_tests = 0
    passed_tests = 0

    for level_name, skills in levels.items():
        print(f"{level_name}:")
        for skill_id in skills:
            total_tests += 1
            if test_generator(skill_id):
                passed_tests += 1
        print()

    print(f"\n{'='*60}")
    print(f"Results: {passed_tests}/{total_tests} generators passed")
    print(f"Coverage: {passed_tests}/{total_tests} = {100*passed_tests/total_tests:.1f}%")

    if passed_tests == total_tests:
        print("✅ ALL GENERATORS WORKING!")
    else:
        print(f"⚠️  {total_tests - passed_tests} generators failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
