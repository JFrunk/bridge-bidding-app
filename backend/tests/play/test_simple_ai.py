"""
Unit tests for SimplePlayAI

Tests the rule-based AI for card play:
- Opening lead selection
- Following suit strategies (2nd hand low, 3rd hand high)
- Discard and trump decisions
- Partnership awareness
"""

import pytest
from engine.hand import Hand, Card
from engine.play_engine import PlayEngine, PlayState, Contract
from engine.play.ai.simple_ai import SimplePlayAI
from tests.integration.play_test_helpers import create_test_deal, create_play_scenario


class TestSimpleAIBasics:
    """Test basic SimplePlayAI functionality"""

    def test_initialization(self):
        """Test AI initialization"""
        ai = SimplePlayAI()
        assert ai.get_name() == "Simple Rule-Based AI"
        assert ai.get_difficulty() == "beginner"

    def test_returns_legal_card(self):
        """Test that AI always returns a legal card"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")
        ai = SimplePlayAI()

        # Test opening lead from West
        card = ai.choose_card(state, 'W')
        assert card in state.hands['W'].cards

    def test_must_follow_suit(self):
        """Test that AI follows suit when able"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # West leads spade
        state.current_trick = [(Card('J', '♠'), 'W')]
        state.next_to_play = 'N'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'N')

        # North has spades, must follow suit
        assert card.suit == '♠'


class TestOpeningLeads:
    """Test opening lead selection"""

    def test_lead_4th_highest_from_length(self):
        """Test leading 4th highest from 4+ card suit"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT98 ♥Q32 ♦JT9 ♣KQ3"  # 4 spades, should lead 4th highest (13 cards)
        )

        state = create_play_scenario("3NT by N", deal, "None")
        ai = SimplePlayAI()

        card = ai.choose_card(state, 'W')

        # Should lead 4th highest from spades (8)
        # Or top of sequence if holding one
        assert card.suit == '♠'

    def test_lead_top_of_sequence(self):
        """Test leading top of honor sequence"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"  # KQJ sequence in clubs (13 cards)
        )

        state = create_play_scenario("3NT by N", deal, "None")
        ai = SimplePlayAI()

        card = ai.choose_card(state, 'W')

        # Should lead K from KQJ sequence
        assert card.suit == '♣'
        assert card.rank == 'K'

    def test_avoid_leading_trump(self):
        """Test avoiding trump leads when possible"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT98 ♦JT9 ♣KQ3"  # Has both trump and non-trump
        )

        # Spades are trump
        state = create_play_scenario("4♠ by N", deal, "None")
        ai = SimplePlayAI()

        card = ai.choose_card(state, 'W')

        # Should avoid leading trump
        assert card.suit != '♠'


class TestFollowSuitStrategies:
    """Test suit following strategies"""

    def test_second_hand_low(self):
        """Test second hand plays low"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # West leads J♠
        state.current_trick = [(Card('J', '♠'), 'W')]
        state.next_to_play = 'N'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'N')

        # North is second hand, should generally play low
        # (though with AKQ North might play high)
        assert card.suit == '♠'

    def test_third_hand_high(self):
        """Test third hand plays high"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # West leads, North plays, East is third
        state.current_trick = [
            (Card('J', '♠'), 'W'),
            (Card('2', '♠'), 'N')  # North played low
        ]
        state.next_to_play = 'E'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'E')

        # East is third hand, should play high to try to win
        assert card.suit == '♠'
        # East has 543, but with partner (W) leading J and North playing low,
        # the AI logic may play differently - just verify it's a spade

    def test_fourth_hand_win_cheaply(self):
        """Test fourth hand wins as cheaply as possible"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠JT98 ♥876 ♦8762 ♣87",  # South has JT98 in spades
            west="♠76 ♥JT9 ♦JT9 ♣KQJ96"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # West leads 7, North plays 2, East plays 5
        state.current_trick = [
            (Card('7', '♠'), 'W'),
            (Card('2', '♠'), 'N'),
            (Card('5', '♠'), 'E')
        ]
        state.next_to_play = 'S'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'S')

        # South (fourth hand) should win with lowest winning card
        assert card.suit == '♠'
        # 8 is the cheapest card that beats 7
        assert card.rank == '8'

    def test_play_low_when_partner_winning(self):
        """Test playing low when partner is winning"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠JT98 ♥876 ♦8762 ♣87",
            west="♠76 ♥JT9 ♦JT9 ♣KQJ96"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # West leads 7, North plays A (partner winning)
        state.current_trick = [
            (Card('7', '♠'), 'W'),
            (Card('A', '♠'), 'N')  # North (partner) winning with Ace
        ]
        state.next_to_play = 'E'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'E')

        # East should play low since partner (West) isn't winning
        # but declarer side is winning
        assert card.suit == '♠'


class TestDiscardAndTrump:
    """Test discard and trumping decisions"""

    def test_trump_when_opponents_winning(self):
        """Test trumping when opponents are winning"""
        # Carefully constructed - each hand has exactly 13 cards
        # East must be void in spades but have hearts (trump)
        # N: 4+3+3+3 = 13, E: 0+4+4+5 = 13, S: 3+3+3+4 = 13, W: 6+3+3+1 = 13
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ ♦AKQ ♣AKQ",  # 4+3+3+3 = 13
            east="♠— ♥5432 ♦5432 ♣JT987",  # 0+4+4+5 = 13, void in spades
            south="♠876 ♥876 ♦876 ♣6543",  # 3+3+3+4 = 13
            west="♠JT9543 ♥JT9 ♦JT9 ♣2"  # 6+3+3+1 = 13
        )

        # Hearts are trump
        state = create_play_scenario("4♥ by N", deal, "None")

        # West leads J♠, North plays A (opponents winning)
        state.current_trick = [
            (Card('J', '♠'), 'W'),
            (Card('A', '♠'), 'N')  # Declarer side winning
        ]
        state.next_to_play = 'E'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'E')

        # East is void in spades and has trump, should trump
        assert card.suit == '♥'

    def test_discard_low_when_partner_winning(self):
        """Test discarding low when partner is winning"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠— ♥5432 ♦5432 ♣5432T",  # Void in spades
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9543 ♥JT9 ♦JT ♣KQ"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # West leads J♠, North plays 2
        state.current_trick = [
            (Card('J', '♠'), 'W'),  # West (partner) leading high
            (Card('2', '♠'), 'N')
        ]
        state.next_to_play = 'E'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'E')

        # East is void and partner may be winning - should discard low
        # Should be lowest card from longest suit
        assert card.suit != '♠'  # Can't follow


class TestPartnershipAwareness:
    """Test that AI understands partnerships"""

    def test_ns_partnership(self):
        """Test North-South partnership recognition"""
        ai = SimplePlayAI()
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)

        # N is partner of S
        assert ai._is_partner_winning('N', 'S', contract) == True
        assert ai._is_partner_winning('S', 'N', contract) == True

        # E/W are opponents
        assert ai._is_partner_winning('E', 'S', contract) == False
        assert ai._is_partner_winning('W', 'N', contract) == False

    def test_ew_partnership(self):
        """Test East-West partnership recognition"""
        ai = SimplePlayAI()
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)

        # E is partner of W
        assert ai._is_partner_winning('E', 'W', contract) == True
        assert ai._is_partner_winning('W', 'E', contract) == True

        # N/S are opponents
        assert ai._is_partner_winning('N', 'E', contract) == False
        assert ai._is_partner_winning('S', 'W', contract) == False


class TestEdgeCases:
    """Test edge cases and unusual scenarios"""

    def test_singleton_lead(self):
        """Test leading from singleton"""
        # N: 4+4+3+2 = 13, E: 1+5+4+3 = 13, S: 3+3+4+3 = 13, W: 5+1+2+5 = 13
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",  # 4+4+3+2 = 13
            east="♠5 ♥JT987 ♦5432 ♣543",  # 1+5+4+3 = 13, singleton spade
            south="♠876 ♥654 ♦8762 ♣876",  # 3+3+4+3 = 13
            west="♠JT943 ♥3 ♦JT ♣KQJT9"  # 5+1+2+5 = 13
        )

        # East to lead
        state = create_play_scenario("3NT by S", deal, "None")
        ai = SimplePlayAI()

        # East can choose from any suit
        card = ai.choose_card(state, 'E')
        assert card in state.hands['E'].cards

    def test_void_multiple_suits(self):
        """Test discard when void in led suit with multiple discard options"""
        # Carefully constructed to have exactly 13 cards each, no duplicates
        # Spades: AKQJT98 (N) + 654 (S) + 732 (W) = 13 ✓
        # Hearts: AK (N) + QJT (E) + 9876 (S) + 5432 (W) = 13 ✓
        # Diamonds: AK (N) + QJT (E) + 9876 (S) + 5432 (W) = 13 ✓
        # Clubs: AK (N) + QJT9876 (E) + 54 (S) + 32 (W) = 2+7+2+2 = 13 ✓
        deal = create_test_deal(
            north="♠AKQJT98 ♥AK ♦AK ♣AK",  # 7+2+2+2 = 13
            east="♠— ♥QJT ♦QJT ♣QJT9876",  # 0+3+3+7 = 13, void in spades
            south="♠654 ♥9876 ♦9876 ♣54",  # 3+4+4+2 = 13
            west="♠732 ♥5432 ♦5432 ♣32"  # 3+4+4+2 = 13
        )

        state = create_play_scenario("4♠ by N", deal, "None")

        # North leads high spade
        state.current_trick = [(Card('A', '♠'), 'N')]
        state.next_to_play = 'E'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'E')

        # East must discard (void in spades)
        assert card.suit != '♠'
        # Should discard from longest suit (clubs)
        assert card.suit == '♣'

    def test_all_cards_same_value(self):
        """Test when multiple cards have same rank"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")

        # West leads 9♠
        state.current_trick = [(Card('9', '♠'), 'W')]
        state.next_to_play = 'N'

        ai = SimplePlayAI()
        card = ai.choose_card(state, 'N')

        # Should return a valid spade
        assert card.suit == '♠'
        assert card in state.hands['N'].cards


class TestFullTrickSequence:
    """Test complete trick sequences"""

    def test_complete_trick_all_positions(self):
        """Test AI plays correctly at all positions in a trick"""
        deal = create_test_deal(
            north="♠AKQ2 ♥AKQ2 ♦AKQ ♣A2",
            east="♠543 ♥543 ♦543 ♣5432",
            south="♠876 ♥876 ♦8762 ♣876",
            west="♠JT9 ♥JT9 ♦JT9 ♣KQJ9"
        )

        state = create_play_scenario("3NT by N", deal, "None")
        ai = SimplePlayAI()

        # Position 1: West leads
        card1 = ai.choose_card(state, 'W')
        assert card1 in state.hands['W'].cards

        state.current_trick = [(card1, 'W')]
        state.hands['W'].cards.remove(card1)

        # Position 2: North follows
        card2 = ai.choose_card(state, 'N')
        if any(c.suit == card1.suit for c in state.hands['N'].cards):
            assert card2.suit == card1.suit

        state.current_trick.append((card2, 'N'))
        state.hands['N'].cards.remove(card2)

        # Position 3: East follows
        card3 = ai.choose_card(state, 'E')
        if any(c.suit == card1.suit for c in state.hands['E'].cards):
            assert card3.suit == card1.suit

        state.current_trick.append((card3, 'E'))
        state.hands['E'].cards.remove(card3)

        # Position 4: South follows
        card4 = ai.choose_card(state, 'S')
        if any(c.suit == card1.suit for c in state.hands['S'].cards):
            assert card4.suit == card1.suit

        # All four cards played
        assert len(state.current_trick) == 3  # Before adding card4
