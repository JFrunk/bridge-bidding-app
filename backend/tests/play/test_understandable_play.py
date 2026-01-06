"""
Human-Understandable Play Validation Suite

This test suite validates that the DDS + Tactical Overlay produces plays that
follow standard bridge signaling conventions - making AI play "human-understandable."

Architecture Layers Tested:
- Layer 1: DDS produces equivalence sets (multiple cards with same trick count)
- Layer 2: TacticalPlayFilter selects the "human" card from equivalence set
- Layer 3: These tests VALIDATE the selection follows bridge conventions

Test Categories:
1. Top of Sequence Leads - K from KQJ, Q from QJT
2. Lowest of Equals Following - J from QJ when both are DDS-equivalent
3. Signal Integrity - Cards chosen must allow partner to deduce hand
4. Declarer Unit Coordination - No Ace-on-King wastage
5. Defensive Deference - No Q-on-J wastage

Key Principle: If the AI plays a mathematically-correct card that violates
signaling conventions, the "Information Integrity" is broken and partner
cannot deduce the hand accurately.
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


class TestTopOfSequenceLeads:
    """
    Top of Sequence Lead Tests

    When leading from touching honors, always lead the TOP.
    This "denies" the card above and "promises" the cards below.

    Example: Leading K from KQJ promises Q and J, denies A
    Example: Leading Q from QJT promises J and T, denies K
    """

    def test_lead_king_from_kqj(self, filter):
        """
        Leading from KQJ: Must lead K (top of sequence)

        DDS Physics: K, Q, J may all be "equivalent" for trick count
        Human Heuristic: MUST lead K to promise Q and J

        Failure Mode: Leading Q "promises" K (which we have!) - misleading
        """
        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('5', '♠'),
                    Card('8', '♥'), Card('6', '♥'), Card('4', '♥'),
                    Card('7', '♦'), Card('3', '♦'),
                    Card('9', '♣'), Card('2', '♣')
                ]

        # DDS says K, Q, J all take same tricks (equivalence set)
        equiv_set = [Card('K', '♠'), Card('Q', '♠'), Card('J', '♠')]

        result = filter._select_opening_lead(equiv_set, MockHand(), trump_suit='♥')

        assert result.card.rank == 'K', (
            f"Humanity Failure: Led {result.card.rank}♠ from KQJ; expected K♠. "
            f"Leading Q or J is misleading - promises cards we don't have!"
        )
        assert "Sequence" in result.reason, "Should explain top of sequence principle"

    def test_lead_queen_from_qjt(self, filter):
        """
        Leading from QJT: Must lead Q (top of sequence)

        DDS Physics: Q, J, T may all be "equivalent"
        Human Heuristic: Lead Q - denies K, promises J and T
        """
        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('Q', '♠'), Card('J', '♠'), Card('T', '♠'), Card('5', '♠'),
                    Card('8', '♥'), Card('6', '♥'),
                    Card('7', '♦'), Card('3', '♦'),
                    Card('9', '♣'), Card('2', '♣'), Card('4', '♣')
                ]

        equiv_set = [Card('Q', '♠'), Card('J', '♠'), Card('T', '♠')]

        result = filter._select_opening_lead(equiv_set, MockHand(), trump_suit='♥')

        assert result.card.rank == 'Q', (
            f"Humanity Failure: Led {result.card.rank}♠ from QJT; expected Q♠. "
            f"Leading J or T promises cards above that we don't have!"
        )

    def test_lead_jack_from_jt9(self, filter):
        """
        Leading from JT9: Must lead J (top of sequence)

        DDS Physics: J, T, 9 often equivalent
        Human Heuristic: Lead J - denies Q, promises T and 9
        """
        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('J', '♦'), Card('T', '♦'), Card('9', '♦'), Card('4', '♦'),
                    Card('K', '♠'), Card('5', '♠'),
                    Card('8', '♥'), Card('3', '♥'),
                    Card('7', '♣'), Card('2', '♣'), Card('A', '♣')
                ]

        equiv_set = [Card('J', '♦'), Card('T', '♦'), Card('9', '♦')]

        result = filter._select_opening_lead(equiv_set, MockHand(), trump_suit=None)

        assert result.card.rank == 'J', (
            f"Humanity Failure: Led {result.card.rank}♦ from JT9; expected J♦."
        )


class TestLowestOfEqualsFollow:
    """
    Lowest of Equals Following Tests

    When following suit with touching honors, play the LOWEST (bottom).
    This signals possession of the higher honor(s).

    Example: Playing J from QJ signals possession of Q
    Example: Playing Q from KQ signals possession of K
    """

    def test_follow_jack_from_qj(self, filter):
        """
        Following with QJ: Play J (lowest of sequence)

        DDS Physics: Q and J both "equivalent" for trick count
        Human Heuristic: Play J to signal possession of Q

        Failure Mode: Playing Q "denies" the J (standard signals)
        """
        # Set up 3rd hand scenario with partner's Ace winning
        class MockState:
            def __init__(self):
                # Partner (N) led A♥, dummy (E) plays 5♥, we (S) follow
                self.current_trick = [
                    (Card('A', '♥'), 'N'),  # Partner leads Ace
                    (Card('5', '♥'), 'E'),  # Dummy plays low
                ]

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('Q', '♥'), Card('J', '♥'), Card('2', '♥'),
                    Card('K', '♠'), Card('5', '♠'),
                    Card('8', '♦'), Card('3', '♦'),
                    Card('7', '♣'), Card('4', '♣')
                ]

        # DDS says Q and J both equivalent (Ace wins regardless)
        equiv_set = [Card('Q', '♥'), Card('J', '♥')]

        result = filter._select_third_hand(equiv_set, MockState(), MockHand())

        assert result.card.rank == 'J', (
            f"Humanity Failure: Played {result.card.rank}♥ from QJ; expected J♥. "
            f"Playing J signals possession of Q - standard convention!"
        )
        # Can be BOTTOM_OF_SEQUENCE or MIN_OF_EQUALS (conserving honors)
        # Both are valid human reasoning for playing the lowest
        assert result.heuristic in [SignalHeuristic.BOTTOM_OF_SEQUENCE, SignalHeuristic.MIN_OF_EQUALS]

    def test_follow_queen_from_kq(self, filter):
        """
        Following with KQ: Play Q (lowest of sequence)

        DDS Physics: K and Q may be equivalent
        Human Heuristic: Play Q to signal possession of K
        """
        class MockState:
            def __init__(self):
                # Ace led, we follow
                self.current_trick = [
                    (Card('A', '♠'), 'W'),
                    (Card('3', '♠'), 'N'),
                ]

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('K', '♠'), Card('Q', '♠'), Card('4', '♠'),
                    Card('9', '♥'), Card('6', '♥'),
                    Card('8', '♦'), Card('2', '♦'),
                    Card('7', '♣'), Card('5', '♣')
                ]

        equiv_set = [Card('K', '♠'), Card('Q', '♠')]

        result = filter._select_third_hand(equiv_set, MockState(), MockHand())

        assert result.card.rank == 'Q', (
            f"Humanity Failure: Played {result.card.rank}♠ from KQ; expected Q♠."
        )

    def test_follow_ten_from_jt(self, filter):
        """
        Following with JT: Play T (lowest of touching)
        """
        class MockState:
            def __init__(self):
                self.current_trick = [
                    (Card('A', '♦'), 'S'),
                    (Card('4', '♦'), 'W'),
                ]

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('J', '♦'), Card('T', '♦'), Card('3', '♦'),
                    Card('K', '♠'), Card('5', '♠'),
                    Card('8', '♥'), Card('2', '♥'),
                    Card('9', '♣'), Card('6', '♣')
                ]

        equiv_set = [Card('J', '♦'), Card('T', '♦')]

        result = filter._select_third_hand(equiv_set, MockState(), MockHand())

        assert result.card.rank == 'T', (
            f"Humanity Failure: Played {result.card.rank}♦ from JT; expected T♦."
        )


class TestInformationIntegrity:
    """
    Information Integrity Tests

    Validates that the AI's play choices allow a human partner to
    accurately deduce the remaining cards in the AI's hand.

    The "Deduction Confidence" principle: Every play must be a
    valid "deduction trigger" under standard signaling conventions.
    """

    def test_opening_lead_deduction(self, filter):
        """
        Partner must be able to deduce holdings from opening lead.

        If AI leads K♠, partner should deduce:
        - AI has Q♠ (top of sequence promise)
        - AI likely has J♠ (extended sequence)
        - AI denies A♠
        """
        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'), Card('3', '♠'),
                    Card('A', '♥'), Card('5', '♥'),
                    Card('8', '♦'), Card('4', '♦'),
                    Card('6', '♣'), Card('2', '♣')
                ]

        equiv_set = [Card('K', '♠'), Card('Q', '♠'), Card('J', '♠')]
        result = filter._select_opening_lead(equiv_set, MockHand(), trump_suit=None)

        # Verify the deduction is valid
        assert result.card.rank == 'K', "Must lead K for valid deduction"

        # The deduction chain:
        # K lead → promises Q → partner expects KQ minimum
        # This is "Information Integrity"

    def test_high_spot_card_encourages(self, filter):
        """
        Discarding a high spot card (7-9) should encourage the suit.

        Partner deduction: "High spot = please lead this suit"
        """
        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('9', '♦'), Card('7', '♦'), Card('4', '♦'),  # Suit to encourage
                    Card('K', '♣'), Card('5', '♣'),
                    Card('8', '♠'), Card('3', '♠')
                ]

        equiv_set = [Card('9', '♦'), Card('7', '♦'), Card('4', '♦')]
        result = filter._select_discard(
            equiv_set, MockHand(), trump_suit='♠',
            want_suit=True, context=PlayContext.DISCARD_FIRST
        )

        # Should discard 9 (high spot) to encourage
        assert result.card.rank == '9', (
            f"Humanity Failure: Discarded {result.card.rank}♦ to encourage; expected 9♦."
        )
        assert result.heuristic == SignalHeuristic.ATTITUDE_SIGNAL

    def test_low_spot_card_discourages(self, filter):
        """
        Discarding a low spot card (2-4) should discourage the suit.

        Partner deduction: "Low spot = don't lead this suit"
        """
        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('9', '♦'), Card('7', '♦'), Card('4', '♦'),
                    Card('K', '♣'), Card('5', '♣'),
                    Card('8', '♠'), Card('3', '♠')
                ]

        equiv_set = [Card('9', '♦'), Card('7', '♦'), Card('4', '♦')]
        result = filter._select_discard(
            equiv_set, MockHand(), trump_suit='♠',
            want_suit=False, context=PlayContext.DISCARD_FIRST
        )

        # Should discard 4 (low spot) to discourage
        assert result.card.rank == '4', (
            f"Humanity Failure: Discarded {result.card.rank}♦ to discourage; expected 4♦."
        )


class TestDeclarerUnitCoordination:
    """
    Declarer Unit Coordination Tests

    Declarer controls both their hand and dummy. These hands form a
    "resource unit" - honors should not be wasted on the same trick.

    The "Ace on King" problem: DDS sees A and 7 as equivalent when
    K is winning from dummy, but a human knows not to waste the Ace.
    """

    def test_no_ace_on_king(self, filter):
        """
        Declarer must NOT play Ace when dummy's King is winning.

        DDS Physics: A♦ and 7♦ both "equivalent" (K wins regardless)
        Human Heuristic: Save the A♦ for later - it's a separate winner!
        """
        class MockContract:
            declarer = 'S'  # South is declarer
            trump_suit = None

        class MockState:
            def __init__(self):
                # North (dummy) leads K♦, East plays 3♦, South (declarer) to play
                self.current_trick = [
                    (Card('K', '♦'), 'N'),  # Dummy leads K
                    (Card('3', '♦'), 'E'),  # Defender plays low
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('A', '♦'), Card('7', '♦'), Card('2', '♦'),
                    Card('Q', '♠'), Card('5', '♠'),
                    Card('J', '♥'), Card('4', '♥'),
                    Card('8', '♣'), Card('3', '♣')
                ]

        equiv_set = [Card('A', '♦'), Card('7', '♦'), Card('2', '♦')]

        result = filter.select_tactical_card(
            equiv_set, MockState(), 'S', MockHand(), trump_suit=None
        )

        # Should play lowest (2 or 7), NOT the Ace
        assert result.card.rank != 'A', (
            f"Humanity Failure: Played A♦ on dummy's K♦! "
            f"This wastes a winner - expected low card."
        )
        assert result.context == PlayContext.DECLARER_CONSERVATION

    def test_no_queen_on_jack_declarer(self, filter):
        """
        Declarer should not play Q when dummy's J is winning.
        """
        class MockContract:
            declarer = 'E'  # East is declarer
            trump_suit = '♠'

        class MockState:
            def __init__(self):
                # West (dummy) leads J♥, South plays 5♥, East (declarer) to play
                self.current_trick = [
                    (Card('J', '♥'), 'W'),  # Dummy leads J
                    (Card('5', '♥'), 'S'),  # Defender plays low
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('Q', '♥'), Card('8', '♥'), Card('3', '♥'),
                    Card('A', '♠'), Card('K', '♠'),
                    Card('7', '♦'), Card('4', '♦'),
                    Card('6', '♣'), Card('2', '♣')
                ]

        equiv_set = [Card('Q', '♥'), Card('8', '♥'), Card('3', '♥')]

        result = filter.select_tactical_card(
            equiv_set, MockState(), 'E', MockHand(), trump_suit='♠'
        )

        assert result.card.rank != 'Q', (
            f"Humanity Failure: Played Q♥ on dummy's J♥! "
            f"Save the Q for later."
        )


class TestDefensiveDeference:
    """
    Defensive Deference Tests

    Defenders should not overtake partner's winning card.
    This preserves defensive resources and maintains suit control.

    The "Q on J" problem: When partner leads J and it's winning,
    don't play Q from Qx - save it for later positional leverage.
    """

    def test_no_queen_on_jack_defender(self, filter):
        """
        Defender must NOT play Q when partner's J is winning.

        Scenario: Partner leads J♠, dummy plays 3♠, we have Q♠ and 7♠
        DDS Physics: Q and 7 both "equivalent" (J wins regardless)
        Human Heuristic: Play 7 - preserve Q for future tricks
        """
        class MockContract:
            declarer = 'E'  # East is declarer
            trump_suit = None

        class MockState:
            def __init__(self):
                # South (partner) leads J♠, dummy (W) plays 3♠, North to play
                self.current_trick = [
                    (Card('J', '♠'), 'S'),  # Partner leads J
                    (Card('3', '♠'), 'W'),  # Dummy plays low
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                # North has Q♠ and 7♠ (4 cards in spades to avoid unblock)
                self.cards = [
                    Card('Q', '♠'), Card('7', '♠'), Card('4', '♠'), Card('2', '♠'),
                    Card('A', '♥'), Card('5', '♥'),
                    Card('8', '♦'), Card('3', '♦'),
                    Card('6', '♣')
                ]

        equiv_set = [Card('Q', '♠'), Card('7', '♠')]

        result = filter.select_tactical_card(
            equiv_set, MockState(), 'N', MockHand(), trump_suit=None
        )

        assert result.card.rank == '7', (
            f"Humanity Failure: Played {result.card.rank}♠ on partner's J♠; "
            f"expected 7♠. Q-on-J wastes defensive resources!"
        )
        assert result.context == PlayContext.DEFENSIVE_DEFERENCE

    def test_no_king_on_queen_defender(self, filter):
        """
        Defender must NOT play K when partner's Q is winning.
        """
        class MockContract:
            declarer = 'S'
            trump_suit = '♥'

        class MockState:
            def __init__(self):
                # West (partner) leads Q♦, dummy (N) plays 5♦, East to play
                self.current_trick = [
                    (Card('Q', '♦'), 'W'),
                    (Card('5', '♦'), 'N'),
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                # East has K♦ and small cards (4 cards to avoid unblock)
                self.cards = [
                    Card('K', '♦'), Card('8', '♦'), Card('4', '♦'), Card('2', '♦'),
                    Card('9', '♠'), Card('5', '♠'),
                    Card('7', '♣'), Card('3', '♣'),
                    Card('6', '♥')
                ]

        equiv_set = [Card('K', '♦'), Card('8', '♦')]

        result = filter.select_tactical_card(
            equiv_set, MockState(), 'E', MockHand(), trump_suit='♥'
        )

        assert result.card.rank == '8', (
            f"Humanity Failure: Played {result.card.rank}♦ on partner's Q♦; "
            f"expected 8♦."
        )


class TestUnblockingExceptions:
    """
    Unblocking Exception Tests

    Sometimes you MUST overtake partner - when blocking would kill the suit.
    These are the ONLY exceptions to the deference principle.

    The "Singleton Ace" problem: Partner leads K from KQJxx.
    You have singleton A. You MUST play A or you'll win the 2nd round
    and kill partner's suit!
    """

    def test_singleton_ace_must_unblock(self, filter):
        """
        Singleton Ace MUST be played to unblock.

        Scenario: Partner leads K♣, we have singleton A♣
        DDS Physics: A♣ is only option anyway
        Human Heuristic: Play A - essential unblock!

        Why: If we hold the A, we win round 2 and can't return the suit
        """
        class MockContract:
            declarer = 'S'
            trump_suit = None

        class MockState:
            def __init__(self):
                # West (partner) leads K♣, dummy plays 4♣, East to play
                self.current_trick = [
                    (Card('K', '♣'), 'W'),
                    (Card('4', '♣'), 'N'),
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                # East has SINGLETON A♣
                self.cards = [
                    Card('A', '♣'),  # Singleton - must unblock!
                    Card('Q', '♠'), Card('7', '♠'), Card('3', '♠'),
                    Card('J', '♥'), Card('5', '♥'), Card('2', '♥'),
                    Card('9', '♦'), Card('6', '♦'), Card('4', '♦')
                ]

        # Check unblock detection
        should_unblock = filter._should_unblock([Card('A', '♣')], MockHand(), '♣')
        assert should_unblock, "Must recognize singleton A as requiring unblock"

    def test_doubleton_ace_must_unblock(self, filter):
        """
        Doubleton Ax must play A to unblock.

        Scenario: Partner leads K from KQJxx, we have A-5 doubleton
        Human Heuristic: Play A now - if we play 5, we win round 4 and block
        """
        class MockContract:
            declarer = 'S'
            trump_suit = None

        class MockState:
            def __init__(self):
                self.current_trick = [
                    (Card('K', '♥'), 'W'),
                    (Card('3', '♥'), 'N'),
                ]
                self.trick_history = []
                self.contract = MockContract()

        class MockHand:
            def __init__(self):
                # Doubleton A-5
                self.cards = [
                    Card('A', '♥'), Card('5', '♥'),  # Doubleton
                    Card('Q', '♠'), Card('7', '♠'), Card('3', '♠'),
                    Card('J', '♦'), Card('8', '♦'), Card('4', '♦'),
                    Card('9', '♣'), Card('6', '♣'), Card('2', '♣')
                ]

        equiv_set = [Card('A', '♥'), Card('5', '♥')]

        # Check unblock detection
        should_unblock = filter._should_unblock(equiv_set, MockHand(), '♥')
        assert should_unblock, "Must recognize doubleton Ace as requiring unblock"

    def test_tripleton_ace_no_unblock(self, filter):
        """
        Tripleton Axx should NOT unblock immediately.

        With 3+ cards, we can follow low twice and still have A to return.
        """
        class MockHand:
            def __init__(self):
                self.cards = [
                    Card('A', '♦'), Card('7', '♦'), Card('3', '♦'),  # 3 cards
                    Card('K', '♠'), Card('5', '♠'),
                    Card('Q', '♥'), Card('4', '♥'),
                    Card('9', '♣'), Card('6', '♣'), Card('2', '♣')
                ]

        equiv_set = [Card('A', '♦'), Card('7', '♦'), Card('3', '♦')]

        should_unblock = filter._should_unblock(equiv_set, MockHand(), '♦')
        assert not should_unblock, "Should NOT unblock with 3+ cards"


class TestHeuristicScorecard:
    """
    Heuristic Scorecard Audit

    This class provides a structured audit of the tactical overlay
    against the standard bridge heuristics.

    Use this to generate a "pass/fail" report for each heuristic.
    """

    @pytest.fixture
    def scorecard_scenarios(self):
        """Define scenarios for scorecard audit"""
        return [
            {
                "heuristic": "Top of Sequence (Lead)",
                "equiv_set": ["K♠", "Q♠", "J♠"],
                "expected": "K♠",
                "context": "opening_lead"
            },
            {
                "heuristic": "Bottom of Sequence (Follow)",
                "equiv_set": ["Q♥", "J♥"],
                "expected": "J♥",
                "context": "third_hand"
            },
            {
                "heuristic": "2nd Hand Low",
                "equiv_set": ["Q♦", "J♦", "T♦"],
                "expected": "T♦",
                "context": "second_hand"
            },
            {
                "heuristic": "Win Cheaply (4th Hand)",
                "equiv_set": ["A♣", "K♣", "Q♣"],
                "trick_winner": "J♣",
                "expected": "Q♣",
                "context": "fourth_hand"
            },
        ]

    def test_scorecard_summary(self, filter, scorecard_scenarios):
        """
        Run all scorecard scenarios and produce summary.

        This test validates the tactical overlay against standard heuristics
        and produces a human-readable report.
        """
        results = []

        # Test 2nd hand low
        cards = [Card('Q', '♦'), Card('J', '♦'), Card('T', '♦')]
        result = filter._select_second_hand(cards, None)
        results.append({
            "heuristic": "2nd Hand Low",
            "expected": "T",
            "actual": result.card.rank,
            "passed": result.card.rank == 'T'
        })

        # Test 4th hand cheapest winner
        class MockState4th:
            def __init__(self):
                self.current_trick = [
                    (Card('7', '♣'), 'W'),
                    (Card('J', '♣'), 'N'),  # Current winner
                    (Card('3', '♣'), 'E')
                ]

        cards = [Card('A', '♣'), Card('K', '♣'), Card('Q', '♣')]
        result = filter._select_fourth_hand(cards, MockState4th())
        results.append({
            "heuristic": "Win Cheaply",
            "expected": "Q",
            "actual": result.card.rank,
            "passed": result.card.rank == 'Q'
        })

        # Print scorecard
        print("\n" + "=" * 60)
        print("HEURISTIC SCORECARD")
        print("=" * 60)
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"{r['heuristic']:25} | Expected: {r['expected']} | Got: {r['actual']} | {status}")
        print("=" * 60)

        # Assert all passed
        all_passed = all(r["passed"] for r in results)
        assert all_passed, "Some heuristics failed - see scorecard above"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
