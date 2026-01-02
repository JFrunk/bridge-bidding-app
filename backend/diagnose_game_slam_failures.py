#!/usr/bin/env python3
"""
Diagnostic Script: Categorize Game/Slam Failures

This script runs 500+ hands through the bidding system and categorizes
failures to determine the root cause:

1. VALIDATION_REJECTED: Module suggested game bid, validation rejected it
2. MODULE_NOT_ATTEMPTING: Module returned Pass or non-game bid when game was available
3. CONTEXT_NOT_TRACKED: Combined points not being properly tracked

Output: Detailed breakdown of failure types to guide architectural fix.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import random
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from engine.hand import Hand, Card
# from engine.hand_constructor import generate_constrained_hands
from engine.bidding_engine import BiddingEngine
from engine.ai.feature_extractor import extract_features
from engine.ai.auction_context import analyze_auction_context
from engine.ai.decision_engine import select_bidding_module
from engine.ai.module_registry import ModuleRegistry
from engine.ai.validation_pipeline import ValidationPipeline

# Suppress ALL verbose output
import logging
logging.getLogger().setLevel(logging.CRITICAL)

# Suppress print statements from decision_engine
import sys
import io

class SuppressOutput:
    """Context manager to suppress stdout during execution."""
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        return self

    def __exit__(self, *args):
        sys.stdout = self._original_stdout


class GameSlamDiagnostic:
    """Diagnose why game/slam contracts aren't being reached."""

    def __init__(self):
        self.engine = BiddingEngine()
        self.validation_pipeline = ValidationPipeline()

        # Categorized failures
        self.failures = {
            'validation_rejected': [],      # Module tried game, validation rejected
            'module_not_attempting': [],    # Module returned non-game bid
            'context_not_updated': [],      # Combined points not properly tracked
            'game_forcing_ignored': [],     # Game forcing sequence not recognized
        }

        # Success tracking
        self.successes = []
        self.total_game_worthy_hands = 0

    def run_diagnostic(self, num_hands: int = 500):
        """Run diagnostic on specified number of hands."""
        print(f"Running game/slam diagnostic on {num_hands} hands...")
        print("=" * 70)

        positions = ['North', 'East', 'South', 'West']

        for hand_num in range(num_hands):
            if (hand_num + 1) % 100 == 0:
                print(f"  Progress: {hand_num + 1}/{num_hands} hands analyzed")

            # Generate 4 random hands
            hands = self._generate_four_hands()

            # Check if NS partnership has game values (25+ combined HCP)
            ns_hcp = hands['South'].hcp + hands['North'].hcp
            ew_hcp = hands['East'].hcp + hands['West'].hcp

            # Only analyze game-worthy hands for NS partnership
            if ns_hcp >= 25:
                self.total_game_worthy_hands += 1
                self._analyze_auction(hands, positions, hand_num, ns_hcp)

        self._print_report()

    def _generate_four_hands(self) -> Dict[str, Hand]:
        """Generate 4 random hands (complete deal)."""
        deck = []
        for suit in ['♠', '♥', '♦', '♣']:
            for rank in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']:
                deck.append(Card(rank=rank, suit=suit))

        random.shuffle(deck)

        hands = {}
        for i, pos in enumerate(['North', 'East', 'South', 'West']):
            cards = deck[i*13:(i+1)*13]
            hands[pos] = Hand(cards)

        return hands

    def _analyze_auction(self, hands: Dict[str, Hand], positions: List[str],
                         hand_num: int, ns_hcp: int):
        """
        Simulate auction and analyze why game wasn't reached.
        """
        auction_history = []
        dealer = 'North'  # Start with North as dealer
        vulnerability = 'None'

        game_reached = False
        max_bids = 20  # Prevent infinite loops

        # Track what each module suggested vs what was accepted
        bid_trace = []

        for bid_round in range(max_bids):
            bidder_idx = bid_round % 4
            bidder_pos = positions[(positions.index(dealer) + bid_round) % 4]
            hand = hands[bidder_pos]

            # Get features and module (suppress verbose output)
            with SuppressOutput():
                features = extract_features(hand, auction_history, bidder_pos, vulnerability, dealer)
                module_name = select_bidding_module(features)

            # Also analyze auction context to check combined points
            my_index = positions.index(bidder_pos)
            auction_context = analyze_auction_context(auction_history, positions, my_index)

            if module_name == 'pass_by_default':
                bid = 'Pass'
                explanation = 'No module selected'
            else:
                specialist = ModuleRegistry.get(module_name)
                if specialist:
                    with SuppressOutput():
                        result = specialist.evaluate(hand, features)
                    if result:
                        suggested_bid = result[0]
                        explanation = result[1]
                        metadata = result[2] if len(result) > 2 else None

                        # Check validation
                        is_valid, validation_error = self.validation_pipeline.validate(
                            suggested_bid, hand, features, auction_history, metadata
                        )

                        if is_valid:
                            bid = suggested_bid
                        else:
                            # VALIDATION REJECTED - key failure type
                            if bidder_pos in ['North', 'South'] and self._is_game_bid(suggested_bid):
                                self.failures['validation_rejected'].append({
                                    'hand_num': hand_num,
                                    'ns_hcp': ns_hcp,
                                    'bidder': bidder_pos,
                                    'suggested_bid': suggested_bid,
                                    'validation_error': validation_error,
                                    'hand_hcp': hand.hcp,
                                    'module': module_name,
                                    'auction': auction_history.copy(),
                                    'game_forcing': auction_context.ranges.game_forcing,
                                    'combined_midpoint': auction_context.ranges.combined_midpoint,
                                })
                            bid = 'Pass'
                    else:
                        bid = 'Pass'
                        explanation = 'Module returned None'
                else:
                    bid = 'Pass'
                    explanation = f'Module {module_name} not found'

            # Track NS bids that should have been game
            if bidder_pos in ['North', 'South']:
                should_bid_game = ns_hcp >= 25 and not game_reached
                bid_trace.append({
                    'position': bidder_pos,
                    'bid': bid,
                    'module': module_name,
                    'should_bid_game': should_bid_game,
                    'combined_midpoint': auction_context.ranges.combined_midpoint,
                    'game_forcing': auction_context.ranges.game_forcing,
                    'hand_hcp': hand.hcp,
                })

            auction_history.append(bid)

            # Check if game was reached
            if self._is_game_bid(bid):
                game_reached = True

            # Check for auction end (3 consecutive passes after at least one bid)
            if len(auction_history) >= 4:
                non_pass_bids = [b for b in auction_history if b != 'Pass']
                if len(non_pass_bids) > 0 and auction_history[-3:] == ['Pass', 'Pass', 'Pass']:
                    break

            # Also end if all pass
            if auction_history == ['Pass', 'Pass', 'Pass', 'Pass']:
                break

        # Analyze final result
        if game_reached:
            self.successes.append({'hand_num': hand_num, 'ns_hcp': ns_hcp})
        else:
            # Game-worthy hand didn't reach game - categorize why
            self._categorize_failure(hand_num, ns_hcp, auction_history, bid_trace, hands)

    def _is_game_bid(self, bid: str) -> bool:
        """Check if bid is at game level or higher."""
        if not bid or bid in ['Pass', 'X', 'XX']:
            return False
        try:
            level = int(bid[0])
            strain = bid[1:]
            # Game levels: 3NT, 4♥, 4♠, 5♣, 5♦ and higher
            if level >= 5:
                return True
            if level == 4 and strain in ['♥', '♠', 'NT']:
                return True
            if level >= 3 and strain == 'NT':
                return True
        except:
            return False
        return False

    def _categorize_failure(self, hand_num: int, ns_hcp: int,
                           auction: List[str], bid_trace: List[dict],
                           hands: Dict[str, Hand]):
        """Categorize why game wasn't reached."""

        # Check if combined midpoint was ever correct
        midpoint_issues = [t for t in bid_trace if t['combined_midpoint'] < 20 and ns_hcp >= 25]

        if midpoint_issues:
            self.failures['context_not_updated'].append({
                'hand_num': hand_num,
                'ns_hcp': ns_hcp,
                'auction': auction,
                'trace': bid_trace,
                'issue': 'Combined midpoint never reached 25 despite 25+ HCP',
            })
            return

        # Check if game forcing was set but game not reached
        gf_set = any(t['game_forcing'] for t in bid_trace)
        if gf_set:
            self.failures['game_forcing_ignored'].append({
                'hand_num': hand_num,
                'ns_hcp': ns_hcp,
                'auction': auction,
                'trace': bid_trace,
                'issue': 'game_forcing=True but game not bid',
            })
            return

        # Default: module didn't attempt game
        self.failures['module_not_attempting'].append({
            'hand_num': hand_num,
            'ns_hcp': ns_hcp,
            'auction': auction,
            'trace': bid_trace,
            'n_hand': str(hands['North']),
            's_hand': str(hands['South']),
        })

    def _print_report(self):
        """Print diagnostic report."""
        print("\n" + "=" * 70)
        print("GAME/SLAM DIAGNOSTIC REPORT")
        print("=" * 70)

        total_failures = sum(len(v) for v in self.failures.values())
        success_count = len(self.successes)

        print(f"\nTotal game-worthy hands (NS 25+ HCP): {self.total_game_worthy_hands}")
        print(f"Games reached: {success_count} ({100*success_count/max(1,self.total_game_worthy_hands):.1f}%)")
        print(f"Games NOT reached: {total_failures} ({100*total_failures/max(1,self.total_game_worthy_hands):.1f}%)")

        print("\n" + "-" * 70)
        print("FAILURE BREAKDOWN BY CATEGORY")
        print("-" * 70)

        for category, failures in self.failures.items():
            pct = 100 * len(failures) / max(1, total_failures)
            print(f"\n{category.upper()}: {len(failures)} failures ({pct:.1f}% of failures)")

            if failures and len(failures) > 0:
                print(f"  Examples (up to 5):")
                for f in failures[:5]:
                    if category == 'validation_rejected':
                        print(f"    Hand {f['hand_num']}: {f['bidder']} tried {f['suggested_bid']}")
                        print(f"      Error: {f['validation_error']}")
                        print(f"      Hand HCP: {f['hand_hcp']}, NS combined: {f['ns_hcp']}")
                        print(f"      Auction: {f['auction']}")
                        print(f"      game_forcing={f['game_forcing']}, combined_midpoint={f['combined_midpoint']}")
                    elif category == 'module_not_attempting':
                        print(f"    Hand {f['hand_num']}: NS had {f['ns_hcp']} HCP")
                        print(f"      Auction: {f['auction']}")
                        # Show last few NS bids
                        ns_bids = [(t['position'], t['bid'], t['module']) for t in f['trace']]
                        print(f"      NS bids: {ns_bids[-4:]}")
                    else:
                        print(f"    Hand {f['hand_num']}: {f.get('issue', 'Unknown')}")

        print("\n" + "=" * 70)
        print("KEY INSIGHTS")
        print("=" * 70)

        # Analyze validation rejections
        val_rejected = self.failures['validation_rejected']
        if val_rejected:
            error_types = defaultdict(int)
            for f in val_rejected:
                # Extract error type
                error = f['validation_error']
                if 'Insufficient HCP' in error:
                    error_types['Insufficient HCP'] += 1
                elif 'cards' in error:
                    error_types['Suit length'] += 1
                else:
                    error_types['Other'] += 1

            print(f"\nValidation rejection breakdown:")
            for err_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
                print(f"  {err_type}: {count}")

        # Check if game_forcing is ever being set
        gf_ignored = self.failures['game_forcing_ignored']
        print(f"\nGame-forcing flag:")
        print(f"  Times set but ignored: {len(gf_ignored)}")

        # Recommendations
        print("\n" + "-" * 70)
        print("RECOMMENDED FIXES")
        print("-" * 70)

        if len(val_rejected) > len(self.failures['module_not_attempting']):
            print("\n1. PRIMARY ISSUE: Validation is rejecting game bids")
            print("   FIX: Make ValidationPipeline check AuctionContext.game_forcing")
            print("        When game_forcing=True, bypass HCP requirements")
        else:
            print("\n1. PRIMARY ISSUE: Modules not attempting game bids")
            print("   FIX: Modules need to check combined_midpoint or game_forcing")
            print("        to decide when to bid game")

        if self.failures['context_not_updated']:
            print("\n2. SECONDARY ISSUE: Combined midpoint not being tracked")
            print("   FIX: Ensure AuctionAnalyzer updates ranges after each bid")


def main():
    diagnostic = GameSlamDiagnostic()
    diagnostic.run_diagnostic(num_hands=500)


if __name__ == '__main__':
    main()
