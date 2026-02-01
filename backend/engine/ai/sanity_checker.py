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

    def check(self, bid: str, hand: Hand, features: Dict, auction: List, metadata: Optional[Dict] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Final sanity check before committing to bid.

        Args:
            bid: The proposed bid
            hand: The hand making the bid
            features: Extracted features from auction
            auction: List of previous bids
            metadata: Optional metadata from convention module (can contain bypass flags)

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

        # Check if metadata indicates this is a convention bid that should bypass sanity checks
        # Preempts, for example, are intentionally weak hands bidding at high levels
        # Takeout double responses also bypass - partner promises support
        #
        # IMPORTANT: Slam bids (6+) can NEVER bypass the Governor HCP check.
        # The Governor is non-overridable for slam validation.
        bid_level = int(bid[0]) if bid[0].isdigit() else 0
        if metadata and (metadata.get('bypass_hcp') or metadata.get('bypass_sanity_check')):
            convention = metadata.get('convention', 'unknown')
            # GOVERNOR OVERRIDE: Slam bids must always go through HCP validation
            if bid_level >= 6:
                logger.debug(f"Governor override: {convention} slam bid '{bid}' must pass HCP validation")
                # Fall through to Governor check below
            else:
                logger.debug(f"Sanity check bypassed for {convention} convention bid '{bid}'")
                return True, bid, None

        # Check if this is a Blackwood/control bid sequence
        # UPDATED: Allow bypass for:
        # 1. Ace responses (5♣/5♦/5♥/5♠ after 4NT)
        # 2. King responses (6♣/6♦/6♥/6♠ after 5NT)
        # 3. Slam signoff by the ASKER after receiving a Blackwood response
        # The "Physics of Information" principle: conventional responses provide
        # control information that supersedes raw HCP calculations
        if self._is_blackwood_sequence(auction):
            # Allow Blackwood ace responses (5-level after 4NT)
            if self._is_blackwood_response(bid, auction):
                return True, bid, None
            # Allow King-ask responses (6-level after 5NT)
            if self._is_king_ask_response(bid, auction):
                logger.debug(f"Allowing king-ask response '{bid}' - conventional bid bypasses Governor")
                return True, bid, None
            # Allow slam signoff by the ASKER after receiving response
            # This is the critical fix: the person who asked for aces can bid slam
            if self._is_slam_signoff_after_blackwood(bid, auction):
                logger.debug(f"Allowing slam signoff '{bid}' after Blackwood response - asker's decision")
                return True, bid, None
            # For other slam bids, fall through to Governor check below

        # Check if this is a Jacoby transfer super-accept sequence - allow game acceptance
        if self._is_jacoby_super_accept_sequence(auction):
            # Partner super-accepted, showing max (17 HCP) with 4+ card support
            # Game is appropriate with any hand
            return True, bid, None

        # bid_level already extracted above for Governor override check

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

        # Check 4: SLAM SAFETY GOVERNOR - Hard HCP floor validation
        # The Physics of Resources: Slam requires specific HCP thresholds
        # - Small Slam (6-level): 33+ combined HCP
        # - Grand Slam (7-level): 37+ combined HCP
        # This is the "Governor" - a non-overridable hard limit
        if bid_level >= 6:
            # Calculate hard ceiling: our HCP + partner's max realistic HCP
            hard_ceiling = self._calculate_hard_ceiling(hand, features, auction)

            # Also get optimistic estimate for comparison/logging
            estimated_combined = self._estimate_combined_hcp(hand, features, auction)

            # Use the LOWER of the two estimates (conservative)
            combined = min(hard_ceiling, estimated_combined)

            # Set thresholds based on slam level
            if bid_level == 7:
                min_required = 37  # Grand slam needs 37+ HCP
                slam_type = "Grand slam"
            else:
                min_required = 33  # Small slam needs 33+ HCP
                slam_type = "Small slam"

            # Allow slight distribution bonus ONLY with confirmed fit
            auction_context = features.get('auction_context')
            distribution_bonus = 0
            if auction_context is not None and auction_context.has_fit:
                distribution_bonus = min(hand.total_points - hand.hcp, 2)

            adjusted_combined = combined + distribution_bonus

            if adjusted_combined < min_required:
                reason = (f"{slam_type} blocked by Governor: "
                         f"{combined} combined HCP + {distribution_bonus} distribution = "
                         f"{adjusted_combined} (need {min_required}+)")
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

        # Bonus for distribution points when we have a fit
        # This helps reach game when we have shape but fewer HCP
        auction_context = features.get('auction_context')
        if auction_context is not None and auction_context.has_fit:
            # Add 1-2 points for distribution when fit is established
            distribution_bonus = min(hand.total_points - hand.hcp, 2)
            combined_hcp += distribution_bonus

        # Find appropriate max level
        for (min_hcp, max_hcp), max_level in self.MAX_BID_LEVELS.items():
            if min_hcp <= combined_hcp <= max_hcp:
                return max_level

        return 2  # Conservative default

    def _get_my_seat(self, features: Dict) -> str:
        """Extract my seat (short form) from features for BiddingState lookup."""
        positions = features.get('positions', [])
        my_index = features.get('my_index')
        if positions and my_index is not None:
            from utils.seats import normalize
            return normalize(positions[my_index])
        return None

    def _estimate_combined_hcp(self, hand: Hand, features: Dict, auction: List) -> int:
        """
        Estimate combined partnership HCP.

        Uses BiddingState (per-seat beliefs) when available, then
        AuctionContext for range tracking, falls back to legacy estimation.
        """
        my_hcp = hand.hcp

        # Use BiddingState if available and partner's range is meaningfully narrowed
        bidding_state = features.get('bidding_state')
        if bidding_state is not None:
            my_seat = self._get_my_seat(features)
            if my_seat:
                partner_belief = bidding_state.partner_of(my_seat)
                spread = partner_belief.hcp[1] - partner_belief.hcp[0]
                if spread <= 25:  # Range has been narrowed from default (0,40)
                    partner_estimate = (partner_belief.hcp[0] + partner_belief.hcp[1]) // 2
                    return my_hcp + partner_estimate

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

    def _calculate_hard_ceiling(self, hand: Hand, features: Dict, auction: List) -> int:
        """
        Calculate hard ceiling for combined HCP.

        This is a CONSERVATIVE estimate used by the Governor to prevent
        slam bids with insufficient resources. Unlike _estimate_combined_hcp
        which uses midpoint (optimistic), this uses realistic maximums.

        Logic:
        - Our HCP is known exactly
        - Partner's max is bounded by their bidding:
          * 1-level opener: max 21 HCP
          * 1NT opener: max 17 HCP
          * 2♣ opener: max 25 HCP (but then we have controls)
          * Simple response: max 12 HCP (forcing) or 10 HCP (non-forcing)
          * Jump shift response: max 18 HCP

        The key insight: partner's range should be capped at realistic values,
        not 40 which inflates the midpoint estimate.
        """
        my_hcp = hand.hcp

        # Use BiddingState if available and partner's range is meaningfully narrowed
        bidding_state = features.get('bidding_state')
        if bidding_state is not None:
            my_seat = self._get_my_seat(features)
            if my_seat:
                partner_belief = bidding_state.partner_of(my_seat)
                spread = partner_belief.hcp[1] - partner_belief.hcp[0]
                if spread <= 25:  # Range has been narrowed from default (0,40)
                    partner_max = partner_belief.hcp[1]
                    return my_hcp + partner_max

        # Use AuctionContext if available
        auction_context = features.get('auction_context')
        if auction_context is not None:
            ranges = auction_context.ranges
            auction_features = features.get('auction_features', {})
            opener_relationship = auction_features.get('opener_relationship')

            if opener_relationship == 'Me':
                # I opened, partner is responder
                # Cap partner's max at realistic response values
                partner_max = ranges.responder_hcp[1] if ranges.responder_hcp else 18
                # Responses rarely exceed 18 HCP (even jump shifts)
                partner_max = min(partner_max, 18)
            elif opener_relationship == 'Partner':
                # Partner opened, I'm responder
                partner_max = ranges.opener_hcp[1] if ranges.opener_hcp else 21
                # Opening bids cap at 21 for 1-level (except 2♣)
                # Check if partner opened 2♣
                opening_bid = auction_features.get('opening_bid', '')
                if opening_bid == '2♣':
                    partner_max = min(partner_max, 25)
                elif opening_bid == '2NT':
                    partner_max = min(partner_max, 22)
                elif opening_bid == '1NT':
                    partner_max = min(partner_max, 17)
                else:
                    partner_max = min(partner_max, 21)
            else:
                # Competitive - very conservative
                partner_max = 15

            return my_hcp + partner_max

        # Legacy fallback - very conservative
        partner_max_hcp = self._estimate_partner_max_hcp(features, auction)
        return my_hcp + partner_max_hcp

    def _estimate_partner_max_hcp(self, features: Dict, auction: List) -> int:
        """
        Conservative estimate of partner's maximum HCP.

        Used for hard ceiling calculation when AuctionContext unavailable.
        """
        auction_features = features.get('auction_features', features)
        opener_relationship = auction_features.get('opener_relationship') or auction_features.get('opener')

        # If partner opened
        if opener_relationship and opener_relationship.lower() == 'partner':
            for bid in auction:
                if bid == "Pass":
                    continue
                if bid == "1NT":
                    return 17  # 1NT opening (15-17 HCP)
                if bid == "2NT":
                    return 22  # 2NT opening (20-22 HCP)
                if bid == "2♣":
                    return 25  # Strong 2♣ (22+ HCP)
                if bid.startswith("1"):
                    return 21  # Standard 1-level opening max
            return 21

        # If I opened and partner responded
        if opener_relationship and opener_relationship.lower() == 'me':
            # Simple responses max at 12-15 HCP
            # Jump shifts max at 18 HCP
            return 18

        # Competitive - very conservative
        return 15

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
                # Check specific NT openings FIRST (before general 1-level check)
                if bid == "1NT":
                    return 15  # 1NT opening (15-17 HCP)
                if bid == "2NT":
                    return 20  # 2NT opening (20-21 HCP)
                if bid == "2♣":
                    return 22  # Strong 2♣ (22+ HCP)
                if bid.startswith("1"):
                    return 13  # Standard 1-level opening
            return 13  # Default opening strength

        # If I opened and partner responded (case-insensitive)
        if opener_relationship and opener_relationship.lower() == 'me' and len(partner_bids) > 0:
            # Get partner's non-pass bids
            partner_nonpass_bids = [b for b in partner_bids if b != 'Pass']

            if len(partner_nonpass_bids) == 0:
                return 0  # Partner only passed

            # Check for game-forcing first responses (applies even with single bid)
            # 3NT response to suit opening = 13-15 HCP balanced
            if '3NT' in partner_nonpass_bids:
                return 13  # Game values

            # 2NT response over major (Jacoby) = 13+ with support
            # 2NT response over minor = natural invitational 11-12
            if '2NT' in partner_nonpass_bids:
                opening_bid = auction_features.get('opening_bid', '')
                if opening_bid and opening_bid[1] in ['♥', '♠']:
                    return 13  # Jacoby 2NT
                return 11  # Natural invitational

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

                # Note: 2NT and 3NT are already checked above (before len>=2 check)

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

        Blackwood is indicated by:
        1. Someone bid 4NT (asking for aces) - NOT after 1NT/2NT/3NT opening without suit shown
        2. A 5-level response (5♣/5♦/5♥/5♠) followed 4NT
        3. The current bid follows a Blackwood response (signoff phase)

        4NT is QUANTITATIVE (NOT Blackwood) when:
        - The auction has been purely NT-based (1NT-4NT or 2NT-4NT with no suit shown)

        This is critical for allowing slam signoff after Blackwood responses.
        """
        has_4nt = False
        has_blackwood_response = False
        nt_only_auction = True  # Track if auction is pure NT

        # Check if any suit was shown (makes 4NT = Blackwood)
        for bid in auction:
            if bid in ['Pass', 'X', 'XX']:
                continue
            if len(bid) >= 2 and bid[0].isdigit() and bid[1] in '♣♦♥♠':
                nt_only_auction = False
                break

        for i, bid in enumerate(auction):
            # Check for 4NT
            if bid == "4NT":
                # 4NT is Blackwood unless it's a pure NT auction (1NT-4NT, 2NT-4NT)
                if not nt_only_auction:
                    has_4nt = True
                # Even in NT auctions, if responder showed a suit, 4NT is Blackwood
                # Example: 1NT - 2♥(transfer) - 2♠ - 4NT is Blackwood for spades

            # Check for Blackwood responses (5♣, 5♦, 5♥, 5♠ after 4NT)
            if len(bid) >= 2 and bid[0] == '5' and bid[1] in '♣♦♥♠':
                # Check if 4NT was bid earlier
                if has_4nt:
                    has_blackwood_response = True

            # Check for 5NT (king ask) - definitely a slam sequence
            if bid == "5NT" and has_4nt:
                return True

        # If we have 4NT followed by a Blackwood response, this is a Blackwood sequence
        # The ASKER is now allowed to bid slam (6/7 level)
        if has_4nt and has_blackwood_response:
            return True

        # If we just have 4NT with no response yet, it's still a potential Blackwood sequence
        # Allow the response to come through
        if has_4nt:
            return True

        return False

    def _is_blackwood_response(self, bid: str, auction: List) -> bool:
        """
        Check if the current bid is a Blackwood ace-showing response.

        Returns True for:
        - 5♣/5♦/5♥/5♠ immediately after 4NT (ace-showing responses)
        - 5NT (king ask)

        These conventional responses should bypass HCP checks.
        Slam bids (6/7 level) should NOT bypass - they're subject to Governor.
        """
        # 5NT is always a Blackwood continuation (king ask)
        if bid == "5NT":
            return True

        # Check for 5-level ace responses after 4NT
        if len(bid) >= 2 and bid[0] == '5' and bid[1] in '♣♦♥♠':
            # Only count as Blackwood response if 4NT was bid recently
            # (within the last few bids, allowing for passes)
            recent_bids = auction[-6:] if len(auction) >= 6 else auction
            for past_bid in recent_bids:
                if past_bid == '4NT':
                    return True

        return False

    def _is_king_ask_response(self, bid: str, auction: List) -> bool:
        """
        Check if the current bid is a response to the 5NT King-ask.

        Returns True for:
        - 6♣ = 0 kings
        - 6♦ = 1 king
        - 6♥ = 2 kings
        - 6♠ = 3 kings

        These are conventional responses and should bypass the HCP Governor.
        """
        # Must be 6-level suit bid
        if len(bid) < 2 or bid[0] != '6' or bid[1] not in '♣♦♥♠':
            return False

        # Check if 5NT (king ask) was bid earlier in the auction
        for past_bid in auction:
            if past_bid == '5NT':
                return True

        return False

    def _is_slam_signoff_after_blackwood(self, bid: str, auction: List) -> bool:
        """
        Check if this is the Blackwood ASKER bidding slam after receiving a response.

        This is critical: the person who bid 4NT (asking for aces) should be
        allowed to bid slam (6-level) based on the information received,
        regardless of the raw HCP calculation.

        Pattern detection:
        - 4NT was bid
        - A 5-level response was given (5♣/5♦/5♥/5♠)
        - Current bid is 6-level (slam)
        - The current bidder is the same seat as the 4NT bidder (the asker)

        We approximate this by checking if:
        1. 4NT was bid
        2. A Blackwood response was given
        3. Current bid is 6-level
        """
        # Must be 6 or 7 level bid
        if len(bid) < 1 or bid[0] not in '67':
            return False

        has_4nt = False
        has_blackwood_response = False
        nt_4_index = -1

        for i, past_bid in enumerate(auction):
            if past_bid == '4NT':
                has_4nt = True
                nt_4_index = i
            # Check for Blackwood response (5♣/5♦/5♥/5♠)
            if len(past_bid) >= 2 and past_bid[0] == '5' and past_bid[1] in '♣♦♥♠':
                if has_4nt:
                    has_blackwood_response = True

        # If we have 4NT followed by a response, allow the slam bid
        # The engine is the asker making a decision based on ace count
        if has_4nt and has_blackwood_response:
            return True

        # Also allow if 5NT king ask was made (implies all aces held)
        if '5NT' in auction:
            return True

        return False

    def _is_jacoby_super_accept_sequence(self, auction: List) -> bool:
        """
        Check if this is a Jacoby transfer super-accept sequence.

        Super-accept patterns:
        - 1NT - Pass - 2♦ - Pass - 3♥ (hearts super-accept)
        - 1NT - Pass - 2♥ - Pass - 3♠ (spades super-accept)

        When partner super-accepts, they show max (17 HCP) with 4+ card support.
        Game is appropriate with any hand, even 0 HCP.
        """
        # Need at least 6 bids to have super-accept pattern
        if len(auction) < 6:
            return False

        # Check for 1NT opening
        if auction[0] != '1NT':
            return False

        # Check for heart super-accept: 1NT - Pass - 2♦ - Pass - 3♥
        if auction[2] == '2♦' and auction[4] == '3♥':
            return True

        # Check for spade super-accept: 1NT - Pass - 2♥ - Pass - 3♠
        if auction[2] == '2♥' and auction[4] == '3♠':
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
