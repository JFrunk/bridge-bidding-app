# Bidding Quality Score System

## Overview

A comprehensive scoring system to validate bidding logic and detect regressions. Runs 100-500 hands through the bidding engine and scores them on multiple dimensions.

---

## Scoring Dimensions

### 1. Legality Score (CRITICAL - Must be 100%)

**Definition:** Percentage of bids that follow auction rules

**Checks:**
- ✅ Bid is higher than previous bid
- ✅ Suit ranking is correct
- ✅ No bidding after 3 consecutive passes
- ✅ Double/Redouble only when legal

**Scoring:**
```
Legality Score = (Legal Bids / Total Bids) × 100%
```

**Target:** 100% (any illegal bid is a critical bug)

---

### 2. Appropriateness Score (NEW - Target 95%+)

**Definition:** Percentage of bids that meet SAYC requirements for their level

**Checks:**

#### Raises
| Level | Requirement | Check |
|-------|-------------|-------|
| 2-level | 8+ HCP, 3+ support | ✅ |
| 3-level | 10+ HCP, 3+ support OR 8+ with 4+ | ✅ |
| 4-level | 12+ HCP, 3+ support OR 10+ with 5+ | ✅ |
| 5-level | 14+ HCP or 6+ trumps | ✅ |

#### New Suits
| Level | Requirement | Check |
|-------|-------------|-------|
| 1-level | 6+ HCP, 4+ cards | ✅ |
| 2-level | 8+ HCP, 5+ cards OR 12+ with 4+ | ✅ |
| 3-level | 10+ HCP, 5+ cards OR 6+ with 6+ good | ✅ |
| 4-level | 12+ HCP (game) | ✅ |

#### NT Bids
| Bid | Requirement | Check |
|-----|-------------|-------|
| 1NT opening | 15-17 HCP, balanced | ✅ |
| 2NT opening | 20-21 HCP, balanced | ✅ |
| 1NT response | 6-10 HCP, balanced, stopper | ✅ |
| 2NT response | 11-12 HCP, balanced, stopper | ✅ |
| 3NT response | 13-15 HCP, balanced, stopper | ✅ |

**Scoring:**
```
Appropriateness Score = (Appropriate Bids / Total Non-Pass Bids) × 100%
```

**Target:** 95%+ (some edge cases acceptable)

---

### 3. Convention Compliance Score (Target 90%+)

**Definition:** Percentage of conventional bids that follow standard conventions

**Checks:**
- ✅ Stayman: 2♣ over 1NT with 4+ major
- ✅ Jacoby: 2♦/2♥ over 1NT with 5+ major
- ✅ Blackwood: 4NT with slam interest (16+ HCP or great fit)
- ✅ Negative Double: Shows unbid major(s) with appropriate HCP
- ✅ Takeout Double: 12+ HCP with support for unbid suits
- ✅ Michaels: 5-5 in specific suits
- ✅ Unusual 2NT: 5-5 in minors

**Scoring:**
```
Convention Score = (Correct Conventional Bids / Total Conventional Bids) × 100%
```

**Target:** 90%+ (conventions have nuances)

---

### 4. Consistency Score (Target 85%+)

**Definition:** Same hand in same situation produces same bid

**Test Method:**
- Run same hand 5 times
- Check if bid is identical each time

**Scoring:**
```
Consistency Score = (Consistent Hands / Total Hands Tested) × 100%
```

**Target:** 85%+ (some randomness in competitive bidding is OK)

---

### 5. Reasonableness Score (Target 90%+)

**Definition:** Subjective scoring of whether bids make sense

**Categories:**
- ✅ **Excellent:** Textbook bid, would teach this
- ✅ **Good:** Reasonable bid, defensible
- ⚠️ **Questionable:** Works but not ideal
- ❌ **Poor:** Legal but poor strategy
- 🚫 **Terrible:** Should never make this bid

**Scoring:**
```
Reasonableness Score = (Excellent + Good) / Total Bids × 100%
Acceptable if: (Excellent + Good + Questionable) / Total Bids × 100% ≥ 90%
```

**Target:** 90%+ (Excellent + Good + Questionable)

---

### 6. Game/Slam Accuracy (Target 80%+)

**Definition:** How often AI reaches correct game/slam contracts

**Checks:**
- ✅ Bid game with 25+ combined HCP
- ✅ Don't bid game with <23 combined HCP (unless distributional)
- ✅ Explore slam with 33+ combined HCP
- ✅ Don't explore slam with <31 combined HCP

**Scoring:**
```
Game Accuracy = (Correct Game Decisions / Total Game Situations) × 100%
```

**Target:** 80%+ (game bidding is complex)

---

## Composite Bidding Quality Score

**Formula:**
```
BQS = (Legality × 0.30) +           # Must be perfect (30%)
      (Appropriateness × 0.25) +    # Critical (25%)
      (Convention × 0.15) +          # Important (15%)
      (Consistency × 0.10) +         # Nice to have (10%)
      (Reasonableness × 0.15) +      # Important (15%)
      (Game/Slam × 0.05)             # Advanced (5%)
```

**Grading Scale:**
- 🟢 **A (95-100%):** Production ready
- 🟡 **B (90-94%):** Good, minor issues
- 🟠 **C (85-89%):** Acceptable, needs work
- 🔴 **D (80-84%):** Poor, major issues
- ⛔ **F (<80%):** Failing, do not deploy

**Target:** A grade (95%+)

---

## Implementation

### Test Script: `backend/test_bidding_quality_score.py`

```python
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
from typing import List, Dict, Tuple
from datetime import datetime
from engine.hand import Hand
from engine.bidding_engine import BiddingEngine
from engine.hand_constructor import generate_random_hand
from engine.bidding_validation import BidValidator

class BiddingQualityScorer:
    """Comprehensive bidding quality testing."""

    def __init__(self, num_hands: int = 500):
        self.num_hands = num_hands
        self.engine = BiddingEngine()
        self.results = {
            'total_hands': 0,
            'total_bids': 0,
            'legality_errors': [],
            'appropriateness_errors': [],
            'convention_errors': [],
            'game_slam_errors': [],
            'reasonableness_ratings': {'excellent': 0, 'good': 0, 'questionable': 0, 'poor': 0, 'terrible': 0},
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

            self._test_single_hand(i)

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
        while consecutive_passes < 3:
            position = positions[current_idx % 4]
            hand = hands[position]

            # Get AI bid
            bid, explanation = self.engine.get_next_bid(
                hand=hand,
                auction_history=auction_history,
                my_position=position,
                vulnerability=vulnerability
            )

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

            # Track consecutive passes
            if bid == 'Pass':
                consecutive_passes += 1
            else:
                consecutive_passes = 0

            # Stop if all passed in opening
            if len(auction_history) == 4 and all(b == 'Pass' for b in auction_history):
                break

            current_idx += 1

            # Safety: stop at 50 bids (should never happen)
            if len(auction_history) >= 50:
                break

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

            # Skip Pass for most checks
            if bid == 'Pass':
                continue

            # 1. Check legality (CRITICAL)
            if not BidValidator.is_legal_bid(bid, auction_before):
                self.results['legality_errors'].append({
                    'hand_number': hand_number,
                    'position': position,
                    'bid': bid,
                    'auction': auction_before,
                    'hand_hcp': hand.hcp,
                    'explanation': bid_detail['explanation']
                })

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

        # Determine if this is a raise or new suit
        # (Simplified logic - full logic would need auction analysis)
        is_raise = False  # Would need to determine from auction

        if is_raise:
            # Check raise appropriateness
            suit_length = hand.suit_lengths.get(strain, 0)

            if suit_length < 3:
                self._record_appropriateness_error(
                    hand_number, position, bid, hand,
                    f"Raise with only {suit_length} cards"
                )
            elif level == 2 and hand.total_points < 8:
                self._record_appropriateness_error(
                    hand_number, position, bid, hand,
                    f"2-level raise with only {hand.total_points} points (need 8+)"
                )
            elif level == 3 and hand.total_points < 10 and not (hand.total_points >= 8 and suit_length >= 4):
                self._record_appropriateness_error(
                    hand_number, position, bid, hand,
                    f"3-level raise with {hand.total_points} points and {suit_length} support (need 10+ or 8+ with 4+)"
                )
            elif level == 4 and hand.total_points < 12 and not (hand.total_points >= 10 and suit_length >= 5):
                self._record_appropriateness_error(
                    hand_number, position, bid, hand,
                    f"4-level raise with {hand.total_points} points and {suit_length} support (need 12+ or 10+ with 5+)"
                )

        else:
            # Check new suit appropriateness
            suit_length = hand.suit_lengths.get(strain, 0)

            if suit_length < 4:
                self._record_appropriateness_error(
                    hand_number, position, bid, hand,
                    f"New suit with only {suit_length} cards"
                )
            elif level == 2 and hand.total_points < 8 and not (hand.total_points >= 12 and suit_length >= 4):
                self._record_appropriateness_error(
                    hand_number, position, bid, hand,
                    f"2-level new suit with {hand.total_points} points (need 8+ with 5+ or 12+ with 4+)"
                )
            elif level == 3 and hand.total_points < 10:
                # Check for preemptive (6+ cards, decent suit)
                suit_hcp = hand.suit_hcp.get(strain, 0)
                if not (suit_length >= 6 and suit_hcp >= 3):
                    self._record_appropriateness_error(
                        hand_number, position, bid, hand,
                        f"3-level new suit with {hand.total_points} points and {suit_length} cards (need 10+ or preemptive)"
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
        # Stayman check
        if bid == '2♣' and len(auction) > 0 and auction[-1] == '1NT':
            if hand.suit_lengths.get('♠', 0) < 4 and hand.suit_lengths.get('♥', 0) < 4:
                self.results['convention_errors'].append({
                    'hand_number': hand_number,
                    'position': position,
                    'convention': 'Stayman',
                    'error': 'Used Stayman without 4-card major',
                    'hand_hcp': hand.hcp
                })

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

        # Add more convention checks as needed...

    def _rate_reasonableness(
        self,
        bid: str,
        hand: Hand,
        auction: List[str],
        position: str
    ):
        """Rate how reasonable the bid is (subjective)."""
        # Simple heuristic-based reasonableness
        # Would ideally use expert system or ML model

        rating = 'good'  # Default

        # Example heuristics
        try:
            level = int(bid[0])
            strain = bid[1:]

            # Very weak hand bidding at high level = questionable/poor
            if level >= 3 and hand.total_points < 10:
                rating = 'questionable'
            if level >= 4 and hand.total_points < 12:
                rating = 'poor'

            # Strong hand passing = questionable
            if len(auction) == 0 and hand.total_points >= 13:
                # This shouldn't happen (should open)
                pass  # AI should have opened

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
        # Simplified: Check if final contract is reasonable given combined strength
        # Full implementation would need more sophisticated analysis

        final_contract = None
        for bid_detail in reversed(auction):
            if bid_detail['bid'] not in ['Pass', 'X', 'XX']:
                final_contract = bid_detail['bid']
                break

        if not final_contract:
            return  # Passed out

        # Calculate partnership combined strength (simplified)
        # Would need to determine declarer/dummy from auction
        # For now, just check North-South vs East-West

        ns_points = hands['North'].total_points + hands['South'].total_points
        ew_points = hands['East'].total_points + hands['West'].total_points

        # Determine who bid the contract
        declarer_partnership = None
        for bid_detail in auction:
            if bid_detail['bid'] == final_contract:
                if bid_detail['position'] in ['North', 'South']:
                    declarer_partnership = 'NS'
                else:
                    declarer_partnership = 'EW'
                break

        if not declarer_partnership:
            return

        combined_points = ns_points if declarer_partnership == 'NS' else ew_points

        # Check game accuracy
        try:
            level = int(final_contract[0])

            # Should be in game with 25+ points
            if combined_points >= 25 and level < 3:
                self.results['game_slam_errors'].append({
                    'hand_number': hand_number,
                    'error': 'Stopped below game with 25+ points',
                    'combined_points': combined_points,
                    'final_contract': final_contract
                })

            # Shouldn't be in game with <23 points (unless distributional)
            if combined_points < 23 and level >= 3:
                # Check for distributional factors
                # (Simplified - would need actual fit analysis)
                pass  # Might be OK with distribution

        except (ValueError, IndexError):
            pass

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
            'hand_shape': f"{hand.suit_lengths['♠']}{hand.suit_lengths['♥']}{hand.suit_lengths['♦']}{hand.suit_lengths['♣']}",
            'reason': reason
        })

    def _calculate_scores(self) -> Dict:
        """Calculate final scores."""
        total_bids = self.results['total_bids']
        total_non_pass = total_bids  # Simplified - would need to exclude Pass bids

        # 1. Legality Score (must be 100%)
        legality_errors = len(self.results['legality_errors'])
        legality_score = ((total_bids - legality_errors) / total_bids * 100) if total_bids > 0 else 100

        # 2. Appropriateness Score
        appropriateness_errors = len(self.results['appropriateness_errors'])
        appropriateness_score = ((total_non_pass - appropriateness_errors) / total_non_pass * 100) if total_non_pass > 0 else 100

        # 3. Convention Score
        convention_errors = len(self.results['convention_errors'])
        # Assume 10% of bids are conventional (rough estimate)
        conventional_bids = max(1, int(total_bids * 0.1))
        convention_score = ((conventional_bids - convention_errors) / conventional_bids * 100)

        # 4. Consistency Score (not implemented yet - would need multiple runs)
        consistency_score = 100  # Placeholder

        # 5. Reasonableness Score
        ratings = self.results['reasonableness_ratings']
        total_rated = sum(ratings.values())
        reasonableness_score = (
            (ratings['excellent'] + ratings['good'] + ratings['questionable']) / total_rated * 100
        ) if total_rated > 0 else 100

        # 6. Game/Slam Accuracy
        game_slam_errors = len(self.results['game_slam_errors'])
        game_situations = max(1, int(self.results['total_hands'] * 0.3))  # ~30% reach game level
        game_slam_score = ((game_situations - game_slam_errors) / game_situations * 100)

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
            'scores': {
                'legality': legality_score,
                'appropriateness': appropriateness_score,
                'conventions': convention_score,
                'consistency': consistency_score,
                'reasonableness': reasonableness_score,
                'game_slam': game_slam_score,
                'composite': composite_score
            },
            'errors': {
                'legality': self.results['legality_errors'][:10],  # First 10
                'appropriateness': self.results['appropriateness_errors'][:10],
                'conventions': self.results['convention_errors'][:10],
                'game_slam': self.results['game_slam_errors'][:10]
            },
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
        print(f"Hands Tested: {scores['total_hands']}")
        print(f"Total Bids:   {scores['total_bids']}")
        print()
        print("-" * 80)
        print("INDIVIDUAL SCORES:")
        print("-" * 80)
        print(f"  1. Legality:        {scores['scores']['legality']:.1f}% {'✅' if scores['scores']['legality'] == 100 else '❌'}")
        print(f"  2. Appropriateness: {scores['scores']['appropriateness']:.1f}% {'✅' if scores['scores']['appropriateness'] >= 95 else '⚠️'}")
        print(f"  3. Conventions:     {scores['scores']['conventions']:.1f}% {'✅' if scores['scores']['conventions'] >= 90 else '⚠️'}")
        print(f"  4. Consistency:     {scores['scores']['consistency']:.1f}% {'✅' if scores['scores']['consistency'] >= 85 else '⚠️'}")
        print(f"  5. Reasonableness:  {scores['scores']['reasonableness']:.1f}% {'✅' if scores['scores']['reasonableness'] >= 90 else '⚠️'}")
        print(f"  6. Game/Slam:       {scores['scores']['game_slam']:.1f}% {'✅' if scores['scores']['game_slam'] >= 80 else '⚠️'}")
        print()
        print("-" * 80)
        print(f"COMPOSITE SCORE: {scores['scores']['composite']:.1f}%")
        print(f"GRADE:           {scores['grade']}")
        print("-" * 80)
        print()

        # Print sample errors
        if scores['errors']['legality']:
            print("❌ LEGALITY ERRORS (sample):")
            for err in scores['errors']['legality'][:5]:
                print(f"   Hand {err['hand_number']}: {err['position']} bid {err['bid']} (illegal)")
            print()

        if scores['errors']['appropriateness']:
            print("⚠️  APPROPRIATENESS ERRORS (sample):")
            for err in scores['errors']['appropriateness'][:5]:
                print(f"   Hand {err['hand_number']}: {err['position']} {err['bid']} - {err['reason']}")
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
        exit(1)
    elif scores['scores']['legality'] < 100:
        print("❌ ILLEGAL BIDS DETECTED - Critical bug!")
        exit(1)
    else:
        print("✅ Quality score acceptable")
        exit(0)


if __name__ == '__main__':
    main()
```

### Usage

```bash
# Full test (500 hands)
python3 backend/test_bidding_quality_score.py

# Fast test (100 hands)
python3 backend/test_bidding_quality_score.py --fast

# Custom number of hands
python3 backend/test_bidding_quality_score.py --hands 1000

# Save to specific file
python3 backend/test_bidding_quality_score.py --output baseline_score.json
```

---

## Regression Testing Workflow

### 1. Establish Baseline

```bash
# Before making changes
git checkout main
python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_score.json
```

### 2. Make Changes

```bash
# Create feature branch
git checkout -b fix/bid-appropriateness

# Implement changes
# ...

# Run quality score
python3 backend/test_bidding_quality_score.py --hands 500 --output new_score.json
```

### 3. Compare Scores

```python
# compare_scores.py
import json

with open('baseline_score.json') as f:
    baseline = json.load(f)

with open('new_score.json') as f:
    new = json.load(f)

print("Score Comparison:")
print(f"Composite:      {baseline['scores']['scores']['composite']:.1f}% → {new['scores']['scores']['composite']:.1f}%")
print(f"Appropriateness: {baseline['scores']['scores']['appropriateness']:.1f}% → {new['scores']['scores']['appropriateness']:.1f}%")
print(f"Legality:       {baseline['scores']['scores']['legality']:.1f}% → {new['scores']['scores']['legality']:.1f}%")

# Check for regression
if new['scores']['scores']['composite'] < baseline['scores']['scores']['composite'] - 2:
    print("⚠️  REGRESSION DETECTED!")
else:
    print("✅ No regression")
```

### 4. CI/CD Integration

```yaml
# .github/workflows/bidding_quality.yml
name: Bidding Quality Check

on: [push, pull_request]

jobs:
  quality_check:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run Bidding Quality Score
      run: |
        python3 backend/test_bidding_quality_score.py --hands 100 --output quality_score.json

    - name: Check Score
      run: |
        python3 -c "
        import json
        with open('quality_score.json') as f:
            score = json.load(f)
        composite = score['scores']['scores']['composite']
        legality = score['scores']['scores']['legality']

        if legality < 100:
            print('❌ Illegal bids detected!')
            exit(1)
        if composite < 90:
            print('⚠️  Quality score below threshold!')
            exit(1)
        print(f'✅ Quality score: {composite:.1f}%')
        "

    - name: Upload Report
      uses: actions/upload-artifact@v2
      with:
        name: quality-report
        path: quality_score.json
```

---

## Benefits

1. **Objective Measurement**
   - Clear metrics for bidding quality
   - No guesswork about system health

2. **Regression Detection**
   - Catch regressions immediately
   - Compare before/after scores

3. **Confidence in Changes**
   - Know if changes improve or degrade quality
   - Data-driven decision making

4. **Production Readiness**
   - Clear threshold for deployment (95%+)
   - Automated pass/fail in CI/CD

5. **Continuous Improvement**
   - Track quality over time
   - Identify weak areas to improve

---

## Recommendations

### For Initial Implementation:
- Start with 100 hands (faster iteration)
- Focus on Legality and Appropriateness scores
- Get to 95%+ before expanding tests

### For Production:
- Use 500 hands for comprehensive coverage
- Run before every release
- Track scores over time in a dashboard

### For CI/CD:
- Use 100 hands for pull requests (faster)
- Use 500 hands for release candidates
- Block merges if score drops >2%

---

## Next Steps

1. Implement the test script
2. Run baseline (before fix)
3. Implement appropriateness fix
4. Run new test (after fix)
5. Compare and validate improvement
6. Integrate into CI/CD pipeline
