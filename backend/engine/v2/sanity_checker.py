"""
Competitive Safety Validator for V2 Schema Engine

Enforces HCP floors and distributional requirements for competitive bidding.
This is the "Governor" that prevents inappropriate bids based on hand strength
and distributional constraints.

Key Rules:
1. Rule of 20 (Opening): HCP + two longest suits >= 20
2. Rule of 6 (Response): Points to respond = 6 + (Level - 1)
3. Overcall HCP Floors: Based on level and suit quality

Part of the V2 Schema Engine's validation pipeline.
"""

import logging
from typing import Dict, Any, Optional, List
from engine.hand import Hand

logger = logging.getLogger(__name__)


class CompetitiveSafetyValidator:
    """
    Enforces HCP floors and distributional requirements for competitive bidding.

    This validator acts as a safety net to prevent bids that violate fundamental
    bridge "physics" - the HCP and distribution requirements that make contracts
    viable.

    Returns validation result with pass/fail and detailed explanation.

    Usage:
        validator = CompetitiveSafetyValidator()
        result = validator.validate_bid(hand, bid, features)
        if not result['valid']:
            # Use result['reason'] for feedback
    """

    # HCP requirements for opening bids
    OPENING_HCP_MIN = 12  # Standard opening
    OPENING_HCP_LIGHT = 10  # Light opening requires Rule of 20

    # HCP requirements for responses by level
    RESPONSE_HCP_FLOORS = {
        1: 6,   # 1-level response needs 6 HCP
        2: 10,  # 2-level new suit needs 10+ HCP (forcing)
        3: 12,  # 3-level response needs 12+ HCP
        4: 13,  # 4-level response needs 13+ HCP (game)
        5: 16,  # 5-level response needs 16+ HCP (slam invitation)
        6: 33,  # 6-level needs combined 33+ HCP (checked via combined estimate)
        7: 37,  # 7-level needs combined 37+ HCP
    }

    # HCP requirements for overcalls
    OVERCALL_1_LEVEL_MIN = 8   # 1-level overcall minimum
    OVERCALL_1_LEVEL_WITH_6CARD = 7  # Can be lighter with 6+ card suit
    OVERCALL_2_LEVEL_MIN = 10  # 2-level overcall minimum
    JUMP_OVERCALL_WEAK_MIN = 5  # Weak jump overcall (preemptive)
    JUMP_OVERCALL_WEAK_MAX = 10
    JUMP_OVERCALL_STRONG_MIN = 15  # Strong jump overcall

    # Suit length requirements
    OVERCALL_SUIT_MIN = 5  # Need 5+ card suit for overcall
    WEAK_OVERCALL_SUIT_MIN = 6  # Need 6+ card suit for weak overcall

    def __init__(self):
        """Initialize the validator."""
        self._enabled = True

    def validate_opening(
        self,
        hand: Hand,
        bid: str,
        vulnerability: str,
        seat: int = 1
    ) -> Dict[str, Any]:
        """
        Check if opening bid meets Rule of 20 or HCP requirements.

        Rule of 20: HCP + length of two longest suits >= 20

        Args:
            hand: The hand making the bid
            bid: The proposed opening bid
            vulnerability: Vulnerability string (None, NS, EW, Both)
            seat: Seat position (1-4, where 4 is balancing seat)

        Returns:
            Validation result dict with 'valid', 'rule', 'reason', etc.
        """
        if bid == 'Pass':
            return self._result(True, 'pass', 'Pass is always valid')

        if bid in ['X', 'XX']:
            # Doubles at opening don't make sense, but not our job to catch that
            return self._result(True, 'opening', 'Non-opening bid')

        hcp = hand.hcp

        # Calculate Rule of 20 value
        lengths = sorted(hand.suit_lengths.values(), reverse=True)
        two_longest = lengths[0] + lengths[1]
        rule_of_20_value = hcp + two_longest
        rule_of_20_met = rule_of_20_value >= 20

        # Calculate distribution bonus
        distribution_bonus = two_longest - 7  # Anything above 4-3 shape gets bonus

        # Handle different opening scenarios
        bid_level = int(bid[0]) if bid[0].isdigit() else 0

        # NT openings have specific requirements
        if bid.endswith('NT'):
            return self._validate_nt_opening(hand, bid, hcp)

        # Preemptive openings (2-level suit except 2C, and 3-4 level)
        if self._is_preemptive_opening(bid):
            return self._validate_preempt_opening(hand, bid, vulnerability, seat)

        # Strong 2C opening
        if bid == '2♣':
            return self._validate_strong_2c_opening(hand, hcp)

        # Standard 1-level suit opening
        if bid_level == 1:
            # Standard: 12+ HCP OR Rule of 20 with 10-11 HCP
            if hcp >= self.OPENING_HCP_MIN:
                return self._result(
                    True, 'opening_hcp',
                    f'Opening with {hcp} HCP meets standard requirement (12+)',
                    hcp=hcp, required_hcp=self.OPENING_HCP_MIN
                )

            # Light opening check
            if hcp >= self.OPENING_HCP_LIGHT and rule_of_20_met:
                # Check vulnerability for light opening
                we_vulnerable = self._check_vulnerability(vulnerability, 'we')
                they_vulnerable = self._check_vulnerability(vulnerability, 'they')

                if we_vulnerable and not they_vulnerable:
                    # Unfavorable - need full 12 HCP
                    return self._result(
                        False, 'rule_of_20',
                        f'Light opening ({hcp} HCP) not allowed at unfavorable vulnerability',
                        hcp=hcp, required_hcp=self.OPENING_HCP_MIN,
                        distribution_bonus=distribution_bonus
                    )

                return self._result(
                    True, 'rule_of_20',
                    f'Light opening: {hcp} HCP + {two_longest} (two longest) = {rule_of_20_value} (Rule of 20 met)',
                    hcp=hcp, required_hcp=self.OPENING_HCP_LIGHT,
                    distribution_bonus=distribution_bonus
                )

            # Below minimum
            reason = f'Opening requires 12+ HCP or 10+ with Rule of 20. Have {hcp} HCP'
            if not rule_of_20_met:
                reason += f', Rule of 20 = {rule_of_20_value} (need 20+)'

            return self._result(
                False, 'opening_floor',
                reason,
                hcp=hcp, required_hcp=self.OPENING_HCP_MIN,
                distribution_bonus=distribution_bonus
            )

        # Higher level opening (unusual) - delegate to preempt logic
        return self._result(True, 'opening', f'Opening bid {bid} accepted')

    def _validate_nt_opening(
        self,
        hand: Hand,
        bid: str,
        hcp: int
    ) -> Dict[str, Any]:
        """Validate NT opening bid requirements."""
        # NT opening requirements
        nt_requirements = {
            '1NT': (15, 17, True),   # 15-17 HCP, balanced
            '2NT': (20, 21, True),   # 20-21 HCP, balanced
            '3NT': (25, 27, True),   # Gambling 3NT or strong balanced
        }

        if bid not in nt_requirements:
            return self._result(True, 'nt_opening', f'{bid} is non-standard NT opening')

        min_hcp, max_hcp, requires_balanced = nt_requirements[bid]

        if hcp < min_hcp:
            return self._result(
                False, 'nt_opening_floor',
                f'{bid} requires {min_hcp}-{max_hcp} HCP, have {hcp}',
                hcp=hcp, required_hcp=min_hcp
            )

        if hcp > max_hcp:
            return self._result(
                False, 'nt_opening_ceiling',
                f'{bid} requires {min_hcp}-{max_hcp} HCP, have {hcp} (too strong)',
                hcp=hcp, required_hcp=max_hcp
            )

        if requires_balanced and not hand.is_balanced:
            return self._result(
                False, 'nt_opening_shape',
                f'{bid} requires balanced hand',
                hcp=hcp, required_hcp=min_hcp
            )

        return self._result(
            True, 'nt_opening',
            f'{bid} opening with {hcp} HCP, balanced',
            hcp=hcp, required_hcp=min_hcp
        )

    def _validate_preempt_opening(
        self,
        hand: Hand,
        bid: str,
        vulnerability: str,
        seat: int
    ) -> Dict[str, Any]:
        """Validate preemptive opening bid."""
        hcp = hand.hcp
        bid_level = int(bid[0])
        bid_suit = bid[1:]

        suit_length = hand.suit_lengths.get(bid_suit, 0)

        # Preempt requirements
        # 2-level: 6+ card suit, 5-10 HCP
        # 3-level: 7+ card suit, 5-10 HCP
        # 4-level: 8+ card suit (4H/4S usually 7+), 5-10 HCP

        preempt_min_length = {2: 6, 3: 7, 4: 7}
        required_length = preempt_min_length.get(bid_level, 6)

        if suit_length < required_length:
            return self._result(
                False, 'preempt_suit_length',
                f'{bid} preempt requires {required_length}+ card suit, have {suit_length}',
                hcp=hcp, required_hcp=5
            )

        # HCP range for preempts (5-10 typically)
        if hcp > 10:
            return self._result(
                False, 'preempt_hcp_ceiling',
                f'Preempt {bid} requires 5-10 HCP, have {hcp} (consider opening at 1-level)',
                hcp=hcp, required_hcp=10
            )

        if hcp < 5:
            # Very weak preempts allowed at favorable vulnerability
            we_vul = self._check_vulnerability(vulnerability, 'we')
            they_vul = self._check_vulnerability(vulnerability, 'they')

            if we_vul:
                return self._result(
                    False, 'preempt_hcp_floor',
                    f'Preempt {bid} with {hcp} HCP too risky when vulnerable',
                    hcp=hcp, required_hcp=5
                )

        return self._result(
            True, 'preempt',
            f'Valid preempt: {bid} with {suit_length}-card suit, {hcp} HCP',
            hcp=hcp, required_hcp=5
        )

    def _validate_strong_2c_opening(
        self,
        hand: Hand,
        hcp: int
    ) -> Dict[str, Any]:
        """Validate strong 2C opening."""
        if hcp >= 22:
            return self._result(
                True, 'strong_2c',
                f'2♣ opening with {hcp} HCP',
                hcp=hcp, required_hcp=22
            )

        # With less than 22 HCP, need compensating playing strength
        # (trick count, etc.) - allow 20-21 with very strong distribution
        if hcp >= 20:
            lengths = sorted(hand.suit_lengths.values(), reverse=True)
            if lengths[0] >= 6:
                return self._result(
                    True, 'strong_2c_distributional',
                    f'2♣ opening with {hcp} HCP and {lengths[0]}-card suit',
                    hcp=hcp, required_hcp=20
                )

        return self._result(
            False, 'strong_2c_floor',
            f'2♣ opening requires 22+ HCP, have {hcp}',
            hcp=hcp, required_hcp=22
        )

    def validate_response(
        self,
        hand: Hand,
        bid: str,
        partner_opening: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if response meets Rule of 6 requirements.

        Rule of 6: Points to respond = 6 + (Level - 1)
        - 1-level response: 6 HCP
        - 2-level new suit: 10+ HCP (forcing)
        - 3-level response: 12+ HCP

        Args:
            hand: The hand making the bid
            bid: The proposed response
            partner_opening: Partner's opening bid
            features: Feature dictionary with auction context

        Returns:
            Validation result dict
        """
        if bid == 'Pass':
            return self._result(True, 'pass', 'Pass is always valid')

        if bid in ['X', 'XX']:
            # Doubles/redoubles have their own requirements
            return self._validate_double(hand, bid, partner_opening, features)

        hcp = hand.hcp
        bid_level = int(bid[0]) if bid[0].isdigit() else 0
        bid_suit = bid[1:] if len(bid) > 1 else None

        # Rule of 6: Required HCP = 6 + (Level - 1)
        rule_of_6_required = 6 + (bid_level - 1)

        # Get the required HCP floor for this level
        required_hcp = self.RESPONSE_HCP_FLOORS.get(bid_level, 6)

        # Special cases for raises (supporting partner's suit)
        if self._is_raise(bid, partner_opening, features):
            return self._validate_raise_response(hand, bid, partner_opening, features)

        # Special cases for NT responses
        if bid.endswith('NT'):
            return self._validate_nt_response(hand, bid, partner_opening, features)

        # New suit responses
        if bid_level >= 2:
            # 2-level new suit forcing - needs 10+ HCP typically
            suit_length = hand.suit_lengths.get(bid_suit, 0) if bid_suit else 0

            if hcp < required_hcp:
                # Check if we have compensating length/quality
                if hcp >= required_hcp - 2 and suit_length >= 6:
                    return self._result(
                        True, 'rule_of_6_compensated',
                        f'{bid} with {hcp} HCP and {suit_length}-card suit',
                        hcp=hcp, required_hcp=required_hcp
                    )

                return self._result(
                    False, 'rule_of_6',
                    f'{bid} requires {required_hcp}+ HCP (Rule of 6: 6 + {bid_level-1}), have {hcp}',
                    hcp=hcp, required_hcp=required_hcp
                )

        # 1-level response
        if bid_level == 1:
            if hcp >= 6:
                return self._result(
                    True, 'response_1_level',
                    f'1-level response with {hcp} HCP',
                    hcp=hcp, required_hcp=6
                )

            # Can respond with less if very distributional
            if hcp >= 4:
                suit_length = hand.suit_lengths.get(bid_suit, 0) if bid_suit else 0
                if suit_length >= 5:
                    return self._result(
                        True, 'response_distributional',
                        f'1-level response with {hcp} HCP and {suit_length}-card suit',
                        hcp=hcp, required_hcp=4
                    )

            return self._result(
                False, 'response_floor',
                f'Response requires 6+ HCP, have {hcp}',
                hcp=hcp, required_hcp=6
            )

        return self._result(
            True, 'response',
            f'Response {bid} with {hcp} HCP accepted',
            hcp=hcp, required_hcp=required_hcp
        )

    def _validate_raise_response(
        self,
        hand: Hand,
        bid: str,
        partner_opening: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a raise of partner's suit."""
        hcp = hand.hcp
        bid_level = int(bid[0])
        bid_suit = bid[1:]

        support = hand.suit_lengths.get(bid_suit, 0)

        # Support point calculation (shortness when raising)
        support_pts = self._calculate_support_points(hand, bid_suit)
        total_strength = hcp + support_pts

        # Raise requirements
        raise_requirements = {
            2: (6, 3),   # Simple raise: 6-9 pts, 3+ support
            3: (10, 4),  # Limit raise: 10-12 pts, 4+ support
            4: (0, 5),   # Preemptive (with fit) or game values
        }

        if bid_level in raise_requirements:
            min_pts, min_support = raise_requirements[bid_level]

            if support < min_support:
                return self._result(
                    False, 'raise_support',
                    f'{bid} raise requires {min_support}+ card support, have {support}',
                    hcp=hcp, required_hcp=min_pts
                )

            if bid_level < 4 and total_strength < min_pts:
                return self._result(
                    False, 'raise_points',
                    f'{bid} raise requires {min_pts}+ points, have {total_strength} ({hcp} HCP + {support_pts} support)',
                    hcp=hcp, required_hcp=min_pts
                )

        return self._result(
            True, 'raise',
            f'{bid} raise with {support}-card support, {total_strength} points',
            hcp=hcp, required_hcp=0
        )

    def _validate_nt_response(
        self,
        hand: Hand,
        bid: str,
        partner_opening: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate NT response."""
        hcp = hand.hcp

        # NT response requirements after suit opening
        nt_response_reqs = {
            '1NT': (6, 10),   # 6-10 HCP, no other bid
            '2NT': (11, 12),  # 11-12 HCP, invitational (or Jacoby 2NT with 4+ support)
            '3NT': (13, 15),  # 13-15 HCP, game values
        }

        if bid in nt_response_reqs:
            min_hcp, max_hcp = nt_response_reqs[bid]

            if hcp < min_hcp:
                return self._result(
                    False, 'nt_response_floor',
                    f'{bid} requires {min_hcp}-{max_hcp} HCP, have {hcp}',
                    hcp=hcp, required_hcp=min_hcp
                )

        return self._result(
            True, 'nt_response',
            f'{bid} response with {hcp} HCP',
            hcp=hcp, required_hcp=hcp
        )

    def validate_overcall(
        self,
        hand: Hand,
        bid: str,
        opponent_bid: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if overcall meets HCP and suit quality floors.

        Overcall requirements:
        - 1-level: 8+ HCP with 5+ card suit (or 7+ with 6+ card suit)
        - 2-level: 10+ HCP with 5+ card suit (quality matters)
        - Jump overcall: Weak (5-10, 6+) or Strong (15+, 6+)

        Args:
            hand: The hand making the bid
            bid: The proposed overcall
            opponent_bid: The opponent's bid being overcalled
            features: Feature dictionary with auction context

        Returns:
            Validation result dict
        """
        if bid == 'Pass':
            return self._result(True, 'pass', 'Pass is always valid')

        if bid in ['X', 'XX']:
            return self._validate_double(hand, bid, opponent_bid, features)

        hcp = hand.hcp
        bid_level = int(bid[0]) if bid[0].isdigit() else 0
        bid_suit = bid[1:] if len(bid) > 1 else None

        # Get suit length and quality
        suit_length = hand.suit_lengths.get(bid_suit, 0) if bid_suit else 0
        suit_quality = self._evaluate_suit_quality(hand, bid_suit) if bid_suit else 'poor'

        # Determine if this is a jump overcall
        opp_level = int(opponent_bid[0]) if opponent_bid and opponent_bid[0].isdigit() else 0
        opp_suit = opponent_bid[1:] if opponent_bid and len(opponent_bid) > 1 else None

        # Suit ranking for determining if 1-level was available
        suit_ranking = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
        our_rank = suit_ranking.get(bid_suit, 0)
        opp_rank = suit_ranking.get(opp_suit, 0)

        # A jump overcall occurs when we bid higher than necessary:
        # 1. Classic jump: bid_level > opp_level + 1 (e.g., 3♠ over 1♦)
        # 2. Single jump at 2-level: When 1-level was available in our suit
        #    (e.g., 2♠ over 1♦ - since 1♠ was available, 2♠ is a jump)
        # Note: After 1NT, no 1-level suit bids are available, so 2-level isn't a jump
        opp_is_suit = opp_suit in suit_ranking
        one_level_available = (opp_level == 1 and opp_is_suit and our_rank > opp_rank)
        is_jump = (bid_level > opp_level + 1) or (bid_level == 2 and one_level_available)

        # NT overcall (1NT overcall of 1-level opening)
        if bid.endswith('NT'):
            return self._validate_nt_overcall(hand, bid, opponent_bid, features)

        # Suit length requirement
        if suit_length < self.OVERCALL_SUIT_MIN:
            # Allow 4-card overcall at 1-level with very good suit
            if bid_level == 1 and suit_length == 4 and suit_quality in ['good', 'excellent']:
                pass  # Allow it
            else:
                return self._result(
                    False, 'overcall_suit_length',
                    f'{bid} overcall requires {self.OVERCALL_SUIT_MIN}+ card suit, have {suit_length}',
                    hcp=hcp, required_hcp=self.OVERCALL_1_LEVEL_MIN
                )

        # Jump overcall (weak or strong)
        if is_jump:
            return self._validate_jump_overcall(hand, bid, suit_length, suit_quality, features)

        # 1-level overcall
        if bid_level == 1:
            required = self.OVERCALL_1_LEVEL_MIN
            if suit_length >= 6:
                required = self.OVERCALL_1_LEVEL_WITH_6CARD

            if hcp < required:
                return self._result(
                    False, 'overcall_floor',
                    f'1-level overcall requires {required}+ HCP, have {hcp}',
                    hcp=hcp, required_hcp=required
                )

            return self._result(
                True, 'overcall_1_level',
                f'1-level overcall with {hcp} HCP, {suit_length}-card suit',
                hcp=hcp, required_hcp=required
            )

        # 2-level overcall
        if bid_level == 2:
            required = self.OVERCALL_2_LEVEL_MIN

            # Quality matters more at 2-level
            if suit_quality == 'poor':
                required += 2  # Need extra HCP with poor suit
            elif suit_quality == 'excellent':
                required -= 1  # Can be lighter with excellent suit

            if hcp < required:
                return self._result(
                    False, 'overcall_floor',
                    f'2-level overcall requires {required}+ HCP, have {hcp} (suit quality: {suit_quality})',
                    hcp=hcp, required_hcp=required
                )

            return self._result(
                True, 'overcall_2_level',
                f'2-level overcall with {hcp} HCP, {suit_length}-card {suit_quality} suit',
                hcp=hcp, required_hcp=required
            )

        # Higher level overcalls
        return self._result(
            True, 'overcall',
            f'{bid} overcall with {hcp} HCP accepted',
            hcp=hcp, required_hcp=10
        )

    def _validate_jump_overcall(
        self,
        hand: Hand,
        bid: str,
        suit_length: int,
        suit_quality: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate jump overcall (weak or strong)."""
        hcp = hand.hcp

        # Weak jump overcall: 5-10 HCP, 6+ card suit
        if hcp <= self.JUMP_OVERCALL_WEAK_MAX:
            if suit_length < self.WEAK_OVERCALL_SUIT_MIN:
                return self._result(
                    False, 'weak_jump_suit',
                    f'Weak jump overcall requires {self.WEAK_OVERCALL_SUIT_MIN}+ card suit, have {suit_length}',
                    hcp=hcp, required_hcp=self.JUMP_OVERCALL_WEAK_MIN
                )

            if hcp < self.JUMP_OVERCALL_WEAK_MIN:
                return self._result(
                    False, 'weak_jump_floor',
                    f'Weak jump overcall requires {self.JUMP_OVERCALL_WEAK_MIN}+ HCP, have {hcp}',
                    hcp=hcp, required_hcp=self.JUMP_OVERCALL_WEAK_MIN
                )

            return self._result(
                True, 'weak_jump_overcall',
                f'Weak jump overcall with {hcp} HCP, {suit_length}-card suit',
                hcp=hcp, required_hcp=self.JUMP_OVERCALL_WEAK_MIN
            )

        # Strong jump overcall: 15+ HCP, 6+ card suit
        if hcp >= self.JUMP_OVERCALL_STRONG_MIN:
            if suit_length < self.WEAK_OVERCALL_SUIT_MIN:
                return self._result(
                    False, 'strong_jump_suit',
                    f'Strong jump overcall requires {self.WEAK_OVERCALL_SUIT_MIN}+ card suit, have {suit_length}',
                    hcp=hcp, required_hcp=self.JUMP_OVERCALL_STRONG_MIN
                )

            return self._result(
                True, 'strong_jump_overcall',
                f'Strong jump overcall with {hcp} HCP, {suit_length}-card suit',
                hcp=hcp, required_hcp=self.JUMP_OVERCALL_STRONG_MIN
            )

        # In-between range (11-14 HCP) - problematic for jump overcall
        return self._result(
            False, 'jump_overcall_range',
            f'Jump overcall with {hcp} HCP in awkward range (need 5-10 weak or 15+ strong)',
            hcp=hcp, required_hcp=self.JUMP_OVERCALL_STRONG_MIN
        )

    def _validate_nt_overcall(
        self,
        hand: Hand,
        bid: str,
        opponent_bid: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate NT overcall."""
        hcp = hand.hcp

        # Get opponent's suit for stopper check
        opp_suit = opponent_bid[1:] if opponent_bid and len(opponent_bid) > 1 else None

        # 1NT overcall requirements: 15-18 HCP, balanced, stopper in opponent's suit
        if bid == '1NT':
            if hcp < 15:
                return self._result(
                    False, 'nt_overcall_floor',
                    f'1NT overcall requires 15-18 HCP, have {hcp}',
                    hcp=hcp, required_hcp=15
                )

            if hcp > 18:
                return self._result(
                    False, 'nt_overcall_ceiling',
                    f'1NT overcall requires 15-18 HCP, have {hcp} (consider double then bid NT)',
                    hcp=hcp, required_hcp=18
                )

            # Check for stopper in opponent's suit
            if opp_suit:
                suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}.get(opp_suit)
                if suit_name and not features.get(f'{suit_name}_stopped', True):
                    return self._result(
                        False, 'nt_overcall_stopper',
                        f'1NT overcall requires stopper in opponent\'s suit ({opp_suit})',
                        hcp=hcp, required_hcp=15
                    )

            return self._result(
                True, 'nt_overcall',
                f'1NT overcall with {hcp} HCP, balanced, stopper in {opp_suit}',
                hcp=hcp, required_hcp=15
            )

        return self._result(True, 'nt_overcall', f'{bid} NT overcall accepted')

    def _validate_double(
        self,
        hand: Hand,
        bid: str,
        context_bid: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate double or redouble."""
        hcp = hand.hcp

        # Takeout double requirements
        if bid == 'X':
            # Basic takeout double: 12+ HCP (or 10+ with shape)
            # Check for support in unbid suits

            if hcp >= 12:
                return self._result(
                    True, 'takeout_double',
                    f'Takeout double with {hcp} HCP',
                    hcp=hcp, required_hcp=12
                )

            if hcp >= 10:
                # Allow lighter with good shape
                lengths = sorted(hand.suit_lengths.values(), reverse=True)
                if lengths[0] + lengths[1] >= 9:  # Good shape
                    return self._result(
                        True, 'takeout_double_shape',
                        f'Takeout double with {hcp} HCP and good shape',
                        hcp=hcp, required_hcp=10
                    )

            return self._result(
                False, 'double_floor',
                f'Takeout double requires 12+ HCP (or 10+ with shape), have {hcp}',
                hcp=hcp, required_hcp=12
            )

        # Redouble
        if bid == 'XX':
            if hcp >= 10:
                return self._result(
                    True, 'redouble',
                    f'Redouble with {hcp} HCP showing strength',
                    hcp=hcp, required_hcp=10
                )

            return self._result(
                False, 'redouble_floor',
                f'Redouble requires 10+ HCP, have {hcp}',
                hcp=hcp, required_hcp=10
            )

        return self._result(True, 'double', f'{bid} accepted')

    def validate_bid(
        self,
        hand: Hand,
        bid: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point - routes to appropriate validator based on context.

        Determines the bidding context (opening, response, overcall, etc.)
        and delegates to the appropriate specialized validator.

        Args:
            hand: The hand making the bid
            bid: The proposed bid
            features: Feature dictionary with full auction context

        Returns:
            Validation result dict with:
            - valid: True/False
            - rule: Rule name that was applied
            - reason: Human-readable explanation
            - hcp: Actual HCP
            - required_hcp: Required HCP for this bid
            - distribution_bonus: Distribution bonus if applicable
        """
        if bid == 'Pass':
            return self._result(True, 'pass', 'Pass is always valid')

        # Extract context from features
        opening_bid = features.get('opening_bid')
        opener_relationship = features.get('opener_relationship', '').lower() if features.get('opener_relationship') else ''
        vulnerability = features.get('vulnerability', 'None')
        seat = features.get('seat', 1)
        is_overcall = features.get('is_overcall', False)
        is_advancer = features.get('is_advancer', False)

        # Determine context and route to appropriate validator

        # Opening bid (no one has bid yet)
        if not opening_bid or opening_bid == 'Pass':
            return self.validate_opening(hand, bid, vulnerability, seat)

        # Response to partner's opening
        if opener_relationship == 'partner':
            return self.validate_response(hand, bid, opening_bid, features)

        # Overcall (opponent opened)
        if opener_relationship == 'opponent' or is_overcall:
            return self.validate_overcall(hand, bid, opening_bid, features)

        # Advancer (partner overcalled) - similar to response but looser
        if is_advancer:
            # Use response validation with looser requirements
            return self.validate_response(hand, bid, features.get('partner_last_bid', ''), features)

        # Default: apply response-like validation
        return self.validate_response(hand, bid, opening_bid or '', features)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _result(
        self,
        valid: bool,
        rule: str,
        reason: str,
        hcp: int = 0,
        required_hcp: int = 0,
        distribution_bonus: int = 0
    ) -> Dict[str, Any]:
        """Create a standardized validation result."""
        return {
            'valid': valid,
            'rule': rule,
            'reason': reason,
            'hcp': hcp,
            'required_hcp': required_hcp,
            'distribution_bonus': distribution_bonus
        }

    def _check_vulnerability(self, vulnerability: str, side: str) -> bool:
        """
        Check if a side is vulnerable.

        Args:
            vulnerability: Vulnerability string (None, NS, EW, Both)
            side: 'we' or 'they'

        Returns:
            True if the specified side is vulnerable
        """
        # For simplicity, assume 'we' is NS and 'they' is EW
        # In real usage, this would be determined by position
        if vulnerability == 'Both':
            return True
        if vulnerability == 'None':
            return False
        if side == 'we':
            return vulnerability == 'NS'
        else:
            return vulnerability == 'EW'

    def _is_preemptive_opening(self, bid: str) -> bool:
        """Check if a bid is a preemptive opening."""
        if not bid or not bid[0].isdigit():
            return False

        level = int(bid[0])
        suit = bid[1:] if len(bid) > 1 else ''

        # 2-level suit (except 2C which is strong)
        if level == 2 and suit != '♣' and suit != 'NT':
            return True

        # 3-level or 4-level suit opening
        if level in [3, 4] and suit != 'NT':
            return True

        return False

    def _is_raise(
        self,
        bid: str,
        partner_bid: str,
        features: Dict[str, Any]
    ) -> bool:
        """Check if bid is a raise of partner's suit."""
        if not bid or not partner_bid:
            return False

        bid_suit = bid[1:] if len(bid) > 1 else ''
        partner_suit = partner_bid[1:] if len(partner_bid) > 1 else ''

        # NT bids aren't raises
        if bid_suit == 'NT' or partner_suit == 'NT':
            return False

        return bid_suit == partner_suit

    def _calculate_support_points(self, hand: Hand, trump_suit: str) -> int:
        """
        Calculate support points (shortness points when raising partner).

        Void: 5 points
        Singleton: 3 points
        Doubleton: 1 point
        """
        support_pts = 0

        for suit, length in hand.suit_lengths.items():
            if suit == trump_suit:
                continue

            if length == 0:
                support_pts += 5
            elif length == 1:
                support_pts += 3
            elif length == 2:
                support_pts += 1

        return support_pts

    def _evaluate_suit_quality(self, hand: Hand, suit: str) -> str:
        """
        Evaluate the quality of a suit.

        Returns: 'poor', 'fair', 'good', or 'excellent'
        """
        if not suit or suit not in hand.suit_lengths:
            return 'poor'

        length = hand.suit_lengths.get(suit, 0)
        suit_hcp = hand.suit_hcp.get(suit, 0)

        # Get cards in suit
        cards_in_suit = [c for c in hand.cards if c.suit == suit]
        high_cards = sum(1 for c in cards_in_suit if c.rank in ['A', 'K', 'Q', 'J', 'T'])

        # Quality assessment
        if length < 4:
            return 'poor'

        # Check for honors
        has_ace = any(c.rank == 'A' for c in cards_in_suit)
        has_king = any(c.rank == 'K' for c in cards_in_suit)
        has_queen = any(c.rank == 'Q' for c in cards_in_suit)

        # Excellent: AK... or AQJ... or KQJ10...
        if (has_ace and has_king) or suit_hcp >= 7:
            return 'excellent'

        # Good: A + Q, or K + J + 10, or 3+ honors
        if high_cards >= 3 or (has_ace and has_queen) or suit_hcp >= 5:
            return 'good'

        # Fair: at least one honor
        if high_cards >= 2 or has_ace or has_king:
            return 'fair'

        return 'poor'

    def disable(self):
        """Disable validation (for testing only)."""
        self._enabled = False
        logger.warning("CompetitiveSafetyValidator DISABLED (should only be for testing)")

    def enable(self):
        """Enable validation."""
        self._enabled = True


# Convenience function for quick validation
def validate_competitive_bid(
    hand: Hand,
    bid: str,
    features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Quick validation of a bid against competitive safety rules.

    Args:
        hand: The hand making the bid
        bid: The proposed bid
        features: Feature dictionary with auction context

    Returns:
        Validation result dict
    """
    validator = CompetitiveSafetyValidator()
    return validator.validate_bid(hand, bid, features)
