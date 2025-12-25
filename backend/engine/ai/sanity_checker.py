"""
Sanity Checker for Bidding Decisions

Final safety net that prevents impossible contracts and runaway auctions.
Runs AFTER validation to catch strategic errors that are technically legal
but practically unsound.

Part of ADR-0002: Bidding System Robustness Improvements
Layer 3: Sanity Check Layer
"""

import logging
from typing import Tuple, Optional, Dict, List
from engine.hand import Hand

logger = logging.getLogger(__name__)


class SanityChecker:
    """
    Post-decision sanity checking to prevent catastrophic auctions.

    Checks if bid makes strategic sense given partnership strength,
    preventing scenarios like:
    - 1NT → 5♦ with inadequate combined HCP
    - Game bids without sufficient strength
    - Competitive bidding spiraling out of control

    Usage:
        checker = SanityChecker()
        should_bid, final_bid, reason = checker.check(bid, hand, features, auction)
        if not should_bid:
            return (final_bid, reason)  # Usually Pass
    """

    # Maximum safe bid levels by estimated combined HCP
    # Bridge rule of thumb: Game needs ~25 points with fit, 26 without
    # Adjusted thresholds to allow game bidding at 24+ with fit
    MAX_BID_LEVELS = {
        (0, 19): 2,     # Part score only (< 20 HCP)
        (20, 23): 3,    # Low invitational (20-23 HCP)
        (24, 32): 4,    # Game level (24+ HCP with fit, 26+ without)
        (33, 36): 5,    # Small slam possible (33-36 HCP)
        (37, 40): 6,    # Small slam (37+ HCP)
        (41, 100): 7,   # Grand slam (very rare)
    }

    def __init__(self):
        self._enabled = True

    def check(self, bid: str, hand: Hand, features: Dict, auction: List) -> Tuple[bool, str, Optional[str]]:
        """
        Final sanity check before committing to bid.

        Args:
            bid: The proposed bid
            hand: The hand making the bid
            features: Extracted features from auction
            auction: List of previous bids

        Returns:
            (should_bid, final_bid, reason)
            - should_bid: True if bid is sane, False to override
            - final_bid: The bid to actually make (usually "Pass" if override)
            - reason: Explanation for override, or None if approved
        """
        if not self._enabled:
            return True, bid, None

        # Pass is always sane
        if bid == "Pass":
            return True, bid, None

        # Doubles/Redoubles are special - allow them
        if bid in ["X", "XX"]:
            return True, bid, None

        # Check if this is a Blackwood/control bid sequence - allow slam bidding
        if self._is_blackwood_sequence(auction):
            # In Blackwood sequences, allow all bids (the convention module handles appropriateness)
            return True, bid, None

        # Extract bid level
        bid_level = int(bid[0])

        # Check 1: Maximum bid level based on HCP
        max_level = self._get_max_safe_level(hand, features, auction)
        if bid_level > max_level:
            reason = f"Bid level {bid_level} exceeds safe maximum {max_level} for partnership strength"
            logger.warning(f"Sanity check prevented: {reason}")
            return False, "Pass", reason

        # Check 2: Trump fit for high-level suit contracts
        if bid_level >= 4 and not bid.endswith("NT"):
            has_fit = self._check_trump_fit(bid, hand, features, auction)
            if not has_fit:
                reason = "No trump fit for game-level suit contract"
                logger.warning(f"Sanity check prevented: {reason}")
                return False, "Pass", reason

        # Check 3: Stop competitive bidding at dangerous levels
        if self._is_competitive(features) and bid_level >= 4:
            if hand.hcp < 12:
                reason = f"Too high in competitive auction with {hand.hcp} HCP (need 12+ for 4-level)"
                logger.warning(f"Sanity check prevented: {reason}")
                return False, "Pass", reason

        # Check 4: Slam bidding requires combined 33+ HCP
        if bid_level >= 6:
            estimated_combined = self._estimate_combined_hcp(hand, features, auction)
            if estimated_combined < 33:
                reason = f"Slam bid with estimated {estimated_combined} combined HCP (need 33+)"
                logger.warning(f"Sanity check prevented: {reason}")
                return False, "Pass", reason

        return True, bid, None

    def _get_max_safe_level(self, hand: Hand, features: Dict, auction: List) -> int:
        """
        Calculate maximum safe bid level based on partnership strength.

        This prevents 1NT → 5♦ type disasters where partnership lacks
        sufficient combined strength.
        """
        # Estimate combined HCP
        combined_hcp = self._estimate_combined_hcp(hand, features, auction)

        # Find appropriate max level
        for (min_hcp, max_hcp), max_level in self.MAX_BID_LEVELS.items():
            if min_hcp <= combined_hcp <= max_hcp:
                return max_level

        return 2  # Conservative default

    def _estimate_combined_hcp(self, hand: Hand, features: Dict, auction: List) -> int:
        """
        Estimate combined partnership HCP.

        Uses AuctionContext for accurate range tracking when available,
        falls back to legacy estimation otherwise.
        """
        my_hcp = hand.hcp

        # Use AuctionContext if available (expert-level range tracking)
        auction_context = features.get('auction_context')
        if auction_context is not None:
            ranges = auction_context.ranges
            auction_features = features.get('auction_features', {})
            opener_relationship = auction_features.get('opener_relationship')

            if opener_relationship == 'Me':
                # I opened, partner responded
                partner_min = ranges.responder_hcp[0]
                partner_max = ranges.responder_hcp[1]
            elif opener_relationship == 'Partner':
                # Partner opened, I'm responding
                partner_min = ranges.opener_hcp[0]
                partner_max = ranges.opener_hcp[1]
            else:
                # Competitive auction - use legacy estimation
                partner_min = self._estimate_partner_hcp(features, auction)
                partner_max = partner_min + 10

            # Use midpoint for better game decisions
            # (minimum was too conservative, causing missed games)
            partner_estimate = (partner_min + partner_max) // 2
            return my_hcp + partner_estimate

        # Fall back to legacy estimation
        partner_min_hcp = self._estimate_partner_hcp(features, auction)
        return my_hcp + partner_min_hcp

    def _estimate_partner_hcp(self, features: Dict, auction: List) -> int:
        """
        Estimate partner's minimum HCP from auction.

        Conservative estimates to avoid overbidding.
        """
        # Support both flat and nested feature formats
        auction_features = features.get('auction_features', features)
        opener_relationship = auction_features.get('opener_relationship') or auction_features.get('opener')
        partner_bids = auction_features.get('partner_bids', [])

        # If partner opened (case-insensitive)
        if opener_relationship and opener_relationship.lower() == 'partner':
            # Find partner's opening bid
            for bid in auction:
                if bid == "Pass":
                    continue
                if bid.startswith("1"):
                    return 13  # Standard opening
                if bid == "1NT":
                    return 15  # 1NT opening
                if bid == "2NT":
                    return 20  # 2NT opening
                if bid == "2♣":
                    return 22  # Strong 2♣
            return 13  # Default opening strength

        # If I opened and partner responded (case-insensitive)
        if opener_relationship and opener_relationship.lower() == 'me' and len(partner_bids) > 0:
            # Get partner's non-pass bids
            partner_nonpass_bids = [b for b in partner_bids if b != 'Pass']

            if len(partner_nonpass_bids) == 0:
                return 0  # Partner only passed

            # If partner bid at 2-level after I rebid 1NT, that's invitational (10-11 HCP)
            # Example: 1♥-1♠-1NT-2♦ shows 10-11 HCP
            if len(partner_nonpass_bids) >= 2:
                # Check if I bid 1NT and partner then bid at 2-level
                my_bids = [bid for i, bid in enumerate(auction)
                          if features['positions'][i % 4] == features['positions'][features['my_index']]
                          and bid not in ['Pass', 'X', 'XX']]

                if '1NT' in my_bids and any(b.startswith('2') for b in partner_nonpass_bids[1:]):
                    return 10  # Invitational values (10-11 HCP)

                # If I bid 2NT and partner bid at 3-level, that's game-forcing or preference (12+ HCP)
                # Example: 1♦-1♥-2NT-3♦ shows 12+ HCP
                if '2NT' in my_bids and any(b.startswith('3') for b in partner_nonpass_bids[1:]):
                    return 12  # Game-forcing values (12+ HCP)

                # If I rebid my suit and partner raised to 3-level, that's invitational (10-12 HCP)
                # Example: 1♥-1♠-2♥-3♥ shows 10-12 HCP
                if len(my_bids) >= 2 and len(partner_nonpass_bids) >= 2:
                    # Check if I rebid my opening suit and partner raised it
                    if len(my_bids[0]) >= 2 and len(my_bids[1]) >= 2:
                        if my_bids[0][1] == my_bids[1][1]:  # Same suit
                            # Check if partner raised to 3-level
                            if any(b.startswith('3') and len(b) >= 2 and b[1] == my_bids[0][1]
                                  for b in partner_nonpass_bids[1:]):
                                return 10  # Invitational values (10-12 HCP)

                # If partner bid 2NT, that's invitational (11-12 HCP)
                if '2NT' in partner_nonpass_bids:
                    return 11  # Invitational 2NT

                # If partner bid 3NT, that's game values (13+ HCP)
                if '3NT' in partner_nonpass_bids:
                    return 13  # Game values

            # Standard 1-level response
            return 6  # Minimum response

        # If partner overcalled (case-insensitive)
        if opener_relationship and opener_relationship.lower() == 'opponent' and len(auction) >= 2:
            return 8  # Overcall minimum

        # Partner hasn't bid yet or passed
        return 0  # Assume nothing

    def _check_trump_fit(self, bid: str, hand: Hand, features: Dict, auction: List) -> bool:
        """
        Check if partnership has trump fit for suit contract.

        For game-level suit contracts (4♥, 4♠, 5♣, 5♦), need 8+ combined trumps.
        """
        suit = bid[1:]
        my_length = hand.suit_lengths.get(suit, 0)

        # If I have 5+, assume partner has at least 3 (raise support)
        if my_length >= 5:
            return True

        # If this is a raise, assume we have fit
        if self._is_raise(suit, auction):
            return True

        # If I have 4 and partner opened/bid this suit
        if my_length >= 4 and self._partner_bid_suit(suit, features, auction):
            return True

        # Otherwise, no clear fit
        return False

    def _is_raise(self, suit: str, auction: List) -> bool:
        """Check if current bid is raising partner's suit."""
        if len(auction) < 2:
            return False

        # Look for partner's last suit bid
        for bid in reversed(auction[:-1]):
            if bid == "Pass" or bid in ["X", "XX"]:
                continue
            if not bid[0].isdigit():
                continue
            if bid.endswith(suit):
                return True

        return False

    def _partner_bid_suit(self, suit: str, features: Dict, auction: List) -> bool:
        """Check if partner has bid this suit."""
        # Simple check: look for suit in auction
        for bid in auction:
            if bid.endswith(suit) and bid != "Pass":
                return True
        return False

    def _is_blackwood_sequence(self, auction: List) -> bool:
        """
        Check if this is a Blackwood or control-bid sequence.

        If 4NT or 5NT appears in the auction (and isn't an opening or overcall),
        this is likely Blackwood asking for aces/kings.
        """
        for i, bid in enumerate(auction):
            # Check for 4NT Blackwood (not as opening, and after game-level bidding)
            if bid == "4NT" and i > 0:
                # 4NT after some bidding is Blackwood
                return True
            # Check for 5NT (king ask after Blackwood)
            if bid == "5NT" and i > 0:
                return True
            # Check for 5-level ace responses (5♣, 5♦, 5♥, 5♠)
            if i > 0 and len(bid) >= 2 and bid[0] == '5' and bid != '5NT':
                # Check if previous bid was 4NT
                prev_bids = [b for b in auction[:i] if b != 'Pass']
                if prev_bids and prev_bids[-1] == '4NT':
                    return True
        return False

    def _is_competitive(self, features: Dict) -> bool:
        """Check if auction is competitive (opponents bidding)."""
        # Support both 'competitive_auction' and nested 'is_contested'
        if 'competitive_auction' in features:
            return features['competitive_auction']
        auction_features = features.get('auction_features', {})
        return auction_features.get('is_contested', False)

    def disable(self):
        """Disable sanity checking (for testing only)."""
        self._enabled = False
        logger.warning("Sanity checker DISABLED (should only be for testing)")

    def enable(self):
        """Enable sanity checking."""
        self._enabled = True
