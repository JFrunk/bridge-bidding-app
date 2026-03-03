#!/usr/bin/env python3
"""
SAYC Compliance Benchmark System

Comprehensive testing of bidding engine against SAYC (Standard American Yellow Card) conventions.
Generates detailed compliance reports and exports results in PBN format for external analysis.

Usage:
    python3 test_sayc_compliance.py --hands 500 --output report.json --pbn hands.pbn
    python3 test_sayc_compliance.py --category openings --hands 100
    python3 test_sayc_compliance.py --category conventions --hands 200
"""

import json
import random
import argparse
import sys
import os
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.bidding_validation import BidValidator


# =============================================================================
# SAYC TEST MATRIX - Comprehensive Convention Coverage
# =============================================================================

class SAYCTestCategory:
    """Defines test categories for systematic SAYC coverage."""

    # Opening bid situations
    OPENING_1NT = "1NT Opening (15-17 HCP)"
    OPENING_2NT = "2NT Opening (20-21 HCP)"
    OPENING_1M = "1M Opening (13+ HCP, 5+ cards)"
    OPENING_1m = "1m Opening (13+ HCP, 3+ cards)"
    OPENING_2C = "2♣ Strong Opening (22+ HCP)"
    OPENING_WEAK_TWO = "Weak Two Bids (2♦/2♥/2♠)"
    OPENING_PREEMPTS = "Preemptive Bids (3-level, 4-level)"

    # Response situations - 1NT
    RESPONSE_STAYMAN = "Stayman (2♣ response to 1NT)"
    RESPONSE_JACOBY = "Jacoby Transfers (2♦/2♥)"
    RESPONSE_1NT_DIRECT = "Direct 1NT Responses"

    # Response situations - Suit openings
    RESPONSE_1M_RAISES = "1M Raises (single, limit, game)"
    RESPONSE_1M_NEW_SUIT = "1M New Suit Responses"
    RESPONSE_1m = "1m Responses"
    RESPONSE_2C = "2♣ Responses"
    RESPONSE_WEAK_TWO = "Weak Two Responses"

    # Competitive bidding
    COMPETITIVE_OVERCALLS = "Simple Overcalls"
    COMPETITIVE_1NT_OVERCALL = "1NT Overcall"
    COMPETITIVE_MICHAELS = "Michaels Cuebid"
    COMPETITIVE_UNUSUAL_2NT = "Unusual 2NT"
    COMPETITIVE_NEGATIVE_DBL = "Negative Doubles"
    COMPETITIVE_TAKEOUT_DBL = "Takeout Doubles"

    # Advanced conventions
    ADVANCED_BLACKWOOD = "Blackwood (4NT ace-asking)"
    ADVANCED_GERBER = "Gerber (4♣ ace-asking)"
    ADVANCED_GSF = "Grand Slam Force (5NT)"
    ADVANCED_SPLINTER = "Splinter Bids"
    ADVANCED_FSF = "Fourth Suit Forcing"

    # Rebids
    REBID_OPENER = "Opener Rebids (min/med/max)"
    REBID_RESPONDER = "Responder Rebids"

    # Game/Slam bidding
    GAME_SLAM_ACCURACY = "Game/Slam Accuracy"


# =============================================================================
# PBN EXPORT UTILITIES
# =============================================================================

class PBNExporter:
    """Export bridge hands and auctions to PBN (Portable Bridge Notation) format."""

    @staticmethod
    def export_deal(hands: Dict[str, Hand], dealer: str, vulnerability: str,
                   auction: List[str], board_number: int = 1) -> str:
        """
        Export a single deal to PBN format.

        Args:
            hands: Dict of {position: Hand} for all 4 players
            dealer: 'North', 'East', 'South', or 'West'
            vulnerability: 'None', 'NS', 'EW', or 'Both'
            auction: List of bids in order
            board_number: Board number

        Returns:
            PBN-formatted string for this deal
        """
        position_map = {'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W'}
        dealer_abbr = position_map.get(dealer, 'N')

        # Build deal string: N:spades.hearts.diamonds.clubs E:... S:... W:...
        deal_parts = []
        for pos in ['North', 'East', 'South', 'West']:
            hand = hands.get(pos)
            if hand:
                pbn_hand = hand.to_pbn()
                deal_parts.append(pbn_hand)
            else:
                deal_parts.append("...")  # Empty hand placeholder

        deal_string = f"{dealer_abbr}:{' '.join(deal_parts)}"

        # Build auction string
        positions = ['North', 'East', 'South', 'West']
        dealer_idx = positions.index(dealer)

        auction_lines = []
        for i, bid in enumerate(auction):
            position = positions[(dealer_idx + i) % 4]
            auction_lines.append(f"{bid}")

        # Format PBN
        pbn = [
            f'[Event "SAYC Compliance Test"]',
            f'[Site "Bridge Bidding Program"]',
            f'[Date "{datetime.now().strftime("%Y.%m.%d")}"]',
            f'[Board "{board_number}"]',
            f'[Dealer "{dealer_abbr}"]',
            f'[Vulnerable "{vulnerability}"]',
            f'[Deal "{deal_string}"]',
            f'[Auction "{dealer_abbr}"]',
        ]

        # Add auction with proper formatting (4 bids per line)
        for i in range(0, len(auction_lines), 4):
            line_bids = auction_lines[i:i+4]
            pbn.append('\t'.join(line_bids))

        pbn.append('[Play ""]')  # Empty play section
        pbn.append('')  # Blank line separator

        return '\n'.join(pbn)

    @staticmethod
    def export_multiple_deals(deals: List[Dict]) -> str:
        """
        Export multiple deals to a single PBN file.

        Args:
            deals: List of deal dictionaries with hands, dealer, vulnerability, auction

        Returns:
            Complete PBN file content
        """
        pbn_header = [
            '% PBN 2.1',
            '% EXPORT',
            f'% Date: {datetime.now().isoformat()}',
            f'% Generator: Bridge Bidding Program - SAYC Compliance Test',
            '',
        ]

        deal_sections = []
        for i, deal in enumerate(deals, 1):
            pbn_deal = PBNExporter.export_deal(
                hands=deal['hands'],
                dealer=deal['dealer'],
                vulnerability=deal['vulnerability'],
                auction=deal['auction'],
                board_number=i
            )
            deal_sections.append(pbn_deal)

        return '\n'.join(pbn_header) + '\n' + '\n'.join(deal_sections)


# =============================================================================
# HAND GENERATION FOR SPECIFIC SCENARIOS
# =============================================================================

def generate_random_hand() -> Hand:
    """Generate a random 13-card bridge hand."""
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['♠', '♥', '♦', '♣']
    deck = [Card(rank, suit) for suit in suits for rank in ranks]
    random.shuffle(deck)
    cards = deck[:13]
    return Hand(cards)


def generate_1nt_hand() -> Hand:
    """Generate a hand suitable for 1NT opening (15-17 HCP, balanced)."""
    max_attempts = 1000
    for _ in range(max_attempts):
        hand = generate_random_hand()
        if 15 <= hand.hcp <= 17 and hand.is_balanced:
            return hand
    # Fallback if can't generate
    return generate_random_hand()


def generate_weak_two_hand() -> Hand:
    """Generate a hand suitable for weak two bid (5-11 HCP, 6-card major)."""
    max_attempts = 1000
    for _ in range(max_attempts):
        hand = generate_random_hand()
        if 5 <= hand.hcp <= 11:
            if hand.suit_lengths['♠'] >= 6 or hand.suit_lengths['♥'] >= 6:
                return hand
    return generate_random_hand()


def generate_opening_hand(min_hcp: int = 12, max_hcp: int = 21) -> Hand:
    """Generate a hand with opening strength."""
    max_attempts = 1000
    for _ in range(max_attempts):
        hand = generate_random_hand()
        if min_hcp <= hand.hcp <= max_hcp:
            return hand
    return generate_random_hand()


# =============================================================================
# SAYC COMPLIANCE SCORER
# =============================================================================

class SAYCComplianceScorer:
    """Comprehensive SAYC compliance testing with detailed analytics."""

    def __init__(self, num_hands: int = 500, test_category: Optional[str] = None):
        self.num_hands = num_hands
        self.test_category = test_category
        self.engine = BiddingEngine()

        # Results storage
        self.results = {
            'total_hands': 0,
            'total_bids': 0,
            'category_results': defaultdict(lambda: {
                'tested': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }),
            'convention_usage': defaultdict(int),
            'legality_errors': [],
            'appropriateness_errors': [],
            'deals_for_export': []  # Store deals for PBN export
        }

    def run_full_test(self) -> Dict:
        """Run comprehensive SAYC compliance tests."""
        print(f"🎯 Running SAYC Compliance Test on {self.num_hands} hands...")
        print(f"⏰ Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if self.test_category:
            print(f"📋 Testing category: {self.test_category}")
        else:
            print(f"📋 Testing all SAYC categories")

        print()

        # Test different categories
        categories_to_test = self._get_categories_to_test()

        hands_per_category = max(1, self.num_hands // len(categories_to_test))

        for category in categories_to_test:
            print(f"   Testing: {category}...")
            self._test_category(category, hands_per_category)

        print()
        print("✅ Testing complete. Calculating compliance scores...")
        print()

        return self._calculate_scores()

    def _get_categories_to_test(self) -> List[str]:
        """Get list of categories to test based on filter."""
        all_categories = [
            SAYCTestCategory.OPENING_1NT,
            SAYCTestCategory.OPENING_1M,
            SAYCTestCategory.RESPONSE_STAYMAN,
            SAYCTestCategory.RESPONSE_JACOBY,
            SAYCTestCategory.COMPETITIVE_TAKEOUT_DBL,
            SAYCTestCategory.ADVANCED_BLACKWOOD,
            SAYCTestCategory.OPENING_WEAK_TWO,
            SAYCTestCategory.OPENING_PREEMPTS,
            SAYCTestCategory.COMPETITIVE_MICHAELS,
            SAYCTestCategory.COMPETITIVE_UNUSUAL_2NT,
            SAYCTestCategory.ADVANCED_SPLINTER,
            SAYCTestCategory.ADVANCED_FSF,
        ]

        if self.test_category:
            # Filter to matching category
            matching = [c for c in all_categories if self.test_category.lower() in c.lower()]
            return matching if matching else all_categories

        return all_categories

    def _test_category(self, category: str, num_hands: int):
        """Test a specific SAYC category."""
        for i in range(num_hands):
            try:
                # Generate hands appropriate for this category
                hands = self._generate_hands_for_category(category)
                dealer = random.choice(['North', 'South', 'East', 'West'])
                vulnerability = random.choice(['None', 'NS', 'EW', 'Both'])

                # Simulate auction
                auction = self._simulate_auction(hands, dealer, vulnerability)

                # Evaluate compliance
                self._evaluate_category_compliance(category, hands, auction, dealer, vulnerability)

                self.results['total_hands'] += 1

            except Exception as e:
                print(f"      Warning: Error testing {category}: {e}")
                continue

    def _generate_hands_for_category(self, category: str) -> Dict[str, Hand]:
        """Generate hands appropriate for a specific test category."""
        hands = {}

        # Generate North hand based on category
        if "1NT" in category:
            hands['North'] = generate_1nt_hand()
        elif "Weak Two" in category:
            hands['North'] = generate_weak_two_hand()
        elif "Opening" in category or "1M" in category or "1m" in category:
            hands['North'] = generate_opening_hand(12, 21)
        else:
            hands['North'] = generate_random_hand()

        # Generate other hands
        for pos in ['East', 'South', 'West']:
            hands[pos] = generate_random_hand()

        return hands

    def _simulate_auction(self, hands: Dict[str, Hand], dealer: str, vulnerability: str) -> List[str]:
        """Simulate a complete auction."""
        positions = ['North', 'East', 'South', 'West']
        dealer_idx = positions.index(dealer)

        auction_history = []
        consecutive_passes = 0
        current_idx = dealer_idx
        max_bids = 50
        bid_count = 0

        while consecutive_passes < 3 and bid_count < max_bids:
            position = positions[current_idx % 4]
            hand = hands[position]

            try:
                bid, explanation = self.engine.get_next_bid(
                    hand=hand,
                    auction_history=auction_history,
                    my_position=position,
                    vulnerability=vulnerability
                )
            except Exception as e:
                bid = 'Pass'
                explanation = f"Error: {e}"

            auction_history.append(bid)
            self.results['total_bids'] += 1

            # Track convention usage
            if 'Stayman' in explanation:
                self.results['convention_usage']['Stayman'] += 1
            elif 'Jacoby' in explanation or 'Transfer' in explanation:
                self.results['convention_usage']['Jacoby Transfer'] += 1
            elif 'Blackwood' in explanation:
                self.results['convention_usage']['Blackwood'] += 1
            elif 'Takeout' in explanation:
                self.results['convention_usage']['Takeout Double'] += 1
            elif 'Michaels' in explanation:
                self.results['convention_usage']['Michaels Cuebid'] += 1
            elif 'Unusual 2NT' in explanation:
                self.results['convention_usage']['Unusual 2NT'] += 1
            elif 'Splinter' in explanation:
                self.results['convention_usage']['Splinter'] += 1
            elif 'Fourth Suit' in explanation:
                self.results['convention_usage']['Fourth Suit Forcing'] += 1

            # Check legality
            if not BidValidator.is_legal_bid(bid, auction_history[:-1]):
                self.results['legality_errors'].append({
                    'bid': bid,
                    'auction': auction_history[:-1],
                    'position': position,
                    'hand_hcp': hand.hcp
                })

            if bid == 'Pass':
                consecutive_passes += 1
            else:
                consecutive_passes = 0

            if len(auction_history) == 4 and all(b == 'Pass' for b in auction_history):
                break

            current_idx += 1
            bid_count += 1

        return auction_history

    def _evaluate_category_compliance(self, category: str, hands: Dict[str, Hand],
                                     auction: List[str], dealer: str, vulnerability: str):
        """Evaluate if auction complies with SAYC for this category."""
        cat_results = self.results['category_results'][category]
        cat_results['tested'] += 1

        # Store deal for PBN export
        self.results['deals_for_export'].append({
            'hands': hands,
            'dealer': dealer,
            'vulnerability': vulnerability,
            'auction': auction,
            'category': category
        })

        positions = ['North', 'East', 'South', 'West']
        dealer_idx = positions.index(dealer)

        # Category-specific compliance checks
        passed = True

        # ======= OPENING BID COMPLIANCE =======

        if category == SAYCTestCategory.OPENING_1NT:
            # Check for 1NT OPENING bid (not rebids or overcalls)
            # Opening bid = first non-pass bid in the auction
            opening_bid = None
            opening_bid_idx = None

            for i, bid in enumerate(auction):
                if bid != 'Pass':
                    opening_bid = bid
                    opening_bid_idx = i
                    break

            # Only check if opening bid was 1NT
            if opening_bid == '1NT':
                opener_pos = positions[(dealer_idx + opening_bid_idx) % 4]
                opener_hand = hands[opener_pos]

                # HCP requirement: 15-17
                if not (15 <= opener_hand.hcp <= 17):
                    passed = False
                    cat_results['errors'].append({
                        'error': f'1NT opened with {opener_hand.hcp} HCP (need 15-17)',
                        'hand': opener_hand.to_pbn()
                    })

                # Balanced requirement
                if not opener_hand.is_balanced:
                    passed = False
                    cat_results['errors'].append({
                        'error': f'1NT opened with unbalanced hand',
                        'shape': f"{opener_hand.suit_lengths['♠']}{opener_hand.suit_lengths['♥']}{opener_hand.suit_lengths['♦']}{opener_hand.suit_lengths['♣']}",
                        'hand': opener_hand.to_pbn()
                    })

        elif category == SAYCTestCategory.OPENING_2NT:
            if '2NT' in auction:
                opener_idx = auction.index('2NT')
                opener_pos = positions[(dealer_idx + opener_idx) % 4]
                opener_hand = hands[opener_pos]

                # HCP requirement: 20-21
                if not (20 <= opener_hand.hcp <= 21):
                    passed = False
                    cat_results['errors'].append({
                        'error': f'2NT opened with {opener_hand.hcp} HCP (need 20-21)',
                        'hand': opener_hand.to_pbn()
                    })

                if not opener_hand.is_balanced:
                    passed = False
                    cat_results['errors'].append({
                        'error': f'2NT opened with unbalanced hand',
                        'hand': opener_hand.to_pbn()
                    })

        elif category == SAYCTestCategory.OPENING_1M:
            # Check for 1♥ or 1♠ OPENING bids (not overcalls)
            # Opening bid = first non-pass bid in the auction
            opening_bid = None
            opening_bid_idx = None

            for i, bid in enumerate(auction):
                if bid != 'Pass':
                    opening_bid = bid
                    opening_bid_idx = i
                    break

            # Only check if opening bid was 1M
            if opening_bid in ['1♥', '1♠']:
                opener_pos = positions[(dealer_idx + opening_bid_idx) % 4]
                opener_hand = hands[opener_pos]
                suit = opening_bid[1]

                # HCP requirement: 12+ (SAYC allows 12)
                if opener_hand.hcp < 12:
                    passed = False
                    cat_results['errors'].append({
                        'error': f'{opening_bid} opened with {opener_hand.hcp} HCP (need 12+)',
                        'hand': opener_hand.to_pbn()
                    })

                # Length requirement: 5+ cards
                if opener_hand.suit_lengths[suit] < 5:
                    passed = False
                    cat_results['errors'].append({
                        'error': f'{opening_bid} opened with only {opener_hand.suit_lengths[suit]} cards (need 5+)',
                        'hand': opener_hand.to_pbn()
                    })

        elif category == SAYCTestCategory.OPENING_WEAK_TWO:
            # Check for 2♦/2♥/2♠ weak two OPENING bids (not overcalls)
            # Opening bid = first non-pass bid in the auction
            opening_bid = None
            opening_bid_idx = None

            for i, bid in enumerate(auction):
                if bid != 'Pass':
                    opening_bid = bid
                    opening_bid_idx = i
                    break

            # Only check if opening bid was a weak two
            if opening_bid in ['2♦', '2♥', '2♠']:
                opener_pos = positions[(dealer_idx + opening_bid_idx) % 4]
                opener_hand = hands[opener_pos]
                suit = opening_bid[1]

                # HCP requirement: 5-11 (SAYC weak two) - Updated to 6-10 per preempts.py
                if not (6 <= opener_hand.hcp <= 10):
                    passed = False
                    cat_results['errors'].append({
                        'error': f'{opening_bid} opened with {opener_hand.hcp} HCP (need 6-10)',
                        'hand': opener_hand.to_pbn()
                    })

                # Length requirement: 6+ cards (should be exactly 6)
                if opener_hand.suit_lengths[suit] != 6:
                    passed = False
                    cat_results['errors'].append({
                        'error': f'{opening_bid} weak two with {opener_hand.suit_lengths[suit]} cards (need exactly 6)',
                        'hand': opener_hand.to_pbn()
                    })

        # ======= RESPONSE COMPLIANCE =======

        elif category == SAYCTestCategory.RESPONSE_STAYMAN:
            # Check for Stayman sequence: 1NT - Pass - 2♣
            if len(auction) >= 3 and auction[0] == '1NT' and auction[2] == '2♣':
                responder_hand = hands[positions[(dealer_idx + 2) % 4]]

                # Stayman requirement: 8+ HCP and 4-card major
                has_4_card_major = (responder_hand.suit_lengths['♠'] >= 4 or
                                   responder_hand.suit_lengths['♥'] >= 4)

                if not has_4_card_major:
                    passed = False
                    cat_results['errors'].append({
                        'error': f'Stayman without 4-card major',
                        'spades': responder_hand.suit_lengths['♠'],
                        'hearts': responder_hand.suit_lengths['♥'],
                        'hand': responder_hand.to_pbn()
                    })

                if responder_hand.hcp < 8:
                    passed = False
                    cat_results['errors'].append({
                        'error': f'Stayman with only {responder_hand.hcp} HCP (need 8+)',
                        'hand': responder_hand.to_pbn()
                    })

        elif category == SAYCTestCategory.RESPONSE_JACOBY:
            # Check for Jacoby transfer: 1NT - Pass - 2♦/2♥
            if len(auction) >= 3 and auction[0] == '1NT':
                if auction[2] == '2♦':  # Hearts transfer
                    responder_hand = hands[positions[(dealer_idx + 2) % 4]]
                    if responder_hand.suit_lengths['♥'] < 5:
                        passed = False
                        cat_results['errors'].append({
                            'error': f'Hearts transfer with only {responder_hand.suit_lengths["♥"]} hearts (need 5+)',
                            'hand': responder_hand.to_pbn()
                        })

                elif auction[2] == '2♥':  # Spades transfer
                    responder_hand = hands[positions[(dealer_idx + 2) % 4]]
                    if responder_hand.suit_lengths['♠'] < 5:
                        passed = False
                        cat_results['errors'].append({
                            'error': f'Spades transfer with only {responder_hand.suit_lengths["♠"]} spades (need 5+)',
                            'hand': responder_hand.to_pbn()
                        })

        # ======= COMPETITIVE BIDDING COMPLIANCE =======

        elif category == SAYCTestCategory.COMPETITIVE_TAKEOUT_DBL:
            # Check for takeout doubles
            if 'X' in auction:
                # Find first double (assuming it's a takeout double)
                dbl_idx = auction.index('X')
                if dbl_idx > 0:  # Not opening bid
                    doubler_pos = positions[(dealer_idx + dbl_idx) % 4]
                    doubler_hand = hands[doubler_pos]

                    # Determine if this is a balancing seat double
                    # Balancing = opponent opened, we passed, opponent passed, now we double
                    # Pattern: (Opp - Pass - Opp - Pass - ... X)
                    is_balancing = False
                    if dbl_idx >= 3:
                        # Check if pattern is: Opp bid, Partner passed, Opp passed
                        # Simple heuristic: if there are 3+ passes before the double, likely balancing
                        passes_before_dbl = sum(1 for b in auction[:dbl_idx] if b == 'Pass')
                        if passes_before_dbl >= 2:
                            is_balancing = True

                    # Takeout double requirement:
                    # Direct seat: 12+ HCP
                    # Balancing seat: 8+ HCP (SAYC allows lower in balancing)
                    min_hcp = 8 if is_balancing else 12
                    if doubler_hand.hcp < min_hcp:
                        passed = False
                        seat_type = "balancing" if is_balancing else "direct"
                        cat_results['errors'].append({
                            'error': f'Takeout double ({seat_type}) with only {doubler_hand.hcp} HCP (need {min_hcp}+)',
                            'hand': doubler_hand.to_pbn()
                        })

        elif category == SAYCTestCategory.ADVANCED_BLACKWOOD:
            # Check for Blackwood: 4NT in auction
            if '4NT' in auction:
                asker_idx = auction.index('4NT')
                asker_pos = positions[(dealer_idx + asker_idx) % 4]
                asker_hand = hands[asker_pos]

                # Blackwood requirement: 16+ HCP (slam interest)
                if asker_hand.hcp < 16:
                    passed = False
                    cat_results['errors'].append({
                        'error': f'Blackwood with only {asker_hand.hcp} HCP (need 16+ for slam)',
                        'hand': asker_hand.to_pbn()
                    })

        # Default: mark as passed if no specific checks failed
        if passed:
            cat_results['passed'] += 1
        else:
            cat_results['failed'] += 1

    def _calculate_scores(self) -> Dict:
        """Calculate final compliance scores."""
        total_bids = max(1, self.results['total_bids'])

        # Overall legality score
        legality_errors = len(self.results['legality_errors'])
        legality_score = ((total_bids - legality_errors) / total_bids * 100)

        # Category compliance scores
        category_scores = {}
        for category, cat_results in self.results['category_results'].items():
            tested = cat_results['tested']
            if tested > 0:
                compliance = (cat_results['passed'] / tested * 100)
                category_scores[category] = {
                    'compliance': round(compliance, 1),
                    'tested': tested,
                    'passed': cat_results['passed'],
                    'failed': cat_results['failed'],
                    'sample_errors': cat_results['errors'][:5]
                }

        # Overall compliance score
        if category_scores:
            avg_compliance = sum(s['compliance'] for s in category_scores.values()) / len(category_scores)
        else:
            avg_compliance = 100.0

        return {
            'test_summary': {
                'total_hands': self.results['total_hands'],
                'total_bids': total_bids,
                'test_categories': len(self.results['category_results']),
                'timestamp': datetime.now().isoformat()
            },
            'scores': {
                'overall_compliance': round(avg_compliance, 1),
                'legality': round(legality_score, 1),
            },
            'category_scores': category_scores,
            'convention_usage': dict(self.results['convention_usage']),
            'legality_errors': self.results['legality_errors'][:10],
            'deals_for_export': self.results['deals_for_export']
        }

    def print_report(self, scores: Dict):
        """Print comprehensive compliance report."""
        print("=" * 80)
        print("SAYC COMPLIANCE REPORT")
        print("=" * 80)
        print()

        summary = scores['test_summary']
        print(f"Hands Tested:       {summary['total_hands']}")
        print(f"Total Bids:         {summary['total_bids']}")
        print(f"Test Categories:    {summary['test_categories']}")
        print(f"Timestamp:          {summary['timestamp']}")
        print()

        print("-" * 80)
        print("OVERALL SCORES:")
        print("-" * 80)
        s = scores['scores']
        print(f"  Overall Compliance: {s['overall_compliance']:5.1f}% {'✅' if s['overall_compliance'] >= 90 else '⚠️'}")
        print(f"  Legality:           {s['legality']:5.1f}% {'✅' if s['legality'] == 100 else '❌'}")
        print()

        print("-" * 80)
        print("CATEGORY COMPLIANCE:")
        print("-" * 80)
        for category, cat_score in scores['category_scores'].items():
            status = '✅' if cat_score['compliance'] >= 90 else '⚠️' if cat_score['compliance'] >= 75 else '❌'
            print(f"  {category:50s} {cat_score['compliance']:5.1f}% {status}")
            print(f"     ({cat_score['passed']}/{cat_score['tested']} passed)")

            if cat_score['sample_errors']:
                print(f"     Sample errors:")
                for err in cat_score['sample_errors'][:3]:
                    print(f"       - {err.get('error', 'Unknown error')}")
        print()

        print("-" * 80)
        print("CONVENTION USAGE:")
        print("-" * 80)
        usage = scores['convention_usage']
        if usage:
            for conv, count in sorted(usage.items(), key=lambda x: -x[1]):
                print(f"  {conv:30s} {count:4d} times")
        else:
            print("  No conventions detected in test")
        print()

        print("=" * 80)

    def export_to_pbn(self, filename: str):
        """Export all tested deals to PBN file."""
        deals = self.results['deals_for_export']
        pbn_content = PBNExporter.export_multiple_deals(deals)

        with open(filename, 'w') as f:
            f.write(pbn_content)

        print(f"📄 PBN export saved to: {filename} ({len(deals)} deals)")

    def save_json_report(self, filename: str, scores: Dict):
        """Save detailed JSON report."""
        # Remove deals from JSON export (too large)
        scores_copy = scores.copy()
        scores_copy.pop('deals_for_export', None)

        with open(filename, 'w') as f:
            json.dump(scores_copy, f, indent=2)

        print(f"📄 JSON report saved to: {filename}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='SAYC Compliance Benchmark System')
    parser.add_argument('--hands', type=int, default=500, help='Number of hands to test (default: 500)')
    parser.add_argument('--category', type=str, help='Test specific category only')
    parser.add_argument('--output', type=str, help='Output JSON file path')
    parser.add_argument('--pbn', type=str, help='Output PBN file path')

    args = parser.parse_args()

    scorer = SAYCComplianceScorer(num_hands=args.hands, test_category=args.category)
    scores = scorer.run_full_test()
    scorer.print_report(scores)

    # Save reports
    if args.output:
        scorer.save_json_report(args.output, scores)

    if args.pbn:
        scorer.export_to_pbn(args.pbn)

    # Exit with status code
    if scores['scores']['legality'] < 100:
        print("❌ LEGALITY FAILURES - Critical bug!")
        return 1
    elif scores['scores']['overall_compliance'] < 75:
        print("⛔ LOW COMPLIANCE SCORE - Needs improvement")
        return 1
    else:
        print("✅ Compliance acceptable")
        return 0


if __name__ == '__main__':
    exit(main())
