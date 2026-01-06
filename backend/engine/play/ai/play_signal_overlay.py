"""
Tactical Play Signal Overlay - Human-Like Card Selection from DDS Equivalence Sets

This module intercepts DDS's "perfect" choices and filters them through standard
bridge signaling conventions, making the AI play like a knowledgeable human partner.

The Problem:
- DDS treats all equal-rank cards identically (e.g., discarding ♠2 vs ♠4 from length of 5)
- A human uses these choices to signal information to partner
- Without this overlay, DDS plays look random and confusing to users

The Solution:
- When DDS returns multiple "equivalent" cards (same trick outcome), this overlay
  selects the card that follows standard bridge conventions
- Every selection includes a `signal_reason` explaining WHY, enabling educational feedback

Signal Categories Implemented:
1. Second Hand Low - Preserve honors, let partner play third hand high
2. Third Hand High - Force declarer to use high cards
3. Bottom of Sequence - Playing Q from KQJ signals the K
4. Top of Sequence - Leading K from KQJ promises Q and J
5. Attitude Signals - High card encourages, low discourages
6. Count Signals - High-low shows even count, low-high shows odd
7. Discard from Length - Protect stoppers, discard from weak suits

Usage:
    from engine.play.ai.play_signal_overlay import TacticalPlayFilter

    filter = TacticalPlayFilter()
    selected, reason = filter.select_tactical_card(
        equivalence_set=tied_cards,
        game_state=state,
        position='S',
        hand=hand
    )

    # reason: "2nd Hand Low: Preserving higher honors for later rounds."
"""

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
import os

# Import Card type
from engine.hand import Card, Hand


class PlayContext(Enum):
    """Context types for card selection decisions"""
    OPENING_LEAD = "opening_lead"
    MIDHAND_LEAD = "midhand_lead"
    SECOND_HAND_FOLLOW = "second_hand_follow"
    THIRD_HAND_FOLLOW = "third_hand_follow"
    FOURTH_HAND_FOLLOW = "fourth_hand_follow"
    DISCARD_FIRST = "discard_first"
    DISCARD_SUBSEQUENT = "discard_subsequent"
    LEAD_FROM_HONOR_SEQUENCE = "lead_from_honor_sequence"
    FOLLOW_FROM_HONOR_SEQUENCE = "follow_from_honor_sequence"
    TRUMP_MANAGEMENT = "trump_management"


class SignalHeuristic(Enum):
    """Heuristic types for card selection"""
    MIN_OF_EQUALS = "min_of_equals"           # Play lowest (2nd hand low)
    MAX_OF_EQUALS = "max_of_equals"           # Play highest (3rd hand high)
    TOP_OF_SEQUENCE = "top_of_sequence"       # Lead K from KQJ
    BOTTOM_OF_SEQUENCE = "bottom_of_sequence" # Play Q from KQJ when following
    ATTITUDE_SIGNAL = "attitude_signal"       # High=encourage, low=discourage
    COUNT_SIGNAL = "count_signal"             # High-low=even, low-high=odd
    CHEAPEST_WINNER = "cheapest_winner"       # Win with lowest card possible
    PROTECT_STOPPERS = "protect_stoppers"     # Don't discard lone honors
    DISCARD_FROM_LENGTH = "discard_from_length"  # Discard low from long suits


@dataclass
class SignalResult:
    """Result of signal-based card selection"""
    card: Card
    heuristic: SignalHeuristic
    reason: str
    context: PlayContext
    is_optimal: bool = True  # True if this follows standard conventions


class TacticalPlayFilter:
    """
    Filters DDS equivalence sets through standard bridge signaling conventions.

    When multiple cards achieve the same DDS trick count, this filter selects
    the card that follows human signaling conventions and provides educational
    feedback explaining the choice.
    """

    # Rank values for comparison (2=2, ..., A=14)
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'T': 10, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the tactical filter.

        Args:
            config_path: Optional path to play_signals.json config file.
                        If None, uses default embedded rules.
        """
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load signal configuration from JSON or use defaults"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)

        # Default embedded configuration
        return {
            "defense_signals": [
                {
                    "context": "SECOND_HAND_FOLLOW",
                    "priority": 1,
                    "heuristic": "MIN_OF_EQUALS",
                    "reason": "2nd Hand Low: Preserving higher honors for later rounds."
                },
                {
                    "context": "THIRD_HAND_FOLLOW",
                    "priority": 1,
                    "heuristic": "MAX_OF_EQUALS",
                    "reason": "3rd Hand High: Forcing declarer to use their highest resources."
                },
                {
                    "context": "LEAD_FROM_HONOR_SEQUENCE",
                    "priority": 2,
                    "heuristic": "TOP_OF_SEQUENCE",
                    "reason": "Top of Sequence: Leading the top (e.g., K from KQJ) promises the cards below."
                },
                {
                    "context": "FOLLOW_FROM_HONOR_SEQUENCE",
                    "priority": 2,
                    "heuristic": "BOTTOM_OF_SEQUENCE",
                    "reason": "Bottom of Sequence: Playing Q from KQJ signals possession of the K."
                },
                {
                    "context": "FOURTH_HAND_FOLLOW",
                    "priority": 1,
                    "heuristic": "CHEAPEST_WINNER",
                    "reason": "Win Cheaply: Taking the trick with your lowest winning card."
                },
                {
                    "context": "DISCARD_FIRST",
                    "priority": 3,
                    "heuristic": "ATTITUDE_SIGNAL",
                    "reason": "Attitude Signal: High card encourages this suit, low discourages."
                },
                {
                    "context": "DISCARD_SUBSEQUENT",
                    "priority": 3,
                    "heuristic": "COUNT_SIGNAL",
                    "reason": "Count Signal: High-low shows even count, low-high shows odd."
                }
            ]
        }

    def select_tactical_card(
        self,
        equivalence_set: List[Card],
        game_state: Any,  # PlayState
        position: str,
        hand: Hand,
        trump_suit: Optional[str] = None,
        want_suit: bool = False  # For attitude signals - do we want partner to lead this?
    ) -> SignalResult:
        """
        Select the tactically correct card from a DDS equivalence set.

        This is the main entry point. Given a set of cards that all achieve
        the same DDS trick count, this method selects the one that follows
        standard bridge conventions.

        Args:
            equivalence_set: List of cards with equal DDS outcomes
            game_state: Current PlayState with trick history
            position: Position making the play ('N', 'E', 'S', 'W')
            hand: Current hand of the player
            trump_suit: Trump suit (None for NT)
            want_suit: For discards - whether we want partner to lead this suit

        Returns:
            SignalResult with selected card, heuristic used, and explanation
        """
        if len(equivalence_set) == 0:
            raise ValueError("Equivalence set cannot be empty")

        if len(equivalence_set) == 1:
            return SignalResult(
                card=equivalence_set[0],
                heuristic=SignalHeuristic.MIN_OF_EQUALS,
                reason="Only one card in equivalence set.",
                context=PlayContext.SECOND_HAND_FOLLOW,
                is_optimal=True
            )

        # Determine the play context
        context = self._determine_context(game_state, position, hand, equivalence_set)

        # Apply the appropriate heuristic based on context
        if context == PlayContext.OPENING_LEAD:
            return self._select_opening_lead(equivalence_set, hand, trump_suit)

        elif context == PlayContext.MIDHAND_LEAD:
            return self._select_midhand_lead(equivalence_set, hand, trump_suit)

        elif context == PlayContext.SECOND_HAND_FOLLOW:
            return self._select_second_hand(equivalence_set, game_state)

        elif context == PlayContext.THIRD_HAND_FOLLOW:
            return self._select_third_hand(equivalence_set, game_state, hand)

        elif context == PlayContext.FOURTH_HAND_FOLLOW:
            return self._select_fourth_hand(equivalence_set, game_state)

        elif context in [PlayContext.DISCARD_FIRST, PlayContext.DISCARD_SUBSEQUENT]:
            return self._select_discard(equivalence_set, hand, trump_suit,
                                       want_suit, context)

        elif context == PlayContext.LEAD_FROM_HONOR_SEQUENCE:
            return self._select_lead_from_sequence(equivalence_set, hand)

        elif context == PlayContext.FOLLOW_FROM_HONOR_SEQUENCE:
            return self._select_follow_from_sequence(equivalence_set, hand)

        else:
            # Default: play lowest
            selected = min(equivalence_set, key=lambda c: self._rank_value(c.rank))
            return SignalResult(
                card=selected,
                heuristic=SignalHeuristic.MIN_OF_EQUALS,
                reason="Default: Playing lowest card from equivalent options.",
                context=context,
                is_optimal=True
            )

    def _determine_context(
        self,
        game_state: Any,
        position: str,
        hand: Hand,
        equivalence_set: List[Card]
    ) -> PlayContext:
        """Determine the play context based on trick state"""
        current_trick = getattr(game_state, 'current_trick', [])
        trick_history = getattr(game_state, 'trick_history', [])

        # Leading
        if not current_trick:
            if not trick_history:
                # Check for honor sequence in equivalence set
                if self._has_honor_sequence(equivalence_set, hand):
                    return PlayContext.LEAD_FROM_HONOR_SEQUENCE
                return PlayContext.OPENING_LEAD
            else:
                if self._has_honor_sequence(equivalence_set, hand):
                    return PlayContext.LEAD_FROM_HONOR_SEQUENCE
                return PlayContext.MIDHAND_LEAD

        # Following or discarding
        led_suit = current_trick[0][0].suit
        has_led_suit = any(c.suit == led_suit for c in hand.cards)

        if not has_led_suit:
            # Discarding - check if first discard in this suit
            discarded_suits = self._get_discarded_suits(game_state, position)
            equiv_suit = equivalence_set[0].suit if equivalence_set else None
            if equiv_suit and equiv_suit not in discarded_suits:
                return PlayContext.DISCARD_FIRST
            return PlayContext.DISCARD_SUBSEQUENT

        # Following suit - check for honor sequence
        if self._equivalence_is_honor_sequence(equivalence_set):
            return PlayContext.FOLLOW_FROM_HONOR_SEQUENCE

        # Determine position in trick
        trick_position = len(current_trick)  # 0=lead, 1=second, 2=third, 3=fourth

        if trick_position == 1:
            return PlayContext.SECOND_HAND_FOLLOW
        elif trick_position == 2:
            return PlayContext.THIRD_HAND_FOLLOW
        else:  # trick_position == 3
            return PlayContext.FOURTH_HAND_FOLLOW

    def _select_opening_lead(
        self,
        equivalence_set: List[Card],
        hand: Hand,
        trump_suit: Optional[str]
    ) -> SignalResult:
        """
        Select opening lead from equivalence set.

        Priority:
        1. Top of sequence (KQJ -> K)
        2. 4th best from length in NT
        3. Top of nothing from weak suits
        4. Avoid leading from tenaces (AQ, KJ)
        """
        best_card = None
        best_score = -1000
        best_reason = ""

        # Group hand cards by suit for analysis
        suits_in_hand = {}
        for c in hand.cards:
            if c.suit not in suits_in_hand:
                suits_in_hand[c.suit] = []
            suits_in_hand[c.suit].append(c)

        for card in equivalence_set:
            score = 0
            reason = ""
            suit = card.suit
            rank_val = self._rank_value(card.rank)
            suit_cards = suits_in_hand.get(suit, [])
            suit_ranks = sorted([self._rank_value(c.rank) for c in suit_cards], reverse=True)

            # Check for top of sequence (3+ touching cards)
            if self._is_top_of_sequence(card, suit_cards):
                score += 50
                reason = "Top of Sequence: Leading the top promises the cards immediately below."

            # 4th best from length (4+ cards) in NT
            elif trump_suit is None and len(suit_cards) >= 4:
                if len(suit_ranks) >= 4 and rank_val == suit_ranks[3]:
                    score += 30
                    reason = "4th Best: Leading 4th highest helps partner count the suit."

            # Top of nothing from weak suits (no honors)
            else:
                honors_in_suit = sum(1 for r in suit_ranks if r >= 11)  # J or higher
                if honors_in_suit == 0 and suit_ranks and rank_val == max(suit_ranks):
                    score += 20
                    reason = "Top of Nothing: Leading high from a weak suit signals no honors."

            # Penalize leading from tenaces
            if self._is_tenace_suit(suit_cards):
                score -= 40

            # Prefer longer suits
            score += len(suit_cards) * 5

            # Don't lead trump unless necessary
            if suit == trump_suit:
                score -= 25

            # Slight preference for lower cards when no other factors
            score -= rank_val * 0.1

            if score > best_score:
                best_score = score
                best_card = card
                best_reason = reason

        if not best_card:
            best_card = equivalence_set[0]
            best_reason = "Default selection from equivalent leads."

        if not best_reason:
            best_reason = "Selected based on suit length and safety."

        return SignalResult(
            card=best_card,
            heuristic=SignalHeuristic.TOP_OF_SEQUENCE if "Sequence" in best_reason
                      else SignalHeuristic.MIN_OF_EQUALS,
            reason=best_reason,
            context=PlayContext.OPENING_LEAD,
            is_optimal=True
        )

    def _select_midhand_lead(
        self,
        equivalence_set: List[Card],
        hand: Hand,
        trump_suit: Optional[str]
    ) -> SignalResult:
        """Select card when leading mid-hand (not opening lead)"""
        best_card = None
        best_score = -1000
        best_reason = ""

        suits_in_hand = {}
        for c in hand.cards:
            if c.suit not in suits_in_hand:
                suits_in_hand[c.suit] = []
            suits_in_hand[c.suit].append(c)

        for card in equivalence_set:
            score = 0
            reason = ""
            suit = card.suit
            rank_val = self._rank_value(card.rank)
            suit_cards = suits_in_hand.get(suit, [])

            # Prefer cashing Aces
            if rank_val == 14:  # Ace
                score += 40
                reason = "Cashing Winners: Playing the Ace while you have the lead."

            # Top of sequence is good
            elif self._is_top_of_sequence(card, suit_cards):
                score += 30
                reason = "Top of Sequence: Forcing out higher honors."

            else:
                # Prefer longer suits for development
                score += len(suit_cards) * 3

                # Slight preference for higher cards when leading
                score += rank_val * 0.5

                # Avoid leading from tenaces
                if self._is_tenace_suit(suit_cards):
                    score -= 20

                reason = "Continuing to develop the suit."

            if score > best_score:
                best_score = score
                best_card = card
                best_reason = reason

        if not best_card:
            best_card = equivalence_set[0]
            best_reason = "Default mid-hand lead selection."

        return SignalResult(
            card=best_card,
            heuristic=SignalHeuristic.MAX_OF_EQUALS,
            reason=best_reason,
            context=PlayContext.MIDHAND_LEAD,
            is_optimal=True
        )

    def _select_second_hand(
        self,
        equivalence_set: List[Card],
        game_state: Any
    ) -> SignalResult:
        """
        Select second hand play: 2nd Hand Low

        The classic principle - play low to preserve honors and let partner
        play third hand high.
        """
        # Play lowest from equivalence set
        selected = min(equivalence_set, key=lambda c: self._rank_value(c.rank))

        return SignalResult(
            card=selected,
            heuristic=SignalHeuristic.MIN_OF_EQUALS,
            reason="2nd Hand Low: Preserving higher honors for later rounds.",
            context=PlayContext.SECOND_HAND_FOLLOW,
            is_optimal=True
        )

    def _select_third_hand(
        self,
        equivalence_set: List[Card],
        game_state: Any,
        hand: Hand
    ) -> SignalResult:
        """
        Select third hand play: 3rd Hand High, with sequence exceptions

        - Play high to force declarer's resources
        - Exception: Play bottom of touching honors (Q from KQJ)
        """
        # Check if equivalence set contains a sequence
        if self._equivalence_is_honor_sequence(equivalence_set):
            # Play bottom of sequence to signal the higher honors
            selected = min(equivalence_set, key=lambda c: self._rank_value(c.rank))
            return SignalResult(
                card=selected,
                heuristic=SignalHeuristic.BOTTOM_OF_SEQUENCE,
                reason="Bottom of Sequence: Playing Q from KQJ signals possession of the K.",
                context=PlayContext.THIRD_HAND_FOLLOW,
                is_optimal=True
            )

        # Standard third hand high
        selected = max(equivalence_set, key=lambda c: self._rank_value(c.rank))

        return SignalResult(
            card=selected,
            heuristic=SignalHeuristic.MAX_OF_EQUALS,
            reason="3rd Hand High: Forcing declarer to use their highest resources.",
            context=PlayContext.THIRD_HAND_FOLLOW,
            is_optimal=True
        )

    def _select_fourth_hand(
        self,
        equivalence_set: List[Card],
        game_state: Any
    ) -> SignalResult:
        """
        Select fourth hand play: Win cheaply or give count

        If winning, use lowest winner. If not winning, give count signal.
        """
        current_trick = getattr(game_state, 'current_trick', [])

        # Determine current winner
        if not current_trick:
            # Shouldn't happen for 4th hand, but handle gracefully
            selected = min(equivalence_set, key=lambda c: self._rank_value(c.rank))
            return SignalResult(
                card=selected,
                heuristic=SignalHeuristic.MIN_OF_EQUALS,
                reason="Playing lowest card.",
                context=PlayContext.FOURTH_HAND_FOLLOW,
                is_optimal=True
            )

        led_suit = current_trick[0][0].suit
        current_winner_value = 0

        for played_card, played_pos in current_trick:
            if played_card.suit == led_suit:
                card_val = self._rank_value(played_card.rank)
                if card_val > current_winner_value:
                    current_winner_value = card_val

        # Check if any card in equivalence set can win
        winning_cards = [c for c in equivalence_set
                        if c.suit == led_suit and
                        self._rank_value(c.rank) > current_winner_value]

        if winning_cards:
            # Win with cheapest winner
            selected = min(winning_cards, key=lambda c: self._rank_value(c.rank))
            return SignalResult(
                card=selected,
                heuristic=SignalHeuristic.CHEAPEST_WINNER,
                reason="Win Cheaply: Taking the trick with your lowest winning card.",
                context=PlayContext.FOURTH_HAND_FOLLOW,
                is_optimal=True
            )
        else:
            # Can't win - play lowest
            selected = min(equivalence_set, key=lambda c: self._rank_value(c.rank))
            return SignalResult(
                card=selected,
                heuristic=SignalHeuristic.MIN_OF_EQUALS,
                reason="Cannot win this trick - playing lowest to conserve resources.",
                context=PlayContext.FOURTH_HAND_FOLLOW,
                is_optimal=True
            )

    def _select_discard(
        self,
        equivalence_set: List[Card],
        hand: Hand,
        trump_suit: Optional[str],
        want_suit: bool,
        context: PlayContext
    ) -> SignalResult:
        """
        Select discard following standard conventions.

        First Discard: Attitude signal (high=encourage, low=discourage)
        Subsequent: Count signal (high-low=even, low-high=odd)

        Also considers:
        - Protect lone high cards (stoppers)
        - Don't discard trump
        - Prefer discarding from length
        """
        best_card = None
        best_score = -1000
        best_reason = ""
        heuristic = SignalHeuristic.DISCARD_FROM_LENGTH

        # Count cards in each suit
        suit_counts = {}
        for c in hand.cards:
            suit_counts[c.suit] = suit_counts.get(c.suit, 0) + 1

        for card in equivalence_set:
            score = 0
            reason = ""
            suit_count = suit_counts.get(card.suit, 0)
            rank_value = self._rank_value(card.rank)

            # First discard: Attitude signal
            if context == PlayContext.DISCARD_FIRST:
                if want_suit:
                    # Encourage: play high
                    score += rank_value * 2
                    reason = "Attitude Signal: Discarding high encourages partner to lead this suit."
                    heuristic = SignalHeuristic.ATTITUDE_SIGNAL
                else:
                    # Discourage: play low
                    score -= rank_value * 2
                    reason = "Attitude Signal: Discarding low discourages this suit."
                    heuristic = SignalHeuristic.ATTITUDE_SIGNAL
            else:
                # Subsequent discard: Count signal
                if suit_count % 2 == 0:  # Even count - play high first
                    score += rank_value
                    reason = "Count Signal: High-low shows even count in this suit."
                else:  # Odd count - play low first
                    score -= rank_value
                    reason = "Count Signal: Low-high shows odd count in this suit."
                heuristic = SignalHeuristic.COUNT_SIGNAL

            # Prefer discarding from longer suits
            score += suit_count * 10

            # Heavily penalize discarding lone high cards (stoppers)
            if suit_count == 1 and rank_value >= 12:  # Q, K, or A
                score -= 100
                reason = "Protecting stopper - this lone honor guards the suit."

            # Penalize discarding from short suits with high cards
            if suit_count <= 2 and rank_value >= 10:  # T or higher
                score -= 20

            # Never discard trump if possible
            if card.suit == trump_suit:
                score -= 80

            # Penalize discarding potential winners
            if rank_value >= 14:  # Ace
                score -= 50

            if score > best_score:
                best_score = score
                best_card = card
                best_reason = reason

        if not best_card:
            best_card = min(equivalence_set, key=lambda c: self._rank_value(c.rank))
            best_reason = "Discarding lowest card from equivalent options."

        return SignalResult(
            card=best_card,
            heuristic=heuristic,
            reason=best_reason,
            context=context,
            is_optimal=True
        )

    def _select_lead_from_sequence(
        self,
        equivalence_set: List[Card],
        hand: Hand
    ) -> SignalResult:
        """Lead top of touching honors (K from KQJ)"""
        selected = max(equivalence_set, key=lambda c: self._rank_value(c.rank))

        return SignalResult(
            card=selected,
            heuristic=SignalHeuristic.TOP_OF_SEQUENCE,
            reason="Top of Sequence: Leading the top (e.g., K from KQJ) promises the cards below.",
            context=PlayContext.LEAD_FROM_HONOR_SEQUENCE,
            is_optimal=True
        )

    def _select_follow_from_sequence(
        self,
        equivalence_set: List[Card],
        hand: Hand
    ) -> SignalResult:
        """Follow with bottom of touching honors (Q from KQJ)"""
        selected = min(equivalence_set, key=lambda c: self._rank_value(c.rank))

        return SignalResult(
            card=selected,
            heuristic=SignalHeuristic.BOTTOM_OF_SEQUENCE,
            reason="Bottom of Sequence: Playing Q from KQJ signals possession of the K.",
            context=PlayContext.FOLLOW_FROM_HONOR_SEQUENCE,
            is_optimal=True
        )

    # ========== Helper Methods ==========

    def _rank_value(self, rank: str) -> int:
        """Get numeric value of rank"""
        return self.RANK_VALUES.get(rank, 0)

    def _is_top_of_sequence(self, card: Card, suit_cards: List[Card]) -> bool:
        """Check if card is top of a 3+ card sequence (KQJ, QJT, etc.)"""
        if len(suit_cards) < 3:
            return False

        ranks = sorted([self._rank_value(c.rank) for c in suit_cards], reverse=True)
        card_rank = self._rank_value(card.rank)

        # Must be the highest card
        if card_rank != ranks[0]:
            return False

        # Check for sequence (consecutive ranks)
        sequence_length = 1
        for i in range(len(ranks) - 1):
            if ranks[i] - ranks[i + 1] == 1:
                sequence_length += 1
            else:
                break

        return sequence_length >= 3

    def _is_tenace_suit(self, suit_cards: List[Card]) -> bool:
        """Check if suit contains a tenace (AQ, KJ, etc.) - avoid leading"""
        ranks = [self._rank_value(c.rank) for c in suit_cards]

        # AQ tenace (14 and 12, missing 13)
        if 14 in ranks and 12 in ranks and 13 not in ranks:
            return True

        # KJ tenace (13 and 11, missing 12)
        if 13 in ranks and 11 in ranks and 12 not in ranks:
            return True

        # QT tenace (12 and 10, missing 11)
        if 12 in ranks and 10 in ranks and 11 not in ranks:
            return True

        return False

    def _has_honor_sequence(self, equivalence_set: List[Card], hand: Hand) -> bool:
        """Check if equivalence set is part of an honor sequence in hand"""
        if not equivalence_set:
            return False

        suit = equivalence_set[0].suit
        suit_cards = [c for c in hand.cards if c.suit == suit]

        # Need at least 2 cards and they should be touching honors
        if len(suit_cards) < 2:
            return False

        ranks = sorted([self._rank_value(c.rank) for c in suit_cards], reverse=True)

        # Check for at least 2 consecutive honors (J or higher)
        for i in range(len(ranks) - 1):
            if ranks[i] >= 11 and ranks[i + 1] >= 10:  # J+ and T+
                if ranks[i] - ranks[i + 1] == 1:
                    return True

        return False

    def _equivalence_is_honor_sequence(self, equivalence_set: List[Card]) -> bool:
        """Check if the equivalence set itself forms a touching sequence"""
        if len(equivalence_set) < 2:
            return False

        # All cards should be same suit
        suits = set(c.suit for c in equivalence_set)
        if len(suits) > 1:
            return False

        ranks = sorted([self._rank_value(c.rank) for c in equivalence_set], reverse=True)

        # Check if consecutive
        for i in range(len(ranks) - 1):
            if ranks[i] - ranks[i + 1] != 1:
                return False

        # Must include honors (J or higher) to be a "sequence"
        return any(r >= 11 for r in ranks)

    def _get_discarded_suits(self, game_state: Any, position: str) -> set:
        """Get suits already discarded by this position in this hand"""
        discarded = set()
        trick_history = getattr(game_state, 'trick_history', [])

        for trick in trick_history:
            if not hasattr(trick, 'cards'):
                continue

            led_suit = trick.cards[0][0].suit if trick.cards else None
            if not led_suit:
                continue

            for card, pos in trick.cards:
                if pos == position and card.suit != led_suit:
                    discarded.add(card.suit)

        return discarded


# Convenience function for external use
def get_tactical_filter() -> TacticalPlayFilter:
    """Get a tactical play filter instance"""
    return TacticalPlayFilter()


# Self-test
if __name__ == '__main__':
    print("Tactical Play Signal Overlay - Self Test")
    print("=" * 50)

    filter = TacticalPlayFilter()

    # Test second hand low
    cards = [Card('Q', '♠'), Card('J', '♠'), Card('T', '♠')]
    result = filter._select_second_hand(cards, None)
    print(f"\nSecond hand from QJT:")
    print(f"  Selected: {result.card.rank}{result.card.suit}")
    print(f"  Reason: {result.reason}")
    assert result.card.rank == 'T', "Should play 10 (lowest)"

    # Test third hand high with sequence
    cards = [Card('K', '♥'), Card('Q', '♥')]

    class MockHand:
        def __init__(self):
            self.cards = [Card('K', '♥'), Card('Q', '♥'), Card('5', '♥')]

    result = filter._select_third_hand(cards, None, MockHand())
    print(f"\nThird hand from KQ (sequence):")
    print(f"  Selected: {result.card.rank}{result.card.suit}")
    print(f"  Reason: {result.reason}")
    assert result.card.rank == 'Q', "Should play Q (bottom of sequence)"

    print("\n✓ All self-tests passed!")
