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


class TestDeferenceAndUnblocking:
    """
    Deference & Unblocking Test Suite

    Tests the Physics of Fluidity - ensuring the AI distinguishes between:
    1. CONSERVATION (Deference): Don't waste honors on partner's winner
    2. FLUIDITY (Unblocking): Get high cards out of the way to let partner run

    These are the only valid exceptions to standard 3rd Hand High.
    """

    def test_positional_deference_q_on_j(self, filter):
        """
        Scenario 1: Positional Deference (fixes Q-on-J wastage)

        Context: South (Partner) leads J♠. East (Opponent) plays 3♠.
        AI Hand (North): Q♠, 7♠
        DDS Equivalence Set: [Q♠, 7♠] (both result in same tricks)
        Expected: Play 7♠ (defer to partner's J)

        First Principle: Do not overtake partner's winning card to preserve
        the Queen for positional leverage over opponents.
        """
        class MockContract:
            declarer = 'E'  # East is declarer
            trump_suit = None  # NT contract

        class MockState:
            def __init__(self):
                # South (partner) led J♠, East (declarer) played 3♠
                # North (defender) to play with Q♠ and 7♠
                self.current_trick = [
                    (Card('J', '♠'), 'S'),  # Partner leads J
                    (Card('3', '♠'), 'E'),  # Declarer plays low
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                # North has Q♠ and 7♠ plus other cards
                self.cards = [
                    Card('Q', '♠'), Card('7', '♠'),
                    Card('A', '♥'), Card('5', '♥'),
                    Card('K', '♦'), Card('4', '♦'),
                    Card('8', '♣'), Card('3', '♣')
                ]

        # Q and 7 are DDS-equivalent (both preserve same trick count)
        equivalence_set = [Card('Q', '♠'), Card('7', '♠')]

        result = filter.select_tactical_card(
            equivalence_set, MockState(), 'N', MockHand(), trump_suit=None
        )

        assert result.card.rank == '7', (
            f"Should play 7♠ to defer to partner's J♠, got {result.card.rank}♠. "
            f"Q-on-J wastes honors!"
        )
        assert result.context == PlayContext.DEFENSIVE_DEFERENCE
        assert "defer" in result.reason.lower() or "partner" in result.reason.lower()

    def test_unblocking_singleton_ace(self, filter):
        """
        Scenario 2: Unblocking Requirement (Fluidity)

        Context: South (Partner) leads K♣. West (Opponent) plays 2♣.
        AI Hand (North): A♣ (singleton)
        DDS Equivalence Set: [A♣] (only card)
        Expected: Play A♣ (unblock for partner)

        First Principle: Even though partner is winning, we MUST play the Ace
        because it's a singleton. If not played now, North will win the next
        club trick and "block" South from running their long club suit.
        """
        class MockContract:
            declarer = 'E'
            trump_suit = None

        class MockState:
            def __init__(self):
                # South leads K♣, West plays 2♣, North to play
                self.current_trick = [
                    (Card('K', '♣'), 'S'),  # Partner leads K
                    (Card('2', '♣'), 'W'),  # Opponent plays low
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                # North has SINGLETON A♣ - must unblock!
                self.cards = [
                    Card('A', '♣'),  # Singleton Ace - blocking card
                    Card('Q', '♥'), Card('5', '♥'),
                    Card('8', '♦'), Card('4', '♦'),
                    Card('7', '♠'), Card('3', '♠')
                ]

        # Only one card - but the key is the _should_unblock check
        equivalence_set = [Card('A', '♣')]

        # First verify the unblocking logic recognizes this
        should_unblock = filter._should_unblock(equivalence_set, MockHand(), '♣')
        assert should_unblock, "Should recognize singleton Ace as blocking card"

        # Now verify the actual play selection
        result = filter.select_tactical_card(
            equivalence_set, MockState(), 'N', MockHand(), trump_suit=None
        )

        assert result.card.rank == 'A', "Must play singleton Ace to unblock"

    def test_declarer_conservation_a_on_k(self, filter):
        """
        Scenario 3: Declarer Unit Coordination (Conservation)

        Context: Declarer (East) leads K♦ from dummy. South plays 5♦.
        AI is West (declarer's hand): A♦, 7♦
        DDS Equivalence Set: [A♦, 7♦]
        Expected: Play 7♦ (conserve the Ace)

        First Principle: Declarer controls both hands. The K♦ and A♦ are a
        single resource unit. Don't spend two honors on one trick.
        """
        class MockContract:
            declarer = 'W'  # West is declarer
            trump_suit = None

        class MockState:
            def __init__(self):
                # East (dummy) leads K♦, South plays 5♦, West (declarer) to play
                self.current_trick = [
                    (Card('K', '♦'), 'E'),  # Dummy leads K
                    (Card('5', '♦'), 'S'),  # Defender plays low
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                # West (declarer) has A♦ and 7♦
                self.cards = [
                    Card('A', '♦'), Card('7', '♦'),
                    Card('Q', '♠'), Card('J', '♠'),
                    Card('K', '♥'), Card('4', '♥'),
                    Card('9', '♣'), Card('2', '♣')
                ]

        equivalence_set = [Card('A', '♦'), Card('7', '♦')]

        result = filter.select_tactical_card(
            equivalence_set, MockState(), 'W', MockHand(), trump_suit=None
        )

        assert result.card.rank == '7', (
            f"Should play 7♦ to conserve A♦, got {result.card.rank}♦. "
            f"Ace-on-King wastes winners!"
        )
        assert result.context == PlayContext.DECLARER_CONSERVATION
        assert "conserv" in result.reason.lower()

    def test_doubleton_honor_unblock(self, filter):
        """
        Test doubleton honor unblocking (Ax situation)

        Context: Partner leads K from KQJxx, we have Ax (doubleton)
        Expected: Play A to unblock, then return x

        If we play x first, partner wins K then Q then J, then we win A
        and can't return the suit (we're out!). Better to play A on K.
        """
        class MockContract:
            declarer = 'E'
            trump_suit = None

        class MockState:
            def __init__(self):
                # South leads K♥, West plays 3♥, North to play
                self.current_trick = [
                    (Card('K', '♥'), 'S'),  # Partner leads K
                    (Card('3', '♥'), 'W'),  # Opponent plays low
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                # North has doubleton A-5 in hearts
                self.cards = [
                    Card('A', '♥'), Card('5', '♥'),  # Doubleton with honor
                    Card('Q', '♠'), Card('7', '♠'),
                    Card('8', '♦'), Card('4', '♦'),
                    Card('6', '♣'), Card('2', '♣')
                ]

        # Both cards in equivalence set
        equivalence_set = [Card('A', '♥'), Card('5', '♥')]

        # Verify unblocking is detected
        should_unblock = filter._should_unblock(equivalence_set, MockHand(), '♥')
        assert should_unblock, "Should recognize doubleton Ace as requiring unblock"

    def test_no_unblock_with_length(self, filter):
        """
        Test that we DON'T unblock when we have 3+ cards

        With 3+ cards, there's no immediate blocking concern - we can
        follow low and still have cards to return to partner later.
        """
        class MockHand:
            def __init__(self):
                # North has 3 hearts including the Ace
                self.cards = [
                    Card('A', '♥'), Card('8', '♥'), Card('3', '♥'),
                    Card('Q', '♠'), Card('7', '♠'),
                    Card('K', '♦'), Card('4', '♦')
                ]

        equivalence_set = [Card('A', '♥'), Card('8', '♥'), Card('3', '♥')]

        should_unblock = filter._should_unblock(equivalence_set, MockHand(), '♥')
        assert not should_unblock, "Should NOT unblock with 3+ cards in suit"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
