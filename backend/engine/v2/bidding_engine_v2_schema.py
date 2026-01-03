"""
Schema-Driven Bidding Engine V2

This engine uses JSON schema files to define bidding rules rather than
Python code. This allows for:
1. Easier rule modifications without code changes
2. System toggling (SAYC vs 2/1) via different schema files
3. Machine-readable rules for analysis and testing
4. Cleaner separation of bidding knowledge from engine logic
"""

from typing import Dict, Optional, Tuple, List
from engine.hand import Hand
from engine.v2.features.enhanced_extractor import extract_flat_features
from engine.v2.interpreters.schema_interpreter import SchemaInterpreter, BidCandidate


class BiddingEngineV2Schema:
    """
    Schema-driven bidding engine.

    Uses JSON schema files to determine bids rather than Python modules.
    This is the core of the refactored V2 approach.
    """

    def __init__(self, schema_dir: str = None):
        """
        Initialize the schema-driven engine.

        Args:
            schema_dir: Path to schema directory. Defaults to engine/v2/schemas/
        """
        self.interpreter = SchemaInterpreter(schema_dir)
        self._bid_legality_cache = {}

    def get_next_bid(
        self,
        hand: Hand,
        auction_history: List[str],
        my_position: str,
        vulnerability: str = 'None',
        dealer: str = 'North'
    ) -> Tuple[str, str]:
        """
        Get the next bid for a hand.

        Args:
            hand: Hand object
            auction_history: List of previous bids
            my_position: Position of bidder (North/East/South/West)
            vulnerability: Vulnerability string
            dealer: Dealer position

        Returns:
            Tuple of (bid, explanation)
        """
        # Extract features in flat format for schema evaluation
        features = extract_flat_features(
            hand, auction_history, my_position, vulnerability, dealer
        )

        # Add auction-derived features needed for schema rules
        features = self._enhance_features(features, hand, auction_history)

        # Evaluate schemas
        result = self.interpreter.evaluate(features)

        if result:
            bid, explanation = result
            # Validate bid is legal
            if self._is_bid_legal(bid, auction_history):
                return (bid, explanation)

        # Fallback to Pass
        return ('Pass', 'No applicable bidding rule found')

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
            from engine.v2.features.enhanced_extractor import evaluate_suit_quality
            features['suit_quality_longest'] = evaluate_suit_quality(hand, longest_suit)

        # Check if all unbid suits have support (for takeout doubles)
        opening_bid = features.get('opening_bid')
        if opening_bid and len(opening_bid) >= 2:
            opening_suit = opening_bid[1] if opening_bid[0].isdigit() else None
            if opening_suit:
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
                interf_suit = interf_bid[1] if len(interf_bid) >= 2 and interf_bid[0].isdigit() else None
                opening_suit = opening_bid[1] if len(opening_bid) >= 2 and opening_bid[0].isdigit() else None

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


# Create singleton for easy import
_default_engine = None


def get_schema_engine() -> BiddingEngineV2Schema:
    """Get the default schema-driven engine instance."""
    global _default_engine
    if _default_engine is None:
        _default_engine = BiddingEngineV2Schema()
    return _default_engine
