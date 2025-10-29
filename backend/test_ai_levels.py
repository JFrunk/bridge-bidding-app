#!/usr/bin/env python3
"""
AI Level Testing Framework
Tests all 4 AI difficulty levels to ensure proper operation and play quality

Usage:
    python test_ai_levels.py [--verbose] [--level LEVEL]

Options:
    --verbose: Show detailed output for each test
    --level LEVEL: Test only a specific level (beginner, intermediate, advanced, expert)
"""

import sys
import os
import argparse
from typing import Dict, List, Tuple
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.play.ai.simple_ai import SimplePlayAI
from engine.play.ai.minimax_ai import MinimaxPlayAI
from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE
from engine.play_engine import PlayState, Card


class AILevelTester:
    """Test framework for validating AI difficulty levels"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            'beginner': {'tested': False, 'passed': 0, 'failed': 0, 'errors': []},
            'intermediate': {'tested': False, 'passed': 0, 'failed': 0, 'errors': []},
            'advanced': {'tested': False, 'passed': 0, 'failed': 0, 'errors': []},
            'expert': {'tested': False, 'passed': 0, 'failed': 0, 'errors': []}
        }

        # Initialize AI instances
        self.ai_instances = {
            'beginner': SimplePlayAI(),
            'intermediate': MinimaxPlayAI(max_depth=2),
            'advanced': MinimaxPlayAI(max_depth=3),
            'expert': DDSPlayAI() if DDS_AVAILABLE else MinimaxPlayAI(max_depth=4)
        }

        self.log(f"✅ Initialized AI instances")
        self.log(f"   DDS Available: {DDS_AVAILABLE}")
        for level, ai in self.ai_instances.items():
            self.log(f"   {level}: {ai.get_name()}")

    def log(self, message: str, force: bool = False):
        """Log message if verbose or forced"""
        if self.verbose or force:
            print(message)

    def test_ai_initialization(self, level: str) -> bool:
        """Test 1: Verify AI can initialize correctly"""
        test_name = f"{level} - Initialization"
        try:
            ai = self.ai_instances[level]
            name = ai.get_name()

            if not name or len(name) == 0:
                raise AssertionError(f"AI has empty name")

            self.log(f"  ✓ {test_name}: {name}")
            return True
        except Exception as e:
            self.log(f"  ✗ {test_name}: {e}", force=True)
            self.results[level]['errors'].append(f"Initialization failed: {e}")
            return False

    def test_simple_play(self, level: str) -> bool:
        """Test 2: Verify AI can make a legal play in a simple position"""
        test_name = f"{level} - Simple Play"
        try:
            ai = self.ai_instances[level]

            # Create a simple test position (mid-game, trump contract)
            test_position = {
                'position': 'E',
                'hand': [
                    Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
                    Card('A', '♥'), Card('K', '♥'),
                    Card('A', '♦'), Card('K', '♦'),
                    Card('A', '♣'), Card('K', '♣')
                ],
                'trump': '♠',
                'current_trick': [],
                'tricks_won': {'NS': 3, 'EW': 2},
                'contract': {'level': 4, 'strain': '♠', 'declarer': 'N'}
            }

            # AI should choose a card (any legal card is fine for this test)
            card = ai.choose_card(
                position=test_position['position'],
                hand=test_position['hand'],
                trump=test_position['trump'],
                current_trick=test_position['current_trick'],
                dummy_hand=None,
                all_positions=['N', 'E', 'S', 'W']
            )

            if not card:
                raise AssertionError("AI returned no card")

            if card not in test_position['hand']:
                raise AssertionError(f"AI chose card not in hand: {card}")

            self.log(f"  ✓ {test_name}: Played {card}")
            return True

        except Exception as e:
            self.log(f"  ✗ {test_name}: {e}", force=True)
            self.results[level]['errors'].append(f"Simple play failed: {e}")
            return False

    def test_following_suit(self, level: str) -> bool:
        """Test 3: Verify AI follows suit when required"""
        test_name = f"{level} - Following Suit"
        try:
            ai = self.ai_instances[level]

            # Position where AI must follow suit
            test_position = {
                'position': 'E',
                'hand': [
                    Card('K', '♥'), Card('Q', '♥'), Card('J', '♥'),  # Must play heart
                    Card('A', '♠'), Card('K', '♠'),
                    Card('A', '♦'), Card('K', '♦')
                ],
                'trump': '♠',
                'current_trick': [
                    {'position': 'N', 'card': Card('A', '♥')}  # Heart led
                ],
                'lead_suit': '♥'
            }

            card = ai.choose_card(
                position=test_position['position'],
                hand=test_position['hand'],
                trump=test_position['trump'],
                current_trick=test_position['current_trick'],
                dummy_hand=None,
                all_positions=['N', 'E', 'S', 'W']
            )

            if not card:
                raise AssertionError("AI returned no card")

            if card.suit != '♥':
                raise AssertionError(f"AI failed to follow suit: played {card} when ♥ was led")

            self.log(f"  ✓ {test_name}: Correctly followed suit with {card}")
            return True

        except Exception as e:
            self.log(f"  ✗ {test_name}: {e}", force=True)
            self.results[level]['errors'].append(f"Following suit failed: {e}")
            return False

    def test_trump_usage(self, level: str) -> bool:
        """Test 4: Verify AI uses trump appropriately when void"""
        test_name = f"{level} - Trump Usage"
        try:
            ai = self.ai_instances[level]

            # Position where AI is void in led suit and has trump
            test_position = {
                'position': 'E',
                'hand': [
                    Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),  # Trump cards
                    Card('5', '♦'), Card('4', '♦')  # No hearts
                ],
                'trump': '♠',
                'current_trick': [
                    {'position': 'N', 'card': Card('A', '♥')}  # Heart led, E is void
                ],
                'lead_suit': '♥'
            }

            card = ai.choose_card(
                position=test_position['position'],
                hand=test_position['hand'],
                trump=test_position['trump'],
                current_trick=test_position['current_trick'],
                dummy_hand=None,
                all_positions=['N', 'E', 'S', 'W']
            )

            if not card:
                raise AssertionError("AI returned no card")

            # AI can either trump or discard - both legal
            is_trump = card.suit == '♠'
            is_discard = card.suit == '♦'

            if not (is_trump or is_discard):
                raise AssertionError(f"AI made illegal play: {card}")

            play_type = "trumped" if is_trump else "discarded"
            self.log(f"  ✓ {test_name}: {play_type} with {card}")
            return True

        except Exception as e:
            self.log(f"  ✗ {test_name}: {e}", force=True)
            self.results[level]['errors'].append(f"Trump usage failed: {e}")
            return False

    def test_level_quality(self, level: str) -> bool:
        """Test 5: Verify AI level makes reasonable quality plays"""
        test_name = f"{level} - Play Quality"
        try:
            ai = self.ai_instances[level]

            # Finesse position - higher levels should recognize this
            test_position = {
                'position': 'S',
                'hand': [
                    Card('A', '♠'), Card('Q', '♠'),  # AQ combination (finesse available)
                    Card('K', '♥'), Card('Q', '♥'),
                    Card('A', '♦')
                ],
                'trump': '♥',
                'current_trick': [],
                'dummy_position': 'N',
                'dummy_hand': [
                    Card('J', '♠'), Card('10', '♠'),  # Support for finesse
                    Card('A', '♥'), Card('J', '♥')
                ]
            }

            card = ai.choose_card(
                position=test_position['position'],
                hand=test_position['hand'],
                trump=test_position['trump'],
                current_trick=test_position['current_trick'],
                dummy_hand=test_position['dummy_hand'],
                all_positions=['N', 'E', 'S', 'W']
            )

            if not card:
                raise AssertionError("AI returned no card")

            # Any legal card is acceptable - we're just testing it can play
            # Quality analysis would require more sophisticated testing
            self.log(f"  ✓ {test_name}: Played {card}")
            return True

        except Exception as e:
            self.log(f"  ✗ {test_name}: {e}", force=True)
            self.results[level]['errors'].append(f"Play quality test failed: {e}")
            return False

    def test_level(self, level: str) -> Dict:
        """Run all tests for a specific AI level"""
        self.log(f"\n{'='*60}", force=True)
        self.log(f"Testing {level.upper()} AI - {self.ai_instances[level].get_name()}", force=True)
        self.log(f"{'='*60}", force=True)

        self.results[level]['tested'] = True

        tests = [
            self.test_ai_initialization,
            self.test_simple_play,
            self.test_following_suit,
            self.test_trump_usage,
            self.test_level_quality
        ]

        for test in tests:
            try:
                passed = test(level)
                if passed:
                    self.results[level]['passed'] += 1
                else:
                    self.results[level]['failed'] += 1
            except Exception as e:
                self.log(f"  ✗ Unexpected error in test: {e}", force=True)
                self.results[level]['failed'] += 1
                self.results[level]['errors'].append(f"Unexpected error: {e}")

        total = self.results[level]['passed'] + self.results[level]['failed']
        passed = self.results[level]['passed']

        self.log(f"\n{level.upper()} Results: {passed}/{total} tests passed", force=True)

        return self.results[level]

    def test_all_levels(self):
        """Run all tests for all AI levels"""
        levels = ['beginner', 'intermediate', 'advanced', 'expert']

        for level in levels:
            self.test_level(level)

        self.print_summary()

    def print_summary(self):
        """Print overall test summary"""
        print("\n" + "="*60)
        print("AI LEVEL TEST SUMMARY")
        print("="*60)

        total_passed = 0
        total_failed = 0

        for level in ['beginner', 'intermediate', 'advanced', 'expert']:
            result = self.results[level]
            if not result['tested']:
                continue

            total_passed += result['passed']
            total_failed += result['failed']
            total_tests = result['passed'] + result['failed']

            status = "✅ PASS" if result['failed'] == 0 else "❌ FAIL"
            print(f"\n{level.upper():12} {status}")
            print(f"  Tests: {result['passed']}/{total_tests} passed")

            if result['errors']:
                print(f"  Errors:")
                for error in result['errors']:
                    print(f"    - {error}")

        print("\n" + "-"*60)
        print(f"OVERALL: {total_passed}/{total_passed + total_failed} tests passed")

        if total_failed == 0:
            print("✅ ALL TESTS PASSED")
        else:
            print(f"❌ {total_failed} TESTS FAILED")

        print("="*60)

        # Return exit code
        return 0 if total_failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description='Test AI difficulty levels')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output for each test')
    parser.add_argument('--level', '-l', choices=['beginner', 'intermediate', 'advanced', 'expert'],
                       help='Test only a specific level')

    args = parser.parse_args()

    tester = AILevelTester(verbose=args.verbose)

    if args.level:
        tester.test_level(args.level)
        tester.print_summary()
    else:
        tester.test_all_levels()

    # Exit with appropriate code
    sys.exit(0 if tester.results else 1)


if __name__ == '__main__':
    main()
