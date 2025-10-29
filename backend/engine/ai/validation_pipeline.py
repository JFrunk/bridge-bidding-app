"""
Validation Pipeline for Bidding Decisions

Centralized validation that CANNOT be bypassed. All bids must pass through
this pipeline before being accepted.

Part of ADR-0002: Bidding System Robustness Improvements
Layer 2: Centralized Validation Pipeline
"""

import logging
from typing import Tuple, Optional, Dict, List
from engine.hand import Hand

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    Composable validation chain for bidding decisions.

    All bids must pass through ALL validators before acceptance.
    Validators run in order and first failure stops the chain.

    Usage:
        pipeline = ValidationPipeline()
        is_valid, error = pipeline.validate(bid, hand, features, auction)
        if not is_valid:
            # Reject bid, use fallback
    """

    def __init__(self):
        self.validators = [
            LegalityValidator(),
            HCPRequirementValidator(),
            SuitLengthValidator(),
            BidLevelAppropriatenessValidator(),
        ]
        self._enabled = True

    def validate(self, bid: str, hand: Hand, features: Dict, auction: List) -> Tuple[bool, Optional[str]]:
        """
        Run all validators on a bid.

        Args:
            bid: The bid to validate (e.g., "1♠", "3NT", "X")
            hand: The hand making the bid
            features: Extracted features from auction
            auction: List of previous bids

        Returns:
            (is_valid, error_message)
            - is_valid: True if bid passes all validators
            - error_message: Description of failure, or None if valid
        """
        if not self._enabled:
            return True, None

        # Pass bid is always valid
        if bid == "Pass":
            return True, None

        for validator in self.validators:
            is_valid, error = validator.validate(bid, hand, features, auction)
            if not is_valid:
                logger.warning(f"Validation failed for {bid}: {error}")
                return False, error

        return True, None

    def add_validator(self, validator):
        """Add custom validator to pipeline."""
        self.validators.append(validator)

    def disable(self):
        """Disable validation (for testing only)."""
        self._enabled = False
        logger.warning("Validation pipeline DISABLED (should only be for testing)")

    def enable(self):
        """Enable validation."""
        self._enabled = True


class LegalityValidator:
    """Validates that bid is legal given auction history."""

    def validate(self, bid: str, hand: Hand, features: Dict, auction: List) -> Tuple[bool, Optional[str]]:
        """Check if bid is legal (higher than last bid)."""
        # Special bids are always legal
        if bid in ["Pass", "X", "XX"]:
            return True, None

        if not auction:
            return True, None  # First bid is always legal

        last_bid = auction[-1]
        if last_bid == "Pass":
            # Find last non-Pass bid
            for prev_bid in reversed(auction[:-1]):
                if prev_bid != "Pass":
                    last_bid = prev_bid
                    break
            else:
                return True, None  # All passes, any bid is legal

        # If last bid was Pass, X, or XX, find the actual last bid
        if last_bid in ["Pass", "X", "XX"]:
            for prev_bid in reversed(auction):
                if prev_bid not in ["Pass", "X", "XX"]:
                    last_bid = prev_bid
                    break
            else:
                return True, None  # No previous bid level

        return self._is_higher_bid(bid, last_bid)

    def _is_higher_bid(self, bid: str, last_bid: str) -> Tuple[bool, Optional[str]]:
        """Check if bid is higher than last_bid."""
        bid_level = int(bid[0])
        last_level = int(last_bid[0])

        if bid_level > last_level:
            return True, None

        if bid_level == last_level:
            # Same level - check suit ranking
            suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}
            bid_suit = bid[1:]
            last_suit = last_bid[1:]

            if suit_rank.get(bid_suit, 0) > suit_rank.get(last_suit, 0):
                return True, None

        return False, f"Bid {bid} not higher than {last_bid}"


class HCPRequirementValidator:
    """
    Validates HCP requirements for bids according to SAYC.

    This prevents inappropriate bids like competitive doubles with 5 HCP
    when 8+ HCP is required.
    """

    # SAYC HCP requirements
    HCP_REQUIREMENTS = {
        'competitive_double': 8,      # Competitive/Negative double minimum
        'overcall_1_level': 8,         # 1-level overcall minimum
        'overcall_2_level': 10,        # 2-level overcall minimum
        'new_suit_2_level': 10,        # 2-level new suit minimum
        '3_level_bid': 10,             # 3-level bid minimum
        '4_level_bid': 12,             # 4-level (game) bid minimum
        '5_level_bid': 13,             # 5-level bid minimum
        '6_level_bid': 16,             # Small slam minimum
        '7_level_bid': 18,             # Grand slam minimum
    }

    def validate(self, bid: str, hand: Hand, features: Dict, auction: List) -> Tuple[bool, Optional[str]]:
        """Check if hand meets HCP requirements for bid."""
        bid_type = self._classify_bid(bid, features, auction)
        required_hcp = self.HCP_REQUIREMENTS.get(bid_type, 0)

        if hand.hcp < required_hcp:
            return False, f"Insufficient HCP for {bid_type}: have {hand.hcp}, need {required_hcp}+"

        return True, None

    def _classify_bid(self, bid: str, features: Dict, auction: List) -> str:
        """Classify bid type for HCP lookup."""
        # Handle doubles
        if bid == "X":
            # Check if competitive/negative double
            if features.get('competitive_auction'):
                return 'competitive_double'
            # Penalty double - no minimum HCP
            return 'penalty_double'

        # Extract level
        level = int(bid[0])

        # Check if overcall
        if features.get('opener') == 'opponent':
            if level == 1:
                return 'overcall_1_level'
            elif level == 2:
                return 'overcall_2_level'

        # Check if new suit by responder
        if features.get('opener') == 'partner' and len(auction) >= 2:
            if level == 2:
                return 'new_suit_2_level'

        # By level
        if level == 3:
            return '3_level_bid'
        elif level == 4:
            return '4_level_bid'
        elif level == 5:
            return '5_level_bid'
        elif level == 6:
            return '6_level_bid'
        elif level == 7:
            return '7_level_bid'

        return 'other'


class SuitLengthValidator:
    """Validates minimum suit length requirements."""

    def validate(self, bid: str, hand: Hand, features: Dict, auction: List) -> Tuple[bool, Optional[str]]:
        """Check if hand has sufficient length in bid suit."""
        # Skip NT bids and special bids
        if bid in ["Pass", "X", "XX"] or bid.endswith("NT"):
            return True, None

        # Extract suit
        suit = bid[1:]
        suit_length = hand.suit_lengths.get(suit, 0)

        # Determine minimum length required
        level = int(bid[0])
        min_length = self._get_min_length(level, features, auction)

        if suit_length < min_length:
            return False, f"Bid {suit} with only {suit_length} cards (need {min_length}+)"

        return True, None

    def _get_min_length(self, level: int, features: Dict, auction: List) -> int:
        """Get minimum suit length for bid level."""
        # 1-level bids: 4+ cards (3 for minors in some cases)
        if level == 1:
            return 4

        # 2-level and higher: 5+ cards for new suits
        if level >= 2:
            return 5

        # Raises: 3+ cards
        if features.get('is_raise'):
            return 3

        return 4  # Default


class BidLevelAppropriatenessValidator:
    """
    Validates that bid level is appropriate for hand strength.

    Prevents bids like 3-level with 7 HCP or 5-level with 10 HCP.
    """

    def validate(self, bid: str, hand: Hand, features: Dict, auction: List) -> Tuple[bool, Optional[str]]:
        """Check if bid level matches hand strength."""
        # Skip special bids
        if bid in ["Pass", "X", "XX"]:
            return True, None

        level = int(bid[0])
        total_points = hand.total_points

        # Check appropriateness by level
        if level >= 3:
            # 3-level needs 10+ points (unless preemptive)
            if total_points < 10 and not self._is_preemptive(hand, auction):
                return False, f"{level}-level bid with only {total_points} points (need 10+)"

        if level >= 4:
            # 4-level (game) needs 12+ points (unless preemptive)
            if total_points < 12 and not self._is_preemptive(hand, auction):
                return False, f"{level}-level bid with only {total_points} points (need 12+)"

        if level >= 5:
            # 5-level needs 13+ points
            if total_points < 13:
                return False, f"{level}-level bid with only {total_points} points (need 13+)"

        return True, None

    def _is_preemptive(self, hand: Hand, auction: List) -> bool:
        """Check if bid is preemptive (long suit, weak hand)."""
        # Preemptive if 6+ card suit and 6-10 HCP
        max_suit_length = max(hand.suit_lengths.values())
        return max_suit_length >= 6 and 6 <= hand.hcp <= 10


class ValidationError(Exception):
    """Raised when a bid fails validation."""
    pass
