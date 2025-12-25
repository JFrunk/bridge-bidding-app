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

    def validate(self, bid: str, hand: Hand, features: Dict, auction: List, metadata: Optional[Dict] = None) -> Tuple[bool, Optional[str]]:
        """
        Run all validators on a bid.

        Args:
            bid: The bid to validate (e.g., "1♠", "3NT", "X")
            hand: The hand making the bid
            features: Extracted features from auction
            auction: List of previous bids
            metadata: Optional metadata dict with bypass flags:
                - bypass_suit_length: Skip suit length validation (for artificial bids)
                - bypass_hcp: Skip HCP validation (for conventional responses)

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

        metadata = metadata or {}

        for validator in self.validators:
            # Check if this validator should be bypassed
            if isinstance(validator, SuitLengthValidator) and metadata.get('bypass_suit_length'):
                logger.debug(f"Bypassing SuitLengthValidator for artificial bid: {bid}")
                continue
            if isinstance(validator, HCPRequirementValidator) and metadata.get('bypass_hcp'):
                logger.debug(f"Bypassing HCPRequirementValidator for conventional response: {bid}")
                continue
            if isinstance(validator, BidLevelAppropriatenessValidator) and metadata.get('bypass_hcp'):
                # Also bypass appropriateness check when bypassing HCP (e.g., responding to 2NT)
                logger.debug(f"Bypassing BidLevelAppropriatenessValidator for response to strong opening: {bid}")
                continue

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

        # For suit bids, allow total points (HCP + distribution) to count
        # This is important for hands with long suits (6+) that have playing strength
        # Example: 8 HCP with 7-card suit = 11 total points, valid for 3-level invitational
        if len(bid) >= 2 and bid[1] in '♣♦♥♠' and bid[0] in '234567':
            # Use total points for suit bids at 2-level or higher
            if hand.total_points >= required_hcp:
                return True, None

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
        min_length = self._get_min_length(bid, level, features, auction)

        if suit_length < min_length:
            return False, f"Bid {suit} with only {suit_length} cards (need {min_length}+)"

        return True, None

    def _get_min_length(self, bid: str, level: int, features: Dict, auction: List) -> int:
        """Get minimum suit length for bid level."""
        # Check for raises first (applies at all levels)
        # SAYC raises require 3+ card support at all levels:
        # - Simple raise (1M-2M): 3+ support, 6-10 pts
        # - Limit raise (1M-3M): 3+ support, 10-12 pts (invitational)
        # - Game raise (1M-4M): 3+ support with distributional values
        # Only Jacoby super-accepts (1NT-2♦-3♥) require 4+ cards
        if self._is_raise(bid, auction, features):
            # Check for Jacoby super-accept specifically (requires 4+ cards)
            if len(auction) >= 4 and auction[0] == '1NT':
                if (auction[2] == '2♦' and bid == '3♥') or (auction[2] == '2♥' and bid == '3♠'):
                    return 4  # Jacoby super-accept needs 4+
            return 3  # All other raises need only 3+ support

        # Check for Jacoby transfer completions (2-level)
        # Pattern: 1NT - Pass - 2♦ - Pass - 2♥ (can be doubleton)
        if self._is_jacoby_completion(bid, auction):
            return 2  # Jacoby completion can be doubleton

        # Check for post-Jacoby continuation bids (opener showing support)
        # Pattern: 1NT - 2♦ - 2♥ - 2NT - 3♥ (opener shows 3-card support)
        # Pattern: 1NT - 2♦ - 2♥ - 2NT - 4♥ (opener accepts with fit)
        # Pattern: 1NT - 2♥ - 2♠ - 2NT - 3♠/4♠ (same for spades)
        if self._is_post_jacoby_continuation(bid, auction):
            return 3  # Only need 3-card support (partner has 5+)

        # 1-level bids: 4+ cards (3 for minors in some cases)
        if level == 1:
            return 4

        # 2-level and higher new suits: 5+ cards
        if level >= 2:
            return 5

        return 4  # Default

    def _is_jacoby_completion(self, bid: str, auction: List) -> bool:
        """
        Check if bid is a normal Jacoby transfer completion (2-level).

        Pattern: 1NT - Pass - 2♦ - Pass - 2♥ (completing transfer with 2-3 hearts)
        Pattern: 1NT - Pass - 2♥ - Pass - 2♠ (completing transfer with 2-3 spades)
        """
        if len(auction) < 4:
            return False

        if auction[0] == '1NT':
            # 2♦ transfer, completing with 2♥
            if auction[2] == '2♦' and bid == '2♥':
                return True
            # 2♥ transfer, completing with 2♠
            if auction[2] == '2♥' and bid == '2♠':
                return True

        return False

    def _is_raise(self, bid: str, auction: List, features: Dict) -> bool:
        """
        Check if this bid is a raise of partner's suit.

        Handles:
        - Direct raises of partner's opening suit (1♥ - 2♥, 1♥ - 3♥, 1♠ - 4♠)
        - Jacoby super-accepts (jump raises after transfer)
        Normal Jacoby completions (2-level) are NOT raises.
        """
        # Check feature flag first
        if features.get('is_raise'):
            return True

        # Extract bid suit
        if len(bid) < 2 or bid[0] not in '1234567':
            return False
        bid_suit = bid[1:]
        if bid_suit not in ['♣', '♦', '♥', '♠']:
            return False

        # Check for direct raise of partner's opening suit
        # Pattern: Partner opens 1M/1m - I raise to 2M/3M/4M (same suit)
        auction_features = features.get('auction_features', {})
        opener_relationship = auction_features.get('opener_relationship', '')
        opening_bid = auction_features.get('opening_bid', '')

        if opener_relationship == 'Partner' and opening_bid:
            # Partner opened - check if we're raising their suit
            if len(opening_bid) >= 2 and opening_bid[1:] == bid_suit:
                # We're bidding the same suit partner opened
                return True

        # Detect Jacoby super-accept sequences (3-level jump = raise)
        # Pattern: 1NT - Pass - 2♦ - Pass - 3♥ (super-accept showing 4+ hearts)
        # Pattern: 1NT - Pass - 2♥ - Pass - 3♠ (super-accept showing 4+ spades)
        # IMPORTANT: Super-accept only happens as the IMMEDIATE response to transfer
        # (auction length 4), not after partner continues (auction length 8+)
        if len(auction) == 4 and auction[0] == '1NT':
            # 2♦ transfer followed by 3♥ super-accept
            if auction[2] == '2♦' and bid == '3♥':
                return True
            # 2♥ transfer followed by 3♠ super-accept
            if auction[2] == '2♥' and bid == '3♠':
                return True

        return False

    def _is_post_jacoby_continuation(self, bid: str, auction: List) -> bool:
        """
        Check if bid is a continuation after Jacoby transfer completion.

        After 1NT - 2♦ - 2♥ - (partner's continuation), opener can bid:
        - 3♥/4♥: Showing 3+ card support (partner has 5+ hearts)
        - 3NT: Preferring NT (only 2 hearts)

        After 1NT - 2♥ - 2♠ - (partner's continuation), opener can bid:
        - 3♠/4♠: Showing 3+ card support (partner has 5+ spades)
        - 3NT: Preferring NT (only 2 spades)

        This allows 3-card support since partner has already shown 5+ in the major.
        """
        # Need at least 8 bids to be in this position:
        # 1NT - X - 2♦ - X - 2♥ - X - 2NT/3♥/etc - X - (now bidding)
        # But auction only shows bids made so far, so we need 8 for our 5th bid
        if len(auction) < 8:
            return False

        # Check for heart transfer sequence
        # Pattern: 1NT - 2♦ - 2♥ - (partner continues) - (our bid)
        # Positions: 0    2    4     6                   8 (our current bid)
        # But we're checking against auction which doesn't include our bid yet
        # So we're at position 8, auction has 8 bids
        if auction[0] == '1NT' and auction[2] == '2♦' and auction[4] == '2♥':
            # Partner continued at position 6 (2NT, 3♥, 3NT, 4♥)
            # Now we're bidding hearts
            if bid in ['3♥', '4♥']:
                return True

        # Check for spade transfer sequence
        # Pattern: 1NT - 2♥ - 2♠ - (partner continues) - (our bid)
        if auction[0] == '1NT' and auction[2] == '2♥' and auction[4] == '2♠':
            # Partner continued at position 6 (2NT, 3♠, 3NT, 4♠)
            # Now we're bidding spades
            if bid in ['3♠', '4♠']:
                return True

        return False


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
