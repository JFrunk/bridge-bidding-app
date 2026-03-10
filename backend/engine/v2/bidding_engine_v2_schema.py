"""
Schema-Driven Bidding Engine V2

This engine uses JSON schema files to define bidding rules rather than
Python code. This allows for:
1. Easier rule modifications without code changes
2. System toggling (SAYC vs 2/1) via different schema files
3. Machine-readable rules for analysis and testing
4. Cleaner separation of bidding knowledge from engine logic
5. Proper forcing level tracking across the auction
6. Monte Carlo integration for bid validation (optional)
"""

import logging
from typing import Dict, Optional, Tuple, List
from engine.hand import Hand
from utils.seats import seat_index, seat_from_index, partner as partner_seat
from engine.v2.features.enhanced_extractor import extract_flat_features
from engine.v2.interpreters.schema_interpreter import (
    SchemaInterpreter,
    BidCandidate,
    BidValidationResult,
    ForcingLevel
)
from engine.v2.inference.conflict_resolver import ConflictResolver, PassThroughResolver

logger = logging.getLogger(__name__)


class BiddingEngineV2Schema:
    """
    Schema-driven bidding engine.

    Uses JSON schema files to determine bids rather than Python modules.
    This is the core of the refactored V2 approach.

    Features:
    - JSON-based bidding rules
    - Forcing level state tracking (NON_FORCING, FORCING_1_ROUND, GAME_FORCE)
    - Validation of bids against forcing constraints
    - Optional Monte Carlo integration for slam/competitive validation
    """

    def __init__(self, schema_dir: str = None, simulator=None, **kwargs):
        """
        Initialize the schema-driven engine.

        Args:
            schema_dir: Path to schema directory. Defaults to engine/v2/schemas/
            simulator: Optional Monte Carlo simulator for bid validation.
                      If None, conflict resolver operates in pass-through mode.
        """
        # Accept and ignore deprecated use_v1_fallback for backward compatibility
        if 'use_v1_fallback' in kwargs:
            pass  # Silently ignore — V1 fallback removed

        self.interpreter = SchemaInterpreter(schema_dir)
        self._bid_legality_cache = {}
        self._total_bid_count = 0
        self._last_auction = None  # Track auction for auto-reset detection

        # Tracking for analysis - stores info about last bid decision
        self._last_rule_id: Optional[str] = None
        self._last_schema_file: Optional[str] = None
        self._last_priority: Optional[int] = None

        # Initialize conflict resolver for Monte Carlo integration
        if simulator is not None:
            self.conflict_resolver = ConflictResolver(simulator)
        else:
            self.conflict_resolver = PassThroughResolver()

    def new_deal(self):
        """Reset state for a new deal. Call this before each new hand."""
        self.interpreter.reset_state()

    def get_forcing_state(self) -> Dict:
        """Get the current forcing state of the auction."""
        return self.interpreter.get_forcing_state()

    def get_next_bid(
        self,
        hand: Hand,
        auction_history: List[str],
        my_position: str,
        vulnerability: str = 'None',
        explanation_level: str = 'detailed',  # Not used by V2, but kept for V1 API compatibility
        dealer: str = 'North'
    ) -> Tuple[str, str]:
        """
        Get the next bid for a hand.

        Args:
            hand: Hand object
            auction_history: List of previous bids
            my_position: Position of bidder (North/East/South/West)
            vulnerability: Vulnerability string
            explanation_level: Explanation level (ignored, for V1 API compatibility)
            dealer: Dealer position

        Returns:
            Tuple of (bid, explanation)
        """
        # Note: explanation_level is ignored - V2 Schema generates its own explanations
        self._total_bid_count += 1

        # Auto-reset forcing state when a new deal is detected.
        # A new deal = auction is not a continuation of the previous one.
        # This handles batch testing where new_deal() isn't called between hands.
        if self._last_auction is None or not auction_history:
            self.interpreter.reset_state()
        elif len(auction_history) <= len(self._last_auction):
            # Auction got shorter or same length — new deal
            self.interpreter.reset_state()
        elif auction_history[:len(self._last_auction)] != self._last_auction:
            # Auction prefix changed — new deal
            self.interpreter.reset_state()
        self._last_auction = list(auction_history) if auction_history else []

        # Extract features in flat format for schema evaluation
        features = extract_flat_features(
            hand, auction_history, my_position, vulnerability, dealer
        )

        # Add forcing state to features for rule evaluation
        forcing_state = self.interpreter.get_forcing_state()
        features['forcing_level'] = forcing_state['forcing_level']
        features['is_game_forced'] = forcing_state['is_game_forced']

        # Add auction-derived features needed for schema rules
        features = self._enhance_features(features, hand, auction_history)

        # Evaluate schemas using soft matching (Best-Match-Wins)
        candidates = self.interpreter.evaluate_all_candidates_with_details(features)

        if candidates:
            # Find the best legal bid that doesn't violate forcing constraints
            # Track best forcing-rejected candidate as fallback
            best_forcing_rejected = None
            # Slam context detection for safety net
            SLAM_SCHEMA_FILES = {'sayc_slam', 'sayc_rkcb', 'sayc_slam_tries'}
            SLAM_RULE_KEYWORDS = {'slam', 'blackwood', 'rkcb', 'grand', 'king_response'}

            for candidate in candidates:
                bid = candidate.bid

                # Validate bid is legal in the auction
                if not self._is_bid_legal(bid, auction_history, my_position, dealer):
                    continue

                # Safety net: reject 6+ level bids that aren't part of a slam sequence.
                # Slam context = partner bid 4NT/5NT (convention), or rule from slam schema,
                # or combined partnership HCP justifies slam. LOTT and competitive rules
                # should never produce 6+ level bids.
                bid_level = int(bid[0]) if bid and bid[0].isdigit() else 0
                if bid_level >= 6:
                    schema_stem = (candidate.schema_file or '').replace('.json', '').split('/')[-1]
                    rule_id = candidate.rule_id or ''
                    partner_last = features.get('partner_last_bid', '')
                    partnership_hcp = features.get('partnership_hcp_min', 0)

                    in_slam_context = (
                        # Rule source indicates slam investigation
                        schema_stem in SLAM_SCHEMA_FILES or
                        any(kw in rule_id for kw in SLAM_RULE_KEYWORDS) or
                        # Auction context indicates slam investigation
                        partner_last in ['4NT', '5NT'] or
                        features.get('in_slam_zone', False) or
                        # Combined partnership HCP justifies slam (33+ for small, 37+ for grand)
                        (bid_level == 6 and partnership_hcp >= 30) or
                        (bid_level == 7 and partnership_hcp >= 35)
                    )
                    if not in_slam_context:
                        logger.warning(
                            f"Safety net: Rejecting {bid} from rule '{rule_id}' — "
                            f"level {bid_level} bid outside slam context "
                            f"(partnership HCP ~{partnership_hcp}, "
                            f"partner last bid: {partner_last or 'N/A'})"
                        )
                        continue

                # Validate against forcing constraints (only in partnership auctions)
                # Skip forcing validation in competitive situations - opponents' bids
                # break forcing sequences between partners
                is_competitive = (
                    features.get('is_overcall') or
                    features.get('is_advancer') or
                    features.get('is_competitive_later')
                )
                if not is_competitive:
                    last_level = features.get('last_contract_level', 0)
                    last_suit = self._get_last_contract_suit(auction_history)
                    forcing_validation = self.interpreter.validate_bid_against_forcing(
                        bid, last_contract_level=last_level, last_contract_suit=last_suit
                    )
                    if not forcing_validation.is_valid:
                        # Track highest-priority non-Pass bid rejected by forcing
                        if best_forcing_rejected is None and bid != 'Pass':
                            best_forcing_rejected = candidate
                        continue

                # Run bid through conflict resolver for Monte Carlo validation
                # This can veto slams or modify competitive decisions
                proposed_rule = {
                    'bid': bid,
                    'priority': candidate.priority,
                    'explanation': candidate.explanation,
                    'rule_id': candidate.rule_id
                }
                final_bid, final_explanation = self.conflict_resolver.review_bid(
                    proposed_rule, hand, auction_history, features
                )

                # Update forcing state based on this bid's metadata
                if candidate.sets_forcing_level:
                    self.interpreter._update_forcing_state(
                        candidate.sets_forcing_level,
                        candidate.rule_id
                    )

                # Store rule info for analysis
                self._last_rule_id = candidate.rule_id
                self._last_schema_file = getattr(candidate, 'schema_file', None)
                self._last_priority = candidate.priority

                # Slam exploration safety net: intercept game bids when slam values exist
                slam_bid = self._slam_exploration_check(
                    final_bid, hand, features, auction_history, my_position, dealer
                )
                if slam_bid:
                    return slam_bid

                return (final_bid, final_explanation)

            # All candidates rejected — if we have a forcing-rejected non-Pass bid,
            # use it rather than defaulting to Pass in a forced auction
            if best_forcing_rejected is not None:
                bid = best_forcing_rejected.bid
                self._last_rule_id = best_forcing_rejected.rule_id
                self._last_schema_file = getattr(best_forcing_rejected, 'schema_file', None)
                self._last_priority = best_forcing_rejected.priority
                if best_forcing_rejected.sets_forcing_level:
                    self.interpreter._update_forcing_state(
                        best_forcing_rejected.sets_forcing_level,
                        best_forcing_rejected.rule_id
                    )
                return (bid, best_forcing_rejected.explanation)

        # No schema rule matched - fallback to Pass (check forcing constraints first)
        self._last_rule_id = 'default_pass'
        self._last_schema_file = None
        self._last_priority = 0
        last_level = features.get('last_contract_level', 0)
        last_suit = self._get_last_contract_suit(auction_history)
        forcing_validation = self.interpreter.validate_bid_against_forcing(
            "Pass", last_contract_level=last_level, last_contract_suit=last_suit
        )
        if not forcing_validation.is_valid:
            # Cannot pass in a forcing auction — find cheapest legal bid
            emergency_bid = self._find_cheapest_legal_bid(
                auction_history, my_position, dealer
            )
            if emergency_bid:
                logger.info(
                    f"Forcing enforcement: {emergency_bid} instead of Pass "
                    f"({forcing_validation.reason})"
                )
                return (emergency_bid,
                        f"Forced bid — {forcing_validation.reason}")

            # Truly stuck — no legal non-Pass bid exists (shouldn't happen)
            return ('Pass', f'Warning: {forcing_validation.reason}')

        return ('Pass', 'No applicable bidding rule found')

    def get_next_bid_structured(
        self,
        hand: Hand,
        auction_history: List[str],
        my_position: str,
        vulnerability: str = 'None',
        dealer: str = 'North'
    ) -> Tuple[str, Dict]:
        """
        Get next bid with structured explanation data (for V1 API compatibility).

        Returns:
            Tuple of (bid, explanation_dict)
        """
        bid, explanation_str = self.get_next_bid(
            hand, auction_history, my_position, vulnerability, 'detailed', dealer
        )

        # Create structured explanation similar to V1 format
        explanation_dict = {
            'primary_reason': explanation_str,
            'convention': {
                'id': None,
                'name': 'V2 Schema'
            },
            'forcing_status': self.interpreter.get_forcing_state().get('forcing_level', 'NON_FORCING'),
            'hand_evaluation': {
                'hcp': hand.hcp,
                'shape': hand.shape_string  # e.g., "5-3-3-2"
            }
        }

        return (bid, explanation_dict)

    def get_bid_candidates(
        self,
        hand: Hand,
        auction_history: List[str],
        my_position: str,
        vulnerability: str = 'None',
        dealer: str = 'North'
    ) -> List[BidCandidate]:
        """
        Get all matching bid candidates for analysis/debugging.

        Args:
            Same as get_next_bid

        Returns:
            List of BidCandidate objects sorted by priority
        """
        features = extract_flat_features(
            hand, auction_history, my_position, vulnerability, dealer
        )
        features = self._enhance_features(features, hand, auction_history)

        return self.interpreter.evaluate_with_details(features)

    def _enhance_features(
        self,
        features: Dict,
        hand: Hand,
        auction_history: List[str]
    ) -> Dict:
        """
        Add derived features needed for schema rules that aren't in base extraction.
        """
        # Auction-level features
        features['auction_length'] = len(auction_history)
        features['last_contract_level'] = 0
        for b in reversed(auction_history):
            if b and b[0].isdigit():
                features['last_contract_level'] = int(b[0])
                break

        # Seat calculation (1-4)
        # For opening bids, seat is based on how many passes before you:
        # - 1st seat (dealer): no passes before
        # - 2nd seat: 1 pass before
        # - 3rd seat: 2 passes before
        # - 4th seat (balancing): 3 passes before
        pass_count = sum(1 for b in auction_history if b == 'Pass')
        features['seat'] = min(pass_count + 1, 4)  # Cap at 4

        # Rule of 20 check
        longest = features.get('longest_suit_length', 0)
        second_longest = sorted(
            [features.get(f'{s}_length', 0) for s in ['spades', 'hearts', 'diamonds', 'clubs']],
            reverse=True
        )[1] if longest > 0 else 0
        features['rule_of_20'] = (features.get('hcp', 0) + longest + second_longest) >= 20

        # Suit quality for longest suit
        longest_suit = features.get('longest_suit')
        if longest_suit:
            from engine.v2.features.enhanced_extractor import evaluate_suit_quality, get_suit_hcp
            features['suit_quality_longest'] = evaluate_suit_quality(hand, longest_suit)
            features['longest_suit_hcp'] = get_suit_hcp(hand, longest_suit)

        # Add suit-specific HCP features (for preempts, overcalls)
        from engine.v2.features.enhanced_extractor import get_suit_hcp
        features['spades_hcp'] = get_suit_hcp(hand, '♠')
        features['hearts_hcp'] = get_suit_hcp(hand, '♥')
        features['diamonds_hcp'] = get_suit_hcp(hand, '♦')
        features['clubs_hcp'] = get_suit_hcp(hand, '♣')

        # Add suit-specific quality features (for preempts)
        from engine.v2.features.enhanced_extractor import evaluate_suit_quality
        features['suit_quality_spades'] = evaluate_suit_quality(hand, '♠')
        features['suit_quality_hearts'] = evaluate_suit_quality(hand, '♥')
        features['suit_quality_diamonds'] = evaluate_suit_quality(hand, '♦')
        features['suit_quality_clubs'] = evaluate_suit_quality(hand, '♣')

        # Check if all unbid suits have support (for takeout doubles)
        opening_bid = features.get('opening_bid')
        if opening_bid and len(opening_bid) >= 2:
            opening_suit_letter = opening_bid[1] if opening_bid[0].isdigit() else None
            if opening_suit_letter:
                # Convert letter format (C, D, H, S) to symbol format (♣, ♦, ♥, ♠)
                letter_to_symbol = {'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠'}
                opening_suit = letter_to_symbol.get(opening_suit_letter, opening_suit_letter)
                unbid_suits = [s for s in ['♠', '♥', '♦', '♣'] if s != opening_suit]
                support_counts = [hand.suit_lengths.get(s, 0) for s in unbid_suits]
                features['support_all_unbid'] = all(c >= 3 for c in support_counts)
                features['unbid_suit_support'] = min(support_counts) if support_counts else 0
                suit_map = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}
                suit_name = suit_map.get(opening_suit, 'spades')
                features['stopper_in_opponent_suit'] = features.get(f'{suit_name}_stopped', False)

        # Check for unbid major support (negative doubles)
        if opening_bid:
            interference = features.get('_nested_features', {}).get('auction_features', {}).get('interference', {})
            if interference.get('present'):
                interf_bid = interference.get('bid', '')
                interf_suit_letter = interf_bid[1] if len(interf_bid) >= 2 and interf_bid[0].isdigit() else None
                opening_suit_letter = opening_bid[1] if len(opening_bid) >= 2 and opening_bid[0].isdigit() else None

                # Convert letter format (C, D, H, S) to symbol format (♣, ♦, ♥, ♠)
                letter_to_symbol = {'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠'}
                interf_suit = letter_to_symbol.get(interf_suit_letter, interf_suit_letter)
                opening_suit = letter_to_symbol.get(opening_suit_letter, opening_suit_letter)

                bid_suits = {opening_suit, interf_suit} - {None}
                unbid_majors = {'♠', '♥'} - bid_suits

                has_4_unbid_major = any(
                    hand.suit_lengths.get(s, 0) >= 4 for s in unbid_majors
                )
                features['has_unbid_major_4'] = has_4_unbid_major
                features['interference_present'] = True
                features['interference_level'] = interference.get('level', 0)
            else:
                features['has_unbid_major_4'] = False
                features['interference_present'] = False
                features['interference_level'] = 0

        return features

    def _slam_exploration_check(
        self,
        selected_bid: str,
        hand: 'Hand',
        features: dict,
        auction_history: List[str],
        my_position: str,
        dealer: str
    ) -> Optional[Tuple[str, str]]:
        """
        Slam exploration safety net: intercept game-level bids when partnership
        has slam values but no slam rule matched.

        Uses midpoint HCP estimate (average of min/max partner HCP) which is more
        realistic than minimum for slam detection. Also considers total points
        (HCP + distribution) to catch distributional slam hands.

        Requirements:
        1. Selected bid is a game bid (3NT, 4♥, 4♠, 5♣, 5♦)
        2. Partnership midpoint HCP >= 33 OR partnership total points >= 33
        3. Own hand has 15+ HCP (or 14+ with a known fit)
        4. Partner has shown 6+ HCP minimum
        5. 4NT hasn't already been bid
        6. 4NT is a legal bid

        Returns:
            (bid, explanation) tuple if slam should be explored, None otherwise
        """
        # Only intercept game-level bids
        game_bids = {'3NT', '4♥', '4♠', '5♣', '5♦'}
        if selected_bid not in game_bids:
            return None

        # Partner must have shown some values
        partner_min = features.get('partner_min_hcp', 0)
        if partner_min < 6:
            return None

        # Need strong own hand (slightly lower threshold with known fit)
        has_fit = features.get('fit_known', False)
        hcp_threshold = 14 if has_fit else 15
        if hand.hcp < hcp_threshold:
            return None

        # Check partnership strength using midpoint estimate
        partnership_mid = features.get('partnership_hcp_mid', 0)
        partnership_total = features.get('partnership_total_points_min', 0)
        partnership_min = features.get('partnership_hcp_min', 0)

        # Primary trigger: midpoint HCP estimate suggests slam
        # Secondary trigger: total points (including distribution) suggest slam
        slam_threshold_met = (
            partnership_mid >= 33 or
            partnership_total >= 33 or
            (partnership_min >= 31 and hand.hcp >= 17)
        )
        if not slam_threshold_met:
            return None

        # Don't re-ask Blackwood
        if '4NT' in auction_history:
            return None

        # Don't trigger if already at slam level
        for bid in auction_history:
            if bid and bid[0].isdigit() and int(bid[0]) >= 6:
                return None

        # Check 4NT is legal
        if not self._is_bid_legal('4NT', auction_history, my_position, dealer):
            # 4NT isn't legal — try direct 6NT for very strong balanced hands
            if hand.is_balanced and partnership_mid >= 33:
                if self._is_bid_legal('6NT', auction_history, my_position, dealer):
                    self._last_rule_id = 'slam_safety_net_direct_6nt'
                    return ('6NT', f'Direct 6NT with ~{partnership_mid} combined HCP')
            return None

        # Bid 4NT (Blackwood) instead of game
        self._last_rule_id = 'slam_safety_net_blackwood'
        aces = sum(1 for c in hand.cards if c.rank == 'A')
        return ('4NT', f'Blackwood — slam values with ~{partnership_mid} combined HCP ({aces} aces)')

    def _find_cheapest_legal_bid(
        self,
        auction_history: List[str],
        my_position: str,
        dealer: str
    ) -> Optional[str]:
        """
        Find the cheapest legal non-Pass bid when forcing requires action.

        Used as an emergency fallback when no schema rule provides a bid
        but the forcing state machine says Pass is illegal.
        """
        # All possible bids in ascending order
        suit_order = ['♣', '♦', '♥', '♠', 'NT']
        for level in range(1, 8):
            for suit in suit_order:
                bid = f"{level}{suit}"
                if self._is_bid_legal(bid, auction_history, my_position, dealer):
                    return bid
        return None

    @staticmethod
    def _get_last_contract_suit(auction_history: List[str]) -> str:
        """Extract the suit of the last contract bid from the auction."""
        for b in reversed(auction_history):
            if b and len(b) >= 2 and b[0].isdigit():
                suit_part = b[1:]
                if suit_part in ('NT', '♠', '♥', '♦', '♣'):
                    return suit_part
        return ''

    def _is_bid_legal(self, bid: str, auction_history: List[str],
                      my_position: str = 'South', dealer: str = 'North') -> bool:
        """
        Check if a bid is legal given the auction history.
        """
        if bid in ['Pass', 'X', 'XX']:
            # X only legal after an opponent's non-pass bid
            if bid == 'X':
                if not auction_history:
                    return False
                my_s = seat_from_index(seat_index(my_position))
                partner_s = partner_seat(my_position)
                dealer_idx = seat_index(dealer)
                for i in range(len(auction_history) - 1, -1, -1):
                    b = auction_history[i]
                    if b not in ['Pass']:
                        bidder_s = seat_from_index(dealer_idx + i)
                        is_opponent = bidder_s != my_s and bidder_s != partner_s
                        return is_opponent and b not in ['X', 'XX']
                return False

            # XX only legal after opponent's X
            if bid == 'XX':
                if not auction_history:
                    return False
                my_s = seat_from_index(seat_index(my_position))
                partner_s = partner_seat(my_position)
                dealer_idx = seat_index(dealer)
                for i in range(len(auction_history) - 1, -1, -1):
                    b = auction_history[i]
                    if b != 'Pass':
                        bidder_s = seat_from_index(dealer_idx + i)
                        is_opponent = bidder_s != my_s and bidder_s != partner_s
                        return is_opponent and b == 'X'
                return False

            return True  # Pass always legal

        # Get last non-pass bid
        last_bid = None
        for b in reversed(auction_history):
            if b not in ['Pass', 'X', 'XX']:
                last_bid = b
                break

        if last_bid is None:
            # First real bid — still check level is valid
            try:
                if int(bid[0]) > 7:
                    return False
            except (ValueError, IndexError):
                return False
            return True

        # Compare levels and suits
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}

        try:
            my_level = int(bid[0])
            # Hard cap: no bid level above 7 is ever legal in bridge
            if my_level > 7:
                return False
            my_suit = bid[1:] if 'NT' not in bid else 'NT'
            if my_suit.startswith('N'):
                my_suit = 'NT'

            last_level = int(last_bid[0])
            last_suit = last_bid[1:] if 'NT' not in last_bid else 'NT'
            if last_suit.startswith('N'):
                last_suit = 'NT'

            # Higher level always OK
            if my_level > last_level:
                return True

            # Same level, need higher suit
            if my_level == last_level:
                return suit_rank.get(my_suit, 0) > suit_rank.get(last_suit, 0)

            return False

        except (ValueError, IndexError):
            return False

    def list_available_rules(self, category: str = None) -> List[Dict]:
        """List all available bidding rules for inspection."""
        return self.interpreter.list_rules(category)

    def get_resolver_stats(self) -> Dict:
        """Get conflict resolver statistics (vetoes, reviews, etc.)."""
        return self.conflict_resolver.get_stats()

    def reset_resolver_stats(self):
        """Reset conflict resolver statistics."""
        self.conflict_resolver.reset_stats()

    def get_fallback_stats(self) -> Dict:
        """Get bid statistics. V1 fallback has been removed — always returns 0 fallbacks."""
        return {
            'total_bids': self._total_bid_count,
            'v1_fallbacks': 0,
            'v2_schema_hits': self._total_bid_count,
            'fallback_rate': 0.0
        }

    def reset_fallback_stats(self):
        """Reset bid statistics."""
        self._total_bid_count = 0

    def evaluate_user_bid(
        self,
        hand: Hand,
        user_bid: str,
        auction_history: List[str],
        my_position: str,
        vulnerability: str = 'None',
        dealer: str = 'North'
    ) -> 'V2BiddingFeedback':
        """
        Evaluate a user's bid against V2 schema rules.

        This is the unified method for user bid evaluation, replacing
        the V1 heuristic-based approach with schema-driven analysis.

        Key advantages:
        1. Alternatives come from actual schema rules (not heuristics)
        2. Same rules explain AI bids and evaluate user bids
        3. Transparent - can show exactly which rules matched

        Args:
            hand: User's Hand object
            user_bid: The bid the user made
            auction_history: List of previous bids
            my_position: User's position (North/East/South/West)
            vulnerability: Vulnerability string
            dealer: Dealer position

        Returns:
            V2BiddingFeedback object with evaluation results
        """
        # Lazy import to avoid circular dependency
        from engine.v2.feedback.bid_evaluator import V2BidEvaluator

        evaluator = V2BidEvaluator(self)
        return evaluator.evaluate_bid(
            hand, user_bid, auction_history,
            my_position, vulnerability, dealer
        )


# Create singleton for easy import
_default_engine = None


def get_schema_engine() -> BiddingEngineV2Schema:
    """Get the default schema-driven engine instance."""
    global _default_engine
    if _default_engine is None:
        _default_engine = BiddingEngineV2Schema()
    return _default_engine
