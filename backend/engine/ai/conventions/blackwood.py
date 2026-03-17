from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from utils.seats import seat_index, seat_from_index
from engine.ai.conventions.texas_transfers import is_texas_transfer_sequence
from typing import Optional, Tuple, Dict, List


class SlamEvaluator:
    """Three-gate decision tree for Grand Slam (7-level) bids."""

    @staticmethod
    def evaluate_grand_slam(hand: Hand, trump_suit: Optional[str],
                            total_keycards: int, has_trump_queen: bool,
                            estimated_combined_hcp: int) -> Tuple[bool, str]:
        """
        Decide whether to bid Grand Slam (7-level).

        Returns (should_bid_grand, reason).
        Three gates must ALL pass:
          Gate 1: All 5 keycards + trump queen
          Gate 2: No dry side suits (doubleton+ without A/K/Q)
          Gate 3: trump quality score >= 9 OR combined trump length >= 10
        """
        # Gate 1: All keycards + queen
        if total_keycards < 5 or not has_trump_queen:
            missing = 5 - total_keycards
            queen_str = "" if has_trump_queen else ", missing trump queen"
            return (False, f"Gate 1 fail: missing {missing} keycard(s){queen_str}")

        # Gate 2: No dry side suits
        if trump_suit:
            for suit in ['♠', '♥', '♦', '♣']:
                if suit == trump_suit:
                    continue
                suit_cards = [c for c in hand.cards if c.suit == suit]
                length = len(suit_cards)
                if length >= 2:
                    has_honor = any(c.rank in ('A', 'K', 'Q') for c in suit_cards)
                    if not has_honor:
                        return (False, f"Gate 2 fail: dry {suit} ({length} cards, no A/K/Q)")

        # Gate 3: Trump quality
        if trump_suit:
            trump_cards = [c for c in hand.cards if c.suit == trump_suit]
            trump_length = len(trump_cards)
            # Trump quality score: A=4, K=3, Q=2, J=1 + length
            honor_points = sum({'A': 4, 'K': 3, 'Q': 2, 'J': 1}.get(c.rank, 0) for c in trump_cards)
            quality_score = honor_points + trump_length
            # Estimate partner trump length from combined (assume 8-fit minimum)
            combined_trump_length = trump_length + max(3, 8 - trump_length)
            if quality_score < 9 and combined_trump_length < 10:
                return (False, f"Gate 3 fail: trump quality {quality_score} < 9 and combined length ~{combined_trump_length} < 10")

        return (True, "All 3 gates passed: full keycards, no dry suits, strong trumps")


class BlackwoodConvention(ConventionModule):
    """
    RKCB 1430 (Roman Key Card Blackwood).

    Key cards: 4 Aces + King of agreed trump suit = 5 key cards.
    Responses to 4NT:
      5♣ = 1 or 4 key cards
      5♦ = 0 or 3 key cards
      5♥ = 2 key cards WITHOUT trump queen
      5♠ = 2 key cards WITH trump queen

    Queen Ask: Cheapest non-trump bid after 5♣/5♦ asks for trump queen.
    King Ask (5NT): Specific king responses (bid suit of king held).
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
        auction_history = features.get('auction_history', [])

        # Check for DOPI/ROPI: interference over partner's 4NT
        dopi_result = self._check_dopi_ropi(hand, features, auction_history)
        if dopi_result:
            return dopi_result
        # Check for answering queen ask
        if self._is_queen_answering_applicable(features, auction_history):
            trump_suit = self._find_trump_suit(features, auction_history)
            return self._get_queen_answer_bid(hand, trump_suit)
        # Check for signoff / queen ask initiation after receiving keycard response
        if self._is_signoff_applicable(features):
            return self._get_signoff_bid(hand, features)
        # Check for answering Blackwood (RKCB 1430)
        if self._is_ace_answering_applicable(features):
            trump_suit = self._find_trump_suit(features, auction_history)
            return self._get_keycard_answer_bid(hand, trump_suit)
        # Check for king-asking (5NT)
        if self._is_king_asking_applicable(hand, features):
            return self._get_king_ask_bid()
        # Check for answering king ask (specific kings)
        if self._is_king_answering_applicable(features):
            trump_suit = self._find_trump_suit(features, auction_history)
            return self._get_king_answer_bid(hand, trump_suit)
        # Check for asking keycards (4NT)
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

        # Use BiddingState for accurate combined strength assessment
        bidding_state = features.get('bidding_state')
        estimated_combined = 0
        if bidding_state is not None:
            from utils.seats import normalize
            positions = features.get('positions', [])
            my_index = features.get('my_index')
            if positions and my_index is not None:
                my_seat = normalize(positions[my_index])
                partner_belief = bidding_state.partner_of(my_seat)
                partner_mid = (partner_belief.hcp[0] + partner_belief.hcp[1]) // 2
                estimated_combined = hand.total_points + partner_mid
        if estimated_combined == 0:
            # Fallback: estimate from auction features
            partner_total_points = features['auction_features'].get('partner_total_points', 0)
            estimated_combined = hand.total_points + partner_total_points

        # MINIMUM HCP requirement for Blackwood
        # SAYC requires 16+ HCP for slam exploration with Blackwood
        # This ensures we have genuine slam values, not just counting on partner
        if hand.hcp < 16:
            return False

        # Strong direct jump raises (e.g., 1♥ - 4♥) indicate slam interest
        # This is a jump to 4-level showing strong support (13-15 pts typically)
        if len(my_previous_bids) == 1 and partner_last_bid[0] == '4' and len(partner_last_bid) == 2:
            partner_suit = partner_last_bid[1]
            # Partner jumped to game in our suit - they have 13-15 pts with fit
            # SAYC: Need 16+ HCP for Blackwood, even with strong total points
            # With 16+ HCP and fit, combined is likely 29+, explore slam
            if hand.hcp >= 16 and hand.total_points >= 17:
                return True
            # With fit and 33+ estimated combined AND 16+ HCP, explore slam
            if hand.hcp >= 16 and estimated_combined >= 33:
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
                    # SAYC: Need 16+ HCP for Blackwood
                    # Need 32+ combined points AND 16+ HCP for Blackwood
                    if hand.hcp >= 16 and estimated_combined >= 32 and hand.total_points >= 16:
                        return True
                    # Very strong opener (18+ HCP) can explore slam if combined is close (30+)
                    if hand.hcp >= 18 and estimated_combined >= 30:
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

                # SAYC: Need 16+ HCP for Blackwood even after jump shift
                if is_major_jump_shift and partner_suit != my_suit and hand.hcp >= 16 and hand.total_points >= 17:
                    return True

        # High combined values warrant slam exploration (33+ combined)
        # BUT only if there's a clear trump fit (partner raised our suit)
        # SAYC: Still need 16+ HCP even with high combined strength
        if hand.hcp >= 16 and estimated_combined >= 33:
            # Partner has raised our suit or we have clear fit
            is_raise = len(my_previous_bids) >= 1 and len(partner_last_bid) >= 2 and partner_last_bid[1:] == my_previous_bids[0][1:]
            if is_raise and partner_last_bid[0] in ['3', '4']:
                return True
            # Without explicit raise, DON'T use Blackwood - estimates can be unreliable
            # Partner showing preference (e.g., 3♠ after 1♦-1♠-3♦) is NOT a raise

        return False

    def _get_ace_ask_bid(self) -> Tuple[str, str]:
        """Returns the 4NT RKCB keycard-asking bid."""
        return ("4NT", "RKCB 1430, asking for key cards (aces + trump king).")

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
        positions = features.get('positions', [])
        partner_index = seat_index(seat_from_index(my_index + 2))

        # TEXAS TRANSFER OVERRIDE: 4NT after a completed Texas Transfer is
        # ALWAYS RKCB, never quantitative. This is the key benefit of Texas.
        if positions and is_texas_transfer_sequence(auction_history, positions, my_index):
            return True

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

    @staticmethod
    def count_key_cards(hand: Hand, trump_suit: Optional[str]) -> int:
        """Count RKCB key cards: 4 aces + king of agreed trump suit."""
        num_aces = sum(1 for c in hand.cards if c.rank == 'A')
        trump_king = 0
        if trump_suit:
            trump_king = 1 if any(c.rank == 'K' and c.suit == trump_suit for c in hand.cards) else 0
        return num_aces + trump_king

    @staticmethod
    def has_trump_queen(hand: Hand, trump_suit: Optional[str]) -> bool:
        """Check if hand holds the queen of agreed trump suit."""
        if not trump_suit:
            return False
        return any(c.rank == 'Q' and c.suit == trump_suit for c in hand.cards)

    def _get_keycard_answer_bid(self, hand: Hand, trump_suit: Optional[str]) -> Tuple[str, str, dict]:
        """RKCB 1430 response: count key cards (aces + trump king).

        5♣ = 1 or 4 key cards
        5♦ = 0 or 3 key cards
        5♥ = 2 key cards WITHOUT trump queen
        5♠ = 2 key cards WITH trump queen
        """
        keycards = self.count_key_cards(hand, trump_suit)
        has_queen = self.has_trump_queen(hand, trump_suit)
        metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'blackwood_response'}

        if keycards in (1, 4):
            return ("5♣", f"RKCB 1430: {keycards} key card(s).", metadata)
        if keycards in (0, 3):
            return ("5♦", f"RKCB 1430: {keycards} key card(s).", metadata)
        if keycards == 2:
            if has_queen:
                return ("5♠", "RKCB 1430: 2 key cards WITH trump queen.", metadata)
            else:
                return ("5♥", "RKCB 1430: 2 key cards WITHOUT trump queen.", metadata)
        # keycards == 5 (all aces + trump king)
        if has_queen:
            return ("5♠", "RKCB 1430: 2+ key cards WITH trump queen.", metadata)
        else:
            return ("5♥", "RKCB 1430: 2+ key cards WITHOUT trump queen.", metadata)

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

    def _decode_rkcb_response(self, partner_bid: str, my_keycards: int) -> Tuple[List[int], Optional[bool]]:
        """Decode partner's RKCB 1430 response.

        Returns (possible_keycard_counts, trump_queen_known).
        trump_queen_known: True = has it, False = doesn't, None = ambiguous (need Queen Ask).
        """
        rkcb_responses = {
            '5♣': ([1, 4], None),   # 1 or 4 keycards, queen unknown
            '5♦': ([0, 3], None),   # 0 or 3 keycards, queen unknown
            '5♥': ([2], False),     # 2 keycards WITHOUT queen
            '5♠': ([2], True),      # 2 keycards WITH queen
        }
        return rkcb_responses.get(partner_bid, ([0], None))

    def _resolve_keycard_count(self, possible_counts: List[int], my_keycards: int) -> int:
        """Resolve ambiguous 1/4 or 0/3 response using our own keycard count."""
        if len(possible_counts) == 1:
            return possible_counts[0]
        # For 1/4: if we have 3+ keycards, partner can't have 4 → partner has 1
        # For 0/3: if we have 3+ keycards, partner can't have 3 → partner has 0
        low, high = possible_counts
        if my_keycards + high > 5:
            return low
        # Default to lower count for safety
        return low

    def _get_queen_ask_bid(self, trump_suit: Optional[str]) -> Optional[Tuple[str, str, dict]]:
        """Return the Queen Ask bid: cheapest non-trump bid after 5♣/5♦ response."""
        metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'blackwood_queen_ask'}
        # Cheapest non-trump suit bid at 5-level
        suit_order = ['♣', '♦', '♥', '♠']
        for suit in suit_order:
            if suit != trump_suit:
                return (f"5{suit}", f"Queen Ask: do you have the {trump_suit} queen?", metadata)
        # Fallback (shouldn't happen — at least one suit differs from trump)
        return None

    def _get_signoff_bid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str, dict]]:
        """Signoff after receiving RKCB keycard response.

        May initiate Queen Ask if queen status unknown and slam is viable.
        Uses SlamEvaluator for Grand Slam decisions.
        """
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')
        auction_history = features.get('auction_history', [])
        trump_suit = self._find_trump_suit(features, auction_history)
        signoff_metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'blackwood_signoff'}

        # Count our key cards
        my_keycards = self.count_key_cards(hand, trump_suit)
        my_queen = self.has_trump_queen(hand, trump_suit)

        # Decode partner's RKCB response
        possible_counts, queen_known = self._decode_rkcb_response(partner_last_bid, my_keycards)
        partner_keycards = self._resolve_keycard_count(possible_counts, my_keycards)
        total_keycards = my_keycards + partner_keycards
        missing_keycards = 5 - total_keycards

        # Estimate combined HCP
        estimated_combined = hand.hcp + 16
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

        # Missing 2+ keycards → sign off at 5-level
        if missing_keycards >= 2:
            if trump_suit:
                return (f"5{trump_suit}", f"Signing off: missing {missing_keycards} key cards.", signoff_metadata)
            return ("5NT", "Signing off (no clear trump suit).", signoff_metadata)

        # Missing 1 keycard → small slam
        if missing_keycards == 1:
            if trump_suit:
                return (f"6{trump_suit}", f"Small slam with {total_keycards}/5 key cards.", signoff_metadata)
            return ("6NT", "Small slam in NT.", signoff_metadata)

        # All 5 keycards present — evaluate Grand Slam
        # Determine queen status: from response (5♥/5♠) or our own hand
        has_queen = queen_known if queen_known is not None else my_queen
        if queen_known is None and not my_queen:
            # Queen status unknown and we don't have it — initiate Queen Ask
            # But only if we might want grand slam (need high combined)
            if estimated_combined >= 33:
                queen_ask = self._get_queen_ask_bid(trump_suit)
                if queen_ask:
                    return queen_ask
            # Not enough for grand even with queen — settle for small slam
            has_queen = False

        # Use SlamEvaluator for grand slam decision
        should_grand, reason = SlamEvaluator.evaluate_grand_slam(
            hand, trump_suit, total_keycards, has_queen, estimated_combined)

        if should_grand:
            if trump_suit:
                return (f"7{trump_suit}", f"Grand slam! {reason}", signoff_metadata)
            return ("7NT", f"Grand slam in NT! {reason}", signoff_metadata)
        else:
            # Small slam
            if trump_suit:
                return (f"6{trump_suit}", f"Small slam ({reason}).", signoff_metadata)
            return ("6NT", f"Small slam in NT ({reason}).", signoff_metadata)

    def _is_queen_answering_applicable(self, features: Dict, auction_history: list) -> bool:
        """Check if partner is asking for the trump queen (Queen Ask).

        Queen Ask = cheapest non-trump bid after a 5♣ or 5♦ RKCB response.
        Detect: we responded 5♣/5♦, partner bid a suit at 5-level that isn't trump.
        """
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')
        if not partner_last_bid or len(partner_last_bid) < 2:
            return False
        if partner_last_bid[0] != '5' or partner_last_bid[1] not in '♣♦♥♠':
            return False

        my_index = features.get('my_index', 0)
        # Check that WE responded 5♣ or 5♦ (meaning we gave an RKCB response)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if (i % 4) == my_index and auction_history[i] not in ('Pass', 'X', 'XX')]
        if not my_bids:
            return False
        my_last = my_bids[-1]
        if my_last not in ('5♣', '5♦'):
            return False

        # Partner's bid must be a different suit than trump (it's the queen ask)
        trump_suit = self._find_trump_suit(features, auction_history)
        if partner_last_bid[1] == trump_suit:
            return False

        # Verify partner bid 4NT earlier (they initiated RKCB)
        partner_index = seat_index(seat_from_index(my_index + 2))
        partner_bids = [auction_history[i] for i in range(len(auction_history))
                        if (i % 4) == partner_index and auction_history[i] not in ('Pass', 'X', 'XX')]
        return '4NT' in partner_bids

    def _get_queen_answer_bid(self, hand: Hand, trump_suit: Optional[str]) -> Tuple[str, str, dict]:
        """Answer the Queen Ask.

        With trump queen: bid the trump suit at 6-level (confirms queen + shows suit).
        Without trump queen: bid trump suit at 5-level (sign-off, denying queen).
        """
        metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'blackwood_queen_response'}
        has_queen = self.has_trump_queen(hand, trump_suit)
        if has_queen:
            suit = trump_suit or 'NT'
            return (f"6{suit}", f"Queen Ask: YES, I have the {trump_suit} queen.", metadata)
        else:
            suit = trump_suit or 'NT'
            return (f"5{suit}", f"Queen Ask: NO, I do not have the {trump_suit} queen.", metadata)

    def _check_dopi_ropi(self, hand: Hand, features: Dict, auction_history: list) -> Optional[Tuple[str, str, dict]]:
        """Check for DOPI/ROPI: interference after partner's 4NT RKCB ask.

        DOPI (Double = 0, Pass = 1, Item = 2): When opponent BIDS over 4NT.
        ROPI (Redouble = 0, Pass = 1, Item = 2): When opponent DOUBLES 4NT.

        Only applies at the 5-level (below slam). If opponent bids at 6+, double is penalty.
        """
        if len(auction_history) < 2:
            return None

        my_index = features.get('my_index', 0)
        partner_index = seat_index(seat_from_index(my_index + 2))

        # Find if partner bid 4NT
        partner_bid_4nt = False
        for i, bid in enumerate(auction_history):
            if (i % 4) == partner_index and bid == '4NT':
                partner_bid_4nt = True
                break
        if not partner_bid_4nt:
            return None

        # Check last bid by RHO (opponent)
        rho_index = seat_index(seat_from_index(my_index + 3))  # Right-hand opponent
        last_bid = auction_history[-1]
        last_bidder = (len(auction_history) - 1) % 4

        # Only applies if it's our turn and RHO just acted
        if last_bidder != rho_index:
            return None

        metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'dopi_ropi'}
        trump_suit = self._find_trump_suit(features, auction_history)
        keycards = self.count_key_cards(hand, trump_suit)

        if last_bid == 'X':
            # ROPI: opponent doubled 4NT
            if keycards == 0:
                return ("XX", "ROPI: 0 key cards (redouble).", metadata)
            elif keycards == 1:
                return ("Pass", "ROPI: 1 key card (pass).", metadata)
            else:
                # Step = cheapest available bid
                next_bid = self._cheapest_available_bid(auction_history)
                if next_bid:
                    return (next_bid, f"ROPI: {keycards} key cards.", metadata)
                return ("Pass", f"ROPI: {keycards} key cards (no legal step bid).", metadata)

        elif last_bid not in ('Pass', 'XX') and last_bid[0].isdigit():
            interference_level = int(last_bid[0])
            # If interference is at 6+ level, this is a sacrifice — double is penalty
            if interference_level >= 6:
                return None  # Let normal competitive logic handle it

            # DOPI: opponent bid over 4NT
            if keycards == 0:
                return ("X", "DOPI: 0 key cards (double).", metadata)
            elif keycards == 1:
                return ("Pass", "DOPI: 1 key card (pass).", metadata)
            else:
                # Step = cheapest bid above opponent's interference
                next_bid = self._cheapest_available_bid(auction_history)
                if next_bid:
                    return (next_bid, f"DOPI: {keycards} key cards.", metadata)
                return ("Pass", f"DOPI: {keycards} key cards (no legal step bid).", metadata)

        return None

    def _cheapest_available_bid(self, auction_history: list) -> Optional[str]:
        """Find the cheapest legal suit/NT bid above the current auction level."""
        # Find highest bid in auction
        highest_level = 0
        highest_suit_rank = 0
        suit_ranks = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
        for bid in auction_history:
            if bid in ('Pass', 'X', 'XX') or not bid[0].isdigit():
                continue
            level = int(bid[0])
            if bid.endswith('NT'):
                rank = 5
            else:
                rank = suit_ranks.get(bid[1], 0)
            if level > highest_level or (level == highest_level and rank > highest_suit_rank):
                highest_level = level
                highest_suit_rank = rank

        # Find next legal bid
        suit_order = ['♣', '♦', '♥', '♠', 'NT']
        for level in range(highest_level, 8):
            start_rank = highest_suit_rank + 1 if level == highest_level else 0
            for i, suit in enumerate(suit_order):
                if i + 1 <= start_rank and level == highest_level:
                    continue
                if level <= 7:
                    return f"{level}{suit}"
        return None

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
        partner_index = seat_index(seat_from_index(my_index + 2))

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
        """Check if we should ask for kings (5NT).

        In RKCB, 5NT king ask guarantees all 5 keycards are present
        and promises interest in Grand Slam.
        """
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')

        # Must have asked for keycards (4NT)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]
        if '4NT' not in my_bids:
            return False

        # Partner must have responded with keycards
        if partner_last_bid not in ['5♣', '5♦', '5♥', '5♠']:
            return False

        # Also handle: we asked queen ask, partner answered, now we ask kings
        # Partner could have answered queen ask at 5-level or 6-level
        # For now, only handle direct RKCB response → 5NT sequence

        # Decode partner's RKCB response
        trump_suit = self._find_trump_suit(features, auction_history)
        my_keycards = self.count_key_cards(hand, trump_suit)
        possible_counts, queen_known = self._decode_rkcb_response(partner_last_bid, my_keycards)
        partner_keycards = self._resolve_keycard_count(possible_counts, my_keycards)
        total_keycards = my_keycards + partner_keycards

        # Only ask for kings if all 5 keycards are present
        return total_keycards >= 5

    def _get_king_ask_bid(self) -> Tuple[str, str, dict]:
        """Returns the 5NT king-asking bid (guarantees all 5 keycards)."""
        metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'blackwood_king_ask'}
        return ("5NT", "RKCB: Asking for specific kings (all 5 keycards present, Grand Slam interest).", metadata)

    def _is_king_answering_applicable(self, features: Dict) -> bool:
        """Determines if we are responding to a 5NT king ask."""
        return features['auction_features'].get('partner_last_bid') == '5NT'

    def _get_king_answer_bid(self, hand: Hand, trump_suit: Optional[str]) -> Tuple[str, str, dict]:
        """Specific king responses to 5NT.

        Bid the suit of the cheapest side-suit king you hold:
          6♣ = ♣K
          6♦ = ♦K (denies ♣K)
          6♥ = ♥K (denies ♣K and ♦K)
          6-trump = no side kings
        Trump king is already counted as a keycard, so only report SIDE kings.
        """
        metadata = {'bypass_hcp': True, 'bypass_suit_length': True, 'convention': 'blackwood_king_response'}

        # Check side-suit kings in ascending order (♣, ♦, ♥, ♠ minus trump)
        suit_order = ['♣', '♦', '♥', '♠']
        for suit in suit_order:
            if suit == trump_suit:
                continue
            if any(c.rank == 'K' and c.suit == suit for c in hand.cards):
                return (f"6{suit}", f"King Ask: I have the {suit} King.", metadata)

        # No side kings — bid 6 of trump suit
        if trump_suit:
            return (f"6{trump_suit}", "King Ask: no side-suit kings.", metadata)
        return ("6NT", "King Ask: no side-suit kings.", metadata)
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("blackwood", BlackwoodConvention())
