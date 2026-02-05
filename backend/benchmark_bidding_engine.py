"""
Bidding Engine Performance Benchmark

Measures the performance of BiddingEngineV2 on a set of random hands.
Tracks metrics like:
- Time per bid
- Time per hand
- Total processing time
- Memory usage (if available)
"""

import time
import json
import random
from pathlib import Path
from typing import Dict, List
from engine.bidding_engine_v2 import BiddingEngineV2
from engine.hand import Hand, Card
from engine.performance_monitor import PerformanceMonitor

class BiddingBenchmark:
    """Benchmark the bidding engine performance"""
    
    def __init__(self, num_hands: int = 100):
        self.num_hands = num_hands
        self.engine = BiddingEngineV2()
        self.monitor = PerformanceMonitor()
        
    def generate_random_hand(self) -> Hand:
        """Generate a random 13-card bridge hand"""
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        suits = ['♠', '♥', '♦', '♣']
        deck = [Card(rank, suit) for suit in suits for rank in ranks]
        
        # Shuffle and deal 13 cards
        random.shuffle(deck)
        cards = deck[:13]
        
        return Hand(cards)
    
    def simulate_auction(self, hand: Hand, max_bids: int = 10) -> List[str]:
        """Simulate a simple auction with the engine"""
        auction = []
        dealer = "South"
        my_position = "North"
        vulnerability = "None"
        
        for i in range(max_bids):
            with self.monitor.timer('bid_generation'):
                try:
                    # Alternate positions based on auction length
                    turn_idx = len(auction) % 4
                    positions = ["South", "West", "North", "East"]
                    current_pos = positions[turn_idx]
                    
                    bid, explanation = self.engine.get_next_bid(
                        hand, 
                        auction, 
                        current_pos,
                        vulnerability=vulnerability,
                        dealer=dealer
                    )
                    
                    auction.append(bid)
                    
                    # Stop if three consecutive passes
                    if len(auction) >= 4 and all(b == "Pass" for b in auction[-3:]):
                        break
                        
                except Exception as e:
                    print(f"Error during bidding: {e}")
                    break
        
        return auction
    
    def run_benchmark(self) -> Dict:
        """Run the performance benchmark"""
        print(f"\n{'='*60}")
        print(f"BIDDING ENGINE PERFORMANCE BENCHMARK")
        print(f"{'='*60}")
        print(f"Testing {self.num_hands} random hands...")
        print()
        
        start_time = time.time()
        total_bids = 0
        total_auctions = 0
        
        for i in range(self.num_hands):
            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{self.num_hands} hands...", end='\r')
            
            with self.monitor.timer('hand_processing'):
                hand = self.generate_random_hand()
                auction = self.simulate_auction(hand)
                total_bids += len(auction)
                total_auctions += 1
        
        total_time = time.time() - start_time
        
        print(f"\n\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        
        # Calculate statistics
        stats = self.monitor.get_stats()
        
        bid_gen_stats = stats.get('bid_generation', {})
        hand_proc_stats = stats.get('hand_processing', {})
        
        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'num_hands': self.num_hands,
            'total_bids': total_bids,
            'total_time': round(total_time, 3),
            'time_per_hand': round(total_time / self.num_hands, 4),
            'time_per_bid': round(bid_gen_stats.get('avg', 0), 4),
            'bids_per_second': round(total_bids / total_time if total_time > 0 else 0, 2),
            'hands_per_second': round(self.num_hands / total_time if total_time > 0 else 0, 2),
            'avg_bids_per_hand': round(total_bids / self.num_hands, 2),
            'bid_generation': {
                'avg_ms': round(bid_gen_stats.get('avg', 0), 3),
                'min_ms': round(bid_gen_stats.get('min', 0), 3),
                'max_ms': round(bid_gen_stats.get('max', 0), 3),
                'count': bid_gen_stats.get('count', 0)
            },
            'hand_processing': {
                'avg_ms': round(hand_proc_stats.get('avg', 0), 3),
                'min_ms': round(hand_proc_stats.get('min', 0), 3),
                'max_ms': round(hand_proc_stats.get('max', 0), 3),
                'count': hand_proc_stats.get('count', 0)
            }
        }
        
        # Print results
        print(f"\nTotal hands processed: {self.num_hands}")
        print(f"Total bids generated: {total_bids}")
        print(f"Total time: {total_time:.2f}s")
        print(f"\nThroughput:")
        print(f"  Hands/second: {results['hands_per_second']:.2f}")
        print(f"  Bids/second: {results['bids_per_second']:.2f}")
        print(f"\nLatency:")
        print(f"  Time per hand: {results['time_per_hand']*1000:.2f}ms")
        print(f"  Time per bid: {results['time_per_bid']:.2f}ms")
        print(f"  Avg bids per hand: {results['avg_bids_per_hand']:.1f}")
        print(f"\nBid Generation Details:")
        print(f"  Average: {results['bid_generation']['avg_ms']:.3f}ms")
        print(f"  Min: {results['bid_generation']['min_ms']:.3f}ms")
        print(f"  Max: {results['bid_generation']['max_ms']:.3f}ms")
        
        return results
    
    def save_results(self, results: Dict, filename: str = "benchmark_bidding_perf.json"):
        """Save results to file and compare with previous runs"""
        filepath = Path(filename)
        
        # Load previous results if they exist
        previous_results = []
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    previous_results = data.get('history', [])
            except Exception as e:
                print(f"Warning: Could not load previous results: {e}")
        
        # Add current results to history
        previous_results.append(results)
        
        # Save updated history
        output = {
            'latest': results,
            'history': previous_results
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
        
        # Compare with previous run if available
        if len(previous_results) > 1:
            prev = previous_results[-2]
            curr = results
            
            print(f"\n{'='*60}")
            print("COMPARISON WITH PREVIOUS RUN")
            print(f"{'='*60}")
            print(f"Previous run: {prev['timestamp']}")
            print(f"Current run:  {curr['timestamp']}")
            print()
            
            # Calculate changes
            def pct_change(old, new):
                if old == 0:
                    return 0
                return ((new - old) / old) * 100
            
            metrics = [
                ('Hands/second', 'hands_per_second', True),
                ('Bids/second', 'bids_per_second', True),
                ('Time per hand (ms)', 'time_per_hand', False, 1000),
                ('Time per bid (ms)', 'time_per_bid', False, 1)
            ]
            
            for name, key, higher_is_better, *multiplier in metrics:
                mult = multiplier[0] if multiplier else 1
                old_val = prev.get(key, 0) * mult
                new_val = curr.get(key, 0) * mult
                change = pct_change(old_val, new_val)
                
                if higher_is_better:
                    indicator = "✓" if change >= 0 else "✗"
                else:
                    indicator = "✓" if change <= 0 else "✗"
                
                sign = "+" if change > 0 else ""
                print(f"{indicator} {name:25}: {old_val:8.2f} → {new_val:8.2f} ({sign}{change:+6.1f}%)")
            
            print(f"{'='*60}")

def main():
    """Run the benchmark"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark bidding engine performance")
    parser.add_argument('--hands', type=int, default=100,
                       help="Number of hands to test (default: 100)")
    parser.add_argument('--output', default="benchmark_bidding_perf.json",
                       help="Output file for results")
    
    args = parser.parse_args()
    
    benchmark = BiddingBenchmark(num_hands=args.hands)
    results = benchmark.run_benchmark()
    benchmark.save_results(results, args.output)

if __name__ == '__main__':
    main()
