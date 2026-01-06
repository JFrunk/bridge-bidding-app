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
8. Declarer Conservation - Don't overtake partner's winner (prevents Ace-on-King)
9. Defensive Deference - Defenders don't overtake partner's winner (prevents Q-on-J)

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
    DECLARER_CONSERVATION = "declarer_conservation"  # Declarer/Dummy already winning - conserve
    DEFENSIVE_DEFERENCE = "defensive_deference"  # Defender's partner already winning - defer


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
    DECLARER_CONSERVE = "declarer_conserve"   # Conserve winners when partnership winning
    DEFENSIVE_DEFER = "defensive_defer"       # Defer to partner's winning card


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

        elif context == PlayContext.DECLARER_CONSERVATION:
            return self._select_declarer_conservation(equivalence_set, game_state)

        elif context == PlayContext.DEFENSIVE_DEFERENCE:
            return self._select_defensive_deference(equivalence_set, game_state)

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

        # ========================================================================
        # CRITICAL: Check for Partnership Coordination BEFORE standard play logic
        # Both declarer and defenders should not overtake their partner's winner!
        # ========================================================================

        # Check for Declarer Conservation (Declarer/Dummy partnership)
        if self._should_conserve_declarer_winner(game_state, position, equivalence_set):
            return PlayContext.DECLARER_CONSERVATION

        # Check for Defensive Deference (Defender partnership)
        # Pass hand to check for unblocking situations
        if self._should_defer_to_partner(game_state, position, equivalence_set, hand):
            return PlayContext.DEFENSIVE_DEFERENCE

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
        - Exception: Play low to conserve honors when trick is already won by partner
        """
        # First check: Is the trick already won and we can't improve?
        # If the current winner beats our highest card, we should conserve honors
        current_trick = getattr(game_state, 'current_trick', [])

        if len(current_trick) >= 1:
            led_card = current_trick[0][0]
            led_suit = led_card.suit

            # Find the current winner of the trick
            current_winner_value = 0
            for played_card, played_pos in current_trick:
                if played_card.suit == led_suit:
                    card_val = self._rank_value(played_card.rank)
                    if card_val > current_winner_value:
                        current_winner_value = card_val

            # Get the highest card we could play from the equivalence set
            our_highest = max(equivalence_set, key=lambda c: self._rank_value(c.rank))
            our_highest_value = self._rank_value(our_highest.rank)

            # If current winner beats everything we have, play low to conserve
            if current_winner_value > our_highest_value:
                selected = min(equivalence_set, key=lambda c: self._rank_value(c.rank))
                return SignalResult(
                    card=selected,
                    heuristic=SignalHeuristic.MIN_OF_EQUALS,
                    reason="Conserving honors: Can't beat the current winner, play low to save higher cards.",
                    context=PlayContext.THIRD_HAND_FOLLOW,
                    is_optimal=True
                )

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
                    # Encourage: play a conspicuously high SPOT card (not your winners)
                    # Ideal: 7-9 range to signal encouragement without wasting tricks
                    # Don't discard honors (J+) to encourage - save them to win tricks
                    if rank_value >= 11:  # J, Q, K, A - too valuable to discard for a signal
                        score -= 30  # Penalize discarding honors even when encouraging
                        reason = "Attitude Signal: Prefer signaling with spot cards, not honors."
                    elif rank_value >= 7:  # 7, 8, 9, T - good encouraging signal
                        score += 20 + (rank_value - 7)  # Prefer higher spot card (9 > 8 > 7)
                        reason = "Attitude Signal: High spot card encourages partner to lead this suit."
                    else:  # 2-6 - too low to clearly encourage
                        score += rank_value  # Slight preference for higher within low range
                        reason = "Attitude Signal: Discarding to encourage this suit."
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

    def _select_declarer_conservation(
        self,
        equivalence_set: List[Card],
        game_state: Any
    ) -> SignalResult:
        """
        Conserve winners when declarer/dummy partnership is already winning.

        When declarer controls both hands and one hand has already played a winner,
        play the lowest card from the other hand to conserve high cards.

        Example: If dummy played A♥ and declarer has K♥, play a low card instead
        of wasting the K♥ on a trick already won.
        """
        # Play lowest card to conserve winners
        selected = min(equivalence_set, key=lambda c: self._rank_value(c.rank))

        # Build educational reason
        current_trick = getattr(game_state, 'current_trick', [])
        if current_trick:
            winning_card = self._get_current_winner(current_trick, game_state)
            if winning_card:
                reason = (
                    f"Declarer Conservation: Partnership already winning with "
                    f"{winning_card.rank}{winning_card.suit} - playing low to save "
                    f"higher cards for future tricks."
                )
            else:
                reason = "Declarer Conservation: Playing low to preserve winners."
        else:
            reason = "Declarer Conservation: Playing low to preserve winners."

        return SignalResult(
            card=selected,
            heuristic=SignalHeuristic.DECLARER_CONSERVE,
            reason=reason,
            context=PlayContext.DECLARER_CONSERVATION,
            is_optimal=True
        )

    def _should_conserve_declarer_winner(
        self,
        game_state: Any,
        position: str,
        equivalence_set: List[Card]
    ) -> bool:
        """
        Determine if declarer should conserve winners (not overtake own winner).

        Returns True when:
        1. Position is declarer or dummy (one side controls both hands)
        2. Partner (the other controlled hand) has already played to this trick
        3. Partner's card is currently winning the trick
        4. We have cards that could overtake but shouldn't

        This prevents the "Ace on King" problem where DDS plays both high cards
        to the same trick because they're DDS-equivalent, but a human would
        recognize this wastes a winner.
        """
        current_trick = getattr(game_state, 'current_trick', [])
        contract = getattr(game_state, 'contract', None)

        # Need at least one card played and contract info
        if not current_trick or not contract:
            return False

        declarer = getattr(contract, 'declarer', None)
        if not declarer:
            return False

        # Determine if this position is declarer or dummy
        dummy = self._get_dummy_position(declarer)
        is_declarer_side = position in [declarer, dummy]

        if not is_declarer_side:
            return False  # Defenders use normal signaling

        # Check if partner (the other controlled hand) has played
        partner_pos = dummy if position == declarer else declarer
        partner_played = None

        for card, pos in current_trick:
            if pos == partner_pos:
                partner_played = card
                break

        if not partner_played:
            return False  # Partner hasn't played yet

        # Check if partner is currently winning
        led_suit = current_trick[0][0].suit
        trump_suit = getattr(contract, 'trump_suit', None)
        current_winner_card, current_winner_pos = self._get_trick_winner_info(
            current_trick, led_suit, trump_suit
        )

        if current_winner_pos != partner_pos:
            return False  # Partner isn't winning, normal play applies

        # Partner is winning - check if we have cards that could wastefully overtake
        # Only trigger conservation if we have high cards that could overtake
        partner_rank = self._rank_value(partner_played.rank)

        # Check if any card in equivalence set would overtake partner
        can_overtake = any(
            c.suit == led_suit and self._rank_value(c.rank) > partner_rank
            for c in equivalence_set
        )

        if not can_overtake:
            return False  # No overtaking possible, normal play

        # We have cards that could overtake partner's winner - conserve!
        return True

    def _select_defensive_deference(
        self,
        equivalence_set: List[Card],
        game_state: Any
    ) -> SignalResult:
        """
        Defer to partner's winning card when defending.

        When partner has already played a card that's winning the trick,
        play low to preserve your higher cards for future tricks.

        Example: Partner led J♥, you have Q♥ and 7♥ - play 7♥ to keep Q♥
        for later when you might need it to capture declarer's King.
        """
        # Play lowest card to defer to partner
        selected = min(equivalence_set, key=lambda c: self._rank_value(c.rank))

        # Build educational reason
        current_trick = getattr(game_state, 'current_trick', [])
        if current_trick:
            winning_card = self._get_current_winner(current_trick, game_state)
            if winning_card:
                reason = (
                    f"Defensive Deference: Partner is winning with "
                    f"{winning_card.rank}{winning_card.suit} - playing low to preserve "
                    f"higher cards for future tricks."
                )
            else:
                reason = "Defensive Deference: Playing low to support partner's winner."
        else:
            reason = "Defensive Deference: Playing low to support partner's winner."

        return SignalResult(
            card=selected,
            heuristic=SignalHeuristic.DEFENSIVE_DEFER,
            reason=reason,
            context=PlayContext.DEFENSIVE_DEFERENCE,
            is_optimal=True
        )

    def _should_defer_to_partner(
        self,
        game_state: Any,
        position: str,
        equivalence_set: List[Card],
        hand: 'Hand' = None
    ) -> bool:
        """
        Determine if defender should defer to partner's winning card.

        Returns True when:
        1. Position is a defender (not declarer or dummy)
        2. Partner (the other defender) has already played to this trick
        3. Partner's card is currently winning the trick
        4. We have cards that could wastefully overtake
        5. We should NOT unblock (see _should_unblock)

        This prevents the "Queen on Jack" problem where defenders waste
        honors on the same trick.

        EXCEPTION: If we need to unblock (doubleton honor when partner leads),
        we should NOT defer - we should play the honor to get out of the way.
        """
        current_trick = getattr(game_state, 'current_trick', [])
        contract = getattr(game_state, 'contract', None)

        # Need at least one card played and contract info
        if not current_trick or not contract:
            return False

        declarer = getattr(contract, 'declarer', None)
        if not declarer:
            return False

        # Determine if this position is a defender
        dummy = self._get_dummy_position(declarer)
        is_defender = position not in [declarer, dummy]

        if not is_defender:
            return False  # Declarer/Dummy use conservation logic instead

        # Get defender's partner position
        defender_partner = self._get_defender_partner(position, declarer)
        if not defender_partner:
            return False

        # Check if partner has played
        partner_played = None
        for card, pos in current_trick:
            if pos == defender_partner:
                partner_played = card
                break

        if not partner_played:
            return False  # Partner hasn't played yet

        # Check if partner LED the suit (first to play)
        led_by_partner = current_trick[0][1] == defender_partner

        # Check if we should UNBLOCK instead of defer
        if led_by_partner and hand is not None:
            led_suit = current_trick[0][0].suit
            if self._should_unblock(equivalence_set, hand, led_suit):
                return False  # Don't defer - need to unblock!

        # Check if partner is currently winning
        led_suit = current_trick[0][0].suit
        trump_suit = getattr(contract, 'trump_suit', None)
        current_winner_card, current_winner_pos = self._get_trick_winner_info(
            current_trick, led_suit, trump_suit
        )

        if current_winner_pos != defender_partner:
            return False  # Partner isn't winning, normal play applies

        # Partner is winning - check if we have cards that could wastefully overtake
        partner_rank = self._rank_value(partner_played.rank)

        # Check if any card in equivalence set would overtake partner
        can_overtake = any(
            c.suit == led_suit and self._rank_value(c.rank) > partner_rank
            for c in equivalence_set
        )

        if not can_overtake:
            return False  # No overtaking possible, normal play

        # We have cards that could overtake partner's winner - defer!
        return True

    def _get_defender_partner(self, position: str, declarer: str) -> Optional[str]:
        """Get the partner position for a defender."""
        dummy = self._get_dummy_position(declarer)

        # The two defenders are the positions that are NOT declarer or dummy
        all_positions = ['N', 'E', 'S', 'W']
        defenders = [p for p in all_positions if p not in [declarer, dummy]]

        if position not in defenders:
            return None  # Not a defender

        # Return the other defender
        return [d for d in defenders if d != position][0]

    def _should_unblock(
        self,
        equivalence_set: List[Card],
        hand: 'Hand',
        led_suit: str
    ) -> bool:
        """
        Determine if we should unblock (play high) instead of defer.

        Returns True when:
        1. We have a doubleton in the led suit (exactly 2 cards)
        2. One of those cards is an honor (A, K, Q)
        3. Playing low would "block" partner from running the suit

        The classic unblocking situation:
        - Partner leads K from KQJxx
        - We have Ax (doubleton Ace)
        - If we play x, partner wins with K, then Q, then we win with A
        - Now we're "stuck" on lead and can't return the suit
        - Better to unblock: play A on partner's K, then return the x

        This is a heuristic - we can't be certain partner has length,
        but when partner leads an honor and we have doubleton honor,
        unblocking is usually correct.
        """
        if hand is None:
            return False

        # Count cards in the led suit
        suit_cards = [c for c in hand.cards if c.suit == led_suit]
        suit_length = len(suit_cards)

        # Only consider unblocking with doubleton
        if suit_length != 2:
            return False

        # Check if we have an honor in the equivalence set
        # that's part of a doubleton
        honor_ranks = ['A', 'K', 'Q']
        equiv_honors = [c for c in equivalence_set
                       if c.suit == led_suit and c.rank in honor_ranks]

        if not equiv_honors:
            return False  # No honor to unblock with

        # We have a doubleton with an honor - should unblock
        return True

    def _get_dummy_position(self, declarer: str) -> str:
        """Get dummy's position (opposite declarer)"""
        opposite = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
        return opposite.get(declarer, 'N')

    def _get_trick_winner_info(
        self,
        current_trick: List,
        led_suit: str,
        trump_suit: Optional[str]
    ) -> Tuple[Optional[Card], Optional[str]]:
        """
        Determine current trick winner considering trump.

        Returns (winning_card, winning_position) or (None, None) if empty.
        """
        if not current_trick:
            return None, None

        winner_card = None
        winner_pos = None
        winner_rank = -1

        for card, pos in current_trick:
            card_rank = self._rank_value(card.rank)

            # Trump beats non-trump
            if trump_suit and card.suit == trump_suit:
                if winner_card is None or winner_card.suit != trump_suit:
                    # First trump or replacing non-trump winner
                    winner_card = card
                    winner_pos = pos
                    winner_rank = card_rank
                elif card_rank > winner_rank:
                    # Higher trump
                    winner_card = card
                    winner_pos = pos
                    winner_rank = card_rank
            elif card.suit == led_suit:
                # Following suit (no trump played yet or this isn't trump)
                if winner_card is None or (winner_card.suit != trump_suit and card_rank > winner_rank):
                    winner_card = card
                    winner_pos = pos
                    winner_rank = card_rank
            # Off-suit non-trump cards don't win

        return winner_card, winner_pos

    def _get_current_winner(self, current_trick: List, game_state: Any) -> Optional[Card]:
        """Get the currently winning card in the trick"""
        if not current_trick:
            return None

        led_suit = current_trick[0][0].suit
        contract = getattr(game_state, 'contract', None)
        trump_suit = getattr(contract, 'trump_suit', None) if contract else None

        winner_card, _ = self._get_trick_winner_info(current_trick, led_suit, trump_suit)
        return winner_card

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
