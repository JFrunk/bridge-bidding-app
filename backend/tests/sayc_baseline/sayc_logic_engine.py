"""
SAYC Logic Engine - Ground Truth Validation

Based on the Gemini conversation analysis, this module implements
the "physics" of SAYC bidding for validation and testing purposes.

This serves as:
1. A reference implementation for correct SAYC logic
2. A validator for user bid evaluation
3. A test oracle for comparing against our bidding engine

Key concepts from Gemini:
- Reverse: Higher suit at 2-level requires 17+ HCP
- Jump Shift: Skipping a level into new suit requires 19+ HCP
- Minor tiebreakers: 3-3 = 1C, 4-4 = 1D
- Up the line: With 4-4 majors, bid hearts first
"""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class BidClassification(Enum):
    """Classification of bid types per Gemini framework."""
    NATURAL = "natural"
    REVERSE = "reverse"
    JUMP_SHIFT = "jump_shift"
    ILLEGAL_REVERSE = "illegal_reverse"
    ILLEGAL_JUMP_SHIFT = "illegal_jump_shift"


@dataclass
class ValidationResult:
    """Result of validating a bid against SAYC rules."""
    valid: bool
    classification: BidClassification
    reason: str
    correct_bid: Optional[str] = None
    rule_violated: Optional[str] = None


class SAYCLogicEngine:
    """
    Ground truth SAYC logic engine for validation.

    Based on Gemini conversation framework and ACBL SAYC booklet.
    """

    SUIT_RANKS = {'C': 1, '♣': 1, 'D': 2, '♦': 2, 'H': 3, '♥': 3, 'S': 4, '♠': 4, 'NT': 5}
    SUIT_SYMBOLS = {'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠'}

    def __init__(self):
        # Load ground truth data
        self.ground_truth = self._load_ground_truth()

    def _load_ground_truth(self) -> Dict:
        """Load ground truth JSON data."""
        json_path = Path(__file__).parent / "sayc_ground_truth.json"
        if json_path.exists():
            with open(json_path) as f:
                return json.load(f)
        return {}

    # ==================== HCP Calculation ====================

    def calculate_hcp(self, hand_dict: Dict[str, str]) -> int:
        """
        Calculate High Card Points.

        Args:
            hand_dict: {'S': 'AK2', 'H': 'QJ5', 'D': 'K104', 'C': 'J93'}

        Returns:
            Integer HCP value
        """
        points_map = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
        return sum(
            points_map.get(card, 0)
            for cards in hand_dict.values()
            for card in cards
        )

    def calculate_distribution_points(self, hand_dict: Dict[str, str]) -> int:
        """
        Calculate distribution points for opening.

        +1 for 5-card suit, +2 for 6-card, +3 for 7+
        """
        dist_points = 0
        for suit, cards in hand_dict.items():
            length = len(cards)
            if length >= 7:
                dist_points += 3
            elif length == 6:
                dist_points += 2
            elif length == 5:
                dist_points += 1
        return dist_points

    def calculate_support_points(self, hand_dict: Dict[str, str]) -> int:
        """
        Calculate support points (used after fit found).

        Void: +5, Singleton: +3, Doubleton: +1
        """
        support_points = 0
        for suit, cards in hand_dict.items():
            length = len(cards)
            if length == 0:
                support_points += 5
            elif length == 1:
                support_points += 3
            elif length == 2:
                support_points += 1
        return support_points

    def get_suit_lengths(self, hand_dict: Dict[str, str]) -> Dict[str, int]:
        """Get lengths of each suit."""
        return {suit: len(cards) for suit, cards in hand_dict.items()}

    def is_balanced(self, hand_dict: Dict[str, str]) -> bool:
        """
        Check if hand is balanced.

        Balanced = no voids, no singletons, at most one doubleton.
        """
        lengths = self.get_suit_lengths(hand_dict)
        if any(l == 0 for l in lengths.values()):
            return False
        if any(l == 1 for l in lengths.values()):
            return False
        if list(lengths.values()).count(2) > 1:
            return False
        return True

    # ==================== Opening Bid Logic ====================

    def evaluate_opening_bid(self, hand_dict: Dict[str, str]) -> Tuple[str, str]:
        """
        Determine correct SAYC opening bid.

        Returns:
            (bid, explanation)
        """
        hcp = self.calculate_hcp(hand_dict)
        dist_points = self.calculate_distribution_points(hand_dict)
        total_points = hcp + dist_points
        lengths = self.get_suit_lengths(hand_dict)
        balanced = self.is_balanced(hand_dict)

        # Strong artificial 2C
        if total_points >= 22:
            return "2♣", "22+ points, strong artificial game-forcing"

        # 2NT opening
        if 20 <= hcp <= 21 and balanced:
            return "2NT", "20-21 HCP balanced"

        # 1NT opening
        if 15 <= hcp <= 17 and balanced:
            return "1NT", "15-17 HCP balanced"

        # Not enough to open
        if hcp < 13:
            return "Pass", f"Only {hcp} HCP, need 13+ to open"

        # Major suit openings (5+ cards)
        spades = lengths.get('S', lengths.get('♠', 0))
        hearts = lengths.get('H', lengths.get('♥', 0))

        if spades >= 5 or hearts >= 5:
            if spades >= hearts:
                return "1♠", f"5+ spades, {hcp} HCP"
            else:
                return "1♥", f"5+ hearts, {hcp} HCP"

        # Minor suit tiebreakers
        diamonds = lengths.get('D', lengths.get('♦', 0))
        clubs = lengths.get('C', lengths.get('♣', 0))

        if diamonds > clubs:
            return "1♦", f"Longer diamonds ({diamonds} vs {clubs})"
        if clubs > diamonds:
            return "1♣", f"Longer clubs ({clubs} vs {diamonds})"

        # Equal minors
        if diamonds == clubs:
            if diamonds == 3:
                return "1♣", "3-3 in minors, open 1♣ (short club)"
            if diamonds >= 4:
                return "1♦", "4-4 in minors, open 1♦"

        return "1♣", "Default minor opening"

    # ==================== Bid Classification ====================

    def classify_rebid(
        self,
        opener_first_suit: str,
        opener_second_suit: str,
        rebid_level: int,
        opener_hcp: int
    ) -> ValidationResult:
        """
        Classify opener's rebid per Gemini framework.

        Detects: Reverse, Jump Shift, or Natural bid.
        Validates HCP requirements.
        """
        # Normalize suit symbols
        rank1 = self.SUIT_RANKS.get(opener_first_suit, 0)
        rank2 = self.SUIT_RANKS.get(opener_second_suit, 0)

        # Check for Reverse
        # Definition: Second suit higher ranking than first at 2-level
        if rebid_level == 2 and rank2 > rank1 and opener_first_suit != opener_second_suit:
            if opener_hcp >= 17:
                return ValidationResult(
                    valid=True,
                    classification=BidClassification.REVERSE,
                    reason=f"Valid reverse with {opener_hcp} HCP (17+ required)"
                )
            else:
                return ValidationResult(
                    valid=False,
                    classification=BidClassification.ILLEGAL_REVERSE,
                    reason=f"Illegal reverse: {opener_hcp} HCP but need 17+",
                    rule_violated="reverse_hcp_requirement"
                )

        # Check for Jump Shift
        # Definition: Skipping a level into a new suit
        if rebid_level >= 3 and opener_first_suit != opener_second_suit:
            if opener_hcp >= 19:
                return ValidationResult(
                    valid=True,
                    classification=BidClassification.JUMP_SHIFT,
                    reason=f"Valid jump shift with {opener_hcp} HCP (19+ required)"
                )
            else:
                return ValidationResult(
                    valid=False,
                    classification=BidClassification.ILLEGAL_JUMP_SHIFT,
                    reason=f"Illegal jump shift: {opener_hcp} HCP but need 19+",
                    rule_violated="jump_shift_hcp_requirement"
                )

        return ValidationResult(
            valid=True,
            classification=BidClassification.NATURAL,
            reason="Natural rebid"
        )

    def is_reverse(self, first_suit: str, second_suit: str, level: int) -> bool:
        """
        Check if a bid constitutes a reverse.

        Reverse = bidding higher suit at 2-level.
        Example: 1D - 1S - 2H (hearts > diamonds)
        """
        rank1 = self.SUIT_RANKS.get(first_suit, 0)
        rank2 = self.SUIT_RANKS.get(second_suit, 0)
        return level == 2 and rank2 > rank1 and first_suit != second_suit

    def is_jump_shift(self, opening_level: int, rebid_level: int, is_new_suit: bool) -> bool:
        """
        Check if a bid is a jump shift.

        Jump shift = skipping a level into a new suit.
        Example: 1C -> 2H (skipped 1H)
        """
        return is_new_suit and (rebid_level - opening_level >= 2)

    # ==================== Response Logic ====================

    def evaluate_response_to_minor(
        self,
        opening_bid: str,
        responder_hand: Dict[str, str]
    ) -> Tuple[str, str]:
        """
        Determine correct response to 1C/1D opening.

        Priority: 4-card major > NT ladder > Minor support
        """
        hcp = self.calculate_hcp(responder_hand)
        lengths = self.get_suit_lengths(responder_hand)

        if hcp < 6:
            return "Pass", f"Only {hcp} HCP, need 6+ to respond"

        # Get major suit lengths
        spades = lengths.get('S', lengths.get('♠', 0))
        hearts = lengths.get('H', lengths.get('♥', 0))

        # Priority 1: Show 4-card major at 1-level
        # "Up the line" rule: with 4-4, bid hearts first
        if hcp >= 6:
            if hearts >= 4 and spades >= 4:
                return "1♥", "4-4 majors, bid up the line"
            if hearts >= 4:
                return "1♥", f"4+ hearts, {hcp} HCP"
            if spades >= 4:
                return "1♠", f"4+ spades, {hcp} HCP"

        # Priority 2: NT ladder (no 4-card major)
        if 6 <= hcp <= 9:
            return "1NT", f"6-9 HCP, no 4-card major"
        if 10 <= hcp <= 12:
            return "2NT", f"10-12 HCP invitational"
        if 13 <= hcp <= 15:
            return "3NT", f"13-15 HCP, game values"

        return "1NT", "Default response"

    # ==================== Game/Slam Threshold Logic ====================

    def calculate_game_threshold(
        self,
        combined_hcp: int,
        trump_fit_length: int,
        has_void: bool = False,
        has_singleton: bool = False
    ) -> Tuple[str, str]:
        """
        Determine appropriate contract level based on combined strength.

        Per Gemini: Adjust thresholds based on fit quality.
        """
        base_game_threshold = 25
        base_slam_threshold = 33

        # Fit bonus: Better fit = lower threshold
        if trump_fit_length >= 10:
            base_game_threshold -= 2
            base_slam_threshold -= 2
        elif trump_fit_length >= 9:
            base_game_threshold -= 1
            base_slam_threshold -= 1

        # Distribution bonus with fit
        if trump_fit_length >= 8:
            if has_void:
                base_game_threshold -= 2
                base_slam_threshold -= 2
            elif has_singleton:
                base_game_threshold -= 1
                base_slam_threshold -= 1

        # Determine level
        if combined_hcp >= base_slam_threshold:
            return "slam", f"33+ effective points (slam threshold: {base_slam_threshold})"
        elif combined_hcp >= base_game_threshold:
            return "game", f"25+ effective points (game threshold: {base_game_threshold})"
        elif combined_hcp >= base_game_threshold - 2:
            return "invitational", "Near game values"
        else:
            return "partscore", "Below game values"

    # ==================== Forcing Bid Detection ====================

    def is_forcing_sequence(self, auction_history: List[str]) -> Tuple[bool, str]:
        """
        Determine if current auction is in a forcing sequence.

        Forcing sequences in SAYC:
        - After 2C opening (game forcing)
        - After reverse (one round forcing)
        - After jump shift (game forcing)
        - New suit at 1-level by responder (forcing one round)
        """
        if not auction_history:
            return False, "No auction"

        # 2C opening is game forcing
        if "2♣" in auction_history or "2C" in auction_history:
            return True, "2♣ is game forcing"

        # TODO: Detect reverse and jump shift in history

        return False, "Not in forcing sequence"

    # ==================== Test Case Validation ====================

    def validate_against_ground_truth(
        self,
        hand_str: str,
        history: List[str],
        actual_bid: str
    ) -> ValidationResult:
        """
        Validate a bid against ground truth test cases.

        Args:
            hand_str: Hand in dot-notation (S.H.D.C)
            history: Bidding history
            actual_bid: The bid being validated

        Returns:
            ValidationResult with pass/fail and explanation
        """
        # Convert hand string to dict
        hand_dict = self._parse_hand_string(hand_str)

        # Look up ground truth
        history_key = "-".join(history) if history else "opening"

        # Find matching test case
        test_cases = self.ground_truth.get("test_cases", {})
        for category in test_cases.values():
            for case in category:
                if case.get("hand") == hand_str:
                    if case.get("history", []) == history:
                        expected = case.get("expected")
                        if actual_bid == expected:
                            return ValidationResult(
                                valid=True,
                                classification=BidClassification.NATURAL,
                                reason=f"Matches ground truth: {case.get('reason')}"
                            )
                        else:
                            return ValidationResult(
                                valid=False,
                                classification=BidClassification.NATURAL,
                                reason=f"Expected {expected}, got {actual_bid}",
                                correct_bid=expected
                            )

        return ValidationResult(
            valid=True,  # No ground truth = assume valid
            classification=BidClassification.NATURAL,
            reason="No ground truth case found"
        )

    def _parse_hand_string(self, hand_str: str) -> Dict[str, str]:
        """
        Parse hand from dot-notation to dict.

        Example: "AK2.QJ5.K104.J93" -> {'S': 'AK2', 'H': 'QJ5', 'D': 'K104', 'C': 'J93'}
        """
        parts = hand_str.split('.')
        if len(parts) != 4:
            return {}
        return {
            'S': parts[0],
            'H': parts[1],
            'D': parts[2],
            'C': parts[3]
        }


class SAYCTestRunner:
    """
    Test runner for comparing bidding engine against ground truth.
    """

    def __init__(self, bidding_engine=None):
        self.logic_engine = SAYCLogicEngine()
        self.bidding_engine = bidding_engine  # Our actual engine
        self.results = []

    def run_test_case(self, test_case: Dict) -> Dict:
        """Run a single test case and compare results."""
        hand_str = test_case.get("hand")
        history = test_case.get("history", [])
        expected = test_case.get("expected")

        # Get our engine's bid (if available)
        if self.bidding_engine:
            # TODO: Convert hand_str to Hand object and call engine
            actual = None
        else:
            # Use logic engine as fallback
            hand_dict = self.logic_engine._parse_hand_string(hand_str)
            if not history:
                actual, _ = self.logic_engine.evaluate_opening_bid(hand_dict)
            else:
                actual = None  # Would need full response logic

        result = {
            "test_id": test_case.get("id"),
            "hand": hand_str,
            "history": history,
            "expected": expected,
            "actual": actual,
            "passed": actual == expected if actual else None,
            "reason": test_case.get("reason")
        }

        self.results.append(result)
        return result

    def run_all_tests(self) -> Dict:
        """Run all test cases from ground truth."""
        ground_truth = self.logic_engine.ground_truth
        test_cases = ground_truth.get("test_cases", {})

        total = 0
        passed = 0

        for category, cases in test_cases.items():
            for case in cases:
                result = self.run_test_case(case)
                total += 1
                if result.get("passed"):
                    passed += 1

        return {
            "total": total,
            "passed": passed,
            "pass_rate": passed / total if total > 0 else 0,
            "results": self.results
        }


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    # Demo usage
    engine = SAYCLogicEngine()

    # Test opening bid
    hand = {'S': 'K62', 'H': 'AQ5', 'D': 'KT8', 'C': 'AJ93'}
    bid, reason = engine.evaluate_opening_bid(hand)
    print(f"Opening: {bid} - {reason}")

    # Test reverse classification
    result = engine.classify_rebid('D', 'H', 2, 17)
    print(f"Reverse test: {result}")

    # Test response
    responder = {'S': 'KJ82', 'H': '32', 'D': 'QJ5', 'C': 'T842'}
    bid, reason = engine.evaluate_response_to_minor("1D", responder)
    print(f"Response: {bid} - {reason}")

    # Run test suite
    runner = SAYCTestRunner()
    results = runner.run_all_tests()
    print(f"\nTest Results: {results['passed']}/{results['total']} passed ({results['pass_rate']:.1%})")
