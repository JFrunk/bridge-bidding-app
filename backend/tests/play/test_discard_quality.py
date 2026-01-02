"""
Targeted Discard Quality Test

This test specifically measures the quality of discard decisions,
which is the behavior fixed by the tiebreaker bug fix.

The bug: AI was sometimes discarding high cards (K, Q) when low cards
were available, particularly in positions where all discards evaluated
to similar "losing" scores.

This test creates many discard scenarios and measures:
1. How often AI discards honors when low cards are available (should be ~0%)
2. Average rank of discarded cards (lower is better)
"""

import pytest
import random
from typing import List, Tuple
from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.play.ai.minimax_ai import MinimaxPlayAI
from tests.integration.play_test_helpers import create_test_deal, create_play_scenario


class DiscardQualityTester:
    """Tests discard quality across many scenarios"""

    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    def __init__(self, ai_depth: int = 3):
        self.ai = MinimaxPlayAI(max_depth=ai_depth)
        self.results = []

    def create_discard_scenario(self, seed: int) -> Tuple[PlayState, str, List[Card]]:
        """
        Create a scenario where East must discard (void in spades).

        Returns:
            - PlayState with East to discard
            - Position ('E')
            - List of East's legal cards (for analysis)
        """
        random.seed(seed)

        # Standard deal where East has varying hand strength
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",      # Strong hand
            east="♠543 ♥K543 ♦543 ♣543",        # Has King + low cards
            south="♠JT98 ♥JT9 ♦JT9 ♣KQJ",      # Medium hand
            west="♠76 ♥876 ♦8762 ♣T987"         # Weak hand
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # Remove East's spades to create void
        state.hands['E'].cards = [c for c in state.hands['E'].cards if c.suit != '♠']

        # North leads high spade
        state.current_trick = [(Card('A', '♠'), 'N')]
        state.next_to_play = 'E'

        return state, 'E', list(state.hands['E'].cards)

    def create_losing_discard_scenario(self, seed: int) -> Tuple[PlayState, str, List[Card]]:
        """
        Create a scenario where East must discard in a losing position.

        This tests the specific bug where all discards evaluate similarly
        in lost positions.
        """
        random.seed(seed)

        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥K543 ♦543 ♣543",
            south="♠JT98 ♥JT9 ♦JT9 ♣KQJ",
            west="♠76 ♥876 ♦8762 ♣T987"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # Simulate late game - N/S already won most tricks
        state.hands['N'].cards = [Card('Q', '♠')]
        state.hands['E'].cards = [Card('K', '♥'), Card('3', '♦'), Card('4', '♣')]
        state.hands['S'].cards = [Card('J', '♠')]
        state.hands['W'].cards = [Card('7', '♠')]

        state.tricks_won = {'N': 6, 'S': 4, 'E': 1, 'W': 1}

        # North leads spade, East must discard
        state.current_trick = [(Card('Q', '♠'), 'N')]
        state.next_to_play = 'E'

        return state, 'E', list(state.hands['E'].cards)

    def run_scenario(self, state: PlayState, position: str,
                     legal_cards: List[Card]) -> dict:
        """Run one discard scenario and record results"""
        card = self.ai.choose_card(state, position)

        # Analyze the discard
        rank_value = self.RANK_VALUES[card.rank]
        lowest_available = min(self.RANK_VALUES[c.rank] for c in legal_cards)
        highest_available = max(self.RANK_VALUES[c.rank] for c in legal_cards)

        # Check if an honor was discarded when low cards available
        honor_discarded = card.rank in ['A', 'K', 'Q', 'J']
        low_cards_available = any(self.RANK_VALUES[c.rank] <= 5 for c in legal_cards)
        bad_discard = honor_discarded and low_cards_available

        return {
            'card': f"{card.rank}{card.suit}",
            'rank_value': rank_value,
            'lowest_available': lowest_available,
            'highest_available': highest_available,
            'honor_discarded': honor_discarded,
            'low_cards_available': low_cards_available,
            'bad_discard': bad_discard,
            'optimal': rank_value == lowest_available
        }

    def run_test_suite(self, num_scenarios: int = 50) -> dict:
        """Run full test suite and return aggregate results"""
        results = []

        # Test normal discard scenarios
        for i in range(num_scenarios // 2):
            state, pos, cards = self.create_discard_scenario(seed=i)
            result = self.run_scenario(state, pos, cards)
            result['scenario_type'] = 'normal'
            results.append(result)

        # Test losing position scenarios
        for i in range(num_scenarios // 2):
            state, pos, cards = self.create_losing_discard_scenario(seed=i + 1000)
            result = self.run_scenario(state, pos, cards)
            result['scenario_type'] = 'losing'
            results.append(result)

        # Calculate aggregate stats
        total = len(results)
        bad_discards = sum(1 for r in results if r['bad_discard'])
        optimal_discards = sum(1 for r in results if r['optimal'])
        avg_rank = sum(r['rank_value'] for r in results) / total
        honor_discards = sum(1 for r in results if r['honor_discarded'])

        return {
            'total_scenarios': total,
            'bad_discard_count': bad_discards,
            'bad_discard_rate': bad_discards / total * 100,
            'optimal_discard_count': optimal_discards,
            'optimal_discard_rate': optimal_discards / total * 100,
            'honor_discard_count': honor_discards,
            'honor_discard_rate': honor_discards / total * 100,
            'avg_rank_discarded': avg_rank,
            'results': results
        }


class TestDiscardQuality:
    """Test suite for discard quality measurement"""

    def test_no_bad_discards_depth2(self):
        """At depth 2, should have zero bad discards"""
        tester = DiscardQualityTester(ai_depth=2)
        stats = tester.run_test_suite(num_scenarios=20)

        print(f"\n=== Depth 2 Discard Quality ===")
        print(f"Bad discard rate: {stats['bad_discard_rate']:.1f}%")
        print(f"Optimal discard rate: {stats['optimal_discard_rate']:.1f}%")
        print(f"Avg rank discarded: {stats['avg_rank_discarded']:.1f}")

        # CRITICAL: No bad discards allowed
        assert stats['bad_discard_rate'] == 0, \
            f"Bad discard rate is {stats['bad_discard_rate']:.1f}% - should be 0%"

    def test_no_bad_discards_depth3(self):
        """At depth 3, should have zero bad discards"""
        tester = DiscardQualityTester(ai_depth=3)
        stats = tester.run_test_suite(num_scenarios=20)

        print(f"\n=== Depth 3 Discard Quality ===")
        print(f"Bad discard rate: {stats['bad_discard_rate']:.1f}%")
        print(f"Optimal discard rate: {stats['optimal_discard_rate']:.1f}%")
        print(f"Avg rank discarded: {stats['avg_rank_discarded']:.1f}")

        # CRITICAL: No bad discards allowed
        assert stats['bad_discard_rate'] == 0, \
            f"Bad discard rate is {stats['bad_discard_rate']:.1f}% - should be 0%"

    def test_high_optimal_rate(self):
        """Should have high rate of optimal (lowest rank) discards"""
        tester = DiscardQualityTester(ai_depth=3)
        stats = tester.run_test_suite(num_scenarios=30)

        print(f"\n=== Optimal Discard Rate ===")
        print(f"Optimal: {stats['optimal_discard_rate']:.1f}%")

        # Should pick optimal (lowest) card most of the time
        assert stats['optimal_discard_rate'] >= 80, \
            f"Optimal rate {stats['optimal_discard_rate']:.1f}% below 80% threshold"

    def test_low_average_rank(self):
        """Average rank of discards should be low (< 7)"""
        tester = DiscardQualityTester(ai_depth=3)
        stats = tester.run_test_suite(num_scenarios=30)

        print(f"\n=== Average Discard Rank ===")
        print(f"Avg rank: {stats['avg_rank_discarded']:.1f} (2=deuce, 14=ace)")

        # Average should be low (preferring low cards)
        # With proper discard logic, should be around 3-5
        assert stats['avg_rank_discarded'] < 7, \
            f"Avg rank {stats['avg_rank_discarded']:.1f} too high (should be < 7)"


class TestUserReportedBug:
    """
    Test the exact scenario from user's bug report.

    User reported: East discarded ♥K on trick 11 when ♣8 was available.
    Contract: 1NT by E
    Trick 11: North leads ♠J, East must discard (void in spades)
    East's hand at trick 11: ♥K, ♣Q8 (reconstructed from play history)
    """

    def test_user_reported_scenario_exact(self):
        """
        Reproduce the EXACT scenario from user's bug report.

        From the hand data:
        - Contract: 1NT by E
        - Trick 11: N leads ♠J, E discards ♥K (BUG!), S plays ♠2, W plays ♠5
        - East was void in spades, had ♥K and ♣Q8 remaining

        The AI should discard ♣8, not ♥K.
        """
        # Create a minimal state matching trick 11 of the reported hand
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",      # Dummy values for valid 13-card hands
            east="♠543 ♥K543 ♦543 ♣543",
            south="♠JT98 ♥JT9 ♦JT9 ♣KQJ",
            west="♠76 ♥876 ♦8762 ♣T987"
        )

        state = create_play_scenario("1NT by E", deal, "None")

        # Set up trick 11 position: East has ♥K and ♣Q8 remaining
        state.hands['N'].cards = [Card('J', '♠'), Card('9', '♠')]
        state.hands['E'].cards = [Card('K', '♥'), Card('Q', '♣'), Card('8', '♣')]  # The bug scenario
        state.hands['S'].cards = [Card('2', '♠'), Card('6', '♣')]
        state.hands['W'].cards = [Card('5', '♠'), Card('Q', '♠')]

        # N/S have won 9 tricks, E/W have won 2
        state.tricks_won = {'N': 5, 'S': 4, 'E': 1, 'W': 1}

        # North leads ♠J
        state.current_trick = [(Card('J', '♠'), 'N')]
        state.next_to_play = 'E'

        ai = MinimaxPlayAI(max_depth=3)
        card = ai.choose_card(state, 'E')

        print(f"\nUser bug scenario: East chose {card.rank}{card.suit}")
        print(f"East's hand: ♥K, ♣Q8")
        print(f"Expected: ♣8 (lowest non-honor)")

        # The fix should make East discard ♣8, not ♥K or ♣Q
        assert card.rank == '8', \
            f"BUG REPRODUCED: East discarded {card.rank}{card.suit} instead of ♣8"

    def test_user_scenario_with_only_k_and_low(self):
        """
        Simpler version: East has only ♥K and ♦8.
        Should always discard ♦8.
        """
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥K543 ♦543 ♣543",
            south="♠JT98 ♥JT9 ♦JT9 ♣KQJ",
            west="♠76 ♥876 ♦8762 ♣T987"
        )

        state = create_play_scenario("1NT by E", deal, "None")

        # Minimal hand: just K and 8
        state.hands['N'].cards = [Card('J', '♠')]
        state.hands['E'].cards = [Card('K', '♥'), Card('8', '♦')]
        state.hands['S'].cards = [Card('2', '♠')]
        state.hands['W'].cards = [Card('5', '♠')]

        state.tricks_won = {'N': 6, 'S': 4, 'E': 1, 'W': 1}

        state.current_trick = [(Card('J', '♠'), 'N')]
        state.next_to_play = 'E'

        ai = MinimaxPlayAI(max_depth=3)
        card = ai.choose_card(state, 'E')

        print(f"\nSimple K vs 8 scenario: East chose {card.rank}{card.suit}")

        assert card.rank == '8', \
            f"East discarded {card.rank}{card.suit} - should be ♦8, not ♥K"


def run_comparison_test():
    """
    Run this to compare before/after fix.

    Usage:
        # Before fix:
        git stash
        python -c "from tests.play.test_discard_quality import run_comparison_test; run_comparison_test()"

        # After fix:
        git stash pop
        python -c "from tests.play.test_discard_quality import run_comparison_test; run_comparison_test()"
    """
    print("=" * 60)
    print("DISCARD QUALITY COMPARISON TEST")
    print("=" * 60)

    tester = DiscardQualityTester(ai_depth=3)
    stats = tester.run_test_suite(num_scenarios=50)

    print(f"\nTotal scenarios: {stats['total_scenarios']}")
    print(f"\n--- Key Metrics ---")
    print(f"Bad discard rate:     {stats['bad_discard_rate']:5.1f}% (should be 0%)")
    print(f"Optimal discard rate: {stats['optimal_discard_rate']:5.1f}% (should be >80%)")
    print(f"Honor discard rate:   {stats['honor_discard_rate']:5.1f}% (lower is better)")
    print(f"Avg rank discarded:   {stats['avg_rank_discarded']:5.1f} (lower is better)")

    print(f"\n--- Pass/Fail ---")
    passed = stats['bad_discard_rate'] == 0
    print(f"{'✅ PASS' if passed else '❌ FAIL'}: Zero bad discards")

    # Also run user bug test
    print("\n" + "=" * 60)
    print("USER BUG SCENARIO TEST")
    print("=" * 60)

    try:
        test = TestUserReportedBug()
        test.test_user_scenario_with_only_k_and_low()
        print("✅ PASS: K vs 8 scenario - correctly chose 8")
    except AssertionError as e:
        print(f"❌ FAIL: {e}")

    try:
        test.test_user_reported_scenario_exact()
        print("✅ PASS: Exact user scenario - correctly chose 8")
    except AssertionError as e:
        print(f"❌ FAIL: {e}")

    return stats


if __name__ == '__main__':
    run_comparison_test()
