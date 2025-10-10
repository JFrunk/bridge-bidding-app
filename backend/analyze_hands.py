"""
Hand Analysis Tool - Systematically reviews bidding in saved hands
Identifies errors according to SAYC bidding standards and proposes fixes.
"""

import json
import os
from pathlib import Path
from engine.bidding_engine import BiddingEngine
from engine.hand import Hand, Card

class HandAnalyzer:
    def __init__(self):
        self.engine = BiddingEngine()
        self.errors_found = []

    def create_hand(self, hand_str):
        """Helper to create a hand from string representation."""
        cards = []
        current_suit = None
        for char in hand_str:
            if char in '♠♥♦♣':
                current_suit = char
            elif char in 'AKQJT98765432':
                if current_suit:
                    cards.append(Card(char, current_suit))
        return Hand(cards)

    def count_aces(self, hand):
        """Count aces in a hand."""
        return sum(1 for card in hand.cards if card.rank == 'A')

    def convert_hand_from_json(self, hand_data):
        """Convert JSON hand data to Hand object."""
        cards = []
        for card_dict in hand_data['cards']:
            cards.append(Card(card_dict['rank'], card_dict['suit']))
        return Hand(cards)

    def hand_to_string(self, hand):
        """Convert Hand object to readable string format."""
        suits = ['♠', '♥', '♦', '♣']
        result = []
        for suit in suits:
            suit_cards = sorted([c.rank for c in hand.cards if c.suit == suit],
                              key=lambda r: 'AKQJT98765432'.index(r))
            if suit_cards:
                result.append(f"{suit}{''.join(suit_cards)}")
        return ' '.join(result)

    def analyze_hand_file(self, filepath):
        """Analyze a single hand file and identify bidding errors."""
        print(f"\n{'='*80}")
        print(f"ANALYZING: {os.path.basename(filepath)}")
        print(f"{'='*80}")

        with open(filepath, 'r') as f:
            data = json.load(f)

        # Extract hand data
        all_hands_data = data.get('all_hands', data.get('hands', {}))
        hands = {
            'North': self.convert_hand_from_json(all_hands_data['North']),
            'East': self.convert_hand_from_json(all_hands_data['East']),
            'South': self.convert_hand_from_json(all_hands_data['South']),
            'West': self.convert_hand_from_json(all_hands_data['West'])
        }

        # Store hand strings for display
        hand_strings = {pos: self.hand_to_string(hand) for pos, hand in hands.items()}

        auction = data['auction']
        vulnerability = data.get('vulnerability', 'None')

        # Display hands
        print("\n📋 HANDS:")
        for position, hand in hands.items():
            print(f"{position:5s}: {hand_strings[position]:40s} ({hand.hcp} HCP, {self.count_aces(hand)} aces)")

        # Display auction
        print(f"\n🎯 AUCTION (Vulnerability: {vulnerability}):")
        auction_display = []
        for i, bid_info in enumerate(auction):
            position = ['North', 'East', 'South', 'West'][i % 4]
            bid = bid_info['bid']
            explanation = bid_info.get('explanation', '')
            auction_display.append(f"{position:5s}: {bid:4s} - {explanation}")

        for line in auction_display:
            print(f"  {line}")

        # Analyze each bid in sequence
        print(f"\n🔍 BIDDING ANALYSIS:")
        errors = []
        warnings = []

        auction_history = []
        positions = ['North', 'East', 'South', 'West']

        for i, bid_info in enumerate(auction):
            position = positions[i % 4]
            actual_bid = bid_info['bid']
            actual_explanation = bid_info.get('explanation', '')

            # Build auction history
            auction_history.append(actual_bid)

            # Get AI recommendation for this position
            hand = hands[position]

            try:
                ai_bid, ai_explanation = self.engine.get_next_bid(
                    hand,
                    auction_history[:-1],  # Don't include current bid
                    position,
                    vulnerability
                )

                # Check if actual bid matches AI recommendation
                if actual_bid != ai_bid:
                    # Check if it's a critical error
                    is_critical = self._is_critical_error(actual_bid, ai_bid, auction_history)

                    error_info = {
                        'position': position,
                        'hand': hand_strings[position],
                        'hcp': hand.hcp,
                        'aces': self.count_aces(hand),
                        'auction_so_far': ' - '.join(auction_history[:-1]) if len(auction_history) > 1 else "Opening",
                        'actual_bid': actual_bid,
                        'actual_explanation': actual_explanation,
                        'recommended_bid': ai_bid,
                        'recommended_explanation': ai_explanation,
                        'is_critical': is_critical
                    }

                    if is_critical:
                        errors.append(error_info)
                    else:
                        warnings.append(error_info)

            except Exception as e:
                print(f"  ⚠️  Error analyzing {position}'s bid: {e}")

        # Report findings
        if errors:
            print(f"\n❌ CRITICAL ERRORS FOUND ({len(errors)}):")
            for i, error in enumerate(errors, 1):
                print(f"\n  Error #{i}: {error['position']}'s bid")
                print(f"    Hand: {error['hand']} ({error['hcp']} HCP, {error['aces']} aces)")
                print(f"    After: {error['auction_so_far']}")
                print(f"    ❌ Bid: {error['actual_bid']} - {error['actual_explanation']}")
                print(f"    ✅ Should be: {error['recommended_bid']} - {error['recommended_explanation']}")

            self.errors_found.extend(errors)

        if warnings:
            print(f"\n⚠️  QUESTIONABLE BIDS ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                print(f"\n  Warning #{i}: {warning['position']}'s bid")
                print(f"    Hand: {warning['hand']} ({warning['hcp']} HCP, {warning['aces']} aces)")
                print(f"    After: {warning['auction_so_far']}")
                print(f"    ⚠️  Bid: {warning['actual_bid']} - {warning['actual_explanation']}")
                print(f"    💡 AI suggests: {warning['recommended_bid']} - {warning['recommended_explanation']}")

        if not errors and not warnings:
            print("  ✅ No issues found - all bids match AI recommendations!")

        return {
            'file': os.path.basename(filepath),
            'errors': errors,
            'warnings': warnings
        }

    def _is_critical_error(self, actual_bid, ai_bid, auction_history):
        """
        Determine if a bidding discrepancy is a critical error or just questionable.

        Critical errors:
        - Pass when should bid slam (6 or 7 level)
        - Bid slam when should pass/sign off
        - Wrong response to conventions (Blackwood, Stayman, etc.)
        - Bidding game when should stop in partscore (or vice versa)
        """
        # Pass when slam was available
        if actual_bid == 'Pass' and ai_bid[0] in ['6', '7']:
            return True

        # Bid slam when shouldn't
        if actual_bid[0] in ['6', '7'] and ai_bid == 'Pass':
            return True

        # Wrong Blackwood response
        if len(auction_history) >= 2 and auction_history[-2] == '4NT':
            if actual_bid[0] == '5' and ai_bid[0] == '5' and actual_bid != ai_bid:
                return True

        # Significant level difference (2+ levels)
        try:
            actual_level = int(actual_bid[0]) if actual_bid[0].isdigit() else 0
            ai_level = int(ai_bid[0]) if ai_bid[0].isdigit() else 0
            if abs(actual_level - ai_level) >= 2:
                return True
        except:
            pass

        # Game vs partscore difference
        if actual_bid in ['3NT', '4♥', '4♠', '5♣', '5♦'] and ai_bid[0] in ['1', '2']:
            return True
        if ai_bid in ['3NT', '4♥', '4♠', '5♣', '5♦'] and actual_bid[0] in ['1', '2']:
            return True

        # Otherwise it's just questionable
        return False

    def analyze_all_hands(self, directory):
        """Analyze all hand files in a directory."""
        hand_files = sorted(Path(directory).glob('*.json'))

        if not hand_files:
            print(f"No hand files found in {directory}")
            return

        print(f"\n{'#'*80}")
        print(f"# HAND ANALYSIS REPORT")
        print(f"# Analyzing {len(hand_files)} hands from {directory}")
        print(f"{'#'*80}")

        results = []
        for filepath in hand_files:
            result = self.analyze_hand_file(str(filepath))
            results.append(result)

        # Summary report
        print(f"\n\n{'='*80}")
        print(f"SUMMARY REPORT")
        print(f"{'='*80}")

        total_errors = sum(len(r['errors']) for r in results)
        total_warnings = sum(len(r['warnings']) for r in results)
        clean_hands = sum(1 for r in results if not r['errors'] and not r['warnings'])

        print(f"\nTotal hands analyzed: {len(results)}")
        print(f"Hands with critical errors: {sum(1 for r in results if r['errors'])}")
        print(f"Hands with warnings: {sum(1 for r in results if r['warnings'])}")
        print(f"Clean hands: {clean_hands}")
        print(f"\nTotal critical errors: {total_errors}")
        print(f"Total warnings: {total_warnings}")

        if total_errors > 0:
            print(f"\n{'='*80}")
            print("CRITICAL ERRORS BY TYPE:")
            print(f"{'='*80}")

            error_types = {}
            for result in results:
                for error in result['errors']:
                    # Categorize error
                    category = self._categorize_error(error)
                    if category not in error_types:
                        error_types[category] = []
                    error_types[category].append({
                        'file': result['file'],
                        'position': error['position'],
                        'actual': error['actual_bid'],
                        'recommended': error['recommended_bid']
                    })

            for category, errors in sorted(error_types.items()):
                print(f"\n{category} ({len(errors)} occurrences):")
                for err in errors:
                    print(f"  - {err['file']}: {err['position']} bid {err['actual']}, should be {err['recommended']}")

    def _categorize_error(self, error):
        """Categorize an error by type."""
        actual = error['actual_bid']
        recommended = error['recommended_bid']
        auction = error['auction_so_far']

        # Slam bidding errors
        if actual == 'Pass' and recommended[0] in ['6', '7']:
            return "Missed Slam"
        if actual[0] in ['6', '7'] and recommended in ['Pass', '5♥', '5♠', '5♣', '5♦']:
            return "Overbid to Slam"

        # Convention errors
        if '4NT' in auction:
            return "Blackwood Response Error"
        if '2♣' in auction and '1NT' in auction:
            return "Stayman Error"
        if ('2♦' in auction or '2♥' in auction) and '1NT' in auction:
            return "Jacoby Transfer Error"

        # Game bidding errors
        if actual in ['3NT', '4♥', '4♠'] and recommended[0] in ['1', '2']:
            return "Overbid to Game"
        if recommended in ['3NT', '4♥', '4♠'] and actual[0] in ['1', '2']:
            return "Underbid (Missed Game)"

        # Opening errors
        if len(auction.split()) <= 1:
            return "Opening Bid Error"

        return "Other Error"


if __name__ == '__main__':
    analyzer = HandAnalyzer()
    analyzer.analyze_all_hands('review_requests')
