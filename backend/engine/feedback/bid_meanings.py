"""
Bid Meaning Lookup System

Convention-agnostic system for looking up what a bid "promises" in a given context.
Uses the V2 schema system to extract bid meanings, supporting SAYC now and
extensible to 2/1 and other conventions via additional schema files.

The key insight is that the same schemas that drive bidding decisions also
contain the information about what each bid promises (HCP, shape, forcing status).
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BidMeaning:
    """
    What a bid promises to partner.

    This is the "message" the bid sends - the contract between bidder and partner
    about what the hand looks like.
    """
    bid: str
    rule_id: str                          # e.g., "simple_raise_spades"
    system: str                           # e.g., "SAYC", "2/1"
    hcp_range: Tuple[int, int]            # (min, max) from conditions
    suit_requirements: Dict[str, int]     # {suit: min_length} e.g., {"spades": 4}
    support_promised: Optional[int]       # If raising partner
    shape_description: str                # "balanced", "5+ spades", etc.
    forcing_status: str                   # "sign-off", "invitational", "forcing", "game-forcing"
    message_to_partner: str               # Human-readable: "I have 6-9 HCP with 3+ spade support"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'bid': self.bid,
            'rule_id': self.rule_id,
            'system': self.system,
            'hcp_range': list(self.hcp_range),
            'suit_requirements': self.suit_requirements,
            'support_promised': self.support_promised,
            'shape_description': self.shape_description,
            'forcing_status': self.forcing_status,
            'message_to_partner': self.message_to_partner
        }


class BidMeaningLookup:
    """
    Convention-agnostic bid meaning lookup using V2 schemas.

    Finds the schema rule that best matches a bid in a given context,
    then extracts the "promise" (HCP range, shape, forcing status).

    Usage:
        lookup = BidMeaningLookup(system="SAYC")
        meaning = lookup.get_meaning("2♠", {"partner_last_bid": "1♠", "is_response": True})
        # Returns BidMeaning with hcp_range=(6,9), support_promised=3, etc.

    Future extensibility:
        lookup = BidMeaningLookup(system="2/1")  # Load 2/1 schemas instead
    """

    def __init__(self, system: str = "SAYC"):
        """
        Initialize with a bidding system.

        Args:
            system: The bidding system to use ("SAYC", "2/1", etc.)
        """
        self.system = system
        self.schemas: Dict[str, Dict] = {}
        self._load_schemas()

    def _load_schemas(self):
        """Load all JSON schema files for the configured system."""
        # Determine schema directory
        schema_dir = Path(__file__).parent.parent / 'v2' / 'schemas'

        # Load schemas matching the system prefix
        prefix = self.system.lower().replace('/', '_')  # "SAYC" -> "sayc", "2/1" -> "2_1"

        for schema_file in schema_dir.glob(f'{prefix}_*.json'):
            try:
                with open(schema_file, 'r') as f:
                    schema = json.load(f)
                    category = schema.get('category', schema_file.stem)
                    self.schemas[category] = schema
                    logger.debug(f"Loaded schema: {schema_file.name} ({len(schema.get('rules', []))} rules)")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load schema {schema_file}: {e}")

    def get_meaning(self, bid: str, auction_context: Dict[str, Any]) -> Optional[BidMeaning]:
        """
        Look up what a bid promises in the given context.

        Args:
            bid: The bid string (e.g., "2♠", "1NT", "Pass")
            auction_context: Context dict with keys like:
                - partner_last_bid: str
                - opening_bid: str
                - is_response: bool
                - is_opening: bool
                - is_contested: bool

        Returns:
            BidMeaning if found, None otherwise
        """
        # Normalize bid (handle unicode suits)
        bid = self._normalize_bid(bid)

        # Special case: Pass doesn't have a schema rule
        if bid == 'Pass':
            return self._pass_meaning()

        # Find matching rule across all loaded schemas
        matching_rule = self._find_matching_rule(bid, auction_context)

        if matching_rule:
            return self._rule_to_meaning(matching_rule)

        # Fallback: generate a basic meaning from the bid itself
        return self._fallback_meaning(bid, auction_context)

    def _normalize_bid(self, bid: str) -> str:
        """Normalize bid string (handle different suit representations)."""
        # Already using unicode suits - good
        return bid

    def _find_matching_rule(self, bid: str, context: Dict[str, Any]) -> Optional[Dict]:
        """
        Find the schema rule that best matches this bid in context.

        Uses a scoring system to find the most specific matching rule.
        """
        best_match = None
        best_score = -1

        for category, schema in self.schemas.items():
            for rule in schema.get('rules', []):
                # Check if bid matches
                rule_bid = rule.get('bid', '')
                if not self._bid_matches(rule_bid, bid, context):
                    continue

                # Score how well the context matches
                score = self._score_context_match(rule, context)

                if score > best_score:
                    best_score = score
                    best_match = rule

        return best_match if best_score > 0 else None

    def _bid_matches(self, rule_bid: str, actual_bid: str, context: Dict = None) -> bool:
        """Check if a rule's bid pattern matches the actual bid."""
        # Exact match
        if rule_bid == actual_bid:
            return True

        # Pattern matching for generic rules like "1{suit}"
        if '{suit}' in rule_bid:
            # Extract level from rule
            rule_level = rule_bid[0] if rule_bid[0].isdigit() else None
            actual_level = actual_bid[0] if actual_bid[0].isdigit() else None

            if rule_level and actual_level and rule_level == actual_level:
                # Check if actual bid has a suit
                actual_suit = actual_bid[1:] if len(actual_bid) > 1 else ''
                if actual_suit in ['♠', '♥', '♦', '♣', 'S', 'H', 'D', 'C']:
                    return True

        # Pattern matching for "{partner_suit}" - e.g., "2{partner_suit}" matches "2♠" if partner bid 1♠
        if '{partner_suit}' in rule_bid and context:
            partner_bid = context.get('partner_last_bid', '')
            if partner_bid and len(partner_bid) >= 2:
                partner_suit = partner_bid[1:]  # Get suit from partner's bid
                # Extract level from rule pattern
                rule_level = rule_bid[0] if rule_bid[0].isdigit() else None
                actual_level = actual_bid[0] if actual_bid[0].isdigit() else None
                actual_suit = actual_bid[1:] if len(actual_bid) > 1 else ''

                if rule_level and actual_level and rule_level == actual_level:
                    if actual_suit == partner_suit:
                        return True

        return False

    def _score_context_match(self, rule: Dict, context: Dict) -> int:
        """
        Score how well a rule's conditions match the auction context.

        Higher score = better match. Returns 0 if conditions don't match.
        """
        conditions = rule.get('conditions', {})
        if not conditions:
            return 1  # Rule with no conditions matches weakly

        score = 1  # Base score for having conditions

        # Check key context conditions
        if 'is_opening' in conditions:
            if context.get('is_opening') == conditions['is_opening']:
                score += 10
            else:
                return 0  # Hard mismatch

        if 'is_response' in conditions:
            if context.get('is_response') == conditions['is_response']:
                score += 10
            else:
                return 0

        if 'partner_last_bid' in conditions:
            partner_cond = conditions['partner_last_bid']
            partner_bid = context.get('partner_last_bid')
            if isinstance(partner_cond, dict) and 'in' in partner_cond:
                if partner_bid in partner_cond['in']:
                    score += 20  # Matches one of the allowed bids
                else:
                    return 0
            elif partner_bid == partner_cond:
                score += 20  # Very specific match
            else:
                return 0

        if 'opening_bid' in conditions:
            opening = conditions['opening_bid']
            if isinstance(opening, dict) and 'in' in opening:
                if context.get('opening_bid') in opening['in']:
                    score += 15
                else:
                    return 0
            elif context.get('opening_bid') == opening:
                score += 15
            else:
                return 0

        if 'is_contested' in conditions:
            if context.get('is_contested') == conditions['is_contested']:
                score += 5
            # Don't hard fail on this - it's optional

        return score

    def _rule_to_meaning(self, rule: Dict) -> BidMeaning:
        """Convert a schema rule to a BidMeaning object."""
        conditions = rule.get('conditions', {})

        # Extract HCP range
        hcp = conditions.get('hcp', {})
        hcp_min = hcp.get('min', 0) if isinstance(hcp, dict) else 0
        hcp_max = hcp.get('max', 40) if isinstance(hcp, dict) else 40

        # Extract suit requirements
        suit_requirements = {}
        for suit in ['spades', 'hearts', 'diamonds', 'clubs']:
            length_key = f'{suit}_length'
            if length_key in conditions:
                length = conditions[length_key]
                if isinstance(length, dict) and 'min' in length:
                    suit_requirements[suit] = length['min']

        # Extract support for partner
        support = conditions.get('support_for_partner', {})
        support_promised = support.get('min') if isinstance(support, dict) else None

        # Determine shape description
        shape_desc = self._derive_shape_description(conditions, suit_requirements)

        # Map forcing status
        forcing_raw = rule.get('forcing', 'none')
        forcing_status = self._map_forcing_status(forcing_raw)

        # Generate human-readable message
        message = self._generate_message(
            rule.get('bid', ''),
            hcp_min, hcp_max,
            suit_requirements,
            support_promised,
            shape_desc,
            forcing_status,
            rule.get('explanation', '')
        )

        return BidMeaning(
            bid=rule.get('bid', ''),
            rule_id=rule.get('id', 'unknown'),
            system=self.system,
            hcp_range=(hcp_min, hcp_max),
            suit_requirements=suit_requirements,
            support_promised=support_promised,
            shape_description=shape_desc,
            forcing_status=forcing_status,
            message_to_partner=message
        )

    def _derive_shape_description(self, conditions: Dict, suit_requirements: Dict) -> str:
        """Derive a shape description from conditions."""
        if conditions.get('is_balanced'):
            return "balanced"

        # Check for specific suit lengths
        descriptions = []
        for suit, length in suit_requirements.items():
            suit_symbol = {'spades': '♠', 'hearts': '♥', 'diamonds': '♦', 'clubs': '♣'}.get(suit, suit)
            descriptions.append(f"{length}+ {suit_symbol}")

        if descriptions:
            return ", ".join(descriptions)

        return "any shape"

    def _map_forcing_status(self, forcing_raw: str) -> str:
        """Map schema forcing values to human-readable status."""
        mapping = {
            'none': 'sign-off',
            'one_round': 'forcing one round',
            'game': 'game-forcing'
        }
        return mapping.get(forcing_raw, forcing_raw)

    def _generate_message(self, bid: str, hcp_min: int, hcp_max: int,
                          suit_requirements: Dict, support_promised: Optional[int],
                          shape_desc: str, forcing_status: str,
                          explanation: str) -> str:
        """Generate a human-readable message about what the bid promises."""
        parts = []

        # HCP range
        if hcp_max < 40:
            parts.append(f"{hcp_min}-{hcp_max} HCP")
        elif hcp_min > 0:
            parts.append(f"{hcp_min}+ HCP")

        # Support
        if support_promised:
            parts.append(f"{support_promised}+ card support")

        # Suit length (if not already covered by support)
        if suit_requirements and not support_promised:
            for suit, length in suit_requirements.items():
                suit_symbol = {'spades': '♠', 'hearts': '♥', 'diamonds': '♦', 'clubs': '♣'}.get(suit, suit)
                parts.append(f"{length}+ {suit_symbol}")

        # Shape
        if shape_desc == "balanced":
            parts.append("balanced shape")

        if parts:
            return ", ".join(parts)

        # Fallback to schema explanation
        return explanation or f"Shows {bid}"

    def _pass_meaning(self) -> BidMeaning:
        """Return the meaning of Pass."""
        return BidMeaning(
            bid="Pass",
            rule_id="pass",
            system=self.system,
            hcp_range=(0, 40),
            suit_requirements={},
            support_promised=None,
            shape_description="any shape",
            forcing_status="sign-off",
            message_to_partner="Nothing more to say, or no suitable bid available"
        )

    def _fallback_meaning(self, bid: str, context: Dict) -> Optional[BidMeaning]:
        """Generate a basic meaning when no schema rule matches."""
        # Try to parse the bid for basic info
        if bid in ['X', 'XX']:
            return BidMeaning(
                bid=bid,
                rule_id="fallback_double",
                system=self.system,
                hcp_range=(0, 40),
                suit_requirements={},
                support_promised=None,
                shape_description="varies by context",
                forcing_status="forcing one round",
                message_to_partner="Double (meaning depends on auction context)"
            )

        # Extract level and suit from bid like "2♠"
        if len(bid) >= 2 and bid[0].isdigit():
            level = int(bid[0])
            suit_part = bid[1:]

            # Estimate HCP based on level
            hcp_estimates = {
                1: (6, 21),   # Wide range for 1-level
                2: (6, 12),   # Simple raises or weak twos
                3: (10, 15),  # Invitational or preemptive
                4: (12, 17),  # Game level
                5: (15, 18),  # Game or slam try
                6: (16, 40),  # Slam
                7: (20, 40),  # Grand slam
            }

            return BidMeaning(
                bid=bid,
                rule_id="fallback_generic",
                system=self.system,
                hcp_range=hcp_estimates.get(level, (0, 40)),
                suit_requirements={},
                support_promised=None,
                shape_description="unknown",
                forcing_status="unknown",
                message_to_partner=f"Bid of {bid} (exact meaning depends on auction)"
            )

        return None


# Convenience function for quick lookups
_default_lookup: Optional[BidMeaningLookup] = None

def get_bid_meaning(bid: str, auction_context: Dict[str, Any],
                    system: str = "SAYC") -> Optional[BidMeaning]:
    """
    Convenience function to look up a bid's meaning.

    Args:
        bid: The bid to look up (e.g., "2♠")
        auction_context: Context dict with partner_last_bid, is_response, etc.
        system: Bidding system ("SAYC", "2/1", etc.)

    Returns:
        BidMeaning if found, None otherwise
    """
    global _default_lookup

    # Use cached lookup if same system
    if _default_lookup is None or _default_lookup.system != system:
        _default_lookup = BidMeaningLookup(system=system)

    return _default_lookup.get_meaning(bid, auction_context)
