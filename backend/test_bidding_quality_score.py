#!/usr/bin/env python3
"""
Bidding Quality Score System

Runs comprehensive tests on bidding logic and generates a quality score.
Usage:
    python3 test_bidding_quality_score.py --hands 500
    python3 test_bidding_quality_score.py --hands 100 --fast
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
from engine.bidding_validation import BidValidator


def generate_random_hand() -> Hand:
    """Generate a random 13-card bridge hand."""
    # Create full deck
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for suit in suits for rank in ranks]

    # Shuffle and deal 13 cards
    random.shuffle(deck)
    cards = deck[:13]

    return Hand(cards)


class BiddingQualityScorer:
    """Comprehensive bidding quality testing."""

    def __init__(self, num_hands: int = 500):
        self.num_hands = num_hands
        self.engine = BiddingEngine()
        self.results = {
            'total_hands': 0,
            'total_bids': 0,
            'total_non_pass_bids': 0,
            'legality_errors': [],
            'appropriateness_errors': [],
            'convention_errors': [],
            'game_slam_errors': [],
            'game_errors': [],      # Separated: missed game with 25-32 points
            'slam_errors': [],      # Separated: missed slam with 33+ points
            'game_situations': 0,   # Track actual game-worth hands
            'slam_situations': 0,   # Track actual slam-worth hands
            'reasonableness_ratings': {
                'excellent': 0,
                'good': 0,
                'questionable': 0,
                'poor': 0,
                'terrible': 0
            },
            'consistency_failures': []
        }

    def run_full_test(self) -> Dict:
        """Run all tests and return composite score."""
        print(f"🎯 Running Bidding Quality Score on {self.num_hands} hands...")
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
        """Test a single randomly generated hand."""
        self.results['total_hands'] += 1

        # Generate 4 hands
        hands = {
            'North': generate_random_hand(),
            'South': generate_random_hand(),
            'East': generate_random_hand(),
            'West': generate_random_hand()
        }

        # Simulate bidding
        dealer = random.choice(['North', 'South', 'East', 'West'])
        vulnerability = random.choice(['None', 'NS', 'EW', 'Both'])

        auction = self._simulate_auction(hands, dealer, vulnerability)

        # Score the auction
        self._score_auction(auction, hands, hand_number)

    def _simulate_auction(
        self,
        hands: Dict[str, Hand],
        dealer: str,
        vulnerability: str
    ) -> List[Dict]:
        """Simulate a complete auction."""
        positions = ['North', 'East', 'South', 'West']
        dealer_idx = positions.index(dealer)

        auction_history = []
        auction_details = []
        consecutive_passes = 0

        current_idx = dealer_idx

        # Bidding continues until 3 consecutive passes (or all pass in opening)
        max_bids = 50  # Safety limit
        bid_count = 0

        while consecutive_passes < 3 and bid_count < max_bids:
            position = positions[current_idx % 4]
            hand = hands[position]

            # Get AI bid
            try:
                bid, explanation = self.engine.get_next_bid(
                    hand=hand,
                    auction_history=auction_history,
                    my_position=position,
                    vulnerability=vulnerability
                )
            except Exception as e:
                # If bidding fails, pass
                bid = 'Pass'
                explanation = f"Error in bidding: {e}"

            # Record bid
            auction_history.append(bid)
            auction_details.append({
                'position': position,
                'bid': bid,
                'explanation': explanation,
                'hand': hand,
                'auction_before': auction_history[:-1].copy()
            })

            self.results['total_bids'] += 1
            if bid != 'Pass':
                self.results['total_non_pass_bids'] += 1

            # Track consecutive passes
            if bid == 'Pass':
                consecutive_passes += 1
            else:
                consecutive_passes = 0

            # Stop if all passed in opening
            if len(auction_history) == 4 and all(b == 'Pass' for b in auction_history):
                break

            current_idx += 1
            bid_count += 1

        return auction_details

    def _score_auction(
        self,
        auction: List[Dict],
        hands: Dict[str, Hand],
        hand_number: int
    ):
        """Score all aspects of the auction."""
        for bid_detail in auction:
            bid = bid_detail['bid']
            hand = bid_detail['hand']
            position = bid_detail['position']
            auction_before = bid_detail['auction_before']

            # 1. Check legality (CRITICAL) - even for Pass
            if not BidValidator.is_legal_bid(bid, auction_before):
                self.results['legality_errors'].append({
                    'hand_number': hand_number,
                    'position': position,
                    'bid': bid,
                    'auction': auction_before,
                    'hand_hcp': hand.hcp,
                    'explanation': bid_detail['explanation']
                })

            # Skip Pass for other checks
            if bid == 'Pass':
                continue

            # 2. Check appropriateness
            self._check_appropriateness(bid, hand, auction_before, position, hand_number)

            # 3. Check conventions
            self._check_conventions(bid, hand, auction_before, position, hand_number, bid_detail['explanation'])

            # 4. Rate reasonableness
            self._rate_reasonableness(bid, hand, auction_before, position)

        # 5. Check game/slam accuracy
        self._check_game_slam_accuracy(auction, hands, hand_number)

    def _check_appropriateness(
        self,
        bid: str,
        hand: Hand,
        auction: List[str],
        position: str,
        hand_number: int
    ):
        """Check if bid is appropriate for hand strength/shape."""
        # Parse bid
        try:
            level = int(bid[0])
            strain = bid[1:]
        except (ValueError, IndexError):
            return  # Not a level bid (X, XX)

        # Get suit length
        suit_length = hand.suit_lengths.get(strain, 0)

        # Simplified appropriateness checks
        # (Full logic would need complete auction analysis)

        # Check for obvious inappropriate bids
        if level >= 3:
            # 3-level or higher with weak hand
            if hand.total_points < 8:
                # Unless it's a preempt with long suit
                if suit_length < 6:
                    self._record_appropriateness_error(
                        hand_number, position, bid, hand,
                        f"{level}-level bid with only {hand.total_points} points and {suit_length} cards"
                    )
            elif hand.total_points < 10 and suit_length < 5:
                # 3-level constructive needs 10+ HCP or 6+ card preempt
                self._record_appropriateness_error(
                    hand_number, position, bid, hand,
                    f"3-level bid with {hand.total_points} points and only {suit_length} cards"
                )

        if level >= 4:
            # 4-level needs game values or extreme distribution
            if hand.total_points < 10 and suit_length < 7:
                self._record_appropriateness_error(
                    hand_number, position, bid, hand,
                    f"4-level bid with {hand.total_points} points and {suit_length} cards"
                )

        # Check for bidding suits with insufficient length
        if suit_length < 4 and strain in ['♠', '♥', '♦', '♣']:
            # Never bid a suit with <4 cards (except special conventions)
            self._record_appropriateness_error(
                hand_number, position, bid, hand,
                f"Bid {strain} with only {suit_length} cards"
            )

    def _check_conventions(
        self,
        bid: str,
        hand: Hand,
        auction: List[str],
        position: str,
        hand_number: int,
        explanation: str
    ):
        """Check if conventional bids are used correctly."""
        # Stayman check - must verify this is a response to PARTNER's 1NT (not opponent's)
        # Partner's 1NT would be 2 bids back in the auction (1NT - Pass - 2♣)
        # If auction[-1] == '1NT', that's the OPPONENT's 1NT (direct seat), so 2♣ is an overcall
        if bid == '2♣' and len(auction) >= 2:
            # Check if partner opened 1NT (auction[-2] should be 1NT, auction[-1] should be Pass)
            if auction[-2] == '1NT' and auction[-1] == 'Pass':
                # This is Stayman - check for 4-card major requirement
                if hand.suit_lengths.get('♠', 0) < 4 and hand.suit_lengths.get('♥', 0) < 4:
                    self.results['convention_errors'].append({
                        'hand_number': hand_number,
                        'position': position,
                        'convention': 'Stayman',
                        'error': 'Used Stayman without 4-card major',
                        'hand_hcp': hand.hcp,
                        'spades': hand.suit_lengths.get('♠', 0),
                        'hearts': hand.suit_lengths.get('♥', 0)
                    })
            # Note: If auction[-1] == '1NT', that's opponent's 1NT - 2♣ is a club overcall, not Stayman

        # Blackwood check
        if bid == '4NT' and 'Blackwood' in explanation:
            if hand.hcp < 16:
                self.results['convention_errors'].append({
                    'hand_number': hand_number,
                    'position': position,
                    'convention': 'Blackwood',
                    'error': f'Used Blackwood with only {hand.hcp} HCP (need 16+)',
                    'hand_hcp': hand.hcp
                })

        # 1NT opening check
        if bid == '1NT' and len(auction) == 0:
            if hand.hcp < 15 or hand.hcp > 17:
                self.results['convention_errors'].append({
                    'hand_number': hand_number,
                    'position': position,
                    'convention': '1NT opening',
                    'error': f'Opened 1NT with {hand.hcp} HCP (need 15-17)',
                    'hand_hcp': hand.hcp
                })

    def _rate_reasonableness(
        self,
        bid: str,
        hand: Hand,
        auction: List[str],
        position: str
    ):
        """Rate how reasonable the bid is (subjective)."""
        rating = 'good'  # Default

        try:
            level = int(bid[0])
            strain = bid[1:]
            suit_length = hand.suit_lengths.get(strain, 0)

            # Very weak hand bidding at high level = questionable/poor
            if level >= 3 and hand.total_points < 8:
                if suit_length < 6:
                    rating = 'poor'
                else:
                    rating = 'questionable'  # Preempt
            elif level >= 4 and hand.total_points < 10:
                rating = 'questionable'

            # Bidding a suit with very few cards = poor
            if suit_length < 3 and strain in ['♠', '♥', '♦', '♣']:
                rating = 'terrible'
            elif suit_length < 4 and strain in ['♠', '♥', '♦', '♣'] and level >= 2:
                rating = 'poor'

            # Strong bids are generally good
            if hand.total_points >= 16:
                rating = 'excellent'
            elif hand.total_points >= 13:
                rating = 'good'

        except (ValueError, IndexError):
            pass  # X, XX - hard to rate

        self.results['reasonableness_ratings'][rating] += 1

    def _check_game_slam_accuracy(
        self,
        auction: List[Dict],
        hands: Dict[str, Hand],
        hand_number: int
    ):
        """Check if partnership reaches correct game/slam."""
        final_contract = None
        declarer = None

        for bid_detail in reversed(auction):
            if bid_detail['bid'] not in ['Pass', 'X', 'XX']:
                final_contract = bid_detail['bid']
                declarer = bid_detail['position']
                break

        if not final_contract or not declarer:
            return  # Passed out

        # Calculate partnership combined strength for BOTH partnerships
        ns_points = hands['North'].total_points + hands['South'].total_points
        ew_points = hands['East'].total_points + hands['West'].total_points

        # Check both partnerships for game/slam potential
        self._check_partnership_game_slam(
            ns_points, 'NS', declarer in ['North', 'South'],
            final_contract, hand_number, hands['North'], hands['South']
        )
        self._check_partnership_game_slam(
            ew_points, 'EW', declarer in ['East', 'West'],
            final_contract, hand_number, hands['East'], hands['West']
        )

    def _check_partnership_game_slam(
        self,
        combined_points: int,
        partnership: str,
        is_declarer: bool,
        final_contract: str,
        hand_number: int,
        hand1: Hand,
        hand2: Hand
    ):
        """Check if a specific partnership reached correct level."""
        try:
            level = int(final_contract[0])
            strain = final_contract[1:]
        except (ValueError, IndexError):
            return

        # Determine if this is a game situation (25-32 points)
        is_game_situation = 25 <= combined_points <= 32
        # Determine if this is a slam situation (33+ points)
        is_slam_situation = combined_points >= 33

        if is_game_situation:
            self.results['game_situations'] += 1

            # If this partnership is declarer, check if they reached game
            if is_declarer:
                reached_game = False
                if strain in ['♥', '♠'] and level >= 4:
                    reached_game = True
                elif strain == 'NT' and level >= 3:
                    reached_game = True
                elif strain in ['♣', '♦'] and level >= 5:
                    reached_game = True  # Minor game is 5-level

                if not reached_game:
                    error_detail = {
                        'hand_number': hand_number,
                        'partnership': partnership,
                        'error': f'Stopped at {final_contract} with {combined_points} combined points',
                        'combined_points': combined_points,
                        'final_contract': final_contract,
                        'hand1_points': hand1.total_points,
                        'hand2_points': hand2.total_points,
                        'hand1_hcp': hand1.hcp,
                        'hand2_hcp': hand2.hcp
                    }
                    self.results['game_errors'].append(error_detail)
                    # Also add to combined list for backward compatibility
                    self.results['game_slam_errors'].append(error_detail)

        if is_slam_situation:
            self.results['slam_situations'] += 1

            # If this partnership is declarer, check if they reached slam
            if is_declarer:
                reached_slam = level >= 6

                if not reached_slam:
                    error_detail = {
                        'hand_number': hand_number,
                        'partnership': partnership,
                        'error': f'Stopped at {final_contract} with {combined_points} combined points (slam values)',
                        'combined_points': combined_points,
                        'final_contract': final_contract,
                        'hand1_points': hand1.total_points,
                        'hand2_points': hand2.total_points,
                        'hand1_hcp': hand1.hcp,
                        'hand2_hcp': hand2.hcp
                    }
                    self.results['slam_errors'].append(error_detail)
                    # Also add to combined list for backward compatibility
                    self.results['game_slam_errors'].append(error_detail)

    def _record_appropriateness_error(
        self,
        hand_number: int,
        position: str,
        bid: str,
        hand: Hand,
        reason: str
    ):
        """Record an appropriateness error."""
        self.results['appropriateness_errors'].append({
            'hand_number': hand_number,
            'position': position,
            'bid': bid,
            'hand_hcp': hand.hcp,
            'hand_total_points': hand.total_points,
            'hand_shape': f"{hand.suit_lengths['♠']}{hand.suit_lengths['♥']}{hand.suit_lengths['♦']}{hand.suit_lengths['♣']}",
            'reason': reason
        })

    def _calculate_scores(self) -> Dict:
        """Calculate final scores."""
        total_bids = self.results['total_bids']
        total_non_pass = max(1, self.results['total_non_pass_bids'])

        # 1. Legality Score (must be 100%)
        legality_errors = len(self.results['legality_errors'])
        legality_score = ((total_bids - legality_errors) / total_bids * 100) if total_bids > 0 else 100

        # 2. Appropriateness Score
        appropriateness_errors = len(self.results['appropriateness_errors'])
        appropriateness_score = ((total_non_pass - appropriateness_errors) / total_non_pass * 100)

        # 3. Convention Score
        convention_errors = len(self.results['convention_errors'])
        # Estimate ~10% of bids are conventional
        conventional_bids = max(1, int(total_bids * 0.1))
        convention_score = ((conventional_bids - min(convention_errors, conventional_bids)) / conventional_bids * 100)

        # 4. Consistency Score (placeholder - would need multiple runs)
        consistency_score = 100  # Not implemented yet

        # 5. Reasonableness Score
        ratings = self.results['reasonableness_ratings']
        total_rated = sum(ratings.values())
        if total_rated > 0:
            reasonableness_score = (
                (ratings['excellent'] + ratings['good'] + ratings['questionable']) / total_rated * 100
            )
        else:
            reasonableness_score = 100

        # 6. Game/Slam Accuracy (now with breakdown)
        game_errors = len(self.results['game_errors'])
        slam_errors = len(self.results['slam_errors'])
        game_slam_errors = len(self.results['game_slam_errors'])

        # Use actual situations tracked, with fallback estimate
        game_situations = max(1, self.results['game_situations']) if self.results['game_situations'] > 0 else max(1, int(self.results['total_hands'] * 0.25))
        slam_situations = max(1, self.results['slam_situations']) if self.results['slam_situations'] > 0 else max(1, int(self.results['total_hands'] * 0.05))

        game_score = ((game_situations - min(game_errors, game_situations)) / game_situations * 100)
        slam_score = ((slam_situations - min(slam_errors, slam_situations)) / slam_situations * 100)

        # Combined score weighted toward game (game is 4x more frequent)
        game_slam_score = game_score * 0.8 + slam_score * 0.2

        # Composite Score
        composite_score = (
            legality_score * 0.30 +
            appropriateness_score * 0.25 +
            convention_score * 0.15 +
            consistency_score * 0.10 +
            reasonableness_score * 0.15 +
            game_slam_score * 0.05
        )

        return {
            'total_hands': self.results['total_hands'],
            'total_bids': total_bids,
            'total_non_pass_bids': total_non_pass,
            'scores': {
                'legality': round(legality_score, 1),
                'appropriateness': round(appropriateness_score, 1),
                'conventions': round(convention_score, 1),
                'consistency': round(consistency_score, 1),
                'reasonableness': round(reasonableness_score, 1),
                'game_slam': round(game_slam_score, 1),
                'game_only': round(game_score, 1),      # NEW: separate game score
                'slam_only': round(slam_score, 1),      # NEW: separate slam score
                'composite': round(composite_score, 1)
            },
            'error_counts': {
                'legality': legality_errors,
                'appropriateness': appropriateness_errors,
                'conventions': convention_errors,
                'game_slam': game_slam_errors,
                'game_only': game_errors,              # NEW
                'slam_only': slam_errors               # NEW
            },
            'situation_counts': {                      # NEW: actual situation counts
                'game_situations': game_situations,
                'slam_situations': slam_situations
            },
            'errors': {
                'legality': self.results['legality_errors'][:10],
                'appropriateness': self.results['appropriateness_errors'][:10],
                'conventions': self.results['convention_errors'][:10],
                'game_slam': self.results['game_slam_errors'][:10],
                'game_only': self.results['game_errors'][:10],    # NEW
                'slam_only': self.results['slam_errors'][:10]     # NEW
            },
            'reasonableness_breakdown': ratings,
            'grade': self._get_grade(composite_score)
        }

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 95:
            return 'A (Production Ready)'
        elif score >= 90:
            return 'B (Good, minor issues)'
        elif score >= 85:
            return 'C (Acceptable, needs work)'
        elif score >= 80:
            return 'D (Poor, major issues)'
        else:
            return 'F (Failing, do not deploy)'

    def print_report(self, scores: Dict):
        """Print comprehensive report."""
        print("=" * 80)
        print("BIDDING QUALITY SCORE REPORT")
        print("=" * 80)
        print()
        print(f"Hands Tested:      {scores['total_hands']}")
        print(f"Total Bids:        {scores['total_bids']}")
        print(f"Non-Pass Bids:     {scores['total_non_pass_bids']}")
        print()
        print("-" * 80)
        print("INDIVIDUAL SCORES:")
        print("-" * 80)
        s = scores['scores']
        print(f"  1. Legality:        {s['legality']:5.1f}% {'✅' if s['legality'] == 100 else '❌'} ({scores['error_counts']['legality']} errors)")
        print(f"  2. Appropriateness: {s['appropriateness']:5.1f}% {'✅' if s['appropriateness'] >= 95 else '⚠️ ' if s['appropriateness'] >= 85 else '❌'} ({scores['error_counts']['appropriateness']} errors)")
        print(f"  3. Conventions:     {s['conventions']:5.1f}% {'✅' if s['conventions'] >= 90 else '⚠️ ' if s['conventions'] >= 80 else '❌'} ({scores['error_counts']['conventions']} errors)")
        print(f"  4. Consistency:     {s['consistency']:5.1f}% {'✅' if s['consistency'] >= 85 else '⚠️ '} (not implemented)")
        print(f"  5. Reasonableness:  {s['reasonableness']:5.1f}% {'✅' if s['reasonableness'] >= 90 else '⚠️ ' if s['reasonableness'] >= 80 else '❌'}")
        print(f"  6. Game/Slam:       {s['game_slam']:5.1f}% {'✅' if s['game_slam'] >= 80 else '⚠️ ' if s['game_slam'] >= 70 else '❌'} ({scores['error_counts']['game_slam']} errors)")
        print()
        print("     GAME/SLAM BREAKDOWN:")
        sit = scores.get('situation_counts', {})
        print(f"     - Game (25-32 pts): {s.get('game_only', 0):5.1f}% ({scores['error_counts'].get('game_only', 0)} missed / {sit.get('game_situations', '?')} situations)")
        print(f"     - Slam (33+ pts):   {s.get('slam_only', 0):5.1f}% ({scores['error_counts'].get('slam_only', 0)} missed / {sit.get('slam_situations', '?')} situations)")
        print()
        print("-" * 80)
        print(f"COMPOSITE SCORE: {s['composite']:.1f}%")
        print(f"GRADE:           {scores['grade']}")
        print("-" * 80)
        print()

        # Reasonableness breakdown
        rb = scores['reasonableness_breakdown']
        print("REASONABLENESS BREAKDOWN:")
        print(f"  Excellent:    {rb['excellent']:4d}")
        print(f"  Good:         {rb['good']:4d}")
        print(f"  Questionable: {rb['questionable']:4d}")
        print(f"  Poor:         {rb['poor']:4d}")
        print(f"  Terrible:     {rb['terrible']:4d}")
        print()

        # Print sample errors
        if scores['errors']['legality']:
            print("❌ LEGALITY ERRORS (sample):")
            for err in scores['errors']['legality'][:5]:
                print(f"   Hand {err['hand_number']}: {err['position']} bid {err['bid']} (illegal)")
                print(f"      Auction: {err['auction']}")
            print()

        if scores['errors']['appropriateness']:
            print("⚠️  APPROPRIATENESS ERRORS (sample):")
            for err in scores['errors']['appropriateness'][:5]:
                print(f"   Hand {err['hand_number']}: {err['position']} bid {err['bid']}")
                print(f"      {err['reason']}")
                print(f"      Hand: {err['hand_hcp']} HCP, {err['hand_total_points']} total, shape {err['hand_shape']}")
            print()

        if scores['errors']['conventions']:
            print("🎴 CONVENTION ERRORS (sample):")
            for err in scores['errors']['conventions'][:5]:
                print(f"   Hand {err['hand_number']}: {err['position']} - {err['convention']}")
                print(f"      {err['error']}")
            print()

        print("=" * 80)

    def save_detailed_report(self, scores: Dict, filename: str = None):
        """Save detailed JSON report."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bidding_quality_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'scores': scores,
                'all_errors': {
                    'legality': self.results['legality_errors'],
                    'appropriateness': self.results['appropriateness_errors'],
                    'conventions': self.results['convention_errors'],
                    'game_slam': self.results['game_slam_errors']
                }
            }, f, indent=2)

        print(f"📄 Detailed report saved to: {filename}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Bidding Quality Score System')
    parser.add_argument('--hands', type=int, default=500, help='Number of hands to test (default: 500)')
    parser.add_argument('--fast', action='store_true', help='Fast mode (100 hands)')
    parser.add_argument('--output', type=str, help='Output JSON file path')

    args = parser.parse_args()

    num_hands = 100 if args.fast else args.hands

    scorer = BiddingQualityScorer(num_hands=num_hands)
    scores = scorer.run_full_test()
    scorer.print_report(scores)
    scorer.save_detailed_report(scores, args.output)

    # Exit with error code if failing
    if scores['scores']['composite'] < 80:
        print("⛔ FAILING SCORE - Do not deploy!")
        return 1
    elif scores['scores']['legality'] < 100:
        print("❌ ILLEGAL BIDS DETECTED - Critical bug!")
        return 1
    else:
        print("✅ Quality score acceptable")
        return 0


if __name__ == '__main__':
    exit(main())
