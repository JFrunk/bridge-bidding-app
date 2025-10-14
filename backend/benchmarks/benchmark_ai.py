"""
AI Benchmarking Suite

Compares different play AIs using curated test deals:
- Simple rule-based AI (Phase 1)
- Minimax AI at various depths (Phase 2)
- Future: DDS AI (Phase 3)

Metrics:
- Tricks won per deal
- Search time per move
- Nodes searched per move
- Memory usage
- Success rate (achieving expected result)
"""

import json
import time
import copy
from typing import Dict, List, Tuple
from pathlib import Path

from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.play.ai.simple_ai import SimplePlayAI
from engine.play.ai.minimax_ai import MinimaxPlayAI
from tests.integration.play_test_helpers import create_hand_from_string, create_play_scenario


class BenchmarkResult:
    """Results from benchmarking a single AI on a single deal"""

    def __init__(self, deal_id: str, ai_name: str):
        self.deal_id = deal_id
        self.ai_name = ai_name
        self.tricks_won = {"N": 0, "E": 0, "S": 0, "W": 0}
        self.declarer_tricks = 0
        self.defender_tricks = 0
        self.moves_played = 0
        self.total_time = 0.0
        self.total_nodes = 0
        self.total_pruned = 0
        self.avg_time_per_move = 0.0
        self.avg_nodes_per_move = 0.0
        self.max_time_per_move = 0.0
        self.move_times: List[float] = []
        self.move_nodes: List[int] = []

    def finalize(self):
        """Calculate aggregate statistics"""
        if self.moves_played > 0:
            self.avg_time_per_move = self.total_time / self.moves_played
            self.avg_nodes_per_move = self.total_nodes / self.moves_played
            self.max_time_per_move = max(self.move_times) if self.move_times else 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "deal_id": self.deal_id,
            "ai_name": self.ai_name,
            "tricks_won": self.tricks_won,
            "declarer_tricks": self.declarer_tricks,
            "defender_tricks": self.defender_tricks,
            "moves_played": self.moves_played,
            "total_time": round(self.total_time, 3),
            "total_nodes": self.total_nodes,
            "total_pruned": self.total_pruned,
            "avg_time_per_move": round(self.avg_time_per_move, 4),
            "avg_nodes_per_move": round(self.avg_nodes_per_move, 1),
            "max_time_per_move": round(self.max_time_per_move, 3)
        }


class AIBenchmark:
    """Benchmark AI performance on curated deals"""

    def __init__(self, deals_file: str = "benchmarks/curated_deals.json"):
        """Initialize benchmark with curated deals"""
        self.deals_file = Path(deals_file)
        self.deals = self._load_deals()
        self.results: List[BenchmarkResult] = []

    def _load_deals(self) -> dict:
        """Load curated deals from JSON file"""
        with open(self.deals_file, 'r') as f:
            return json.load(f)

    def _create_deal(self, deal_config: dict) -> Tuple[PlayState, str]:
        """Create PlayState from deal configuration"""
        # Create hands
        hands = {}
        for position, hand_str in deal_config["hands"].items():
            hands[position] = create_hand_from_string(hand_str)

        # Create play state
        state = create_play_scenario(
            deal_config["contract"],
            hands,
            deal_config["vulnerability"]
        )

        return state, deal_config["contract"]

    def _play_hand(self, state: PlayState, ai: object, declarer: str) -> BenchmarkResult:
        """Play a complete hand with given AI"""
        result = BenchmarkResult(state.contract.declarer, ai.get_name())

        # Play until hand is complete
        while not state.is_complete:
            position = state.next_to_play

            # Time the move
            start_time = time.time()
            card = ai.choose_card(state, position)
            elapsed = time.time() - start_time

            # Track statistics
            result.moves_played += 1
            result.total_time += elapsed
            result.move_times.append(elapsed)

            # Get AI statistics if available
            if hasattr(ai, 'get_statistics'):
                stats = ai.get_statistics()
                result.total_nodes += stats.get('nodes', 0)
                result.total_pruned += stats.get('pruned', 0)
                result.move_nodes.append(stats.get('nodes', 0))
            else:
                result.move_nodes.append(0)

            # Play the card
            state.current_trick.append((card, position))
            state.hands[position].cards.remove(card)

            # Check if trick is complete
            if len(state.current_trick) == 4:
                # Determine winner
                winner = self._determine_trick_winner(state)
                state.tricks_won[winner] += 1

                # Save trick to history
                state.trick_history.append(list(state.current_trick))
                state.current_trick = []
                state.next_to_play = winner
            else:
                # Next player
                state.next_to_play = PlayEngine.next_player(position)

        # Finalize results
        result.tricks_won = state.tricks_won

        # Calculate declarer/defender tricks
        declarer_side = [declarer, PlayEngine.partner(declarer)]
        result.declarer_tricks = sum(state.tricks_won[p] for p in declarer_side)
        result.defender_tricks = 13 - result.declarer_tricks

        result.finalize()
        return result

    def _determine_trick_winner(self, state: PlayState) -> str:
        """Determine who won the current trick"""
        if len(state.current_trick) != 4:
            return None

        led_suit = state.current_trick[0][0].suit
        trump_suit = state.contract.trump_suit if state.contract.trump_suit != "NT" else None

        winning_card = None
        winning_position = None

        for card, position in state.current_trick:
            if winning_card is None:
                winning_card = card
                winning_position = position
                continue

            # Trump beats non-trump
            if trump_suit:
                if card.suit == trump_suit and winning_card.suit != trump_suit:
                    winning_card = card
                    winning_position = position
                    continue
                elif card.suit != trump_suit and winning_card.suit == trump_suit:
                    continue

            # Must follow suit
            if card.suit != winning_card.suit:
                continue

            # Compare ranks
            rank_order = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
            if rank_order.index(card.rank) > rank_order.index(winning_card.rank):
                winning_card = card
                winning_position = position

        return winning_position

    def benchmark_ai(self, ai: object, deal_ids: List[str] = None) -> List[BenchmarkResult]:
        """Benchmark an AI on specified deals (or all deals)"""
        if deal_ids is None:
            deal_ids = [deal["id"] for deal in self.deals["deals"]]

        results = []

        for deal_id in deal_ids:
            # Find deal
            deal = next((d for d in self.deals["deals"] if d["id"] == deal_id), None)
            if not deal:
                print(f"Warning: Deal {deal_id} not found")
                continue

            print(f"  Playing {deal_id}: {deal['name']}")

            # Create deal
            state, contract = self._create_deal(deal)
            declarer = state.contract.declarer

            # Play hand
            result = self._play_hand(state, ai, declarer)
            result.deal_id = deal_id

            results.append(result)

            # Print result
            expected = deal.get("expected_result", {}).get("declarer_tricks", "?")
            actual = result.declarer_tricks
            success = "✓" if actual >= expected else "✗"
            print(f"    {success} Expected: {expected}, Actual: {actual}, Time: {result.total_time:.2f}s")

        return results

    def compare_ais(self, ais: List[object], deal_ids: List[str] = None) -> dict:
        """Compare multiple AIs on the same deals"""
        print("\n=== AI Comparison Benchmark ===\n")

        all_results = {}

        for ai in ais:
            print(f"\nBenchmarking: {ai.get_name()}")
            print(f"Difficulty: {ai.get_difficulty()}")
            print("-" * 50)

            results = self.benchmark_ai(ai, deal_ids)
            all_results[ai.get_name()] = results

        return all_results

    def print_summary(self, results: dict):
        """Print summary comparison of results"""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)

        # Group by deal
        deal_ids = set()
        for ai_results in results.values():
            deal_ids.update(r.deal_id for r in ai_results)

        for deal_id in sorted(deal_ids):
            deal = next((d for d in self.deals["deals"] if d["id"] == deal_id), None)
            if not deal:
                continue

            print(f"\n{deal['name']} (Expected: {deal['expected_result']['declarer_tricks']} tricks)")
            print("-" * 80)

            for ai_name, ai_results in results.items():
                result = next((r for r in ai_results if r.deal_id == deal_id), None)
                if not result:
                    continue

                print(f"{ai_name:30} | Tricks: {result.declarer_tricks:2d} | "
                      f"Time: {result.total_time:6.2f}s | "
                      f"Nodes: {result.total_nodes:6d} | "
                      f"Avg/move: {result.avg_time_per_move*1000:5.1f}ms")

        # Overall statistics
        print("\n" + "=" * 80)
        print("OVERALL STATISTICS")
        print("=" * 80)

        for ai_name, ai_results in results.items():
            total_tricks = sum(r.declarer_tricks for r in ai_results)
            total_time = sum(r.total_time for r in ai_results)
            total_nodes = sum(r.total_nodes for r in ai_results)
            total_moves = sum(r.moves_played for r in ai_results)
            avg_time = total_time / total_moves if total_moves > 0 else 0

            # Calculate success rate
            successes = 0
            for result in ai_results:
                deal = next((d for d in self.deals["deals"] if d["id"] == result.deal_id), None)
                if deal:
                    expected = deal.get("expected_result", {}).get("declarer_tricks", 0)
                    if result.declarer_tricks >= expected:
                        successes += 1
            success_rate = successes / len(ai_results) * 100 if ai_results else 0

            print(f"\n{ai_name}:")
            print(f"  Total tricks: {total_tricks} / {len(ai_results) * 13} ({total_tricks / (len(ai_results) * 13) * 100:.1f}%)")
            print(f"  Success rate: {successes}/{len(ai_results)} ({success_rate:.1f}%)")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Total nodes: {total_nodes:,}")
            print(f"  Avg time/move: {avg_time*1000:.2f}ms")
            if total_nodes > 0:
                print(f"  Nodes/second: {total_nodes/total_time:,.0f}")

    def save_results(self, results: dict, filename: str = "benchmarks/benchmark_results.json"):
        """Save benchmark results to JSON file"""
        output = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "deals_file": str(self.deals_file),
            "results": {}
        }

        for ai_name, ai_results in results.items():
            output["results"][ai_name] = [r.to_dict() for r in ai_results]

        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nResults saved to: {filename}")


def main():
    """Run benchmark suite"""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Bridge AI play engines")
    parser.add_argument("--deals", default="benchmarks/curated_deals.json",
                       help="Path to curated deals JSON file")
    parser.add_argument("--output", default="benchmarks/benchmark_results.json",
                       help="Path to save results")
    parser.add_argument("--set", default=None,
                       help="Deal set to benchmark (beginner/intermediate/advanced/all)")
    parser.add_argument("--depth", type=int, nargs="+", default=[2, 3],
                       help="Minimax depths to test (default: 2 3)")

    args = parser.parse_args()

    # Initialize benchmark
    benchmark = AIBenchmark(args.deals)

    # Determine which deals to run
    if args.set and args.set != "all":
        deal_ids = benchmark.deals["deal_sets"].get(args.set, [])
        if not deal_ids:
            print(f"Error: Deal set '{args.set}' not found")
            print(f"Available sets: {list(benchmark.deals['deal_sets'].keys())}")
            return
    else:
        deal_ids = None  # All deals

    # Create AIs to compare
    ais = [SimplePlayAI()]

    for depth in args.depth:
        ais.append(MinimaxPlayAI(max_depth=depth))

    # Run comparison
    results = benchmark.compare_ais(ais, deal_ids)

    # Print summary
    benchmark.print_summary(results)

    # Save results
    benchmark.save_results(results, args.output)


if __name__ == "__main__":
    main()
