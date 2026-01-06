"""
Unit tests for the Tactical Play Signal Overlay

Tests the TacticalPlayFilter which makes DDS play human-like by applying
standard bridge signaling conventions to equivalence sets.

Test Categories:
1. Second Hand Low - preserve honors
2. Third Hand High - force declarer's resources
3. Bottom of Sequence - signal higher honors
4. Discard Signals - attitude and count
5. Opening Leads - top of sequence, 4th best
6. Win Cheaply - use lowest winner
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.hand import Card, Hand
from engine.play.ai.play_signal_overlay import (
    TacticalPlayFilter,
    SignalResult,
    PlayContext,
    SignalHeuristic
)


@pytest.fixture
def filter():
    """Create a TacticalPlayFilter instance"""
    return TacticalPlayFilter()


class TestSecondHandLow:
    """Tests for 2nd hand low principle"""

    def test_second_hand_plays_lowest(self, filter):
        """Second hand should play the lowest card from equivalence set"""
        cards = [Card('Q', '♠'), Card('J', '♠'), Card('T', '♠')]
        result = filter._select_second_hand(cards, None)

        assert result.card.rank == 'T', "Should play lowest (10)"
        assert result.heuristic == SignalHeuristic.MIN_OF_EQUALS
        assert "2nd Hand Low" in result.reason

    def test_second_hand_preserves_honor(self, filter):
        """Second hand should preserve honor cards"""
        cards = [Card('A', '♥'), Card('K', '♥'), Card('Q', '♥')]
        result = filter._select_second_hand(cards, None)

        assert result.card.rank == 'Q', "Should play lowest (Q)"
        assert "Preserving higher honors" in result.reason


class TestThirdHandHigh:
    """Tests for 3rd hand high principle"""

    def test_third_hand_plays_highest_non_sequence(self, filter):
        """Third hand plays highest when not a sequence"""
        # Non-touching cards
        cards = [Card('Q', '♠'), Card('9', '♠'), Card('5', '♠')]

        class MockHand:
            def __init__(self):
                self.cards = cards

        result = filter._select_third_hand(cards, None, MockHand())

        assert result.card.rank == 'Q', "Should play highest (Q)"
        assert result.heuristic == SignalHeuristic.MAX_OF_EQUALS

    def test_third_hand_bottom_of_sequence(self, filter):
        """Third hand plays bottom of touching honors"""
        # Touching sequence KQ
        cards = [Card('K', '♥'), Card('Q', '♥')]

        class MockHand:
            def __init__(self):
                self.cards = [Card('K', '♥'), Card('Q', '♥'), Card('5', '♥')]

        result = filter._select_third_hand(cards, None, MockHand())

        assert result.card.rank == 'Q', "Should play Q (bottom of sequence)"
        assert result.heuristic == SignalHeuristic.BOTTOM_OF_SEQUENCE
        assert "Bottom of Sequence" in result.reason

    def test_third_hand_conserves_honors_when_trick_won(self, filter):
        """Third hand plays low to conserve honors when partner already wins"""
        # Scenario: Partner led Q♦, dummy plays 6♦, we have J♦ and 2♦
        # Partner's Q wins, so we should play 2♦ to save J♦ for later

        class MockState:
            def __init__(self):
                # Partner (N) led Q♦, dummy (E) played 6♦
                # We (S) are third hand with J♦ and 2♦
                self.current_trick = [
                    (Card('Q', '♦'), 'N'),  # Partner's Q leads
                    (Card('6', '♦'), 'E')   # Dummy plays low
                ]

        class MockHand:
            def __init__(self):
                self.cards = [Card('J', '♦'), Card('2', '♦')]

        # Equivalence set: J♦ and 2♦ both preserve the same tricks (Q wins)
        cards = [Card('J', '♦'), Card('2', '♦')]
        result = filter._select_third_hand(cards, MockState(), MockHand())

        assert result.card.rank == '2', "Should play 2 to conserve J"
        assert result.heuristic == SignalHeuristic.MIN_OF_EQUALS
        assert "Conserving honors" in result.reason
        assert result.is_optimal is True

    def test_third_hand_high_when_can_beat_second(self, filter):
        """Third hand plays high when they can beat second hand's card"""
        # Scenario: Partner led 6♦, dummy plays Q♦, we have K♦ and 2♦
        # We should play K♦ to beat dummy's Q

        class MockState:
            def __init__(self):
                # Partner (N) led 6♦, dummy (E) played Q♦
                self.current_trick = [
                    (Card('6', '♦'), 'N'),
                    (Card('Q', '♦'), 'E')
                ]

        class MockHand:
            def __init__(self):
                self.cards = [Card('K', '♦'), Card('2', '♦')]

        cards = [Card('K', '♦'), Card('2', '♦')]
        result = filter._select_third_hand(cards, MockState(), MockHand())

        # K beats Q, so should still play high
        assert result.card.rank == 'K', "Should play K to beat Q"
        assert result.heuristic == SignalHeuristic.MAX_OF_EQUALS


class TestFourthHand:
    """Tests for 4th hand - win cheaply"""

    def test_fourth_hand_wins_cheaply(self, filter):
        """Fourth hand should win with lowest winning card"""

        class MockState:
            def __init__(self):
                # Current trick: 7♠ led, then 9♠, then 3♠
                self.current_trick = [
                    (Card('7', '♠'), 'W'),
                    (Card('9', '♠'), 'N'),
                    (Card('3', '♠'), 'E')
                ]

        cards = [Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠')]
        result = filter._select_fourth_hand(cards, MockState())

        assert result.card.rank == 'J', "Should win with lowest winner (J beats 9)"
        assert result.heuristic == SignalHeuristic.CHEAPEST_WINNER

    def test_fourth_hand_cannot_win_plays_low(self, filter):
        """Fourth hand plays low when cannot win"""

        class MockState:
            def __init__(self):
                # Ace already played
                self.current_trick = [
                    (Card('A', '♠'), 'W'),
                    (Card('9', '♠'), 'N'),
                    (Card('3', '♠'), 'E')
                ]

        # Our highest is K, can't beat A
        cards = [Card('K', '♠'), Card('Q', '♠'), Card('2', '♠')]
        result = filter._select_fourth_hand(cards, MockState())

        assert result.card.rank == '2', "Should play lowest when can't win"


class TestDiscards:
    """Tests for discard signaling"""

    def test_first_discard_attitude_encourage(self, filter):
        """First discard uses attitude - high spot card to encourage"""

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('9', '♦'), Card('7', '♦'), Card('4', '♦'),
                    Card('K', '♣'), Card('5', '♣')
                ]

        cards = [Card('9', '♦'), Card('7', '♦'), Card('4', '♦')]
        result = filter._select_discard(
            cards, MockHand(), None, want_suit=True,
            context=PlayContext.DISCARD_FIRST
        )

        assert result.card.rank == '9', "Should discard high spot card to encourage"
        assert result.heuristic == SignalHeuristic.ATTITUDE_SIGNAL
        assert "encourages" in result.reason.lower()

    def test_encourage_prefers_spot_cards_over_honors(self, filter):
        """When encouraging, prefer high spot cards over honors (save honors to win tricks)"""

        class MockHand:
            def __init__(self):
                # K-9-7-4 in diamonds - should discard 9 to encourage, not K
                self.cards = [
                    Card('K', '♦'), Card('9', '♦'), Card('7', '♦'), Card('4', '♦'),
                    Card('5', '♣'), Card('3', '♣')
                ]

        # K and 9 both in equivalence set (DDS says they're equivalent for trick count)
        cards = [Card('K', '♦'), Card('9', '♦')]
        result = filter._select_discard(
            cards, MockHand(), None, want_suit=True,
            context=PlayContext.DISCARD_FIRST
        )

        assert result.card.rank == '9', "Should discard 9 to encourage, saving K to win tricks"
        assert "spot card" in result.reason.lower() or "encourages" in result.reason.lower()

    def test_first_discard_attitude_discourage(self, filter):
        """First discard uses attitude - low to discourage"""

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('9', '♦'), Card('7', '♦'), Card('4', '♦'),
                    Card('K', '♣'), Card('5', '♣')
                ]

        cards = [Card('9', '♦'), Card('7', '♦'), Card('4', '♦')]
        result = filter._select_discard(
            cards, MockHand(), None, want_suit=False,
            context=PlayContext.DISCARD_FIRST
        )

        assert result.card.rank == '4', "Should discard low to discourage"
        assert "discourages" in result.reason.lower()

    def test_discard_protects_stoppers(self, filter):
        """Should not discard lone high cards (stoppers)"""

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('A', '♦'),  # Lone ace - stopper
                    Card('7', '♣'), Card('5', '♣'), Card('3', '♣')  # Length
                ]

        # Both are in equivalence set
        cards = [Card('A', '♦'), Card('7', '♣')]
        result = filter._select_discard(
            cards, MockHand(), None, want_suit=False,
            context=PlayContext.DISCARD_FIRST
        )

        assert result.card.suit == '♣', "Should discard from clubs, not lone ace"

    def test_discard_never_trump(self, filter):
        """Should never discard trump if possible"""

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('5', '♠'),  # Trump
                    Card('7', '♣'), Card('5', '♣')
                ]

        cards = [Card('5', '♠'), Card('5', '♣')]
        result = filter._select_discard(
            cards, MockHand(), trump_suit='♠', want_suit=False,
            context=PlayContext.DISCARD_FIRST
        )

        assert result.card.suit == '♣', "Should discard club, not trump"


class TestOpeningLeads:
    """Tests for opening lead selection"""

    def test_lead_top_of_sequence(self, filter):
        """Should lead top of touching honors"""

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('5', '♠'),
                    Card('8', '♥'), Card('6', '♥')
                ]

        cards = [Card('K', '♠'), Card('Q', '♠'), Card('J', '♠')]
        result = filter._select_opening_lead(cards, MockHand(), trump_suit='♥')

        assert result.card.rank == 'K', "Should lead K from KQJ"
        assert "Sequence" in result.reason

    def test_avoid_leading_trump(self, filter):
        """Should avoid leading trump when other options exist"""

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('5', '♠'),  # Trump
                    Card('K', '♣'), Card('Q', '♣')  # Non-trump
                ]

        cards = [Card('5', '♠'), Card('K', '♣')]
        result = filter._select_opening_lead(cards, MockHand(), trump_suit='♠')

        assert result.card.suit == '♣', "Should lead club, not trump"


class TestSequenceDetection:
    """Tests for honor sequence detection"""

    def test_detect_touching_honors(self, filter):
        """Should detect touching honors as sequence"""
        cards = [Card('K', '♠'), Card('Q', '♠')]

        assert filter._equivalence_is_honor_sequence(cards), "KQ should be detected as sequence"

    def test_non_touching_not_sequence(self, filter):
        """Non-touching cards are not a sequence"""
        cards = [Card('K', '♠'), Card('J', '♠')]  # Missing Q

        assert not filter._equivalence_is_honor_sequence(cards), "KJ (gap) should not be sequence"

    def test_low_cards_not_sequence(self, filter):
        """Low cards are not an honor sequence"""
        cards = [Card('7', '♠'), Card('6', '♠'), Card('5', '♠')]

        assert not filter._equivalence_is_honor_sequence(cards), "765 are not honors"


class TestTenaceDetection:
    """Tests for tenace (split honor) detection"""

    def test_detect_aq_tenace(self, filter):
        """Should detect AQ tenace"""
        cards = [Card('A', '♠'), Card('Q', '♠'), Card('5', '♠')]

        assert filter._is_tenace_suit(cards), "AQ should be detected as tenace"

    def test_detect_kj_tenace(self, filter):
        """Should detect KJ tenace"""
        cards = [Card('K', '♠'), Card('J', '♠'), Card('5', '♠')]

        assert filter._is_tenace_suit(cards), "KJ should be detected as tenace"

    def test_sequence_not_tenace(self, filter):
        """Solid sequence is not a tenace"""
        cards = [Card('K', '♠'), Card('Q', '♠'), Card('J', '♠')]

        assert not filter._is_tenace_suit(cards), "KQJ is not a tenace"


class TestContextDetermination:
    """Tests for play context determination"""

    def test_opening_lead_context(self, filter):
        """Should identify opening lead"""

        class MockState:
            def __init__(self):
                self.current_trick = []
                self.trick_history = []

        class MockHand:
            def __init__(self):
                self.cards = [Card('K', '♠'), Card('5', '♠')]

        cards = [Card('K', '♠')]
        context = filter._determine_context(MockState(), 'W', MockHand(), cards)

        assert context in [PlayContext.OPENING_LEAD, PlayContext.LEAD_FROM_HONOR_SEQUENCE]

    def test_second_hand_context(self, filter):
        """Should identify second hand follow"""

        class MockState:
            def __init__(self):
                self.current_trick = [(Card('7', '♠'), 'W')]  # One card played
                self.trick_history = []

        class MockHand:
            def __init__(self):
                self.cards = [Card('K', '♠'), Card('5', '♠')]

        cards = [Card('K', '♠'), Card('5', '♠')]
        context = filter._determine_context(MockState(), 'N', MockHand(), cards)

        assert context == PlayContext.SECOND_HAND_FOLLOW

    def test_discard_context(self, filter):
        """Should identify discard situation"""

        class MockState:
            def __init__(self):
                self.current_trick = [(Card('7', '♠'), 'W')]  # Spade led
                self.trick_history = []

        class MockHand:
            def __init__(self):
                # No spades - must discard
                self.cards = [Card('K', '♦'), Card('5', '♦')]

        cards = [Card('K', '♦'), Card('5', '♦')]
        context = filter._determine_context(MockState(), 'N', MockHand(), cards)

        assert context in [PlayContext.DISCARD_FIRST, PlayContext.DISCARD_SUBSEQUENT]


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_single_card_equivalence_set(self, filter):
        """Single card should return immediately"""

        class MockState:
            def __init__(self):
                self.current_trick = [(Card('7', '♠'), 'W')]
                self.trick_history = []

        class MockHand:
            def __init__(self):
                self.cards = [Card('5', '♠')]

        cards = [Card('5', '♠')]
        result = filter.select_tactical_card(cards, MockState(), 'N', MockHand())

        assert result.card.rank == '5'
        assert result.is_optimal

    def test_empty_equivalence_set_raises(self, filter):
        """Empty equivalence set should raise ValueError"""

        class MockState:
            pass

        class MockHand:
            def __init__(self):
                self.cards = []

        with pytest.raises(ValueError):
            filter.select_tactical_card([], MockState(), 'N', MockHand())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
