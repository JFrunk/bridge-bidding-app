"""
Centralized bid safety checks to prevent unreasonable bids.

This module provides centralized safety validation for all bidding modules,
preventing issues like the 7NT disaster (bidding grand slam with 27 combined HCP).

All bidding modules should use these functions instead of implementing their own
validation logic.

Author: Generated for Bridge Bidding App
Date: 2025-10-24
"""

from typing import Optional, Tuple
from engine.hand import Hand


class BidSafety:
    """Centralized safety checks for bid validation and adjustment."""

    # Configuration constants
    MAX_LEVEL_ADJUSTMENT = 2      # Maximum levels we'll adjust a bid
    SLAM_SMALL_MIN_HCP = 33       # Minimum combined HCP for small slam (6-level)
    SLAM_GRAND_MIN_HCP = 37       # Minimum combined HCP for grand slam (7-level)
    GAME_3NT_MIN_HCP = 24         # Minimum combined HCP for 3NT game
    GAME_4M_MIN_TRUMP = 8         # Minimum trump cards for 4M contract

    @staticmethod
    def safe_adjust_bid(
        original_bid: str,
        next_legal: str,
        auction_history: list,
        hand: Hand,
        explanation: str
    ) -> Tuple[str, str]:
        """
        Safely adjust a bid with multiple safety checks.

        This method prevents runaway bid escalation by checking:
        1. Level escalation (max 2 levels)
        2. Point requirements for the adjusted level
        3. Trump requirements for suit contracts

        Args:
            original_bid: The bid we wanted to make (e.g., "2NT")
            next_legal: The next legal bid of same strain (e.g., "4NT")
            auction_history: Full auction history
            hand: Our hand
            explanation: Original explanation for the bid

        Returns:
            (bid, explanation) - Either the adjusted bid or Pass with reason

        Example:
            >>> BidSafety.safe_adjust_bid("2NT", "7NT", [], hand, "Invitational")
            ("Pass", "Cannot make reasonable bid at current auction level...")
        """
        # Check 1: Level escalation (most common issue)
        escalation_check = BidSafety._check_level_escalation(original_bid, next_legal)
        if escalation_check:
            return escalation_check

        # Check 2: Point requirements for the adjusted level
        point_check = BidSafety._check_point_requirements(next_legal, hand, auction_history)
        if point_check:
            return point_check

        # Check 3: Trump requirements for suit contracts
        trump_check = BidSafety._check_trump_requirements(next_legal, hand)
        if trump_check:
            return trump_check

        # All checks passed - allow adjustment
        adjusted_explanation = f"{explanation} [Adjusted from {original_bid} to {next_legal} for legality]"
        return (next_legal, adjusted_explanation)

    @staticmethod
    def _check_level_escalation(original_bid: str, next_legal: str) -> Optional[Tuple[str, str]]:
        """
        Check if adjustment escalates too many levels.

        Prevents: 2NT → 7NT escalation

        Args:
            original_bid: Original bid suggestion
            next_legal: Next legal bid

        Returns:
            (Pass, reason) if escalation too large, None otherwise
        """
        try:
            original_level = int(original_bid[0])
            adjusted_level = int(next_legal[0])

            if adjusted_level - original_level > BidSafety.MAX_LEVEL_ADJUSTMENT:
                return (
                    "Pass",
                    f"Cannot make reasonable bid at current auction level "
                    f"(suggested {original_bid}, would need {next_legal})."
                )
        except (ValueError, IndexError):
            # Not a level bid (e.g., Pass, X, XX) - no check needed
            pass

        return None

    @staticmethod
    def _check_point_requirements(bid: str, hand: Hand, auction_history: list) -> Optional[Tuple[str, str]]:
        """
        Check if we have sufficient points for the bid level.

        This is a conservative estimate based on our hand + typical partner range.
        More sophisticated analysis would consider partner's actual bids.

        Prevents: Bidding slam with only 15 HCP when partner unlikely to have 18+

        Args:
            bid: The adjusted bid to check
            hand: Our hand
            auction_history: Full auction

        Returns:
            (Pass, reason) if insufficient points, None otherwise
        """
        try:
            level = int(bid[0])

            # For slam bids, check if we could possibly have enough points
            if level == 6:
                # Small slam needs 33+ combined
                # Conservative estimate: assume partner has 15+ (we need 18+)
                if hand.hcp < 18:
                    return (
                        "Pass",
                        f"Insufficient points for small slam (have {hand.hcp} HCP, "
                        f"would need 18+ to make 33 combined likely)."
                    )

            elif level == 7:
                # Grand slam needs 37+ combined
                # Conservative estimate: assume partner has 20+ (we need 17+)
                if hand.hcp < 17:
                    return (
                        "Pass",
                        f"Insufficient points for grand slam (have {hand.hcp} HCP, "
                        f"would need 17+ to make 37 combined likely)."
                    )

        except (ValueError, IndexError):
            pass

        return None

    @staticmethod
    def _check_trump_requirements(bid: str, hand: Hand) -> Optional[Tuple[str, str]]:
        """
        Check if we have sufficient trump for suit contracts at game level.

        For 4M contracts, we need a fit. This checks if we have reasonable
        trump length.

        Prevents: Bidding 4♠ with only 2 spades

        Args:
            bid: The adjusted bid to check
            hand: Our hand

        Returns:
            (Pass, reason) if insufficient trump, None otherwise
        """
        if len(bid) < 2:
            return None

        try:
            level = int(bid[0])
            strain = bid[1:]

            # For 4-level major suit contracts, check trump
            if level == 4 and strain in ['♥', '♠']:
                # We need a fit - check our holding
                our_trump = hand.suit_lengths.get(strain, 0)

                # If we have fewer than 3, unlikely to have 8+ combined
                if our_trump < 3:
                    return (
                        "Pass",
                        f"Insufficient trump for {bid} contract "
                        f"(have only {our_trump} {strain})."
                    )

        except (ValueError, IndexError):
            pass

        return None

    @staticmethod
    def is_unreasonable_slam(bid: str, hand: Hand, partner_estimated_hcp: int = 15) -> bool:
        """
        Detect if a slam bid is unreasonable given our hand.

        This is used for monitoring and warnings, not blocking bids.

        Args:
            bid: The bid to check
            hand: Our hand
            partner_estimated_hcp: Conservative estimate of partner's HCP

        Returns:
            True if slam is unreasonable, False otherwise

        Example:
            >>> BidSafety.is_unreasonable_slam("6NT", hand_with_15_hcp, 15)
            True  # 30 combined < 33 required
        """
        try:
            level = int(bid[0])

            if level >= 6:
                combined_hcp = hand.hcp + partner_estimated_hcp

                if level == 6 and combined_hcp < BidSafety.SLAM_SMALL_MIN_HCP:
                    return True

                if level == 7 and combined_hcp < BidSafety.SLAM_GRAND_MIN_HCP:
                    return True

        except (ValueError, IndexError):
            pass

        return False

    @staticmethod
    def log_bid_adjustment(original_bid: str, adjusted_bid: str, reason: str, hand_hcp: int):
        """
        Log bid adjustments for analysis and debugging.

        This helps identify patterns of problematic adjustments.

        Args:
            original_bid: Original bid suggestion
            adjusted_bid: What it was adjusted to
            reason: Reason for adjustment
            hand_hcp: HCP of the hand making the bid

        Note:
            Currently prints to console. Future: send to logging system.
        """
        if adjusted_bid != original_bid and adjusted_bid != "Pass":
            level_diff = BidSafety._calc_level_difference(original_bid, adjusted_bid)

            # Only log if adjusted by 1+ levels (interesting cases)
            if level_diff > 0:
                severity = "⚠️" if level_diff >= 2 else "ℹ️"
                print(
                    f"{severity} [BID ADJUSTMENT] {original_bid} → {adjusted_bid} "
                    f"({level_diff} levels) | HCP: {hand_hcp} | {reason}"
                )

    @staticmethod
    def _calc_level_difference(bid1: str, bid2: str) -> int:
        """Calculate level difference between two bids."""
        try:
            return abs(int(bid2[0]) - int(bid1[0]))
        except (ValueError, IndexError):
            return 0
