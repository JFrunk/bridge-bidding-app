"""
Learning Feedback Generator

Generates structured, educational feedback that helps users understand:
1. What their bid promised (the message sent)
2. What their hand actually is (the reality)
3. The mismatch (the error)
4. The consequence (what partner will assume/do)
5. The principle (generalizable takeaway)

This is the "teaching" layer on top of bid evaluation.
"""

import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Tuple

from engine.hand import Hand
from engine.feedback.bid_meanings import BidMeaningLookup, BidMeaning, get_bid_meaning

logger = logging.getLogger(__name__)


@dataclass
class LearningFeedback:
    """
    Structured learning feedback for a bidding decision.

    Designed to teach users the "why" behind bidding recommendations,
    not just that their bid was wrong.
    """
    # What user's bid promised
    your_bid_promised: str  # "Your bid (2♠) tells partner: 6-9 HCP, 3+ spade support"

    # What hand actually is
    your_hand_is: str  # "Your hand has 11 HCP with 4-card spade support"

    # The mismatch
    the_mismatch: str  # "You undersold your hand by promising weaker values"

    # The consequence
    the_consequence: str  # "Partner will assume you're weaker and may pass when game is makeable"

    # The principle (better bid suggestion)
    the_principle: str  # "With 10-12 HCP and 4+ support, use a limit raise (3♠)"

    # Optional: error category for tracking
    mismatch_type: str = "unknown"  # "undersold", "overbid", "wrong_shape", etc.

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Consequence templates based on mismatch type
CONSEQUENCES = {
    'undersold_hcp': "Partner will assume you're weaker and may pass when game is makeable",
    'undersold_support': "Partner may not realize the strength of the fit",
    'overbid_hcp': "Partner may bid too high expecting more strength from you",
    'overbid_support': "Partner may count on support that isn't there",
    'wrong_shape': "Partner may choose the wrong strain based on your promise",
    'wrong_forcing': "Partner may pass when they shouldn't, or feel forced to bid when they should pass",
    'missed_convention': "You missed an opportunity to use a conventional bid that would better describe your hand",
}

# Principle templates based on mismatch type
PRINCIPLES = {
    'undersold_hcp_raise': "With invitational values (10-12 HCP) and good support, show your strength with a limit raise",
    'undersold_hcp_game': "With game-forcing values (13+ HCP), make sure to reach game - don't stop below",
    'overbid_hcp': "Bid according to your actual values - overbidding can lead to unmakeable contracts",
    'wrong_shape_balanced': "With balanced shape, prefer notrump over suit contracts",
    'wrong_shape_suit': "With a long suit, show it - don't hide your shape from partner",
    'support_priority': "Supporting partner's suit takes priority over showing your own suit when you have a fit",
    'convention_use': "When a convention applies to your hand, using it gives partner more information",
    'forcing_awareness': "Be aware of forcing bids - new suits by responder are forcing, raises are not",
}


class LearningFeedbackGenerator:
    """
    Generates structured learning feedback by comparing:
    - What the user's bid promised
    - What the user's hand actually has
    - What the optimal bid would have promised
    """

    def __init__(self, system: str = "SAYC"):
        self.meaning_lookup = BidMeaningLookup(system=system)

    def generate(
        self,
        user_bid: str,
        optimal_bid: str,
        hand: Hand,
        auction_context: Dict[str, Any],
        optimal_explanation: str = ""
    ) -> Optional[LearningFeedback]:
        """
        Generate learning feedback for a suboptimal bid.

        Args:
            user_bid: The bid the user made
            optimal_bid: The recommended bid
            hand: The user's hand
            auction_context: Context (partner_last_bid, is_response, etc.)
            optimal_explanation: Explanation of why optimal bid is best

        Returns:
            LearningFeedback if meaningful feedback can be generated
        """
        # Don't generate feedback if user bid was optimal
        if user_bid == optimal_bid:
            return None

        # Look up what user's bid promised
        user_meaning = self.meaning_lookup.get_meaning(user_bid, auction_context)

        # Look up what optimal bid promises
        optimal_meaning = self.meaning_lookup.get_meaning(optimal_bid, auction_context)

        # Analyze hand characteristics
        hand_chars = self._analyze_hand(hand, auction_context)

        # Generate the five learning components
        your_bid_promised = self._generate_your_bid_promised(user_bid, user_meaning)
        your_hand_is = self._generate_your_hand_is(hand, hand_chars, auction_context)
        mismatch_type, the_mismatch = self._analyze_mismatch(
            user_meaning, optimal_meaning, hand, hand_chars
        )
        the_consequence = self._generate_consequence(mismatch_type)
        the_principle = self._generate_principle(
            mismatch_type, optimal_bid, optimal_meaning, optimal_explanation
        )

        return LearningFeedback(
            your_bid_promised=your_bid_promised,
            your_hand_is=your_hand_is,
            the_mismatch=the_mismatch,
            the_consequence=the_consequence,
            the_principle=the_principle,
            mismatch_type=mismatch_type
        )

    def _analyze_hand(self, hand: Hand, context: Dict) -> Dict[str, Any]:
        """Analyze hand characteristics relevant to the auction."""
        # Get support for partner's suit if applicable
        partner_suit = self._extract_suit(context.get('partner_last_bid', ''))
        support_count = 0
        if partner_suit:
            support_count = self._count_support(hand, partner_suit)

        return {
            'hcp': hand.hcp,
            'total_points': getattr(hand, 'total_points', hand.hcp),
            'longest_suit': self._get_longest_suit(hand),
            'longest_suit_length': self._get_longest_suit_length(hand),
            'is_balanced': getattr(hand, 'is_balanced', self._check_balanced(hand)),
            'partner_suit': partner_suit,
            'support_for_partner': support_count,
            'spades': len([c for c in hand.cards if c.suit == '♠' or c.suit == 'S']),
            'hearts': len([c for c in hand.cards if c.suit == '♥' or c.suit == 'H']),
            'diamonds': len([c for c in hand.cards if c.suit == '♦' or c.suit == 'D']),
            'clubs': len([c for c in hand.cards if c.suit == '♣' or c.suit == 'C']),
        }

    def _generate_your_bid_promised(self, user_bid: str, meaning: Optional[BidMeaning]) -> str:
        """Generate the 'what your bid promised' text."""
        if meaning:
            return f"Your bid ({user_bid}) tells partner: \"{meaning.message_to_partner}\""
        return f"Your bid ({user_bid}) has a specific meaning in the auction"

    def _generate_your_hand_is(self, hand: Hand, chars: Dict, context: Dict) -> str:
        """Generate the 'what your hand is' text."""
        parts = [f"{chars['hcp']} HCP"]

        # Mention support if relevant
        if chars['partner_suit'] and chars['support_for_partner'] >= 3:
            parts.append(f"{chars['support_for_partner']}-card {chars['partner_suit']} support")

        # Mention shape
        if chars['is_balanced']:
            parts.append("balanced shape")
        elif chars['longest_suit_length'] >= 5:
            parts.append(f"{chars['longest_suit_length']}-card {chars['longest_suit']}")

        # Add strength descriptor
        strength = self._hcp_descriptor(chars['hcp'])
        if strength:
            parts.append(f"({strength})")

        return "Your hand has " + ", ".join(parts)

    def _hcp_descriptor(self, hcp: int) -> str:
        """Get a descriptor for HCP strength."""
        if hcp <= 5:
            return "weak"
        elif hcp <= 9:
            return "minimum responding values"
        elif hcp <= 12:
            return "invitational strength"
        elif hcp <= 15:
            return "game-forcing values"
        elif hcp <= 18:
            return "strong"
        else:
            return "very strong"

    def _analyze_mismatch(
        self,
        user_meaning: Optional[BidMeaning],
        optimal_meaning: Optional[BidMeaning],
        hand: Hand,
        chars: Dict
    ) -> Tuple[str, str]:
        """
        Analyze the mismatch between bid promise and hand reality.

        Returns (mismatch_type, mismatch_description)
        """
        if not user_meaning:
            return "unknown", "Your bid didn't match what your hand shows"

        hcp = chars['hcp']
        user_hcp_min, user_hcp_max = user_meaning.hcp_range

        # Check HCP mismatch
        if hcp > user_hcp_max:
            return "undersold_hcp", (
                f"You undersold your hand by promising {user_hcp_min}-{user_hcp_max} HCP "
                f"when you actually have {hcp}"
            )

        if hcp < user_hcp_min:
            return "overbid_hcp", (
                f"You overbid your hand by promising {user_hcp_min}+ HCP "
                f"when you only have {hcp}"
            )

        # Check support mismatch (if raising)
        if user_meaning.support_promised:
            actual_support = chars.get('support_for_partner', 0)
            if actual_support < user_meaning.support_promised:
                return "overbid_support", (
                    f"You promised {user_meaning.support_promised}+ card support "
                    f"but only have {actual_support}"
                )
            if optimal_meaning and optimal_meaning.support_promised:
                if actual_support >= optimal_meaning.support_promised > user_meaning.support_promised:
                    return "undersold_support", (
                        f"With {actual_support}-card support, you could show more enthusiasm"
                    )

        # Check shape mismatch
        if 'balanced' in user_meaning.shape_description and not chars['is_balanced']:
            return "wrong_shape", "Your bid promised balanced shape but your hand is unbalanced"

        if user_meaning.suit_requirements:
            for suit, required in user_meaning.suit_requirements.items():
                actual = chars.get(suit, 0)
                if actual < required:
                    return "wrong_shape", (
                        f"Your bid promised {required}+ {suit} but you only have {actual}"
                    )

        # Default mismatch
        return "general", "Your bid doesn't accurately describe your hand"

    def _generate_consequence(self, mismatch_type: str) -> str:
        """Generate consequence text based on mismatch type."""
        # Map specific types to general categories for lookup
        if mismatch_type.startswith('undersold'):
            return CONSEQUENCES.get('undersold_hcp',
                "Partner will make decisions based on incorrect information about your hand")
        elif mismatch_type.startswith('overbid'):
            return CONSEQUENCES.get('overbid_hcp',
                "Partner may bid too high based on the strength you showed")
        elif mismatch_type == 'wrong_shape':
            return CONSEQUENCES.get('wrong_shape',
                "Partner may choose a contract that doesn't fit your actual shape")
        else:
            return "Partner's next bid will be based on what you promised, not what you have"

    def _generate_principle(
        self,
        mismatch_type: str,
        optimal_bid: str,
        optimal_meaning: Optional[BidMeaning],
        optimal_explanation: str
    ) -> str:
        """Generate the principle/better bid text."""
        # Start with what the better bid is
        if optimal_meaning:
            better_part = (
                f"Better: {optimal_bid} - shows {optimal_meaning.message_to_partner}"
            )
        else:
            better_part = f"Better: {optimal_bid}"

        # Add principle based on mismatch type
        if mismatch_type == 'undersold_hcp':
            principle = PRINCIPLES.get('undersold_hcp_raise',
                "Bid according to your strength - don't hide values from partner")
        elif mismatch_type == 'overbid_hcp':
            principle = PRINCIPLES.get('overbid_hcp',
                "Bid what you have, not what you wish you had")
        elif mismatch_type == 'wrong_shape':
            principle = PRINCIPLES.get('wrong_shape_suit',
                "Show your actual shape to help partner make good decisions")
        else:
            principle = "Accurate bidding helps partner make the right decisions"

        return f"{better_part}. Remember: {principle}"

    # Helper methods

    def _extract_suit(self, bid: str) -> Optional[str]:
        """Extract suit from a bid string."""
        if not bid or bid in ['Pass', 'X', 'XX']:
            return None
        for suit in ['♠', '♥', '♦', '♣', 'S', 'H', 'D', 'C', 'NT']:
            if suit in bid:
                return suit
        return None

    def _count_support(self, hand: Hand, suit: str) -> int:
        """Count cards in the partner's suit."""
        suit_map = {
            '♠': ['♠', 'S'], '♥': ['♥', 'H'],
            '♦': ['♦', 'D'], '♣': ['♣', 'C'],
            'S': ['♠', 'S'], 'H': ['♥', 'H'],
            'D': ['♦', 'D'], 'C': ['♣', 'C'],
        }
        target_suits = suit_map.get(suit, [suit])
        return len([c for c in hand.cards if c.suit in target_suits])

    def _get_longest_suit(self, hand: Hand) -> str:
        """Get the longest suit in hand."""
        counts = {
            '♠': len([c for c in hand.cards if c.suit in ['♠', 'S']]),
            '♥': len([c for c in hand.cards if c.suit in ['♥', 'H']]),
            '♦': len([c for c in hand.cards if c.suit in ['♦', 'D']]),
            '♣': len([c for c in hand.cards if c.suit in ['♣', 'C']]),
        }
        return max(counts, key=counts.get)

    def _get_longest_suit_length(self, hand: Hand) -> int:
        """Get the length of the longest suit."""
        counts = [
            len([c for c in hand.cards if c.suit in ['♠', 'S']]),
            len([c for c in hand.cards if c.suit in ['♥', 'H']]),
            len([c for c in hand.cards if c.suit in ['♦', 'D']]),
            len([c for c in hand.cards if c.suit in ['♣', 'C']]),
        ]
        return max(counts)

    def _check_balanced(self, hand: Hand) -> bool:
        """Check if hand is balanced (no void, no singleton, at most one doubleton)."""
        counts = [
            len([c for c in hand.cards if c.suit in ['♠', 'S']]),
            len([c for c in hand.cards if c.suit in ['♥', 'H']]),
            len([c for c in hand.cards if c.suit in ['♦', 'D']]),
            len([c for c in hand.cards if c.suit in ['♣', 'C']]),
        ]
        if 0 in counts or 1 in counts:  # Void or singleton
            return False
        if counts.count(2) > 1:  # More than one doubleton
            return False
        return True


# Convenience function
def generate_learning_feedback(
    user_bid: str,
    optimal_bid: str,
    hand: Hand,
    auction_context: Dict[str, Any],
    optimal_explanation: str = "",
    system: str = "SAYC"
) -> Optional[LearningFeedback]:
    """
    Convenience function to generate learning feedback.

    Args:
        user_bid: The bid the user made
        optimal_bid: The recommended bid
        hand: The user's hand
        auction_context: Context dict
        optimal_explanation: Explanation of optimal bid
        system: Bidding system (default SAYC)

    Returns:
        LearningFeedback if meaningful feedback can be generated
    """
    generator = LearningFeedbackGenerator(system=system)
    return generator.generate(user_bid, optimal_bid, hand, auction_context, optimal_explanation)
