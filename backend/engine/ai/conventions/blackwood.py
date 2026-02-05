from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict

class BlackwoodConvention(ConventionModule):
    """
    Playbook for Blackwood, including 4NT (aces) and 5NT (kings).
    """
    def get_constraints(self) -> Dict:
        """Defines requirements for a hand that might ask for aces."""
        return {'hcp_range': (18, 40)}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation function with bid validation."""
        auction_history = features.get('auction_history', [])

        # Get the raw blackwood bid
        result = self._evaluate_blackwood(hand, features)

        if not result:
            return None

        # Handle both 2-tuple (bid, explanation) and 3-tuple (bid, explanation, metadata)
        if len(result) == 3:
            bid, explanation, metadata = result
        else:
            bid, explanation = result
            metadata = {}

        # Always pass Pass bids through
        if bid == "Pass":
            return (bid, explanation, metadata) if metadata else (bid, explanation)

        # Validate the bid is legal
        if BidValidator.is_legal_bid(bid, auction_history):
            # Return 3-tuple if we have metadata (for artificial bid bypass)
            return (bid, explanation, metadata) if metadata else (bid, explanation)

        # Bid is illegal - try to find next legal bid of same strain
        next_legal = get_next_legal_bid(bid, auction_history, max_level_jump=1)
        if next_legal:
            # SANITY CHECK: If adjustment is more than 1 level, something is wrong
            # This is especially critical for Blackwood where 5NT→7NT could happen
            try:
                original_level = int(bid[0])
                adjusted_level = int(next_legal[0])

                if adjusted_level - original_level > 1:
                    # The suggested bid is way off - pass instead of bidding unreasonable slam
                    return ("Pass", f"Cannot make reasonable bid at current auction level (suggested {bid}, would need {next_legal}).")
            except (ValueError, IndexError):
                # Not a level bid (e.g., Pass, X, XX) - allow adjustment
                pass

            adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
            # Preserve metadata for adjusted bids (still artificial)
            return (next_legal, adjusted_explanation, metadata) if metadata else (next_legal, adjusted_explanation)

        # No legal bid possible - pass
        return None

    def _evaluate_blackwood(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates blackwood bid without validation."""
        # Check for signoff after receiving ace response
        if self._is_signoff_applicable(features):
            return self._get_signoff_bid(hand, features)
        # Check for answering Blackwood
        if self._is_ace_answering_applicable(features):
            return self._get_ace_answer_bid(hand)
        # Check for king-asking (5NT)
        if self._is_king_asking_applicable(hand, features):
            return self._get_king_ask_bid()
        # Check for answering king ask
        if self._is_king_answering_applicable(features):
            return self._get_king_answer_bid(hand)
        # Check for asking aces
        if self._is_ace_asking_applicable(hand, features):
            return self._get_ace_ask_bid()
        return None

    def _is_ace_asking_applicable(self, hand: Hand, features: Dict) -> bool:
        """Determines if this hand should ask for aces."""
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        if not partner_last_bid: return False

        auction_history = features.get('auction_history', [])
        my_position = features['positions'][features['my_index']]

        # Get my previous bids to understand auction context
        my_previous_bids = [bid for i, bid in enumerate(auction_history)
                           if features['positions'][i % 4] == my_position
                           and bid not in ['Pass', 'X', 'XX']]

        # Don't trigger Blackwood after 2NT rebid + partner's 3-level preference
        # Example: 1♥-1♠-2NT-3♥ is just preference, not a slam try
        if '2NT' in my_previous_bids and partner_last_bid[0] == '3':
            return False

        # Don't trigger after 1NT rebid + partner's invitational bid
        # Example: 1♥-1♠-1NT-2♦ is invitational, not slam interest
        if '1NT' in my_previous_bids and partner_last_bid[0] in ['2', '3']:
            return False

        # Use AuctionContext for accurate combined strength assessment
        auction_context = features.get('auction_context')
        estimated_combined = 0
        if auction_context is not None:
            estimated_combined = auction_context.ranges.combined_midpoint
        else:
            # Fallback: estimate from auction features
            partner_total_points = features['auction_features'].get('partner_total_points', 0)
            estimated_combined = hand.total_points + partner_total_points

        # MINIMUM HCP requirement for Blackwood
        # Lower threshold when combined strength clearly indicates slam
        # With 33+ combined, we can trigger with 14+ HCP (partner has extras)
        if hand.hcp < 14:
            return False
        if hand.hcp < 16 and estimated_combined < 33:
            return False

        # Strong direct jump raises (e.g., 1♥ - 4♥) indicate slam interest
        # This is a jump to 4-level showing strong support (13-15 pts typically)
        if len(my_previous_bids) == 1 and partner_last_bid[0] == '4' and len(partner_last_bid) == 2:
            partner_suit = partner_last_bid[1]
            # Partner jumped to game in our suit - they have 13-15 pts with fit
            # With 17+ total points ourselves, combined is 30+, explore slam
            if hand.total_points >= 17:
                return True
            # With fit and 33+ estimated combined, explore slam
            if estimated_combined >= 33:
                return True

        # After game-forcing sequence at 3-level, check for slam exploration
        # Example: 1♥ - 2♣ - 2♥ - 3♥ (responder showed game-forcing values and raised)
        if partner_last_bid[0] == '3' and len(partner_last_bid) == 2:
            partner_suit = partner_last_bid[1]
            # Check if partner raised our suit at 3-level (shows extras/slam interest)
            if len(my_previous_bids) >= 1:
                my_first_suit = my_previous_bids[0][1] if len(my_previous_bids[0]) >= 2 else None
                if my_first_suit == partner_suit:
                    # Partner raised our suit - check combined values for slam
                    # Need 32+ combined points AND a strong hand for Blackwood
                    if estimated_combined >= 32 and hand.total_points >= 16:
                        return True
                    # Very strong opener (18+) can explore slam if combined is close (30+)
                    if hand.total_points >= 18 and estimated_combined >= 30:
                        return True

        # After partner's JUMP SHIFT (game-forcing, 17+ pts)
        # A jump shift means partner BID A NEW SUIT ONE LEVEL HIGHER than necessary.
        # Over 1♣: 1♦, 1♥, 1♠ are all 1-level responses (6+ pts)
        #          2♦ is a NORMAL 2-level response (10+ pts, not a jump)
        #          2♥, 2♠ are JUMP SHIFTS (could have bid 1♥/1♠)
        # Over 1♦: 1♥, 1♠ are 1-level responses
        #          2♣ is a NORMAL 2-level response (lower suit, needs 10+)
        #          2♥, 2♠ are JUMP SHIFTS (could have bid 1♥/1♠)
        # Over 1♥: 1♠ is a 1-level response
        #          2♣, 2♦ are NORMAL 2-level responses
        #          2♠ is a JUMP SHIFT (could have bid 1♠)
        # Over 1♠: 2♣, 2♦, 2♥ are all NORMAL 2-level responses (no jump shifts available)
        if len(my_previous_bids) >= 1 and len(partner_last_bid) == 2:
            partner_level = int(partner_last_bid[0]) if partner_last_bid[0].isdigit() else 0
            my_opening_level = int(my_previous_bids[0][0]) if my_previous_bids[0][0].isdigit() else 0

            if my_opening_level == 1 and partner_level == 2:
                partner_suit = partner_last_bid[1]
                my_suit = my_previous_bids[0][1] if len(my_previous_bids[0]) >= 2 else None

                # A jump shift is when partner could have bid their suit at 1-level but chose 2-level
                # Partner can bid at 1-level if their suit ranks HIGHER than opener's suit
                # (because bidding goes in order: ♣ → ♦ → ♥ → ♠ → NT → 2♣ → ...)
                suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
                my_suit_rank = suit_rank.get(my_suit, 0)
                partner_suit_rank = suit_rank.get(partner_suit, 0)

                # Partner could have bid at 1-level ONLY IF their suit ranks higher than opener's
                # 1♣ - 2♦: ♦(2) > ♣(1)? YES, but 1♦ over 1♣ is illegal (must go up in suit rank)
                # Actually, 1♦ IS legal over 1♣! So 2♦ is a jump shift... NO WAIT.
                # I'm confusing myself. Let's be clear:
                # - After 1♣, you CAN bid 1♦ (it's legal - new suit at same level, higher rank)
                # - So 2♦ over 1♣ IS technically a jump... but in practice it's used for 10+ hands
                # - The STRONG jump shifts are 2♥ and 2♠ (majors, 17+ pts)
                # - 2♦ over 1♣ is often used as a simple 2-over-1 response (10+ pts)

                # For safety, only treat MAJOR SUIT jumps as slam-interest jump shifts
                # Minor suit 2-level bids (2♣, 2♦) are typically 2-over-1 showing 10+ pts
                is_major_jump_shift = partner_suit in ['♥', '♠'] and partner_suit_rank > my_suit_rank

                if is_major_jump_shift and partner_suit != my_suit and hand.total_points >= 17:
                    return True

        # High combined values warrant slam exploration (33+ combined)
        # BUT only if there's a clear trump fit (partner raised our suit)
        if estimated_combined >= 33:
            # Partner has raised our suit or we have clear fit
            is_raise = len(my_previous_bids) >= 1 and len(partner_last_bid) >= 2 and partner_last_bid[1:] == my_previous_bids[0][1:]
            if is_raise and partner_last_bid[0] in ['3', '4']:
                return True
            # Without explicit raise, DON'T use Blackwood - estimates can be unreliable
            # Partner showing preference (e.g., 3♠ after 1♦-1♠-3♦) is NOT a raise

        return False

    def _get_ace_ask_bid(self) -> Tuple[str, str]:
        """Returns the 4NT ace-asking bid."""
        return ("4NT", "Blackwood convention, asking for aces.")

    def _is_ace_answering_applicable(self, features: Dict) -> bool:
        """
        Determines if we are responding to a 4NT Blackwood bid.

        4NT is Blackwood (not quantitative) if:
        1. There's a clear suit agreement (opener showed a suit), OR
        2. The auction suggests slam interest (strong hand shown)

        4NT is quantitative (NOT Blackwood) if:
        - Partner opened NT and later bid 4NT with no suit shown
        - No clear suit agreement anywhere in the auction
        """
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        if partner_last_bid != '4NT':
            return False

        auction_history = features.get('auction_history', [])
        if not auction_history:
            return False

        # Find partner's bids in the auction
        my_index = features.get('my_index', 0)
        partner_index = (my_index + 2) % 4

        partner_bids = [
            bid for i, bid in enumerate(auction_history)
            if (i % 4) == partner_index and bid not in ['Pass', 'X', 'XX']
        ]

        # Check if partner actually opened the bidding (was the first non-Pass bid)
        # Find the first non-Pass bid in the auction
        first_bid_index = next((i for i, bid in enumerate(auction_history) if bid != 'Pass'), None)
        partner_actually_opened = first_bid_index is not None and (first_bid_index % 4) == partner_index

        # FIRST: Check for suit agreement - this OVERRIDES quantitative NT considerations
        # If there's any suit shown in the auction, 4NT is Blackwood asking for aces
        # Example: 1NT - 2♥(transfer) - 2♠ - 4♠ - 4NT → Blackwood for spades (not quantitative)
        my_suits = [bid[1] for bid in auction_history if (auction_history.index(bid) % 4) == my_index
                    and len(bid) >= 2 and bid[1] in '♣♦♥♠']
        partner_suits = [bid[1] for bid in partner_bids if len(bid) >= 2 and bid[1] in '♣♦♥♠']

        # If I showed a suit, that could be trump for Blackwood
        # Even if partner opened NT, they could be asking for aces in my suit
        if my_suits:
            # I showed a suit - partner's 4NT is Blackwood
            return True

        # Check for explicit suit agreement (both partners bid same suit)
        common_suits = set(my_suits) & set(partner_suits)
        if common_suits:
            # Explicit suit agreement - definitely Blackwood
            return True

        # Partner bid a suit but I didn't - check if I raised their suit
        if partner_suits:
            # Partner showed a suit - this is Blackwood if we have fit
            return True

        # SECOND: Only if NO suit agreement exists, check for quantitative NT auction
        # Pattern: 1NT - 4NT (no suit shown) → quantitative (inviting 6NT)
        if partner_actually_opened and partner_bids and partner_bids[0] in ['1NT', '2NT', '3NT']:
            return False

        # No suits shown by anyone and partner didn't open NT - unusual, default to Blackwood
        return True

    def _get_ace_answer_bid(self, hand: Hand) -> Tuple[str, str, dict]:
        """Counts aces and returns the correct conventional response."""
        num_aces = sum(1 for card in hand.cards if card.rank == 'A')
        # Metadata to bypass HCP and suit length validation for artificial Blackwood responses
        # Blackwood responses are FORCED - you must respond regardless of HCP
        metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'blackwood_response'}

        if num_aces == 0 or num_aces == 4:
            return ("5♣", "Response to Blackwood: 0 or 4 aces.", metadata)
        if num_aces == 1:
            return ("5♦", "Response to Blackwood: 1 ace.", metadata)
        if num_aces == 2:
            return ("5♥", "Response to Blackwood: 2 aces.", metadata)
        if num_aces == 3:
            return ("5♠", "Response to Blackwood: 3 aces.", metadata)

        return ("Pass", "Error: Could not count aces.", {}) # Should not be reached

    def _is_signoff_applicable(self, features: Dict) -> bool:
        """Check if we asked Blackwood and partner responded."""
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)

        # Check if we bid 4NT and partner responded
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        # Did we ask for aces?
        if '4NT' not in my_bids:
            return False

        # Did partner respond?
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')
        return partner_last_bid in ['5♣', '5♦', '5♥', '5♠']

    def _get_signoff_bid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str, dict]]:
        """Signoff after receiving ace response."""
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')
        auction_history = features.get('auction_history', [])

        # Decode partner's ace count
        ace_responses = {'5♣': [0, 4], '5♦': [1], '5♥': [2], '5♠': [3]}
        partner_aces = ace_responses.get(partner_last_bid, [0])

        # Count our own aces
        my_aces = sum(1 for card in hand.cards if card.rank == 'A')

        # Determine trump suit from auction - look at most recently bid suit by either partner
        # Priority: majors > minors, and most recently bid takes precedence
        trump_suit = self._find_trump_suit(features, auction_history)

        # Metadata for Blackwood signoff bids - bypass HCP and suit length validation
        # Slam bids after Blackwood are FORCED based on ace count, not HCP
        signoff_metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'blackwood_signoff'}

        # Estimate combined HCP for grand slam decision (need 37+ for 7-level)
        estimated_combined = hand.hcp + 16  # Conservative default for partner
        bidding_state = features.get('bidding_state')
        if bidding_state is not None:
            try:
                from utils.seats import normalize
                positions = features.get('positions', [])
                my_idx = features.get('my_index', 0)
                my_seat = normalize(positions[my_idx])
                partner_belief = bidding_state.partner_of(my_seat)
                partner_max_capped = min(partner_belief.hcp[1], 22)
                partner_mid = (partner_belief.hcp[0] + partner_max_capped) // 2
                estimated_combined = hand.hcp + partner_mid
            except Exception:
                pass

        def _decide_slam_level(total_aces, missing_aces):
            """Decide slam bid based on aces and combined HCP."""
            if missing_aces >= 2:
                # Missing 2+ aces, sign off at 5-level
                if trump_suit:
                    return (f"5{trump_suit}", f"Signing off at 5-level, missing {missing_aces} aces.", signoff_metadata)
                return ("5NT", "Signing off (no clear trump suit).", signoff_metadata)
            elif missing_aces == 1:
                # Missing 1 ace, bid small slam
                if trump_suit:
                    return (f"6{trump_suit}", f"Bidding small slam with {total_aces} aces.", signoff_metadata)
                return ("6NT", "Bidding small slam in NT.", signoff_metadata)
            else:
                # All 4 aces present — grand slam needs ~37 combined HCP
                # Use 36 threshold to account for estimation imprecision (±1 HCP)
                if estimated_combined >= 36:
                    if trump_suit:
                        return (f"7{trump_suit}", f"Bidding grand slam with all 4 aces and ~{estimated_combined} combined HCP!", signoff_metadata)
                    return ("7NT", "Bidding grand slam in NT with all 4 aces.", signoff_metadata)
                else:
                    # All aces but insufficient HCP for grand — settle for small slam
                    if trump_suit:
                        return (f"6{trump_suit}", f"Small slam with all aces but ~{estimated_combined} combined HCP (need 37+ for grand).", signoff_metadata)
                    return ("6NT", f"Small slam in NT with all aces but ~{estimated_combined} combined HCP (need 37+ for grand).", signoff_metadata)

        # Decide slam level based on aces
        if partner_aces[0] == 0 or (len(partner_aces) > 1 and partner_aces[1] == 4):
            # Partner has 0 or 4 aces - assume 0 for safety
            missing_aces = 4 - my_aces
            return _decide_slam_level(my_aces, missing_aces)
        else:
            # Partner has definite count
            total_aces = my_aces + partner_aces[0]
            missing_aces = 4 - total_aces
            return _decide_slam_level(total_aces, missing_aces)

    def _find_trump_suit(self, features: Dict, auction_history: list) -> Optional[str]:
        """
        Find the agreed trump suit from the auction.

        Priority:
        1. Most recently bid major (♥ or ♠) by either partner
        2. Most recently bid minor (♦ or ♣) by either partner
        3. NT if no suit agreement

        Excludes the 4NT Blackwood bid and 5-level responses.
        """
        my_index = features.get('my_index', 0)
        partner_index = (my_index + 2) % 4

        # Collect suits bid by partnership (excluding 4NT and Blackwood responses)
        partnership_suits = []
        for i, bid in enumerate(auction_history):
            bidder_idx = i % 4
            if bidder_idx not in [my_index, partner_index]:
                continue  # Skip opponent bids
            if bid in ['Pass', 'X', 'XX', '4NT']:
                continue
            if len(bid) >= 2 and bid[0].isdigit() and bid[1] in '♣♦♥♠':
                level = int(bid[0])
                suit = bid[1]
                # Skip 5-level responses (Blackwood answers)
                if level == 5:
                    continue
                partnership_suits.append((i, suit))

        if not partnership_suits:
            return None

        # Find most recent major suit
        for i in reversed(range(len(partnership_suits))):
            _, suit = partnership_suits[i]
            if suit in ['♥', '♠']:
                return suit

        # Fall back to most recent minor
        for i in reversed(range(len(partnership_suits))):
            _, suit = partnership_suits[i]
            if suit in ['♦', '♣']:
                return suit

        return None

    def _is_king_asking_applicable(self, hand: Hand, features: Dict) -> bool:
        """Check if we should ask for kings (all aces present)."""
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')

        # Must have asked for aces
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]
        if '4NT' not in my_bids:
            return False

        # Partner must have responded with aces
        if partner_last_bid not in ['5♣', '5♦', '5♥', '5♠']:
            return False

        # Decode partner's aces
        ace_responses = {'5♣': [0, 4], '5♦': [1], '5♥': [2], '5♠': [3]}
        partner_aces = ace_responses.get(partner_last_bid, [0])
        my_aces = sum(1 for card in hand.cards if card.rank == 'A')

        # Only ask for kings if we have all 4 aces
        if len(partner_aces) > 1 and 4 in partner_aces:
            # Partner might have 4 aces
            return True
        elif my_aces + partner_aces[0] == 4:
            # We have all 4 aces
            return True

        return False

    def _get_king_ask_bid(self) -> Tuple[str, str]:
        """Returns the 5NT king-asking bid."""
        return ("5NT", "Asking for kings (all aces present).")

    def _is_king_answering_applicable(self, features: Dict) -> bool:
        """Determines if we are responding to a 5NT king ask."""
        return features['auction_features'].get('partner_last_bid') == '5NT'

    def _get_king_answer_bid(self, hand: Hand) -> Tuple[str, str, dict]:
        """Counts kings and returns the correct conventional response (same as aces)."""
        num_kings = sum(1 for card in hand.cards if card.rank == 'K')
        # Metadata to bypass HCP and suit length validation for artificial 5NT king responses
        # King responses are FORCED - you must respond regardless of HCP
        metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'blackwood_king_response'}

        if num_kings == 0 or num_kings == 4:
            return ("6♣", "Response to 5NT: 0 or 4 kings.", metadata)
        if num_kings == 1:
            return ("6♦", "Response to 5NT: 1 king.", metadata)
        if num_kings == 2:
            return ("6♥", "Response to 5NT: 2 kings.", metadata)
        if num_kings == 3:
            return ("6♠", "Response to 5NT: 3 kings.", metadata)

        return ("Pass", "Error: Could not count kings.", {})
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("blackwood", BlackwoodConvention())
