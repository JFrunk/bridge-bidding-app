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
7. Optional V1 fallback when no schema rule matches
"""

import logging
from typing import Dict, Optional, Tuple, List
from engine.hand import Hand
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

    def __init__(self, schema_dir: str = None, simulator=None, use_v1_fallback: bool = True):
        """
        Initialize the schema-driven engine.

        Args:
            schema_dir: Path to schema directory. Defaults to engine/v2/schemas/
            simulator: Optional Monte Carlo simulator for bid validation.
                      If None, conflict resolver operates in pass-through mode.
            use_v1_fallback: If True, falls back to V1 engine when no schema rule matches.
                            This provides better coverage while V2 schemas are incomplete.
        """
        self.interpreter = SchemaInterpreter(schema_dir)
        self._bid_legality_cache = {}
        self.use_v1_fallback = use_v1_fallback
        self._v1_engine = None  # Lazy-loaded
        self._v1_fallback_count = 0
        self._total_bid_count = 0

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

        # Evaluate schemas and get candidates
        candidates = self.interpreter.evaluate_with_details(features)

        if candidates:
            # Find the best legal bid that doesn't violate forcing constraints
            for candidate in candidates:
                bid = candidate.bid

                # Validate bid is legal in the auction
                if not self._is_bid_legal(bid, auction_history):
                    continue

                # Validate against forcing constraints (only in partnership auctions)
                # Skip forcing validation in competitive situations - opponents' bids
                # break forcing sequences between partners
                is_competitive = features.get('is_overcall') or features.get('is_advancer') or features.get('is_competitive_later')
                if not is_competitive:
                    forcing_validation = self.interpreter.validate_bid_against_forcing(bid)
                    if not forcing_validation.is_valid:
                        # Skip this bid if it violates forcing
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

                return (final_bid, final_explanation)

        # No schema rule matched - try V1 fallback if enabled
        if self.use_v1_fallback:
            self._last_rule_id = 'v1_fallback'
            self._last_schema_file = None
            self._last_priority = 0
            return self._get_v1_fallback_bid(hand, auction_history, my_position, vulnerability)

        # Fallback to Pass (but check forcing constraints first)
        self._last_rule_id = 'default_pass'
        self._last_schema_file = None
        self._last_priority = 0
        forcing_validation = self.interpreter.validate_bid_against_forcing("Pass")
        if not forcing_validation.is_valid:
            # Cannot pass - return a warning explanation
            return ('Pass', f'Warning: {forcing_validation.reason}')

        return ('Pass', 'No applicable bidding rule found')

    def _get_v1_engine(self):
        """Lazy-load the V1 engine for fallback."""
        if self._v1_engine is None:
            from engine.bidding_engine import BiddingEngine
            self._v1_engine = BiddingEngine()
        return self._v1_engine

    def _get_v1_fallback_bid(
        self,
        hand: Hand,
        auction_history: List[str],
        my_position: str,
        vulnerability: str
    ) -> Tuple[str, str]:
        """
        Get bid from V1 engine when V2 schema has no matching rule.

        Returns:
            Tuple of (bid, explanation) with V1 fallback note
        """
        self._v1_fallback_count += 1

        try:
            v1_engine = self._get_v1_engine()
            bid, explanation = v1_engine.get_next_bid(
                hand=hand,
                auction_history=auction_history,
                my_position=my_position,
                vulnerability=vulnerability
            )
            # Add note that this came from V1 fallback (useful for debugging)
            logger.debug(f"V2 Schema fallback to V1: {bid} - {explanation}")
            return (bid, explanation)
        except Exception as e:
            logger.warning(f"V1 fallback failed: {e}")
            return ('Pass', f'Fallback error: {str(e)}')

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

    def _is_bid_legal(self, bid: str, auction_history: List[str]) -> bool:
        """
        Check if a bid is legal given the auction history.
        """
        if bid in ['Pass', 'X', 'XX']:
            # X only legal after opponent bid
            if bid == 'X':
                if not auction_history:
                    return False
                # Must have a non-pass bid to double
                for b in reversed(auction_history):
                    if b not in ['Pass']:
                        return b not in ['X', 'XX']
                return False

            # XX only legal after X
            if bid == 'XX':
                if not auction_history:
                    return False
                for b in reversed(auction_history):
                    if b != 'Pass':
                        return b == 'X'
                return False

            return True  # Pass always legal

        # Get last non-pass bid
        last_bid = None
        for b in reversed(auction_history):
            if b not in ['Pass', 'X', 'XX']:
                last_bid = b
                break

        if last_bid is None:
            return True  # First real bid

        # Compare levels and suits
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}

        try:
            my_level = int(bid[0])
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
        """Get V1 fallback usage statistics."""
        return {
            'total_bids': self._total_bid_count,
            'v1_fallbacks': self._v1_fallback_count,
            'v2_schema_hits': self._total_bid_count - self._v1_fallback_count,
            'fallback_rate': (
                self._v1_fallback_count / max(1, self._total_bid_count) * 100
            )
        }

    def reset_fallback_stats(self):
        """Reset V1 fallback statistics."""
        self._v1_fallback_count = 0
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
