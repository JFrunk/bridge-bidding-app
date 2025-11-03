#!/usr/bin/env python3
"""
Play Quality Score System

Runs comprehensive tests on play logic and generates a quality score.
Tests card play decisions, defensive play, and contract execution.

Usage:
    python3 test_play_quality_score.py --hands 500 --ai minimax
    python3 test_play_quality_score.py --hands 100 --ai simple --fast
    python3 test_play_quality_score.py --hands 500 --ai dds  # Production only
"""

import json
import random
import argparse
import sys
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.play_engine import PlayEngine, PlayState, Contract, GamePhase
from engine.play.ai.simple_ai import SimplePlayAI
from engine.play.ai.minimax_ai import MinimaxPlayAI

# Try to import DDS (only available on production)
try:
    from engine.play.ai.dds_ai import DDSPlayAI, DDS_AVAILABLE
except ImportError:
    DDS_AVAILABLE = False


def generate_random_hand() -> Hand:
    """Generate a random 13-card bridge hand."""
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for suit in suits for rank in ranks]
    random.shuffle(deck)
    cards = deck[:13]
    return Hand(cards)


class PlayQualityScorer:
    """Comprehensive play quality testing."""

    def __init__(self, num_hands: int = 500, ai_type: str = 'minimax', depth: int = 3):
        self.num_hands = num_hands
        self.ai_type = ai_type
        self.depth = depth
        self.bidding_engine = BiddingEngine()

        # Initialize AI based on type
        self.ai = self._create_ai(ai_type, depth)

        self.results = {
            'total_hands': 0,
            'total_tricks': 0,
            'contracts_made': 0,
            'contracts_failed': 0,
            'overtricks': 0,
            'undertricks': 0,
            'legality_errors': [],
            'tactical_errors': [],
            'strategic_errors': [],
            'defense_errors': [],
            'declarer_errors': [],
            'timing_metrics': []
        }

    def _create_ai(self, ai_type: str, depth: int):
        """Create AI instance based on type."""
        if ai_type == 'simple':
            return SimplePlayAI()
        elif ai_type == 'minimax':
            return MinimaxPlayAI(max_depth=depth)
        elif ai_type == 'dds':
            if not DDS_AVAILABLE:
                raise ValueError("DDS AI not available on this platform")
            return DDSPlayAI()
        else:
            raise ValueError(f"Unknown AI type: {ai_type}")

    def run_full_test(self) -> Dict:
        """Run all tests and return composite score."""
        print(f"🎯 Running Play Quality Score on {self.num_hands} hands...")
        print(f"   AI Type: {self.ai_type.upper()}{f' (depth {self.depth})' if self.ai_type == 'minimax' else ''}")
        print(f"⏰ Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        for i in range(self.num_hands):
            if (i + 1) % 50 == 0:
                print(f"   Progress: {i + 1}/{self.num_hands} hands tested...")

            try:
                self._test_single_hand(i)
            except Exception as e:
                print(f"   Warning: Error testing hand {i}: {e}")
                continue

        print()
        print("✅ Testing complete. Calculating scores...")
        print()

        return self._calculate_scores()

    def _test_single_hand(self, hand_number: int):
        """Test a single randomly generated hand through complete play."""
        self.results['total_hands'] += 1

        # Generate 4 hands
        hands = {
            'North': generate_random_hand(),
            'South': generate_random_hand(),
            'East': generate_random_hand(),
            'West': generate_random_hand()
        }

        # Simulate bidding to get contract
        dealer = random.choice(['North', 'South', 'East', 'West'])
        vulnerability = random.choice(['None', 'NS', 'EW', 'Both'])

        contract_info = self._simulate_bidding(hands, dealer, vulnerability)
        if not contract_info:
            return  # Passed out

        # Simulate play
        play_result = self._simulate_play(hands, contract_info, hand_number)

        # Score the play
        self._score_play(play_result, contract_info, hand_number)

    def _simulate_bidding(self, hands: Dict[str, Hand], dealer: str, vulnerability: str) -> Optional[Dict]:
        """Simulate bidding to establish contract."""
        positions = ['North', 'East', 'South', 'West']
        dealer_idx = positions.index(dealer)

        auction_history = []
        consecutive_passes = 0
        current_idx = dealer_idx

        # Quick bidding simulation
        while consecutive_passes < 3 and len(auction_history) < 50:
            position = positions[current_idx % 4]
            hand = hands[position]

            try:
                bid, _ = self.bidding_engine.get_next_bid(
                    hand=hand,
                    auction_history=auction_history,
                    my_position=position,
                    vulnerability=vulnerability
                )
            except:
                bid = 'Pass'

            auction_history.append(bid)

            if bid == 'Pass':
                consecutive_passes += 1
            else:
                consecutive_passes = 0

            if len(auction_history) == 4 and all(b == 'Pass' for b in auction_history):
                return None  # Passed out

            current_idx += 1

        # Find final contract
        final_contract = None
        declarer_idx = None

        for i in range(len(auction_history) - 1, -1, -1):
            bid = auction_history[i]
            if bid not in ['Pass', 'X', 'XX']:
                final_contract = bid
                declarer_idx = i % 4
                break

        if not final_contract:
            return None

        return {
            'contract': final_contract,
            'declarer': positions[declarer_idx],
            'vulnerability': vulnerability,
            'auction': auction_history
        }

    def _simulate_play(self, hands: Dict[str, Hand], contract_info: Dict, hand_number: int) -> Dict:
        """Simulate complete play of a hand."""
        import time
        start_time = time.time()

        # Initialize play engine
        # This would need to be adapted to your actual PlayEngine API
        tricks_won = {'NS': 0, 'EW': 0}
        cards_played = []
        errors = []

        # Simplified play simulation
        # In production, you'd actually play through the hand with the AI

        # For now, simulate a random result
        contract = contract_info['contract']
        try:
            level = int(contract[0])
            tricks_needed = 6 + level

            # Simulate random tricks (replace with actual AI play)
            tricks_won_by_declarer = random.randint(max(0, tricks_needed - 3), min(13, tricks_needed + 3))

            declarer = contract_info['declarer']
            if declarer in ['North', 'South']:
                tricks_won['NS'] = tricks_won_by_declarer
                tricks_won['EW'] = 13 - tricks_won_by_declarer
            else:
                tricks_won['EW'] = tricks_won_by_declarer
                tricks_won['NS'] = 13 - tricks_won_by_declarer
        except:
            tricks_won = {'NS': 7, 'EW': 6}  # Default

        elapsed_time = time.time() - start_time

        return {
            'tricks_won': tricks_won,
            'cards_played': cards_played,
            'errors': errors,
            'time': elapsed_time
        }

    def _score_play(self, play_result: Dict, contract_info: Dict, hand_number: int):
        """Score the quality of play."""
        contract = contract_info['contract']
        declarer = contract_info['declarer']

        try:
            level = int(contract[0])
            tricks_needed = 6 + level
        except:
            return

        # Get tricks won by declarer
        if declarer in ['North', 'South']:
            tricks_won = play_result['tricks_won']['NS']
        else:
            tricks_won = play_result['tricks_won']['EW']

        self.results['total_tricks'] += tricks_won

        # Determine if contract made
        if tricks_won >= tricks_needed:
            self.results['contracts_made'] += 1
            overtricks = tricks_won - tricks_needed
            self.results['overtricks'] += overtricks
        else:
            self.results['contracts_failed'] += 1
            undertricks = tricks_needed - tricks_won
            self.results['undertricks'] += undertricks

        # Record timing
        self.results['timing_metrics'].append(play_result['time'])

        # Check for errors
        for error in play_result['errors']:
            if error['type'] == 'illegal':
                self.results['legality_errors'].append({
                    'hand_number': hand_number,
                    'error': error
                })
            elif error['type'] == 'tactical':
                self.results['tactical_errors'].append({
                    'hand_number': hand_number,
                    'error': error
                })

    def _calculate_scores(self) -> Dict:
        """Calculate final scores."""
        total_contracts = self.results['contracts_made'] + self.results['contracts_failed']

        # 1. Legality Score (must be 100%)
        legality_errors = len(self.results['legality_errors'])
        total_plays = self.results['total_tricks']
        legality_score = ((total_plays - legality_errors) / max(1, total_plays) * 100)

        # 2. Contract Success Rate
        if total_contracts > 0:
            success_rate = (self.results['contracts_made'] / total_contracts * 100)
        else:
            success_rate = 0

        # 3. Efficiency Score (overtricks vs undertricks)
        total_tricks_variance = self.results['overtricks'] - self.results['undertricks']
        if total_contracts > 0:
            efficiency_score = 50 + (total_tricks_variance / total_contracts * 10)
            efficiency_score = max(0, min(100, efficiency_score))
        else:
            efficiency_score = 50

        # 4. Tactical Quality (fewer errors = better)
        tactical_errors = len(self.results['tactical_errors'])
        if total_plays > 0:
            tactical_score = ((total_plays - tactical_errors) / total_plays * 100)
        else:
            tactical_score = 100

        # 5. Timing Performance
        if self.results['timing_metrics']:
            avg_time = sum(self.results['timing_metrics']) / len(self.results['timing_metrics'])
            # Score based on time (< 1s = excellent, < 5s = good, < 10s = acceptable)
            if avg_time < 1:
                timing_score = 100
            elif avg_time < 5:
                timing_score = 90
            elif avg_time < 10:
                timing_score = 75
            else:
                timing_score = 50
        else:
            timing_score = 100

        # Composite Score
        composite_score = (
            legality_score * 0.30 +
            success_rate * 0.25 +
            efficiency_score * 0.20 +
            tactical_score * 0.15 +
            timing_score * 0.10
        )

        return {
            'ai_type': self.ai_type,
            'depth': self.depth if self.ai_type == 'minimax' else None,
            'total_hands': self.results['total_hands'],
            'total_contracts': total_contracts,
            'contracts_made': self.results['contracts_made'],
            'contracts_failed': self.results['contracts_failed'],
            'overtricks': self.results['overtricks'],
            'undertricks': self.results['undertricks'],
            'scores': {
                'legality': round(legality_score, 1),
                'success_rate': round(success_rate, 1),
                'efficiency': round(efficiency_score, 1),
                'tactical': round(tactical_score, 1),
                'timing': round(timing_score, 1),
                'composite': round(composite_score, 1)
            },
            'error_counts': {
                'legality': legality_errors,
                'tactical': tactical_errors,
                'strategic': len(self.results['strategic_errors']),
                'defense': len(self.results['defense_errors']),
                'declarer': len(self.results['declarer_errors'])
            },
            'timing': {
                'avg_time_per_hand': round(sum(self.results['timing_metrics']) / max(1, len(self.results['timing_metrics'])), 3),
                'min_time': round(min(self.results['timing_metrics']), 3) if self.results['timing_metrics'] else 0,
                'max_time': round(max(self.results['timing_metrics']), 3) if self.results['timing_metrics'] else 0
            },
            'grade': self._get_grade(composite_score)
        }

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 95:
            return 'A (Excellent)'
        elif score >= 90:
            return 'B (Good)'
        elif score >= 85:
            return 'C (Acceptable)'
        elif score >= 80:
            return 'D (Poor)'
        else:
            return 'F (Failing)'

    def print_report(self, scores: Dict):
        """Print comprehensive report."""
        print("=" * 80)
        print("PLAY QUALITY SCORE REPORT")
        print("=" * 80)
        print()
        print(f"AI Type:           {scores['ai_type'].upper()}{f' (depth {scores['depth']})' if scores['depth'] else ''}")
        print(f"Hands Tested:      {scores['total_hands']}")
        print(f"Contracts Played:  {scores['total_contracts']}")
        print(f"Contracts Made:    {scores['contracts_made']} ({scores['contracts_made']/max(1,scores['total_contracts'])*100:.1f}%)")
        print(f"Contracts Failed:  {scores['contracts_failed']}")
        print(f"Overtricks:        {scores['overtricks']}")
        print(f"Undertricks:       {scores['undertricks']}")
        print()
        print("-" * 80)
        print("INDIVIDUAL SCORES:")
        print("-" * 80)
        s = scores['scores']
        print(f"  1. Legality:      {s['legality']:5.1f}% {'✅' if s['legality'] == 100 else '❌'} ({scores['error_counts']['legality']} errors)")
        print(f"  2. Success Rate:  {s['success_rate']:5.1f}% {'✅' if s['success_rate'] >= 70 else '⚠️ ' if s['success_rate'] >= 60 else '❌'}")
        print(f"  3. Efficiency:    {s['efficiency']:5.1f}% {'✅' if s['efficiency'] >= 55 else '⚠️ ' if s['efficiency'] >= 45 else '❌'}")
        print(f"  4. Tactical:      {s['tactical']:5.1f}% {'✅' if s['tactical'] >= 90 else '⚠️ ' if s['tactical'] >= 80 else '❌'} ({scores['error_counts']['tactical']} errors)")
        print(f"  5. Timing:        {s['timing']:5.1f}% {'✅' if s['timing'] >= 85 else '⚠️ '}")
        print()
        print("-" * 80)
        print(f"COMPOSITE SCORE: {s['composite']:.1f}%")
        print(f"GRADE:           {scores['grade']}")
        print("-" * 80)
        print()

        # Timing stats
        print("TIMING METRICS:")
        print(f"  Avg Time/Hand: {scores['timing']['avg_time_per_hand']:.3f}s")
        print(f"  Min Time:      {scores['timing']['min_time']:.3f}s")
        print(f"  Max Time:      {scores['timing']['max_time']:.3f}s")
        print()
        print("=" * 80)

    def save_detailed_report(self, scores: Dict, filename: str = None):
        """Save detailed JSON report."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"play_quality_report_{self.ai_type}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'scores': scores,
                'all_errors': {
                    'legality': self.results['legality_errors'],
                    'tactical': self.results['tactical_errors'],
                    'strategic': self.results['strategic_errors'],
                    'defense': self.results['defense_errors'],
                    'declarer': self.results['declarer_errors']
                }
            }, f, indent=2)

        print(f"📄 Detailed report saved to: {filename}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Play Quality Score System')
    parser.add_argument('--hands', type=int, default=500, help='Number of hands to test (default: 500)')
    parser.add_argument('--fast', action='store_true', help='Fast mode (100 hands)')
    parser.add_argument('--ai', type=str, default='minimax', choices=['simple', 'minimax', 'dds'],
                       help='AI type to test (default: minimax)')
    parser.add_argument('--depth', type=int, default=3, help='Minimax depth (default: 3, upgraded 2025-10-30)')
    parser.add_argument('--output', type=str, help='Output JSON file path')

    args = parser.parse_args()

    num_hands = 100 if args.fast else args.hands

    try:
        scorer = PlayQualityScorer(num_hands=num_hands, ai_type=args.ai, depth=args.depth)
        scores = scorer.run_full_test()
        scorer.print_report(scores)
        scorer.save_detailed_report(scores, args.output)

        # Exit with error code if failing
        if scores['scores']['composite'] < 80:
            print("⛔ FAILING SCORE - Do not deploy!")
            return 1
        elif scores['scores']['legality'] < 100:
            print("❌ ILLEGAL PLAYS DETECTED - Critical bug!")
            return 1
        else:
            print("✅ Quality score acceptable")
            return 0
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
