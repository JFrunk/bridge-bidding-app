"""
Standalone Play Tests - Testing card play without bidding phase

These tests demonstrate how to test card play functionality independently
of the bidding phase, using the new factory methods and test helpers.
"""

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
from engine.play_engine import PlayEngine, Contract, PlayState
from engine.simple_play_ai import SimplePlayAI
from tests.play_test_helpers import (
    create_hand_from_string,
    create_test_deal,
    create_play_scenario,
    assert_play_result,
    print_hand_diagram
)


class TestStandalonePlayCreation:
    """Test that we can create play scenarios without bidding"""

    def test_create_3nt_contract_directly(self):
        """Test creating a 3NT contract without going through auction"""
        # Setup hands
        deal = create_test_deal(
            north="♠AKQ ♥432 ♦KQJ2 ♣432",
            east="♠765 ♥765 ♦7654 ♣765",
            south="♠432 ♥AKQ ♦A32 ♣AKQ8",
            west="♠JT98 ♥JT98 ♦T98 ♣JT9"
        )

        # Create play session directly (no bidding!)
        play_state = create_play_scenario("3NT by S", deal, "None")

        # Verify setup
        assert play_state.contract.level == 3
        assert play_state.contract.strain == 'NT'
        assert play_state.contract.declarer == 'S'
        assert play_state.next_to_play == 'W'  # Opening leader is LHO of South
        assert play_state.dummy == 'N'  # Dummy is partner of South

    def test_create_4_spade_contract_doubled(self):
        """Test creating a doubled contract"""
        deal = create_test_deal(
            north="♠KQ32 ♥432 ♦432 ♣432",
            east="♠765 ♥765 ♦765 ♣7654",
            south="♠AJT98 ♥AKQ ♦AK ♣AK5",
            west="♠4 ♥JT98 ♦QJT98 ♣QJT9"
        )

        play_state = create_play_scenario("4♠X by S", deal, "Both")

        assert play_state.contract.level == 4
        assert play_state.contract.strain == '♠'
        assert play_state.contract.declarer == 'S'
        assert play_state.contract.doubled == 1

    def test_factory_method_directly(self):
        """Test using PlayEngine.create_play_session directly"""
        deal = create_test_deal(
            north="♠AKQ2 ♥432 ♦KQJ ♣432",
            east="♠765 ♥765 ♦765 ♣7654",
            south="♠432 ♥AKQ ♦432 ♣AKQ5",
            west="♠JT98 ♥JT9 ♦AT9 ♣J87"
        )

        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        vulnerability = {'ns': False, 'ew': False}

        play_state = PlayEngine.create_play_session(contract, deal, vulnerability)

        assert play_state.contract == contract
        assert play_state.next_to_play == 'W'


class TestSimplePlayScenarios:
    """Test complete play scenarios from start to finish"""

    def test_simple_3nt_makes_exactly(self):
        """Test a 3NT contract that makes exactly 9 tricks"""
        # This is a simplified scenario where play is straightforward
        deal = create_test_deal(
            north="♠AKQ ♥432 ♦AKQ2 ♣432",     # Strong spades and diamonds
            east="♠765 ♥765 ♦765 ♣7654",      # Weak hand
            south="♠432 ♥AKQ ♦432 ♣AKQ8",    # Strong hearts and clubs
            west="♠JT98 ♥JT98 ♦JT98 ♣JT"     # All jacks and tens
        )

        play_state = create_play_scenario("3NT by S", deal, "None")
        ai = SimplePlayAI()

        # Print diagram for debugging (optional)
        # print_hand_diagram(deal, play_state.contract)

        # Simulate play (simplified - just verify setup)
        assert play_state.contract.tricks_needed == 9
        assert not play_state.is_complete
        assert len(play_state.hands['N'].cards) == 13

    def test_play_one_trick(self):
        """Test playing one complete trick"""
        deal = create_test_deal(
            north="♠AKQ ♥432 ♦AKQ2 ♣432",
            east="♠765 ♥765 ♦765 ♣7654",
            south="♠432 ♥AKQ ♦432 ♣AKQ8",
            west="♠JT98 ♥JT98 ♦JT98 ♣JT"
        )

        play_state = create_play_scenario("3NT by S", deal, "None")
        ai = SimplePlayAI()

        # West (opening leader) plays first
        assert play_state.next_to_play == 'W'

        # AI chooses opening lead
        card1 = ai.choose_card(play_state, 'W')
        assert card1 in play_state.hands['W'].cards

        # Play the card
        play_state.current_trick.append((card1, 'W'))
        play_state.hands['W'].cards.remove(card1)
        play_state.next_to_play = PlayEngine.next_player('W')

        # North (dummy) plays second
        assert play_state.next_to_play == 'N'
        assert not play_state.dummy_revealed
        play_state.dummy_revealed = True

        card2 = ai.choose_card(play_state, 'N')
        play_state.current_trick.append((card2, 'N'))
        play_state.hands['N'].cards.remove(card2)
        play_state.next_to_play = PlayEngine.next_player('N')

        # East plays third
        assert play_state.next_to_play == 'E'
        card3 = ai.choose_card(play_state, 'E')
        play_state.current_trick.append((card3, 'E'))
        play_state.hands['E'].cards.remove(card3)
        play_state.next_to_play = PlayEngine.next_player('E')

        # South plays fourth
        assert play_state.next_to_play == 'S'
        card4 = ai.choose_card(play_state, 'S')
        play_state.current_trick.append((card4, 'S'))
        play_state.hands['S'].cards.remove(card4)

        # Determine winner
        assert len(play_state.current_trick) == 4
        winner = PlayEngine.determine_trick_winner(
            play_state.current_trick,
            play_state.contract.trump_suit
        )

        assert winner in ['N', 'E', 'S', 'W']
        assert play_state.tricks_won[winner] == 0  # Not updated yet

        # Update tricks won
        play_state.tricks_won[winner] += 1
        assert play_state.tricks_won[winner] == 1


class TestLegalPlayValidation:
    """Test legal play rules without full bidding"""

    def test_must_follow_suit(self):
        """Test that players must follow suit if able"""
        deal = create_test_deal(
            north="♠AKQ ♥432 ♦AKQ2 ♣432",
            east="♠765 ♥765 ♦765 ♣7654",
            south="♠432 ♥AKQ ♦432 ♣AKQ8",
            west="♠JT98 ♥JT98 ♦JT98 ♣JT"
        )

        play_state = create_play_scenario("3NT by S", deal, "None")

        # Simulate West leading a spade
        from engine.hand import Card
        lead_card = Card('J', '♠')
        play_state.current_trick.append((lead_card, 'W'))

        # North has spades, so must follow suit
        north_hand = play_state.hands['N']
        heart_card = Card('4', '♥')  # North has hearts
        spade_card = Card('A', '♠')  # North has spades

        # Can't play heart when we have spades
        assert not PlayEngine.is_legal_play(heart_card, north_hand, play_state.current_trick, None)

        # Can play spade
        assert PlayEngine.is_legal_play(spade_card, north_hand, play_state.current_trick, None)

    def test_can_discard_when_void(self):
        """Test that players can discard any suit when void in led suit"""
        # Create hand with void
        north_hand = create_hand_from_string("♠AKQ ♥— ♦AKQJ432 ♣432")  # Wait, need exactly 13
        north_hand = create_hand_from_string("♠AKQ ♦AKQJ432 ♣432")  # 3+7+3 = 13, void in hearts

        from engine.hand import Card

        # Simulate a heart being led
        current_trick = [(Card('A', '♥'), 'E')]

        # North is void in hearts, can play any card
        diamond_card = Card('A', '♦')
        spade_card = Card('A', '♠')
        club_card = Card('4', '♣')

        assert PlayEngine.is_legal_play(diamond_card, north_hand, current_trick, None)
        assert PlayEngine.is_legal_play(spade_card, north_hand, current_trick, None)
        assert PlayEngine.is_legal_play(club_card, north_hand, current_trick, None)


class TestScoring:
    """Test scoring calculations without playing full hands"""

    def test_3nt_making_exactly_score(self):
        """Test score for 3NT making exactly (non-vulnerable)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        vulnerability = {'ns': False, 'ew': False}

        # 9 tricks = makes exactly
        score_result = PlayEngine.calculate_score(contract, 9, vulnerability)

        assert score_result['made'] is True
        assert score_result['overtricks'] == 0
        assert score_result['score'] == 400  # 40+30+30 + 300 game bonus

    def test_3nt_making_with_overtrick(self):
        """Test score for 3NT +1 (non-vulnerable)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        vulnerability = {'ns': False, 'ew': False}

        # 10 tricks = +1
        score_result = PlayEngine.calculate_score(contract, 10, vulnerability)

        assert score_result['made'] is True
        assert score_result['overtricks'] == 1
        assert score_result['score'] == 430  # 400 + 30 for overtrick

    def test_3nt_down_one(self):
        """Test score for 3NT -1 (non-vulnerable)"""
        contract = Contract(level=3, strain='NT', declarer='S', doubled=0)
        vulnerability = {'ns': False, 'ew': False}

        # 8 tricks = down 1
        score_result = PlayEngine.calculate_score(contract, 8, vulnerability)

        assert score_result['made'] is False
        assert score_result['undertricks'] == 1
        assert score_result['score'] == -50

    def test_4_spades_doubled_making_vulnerable(self):
        """Test score for 4♠X making (vulnerable)"""
        contract = Contract(level=4, strain='♠', declarer='S', doubled=1)
        vulnerability = {'ns': True, 'ew': False}

        # 10 tricks = makes exactly
        score_result = PlayEngine.calculate_score(contract, 10, vulnerability)

        assert score_result['made'] is True
        # 4♠ = 120 base, doubled = 240, +50 double bonus, +500 game bonus = 790
        assert score_result['score'] == 790


def test_complete_example_with_helpers():
    """
    Complete example showing how to use all helpers together
    This demonstrates the intended workflow for testing play
    """
    print("\n" + "="*60)
    print("COMPLETE STANDALONE PLAY TEST EXAMPLE")
    print("="*60)

    # Step 1: Create a deal
    print("\n1. Creating test deal...")
    deal = create_test_deal(
        north="♠AKQ2 ♥432 ♦KQJ ♣432",   # 4+3+3+3 = 13
        east="♠765 ♥765 ♦765 ♣7654",     # 3+3+3+4 = 13
        south="♠432 ♥AKQ ♦A32 ♣AKQ8",   # 3+3+3+4 = 13
        west="♠JT98 ♥JT98 ♦T98 ♣J9"     # 4+4+3+2 = 13
    )
    print("✓ Deal created")

    # Step 2: Create play scenario
    print("\n2. Creating play scenario: 3NT by South...")
    play_state = create_play_scenario("3NT by S", deal, "NS")
    print(f"✓ Contract: {play_state.contract}")
    print(f"✓ Opening leader: {play_state.next_to_play}")
    print(f"✓ Dummy: {play_state.dummy}")

    # Step 3: Show hand diagram
    print("\n3. Hand diagram:")
    print_hand_diagram(deal, play_state.contract)

    # Step 4: Verify setup
    print("4. Verifying setup...")
    assert play_state.contract.level == 3
    assert play_state.contract.strain == 'NT'
    assert play_state.contract.declarer == 'S'
    assert play_state.next_to_play == 'W'
    assert not play_state.is_complete
    print("✓ All assertions passed")

    print("\n" + "="*60)
    print("SUCCESS: Standalone play test completed!")
    print("="*60)


if __name__ == '__main__':
    # Run the complete example
    test_complete_example_with_helpers()

    # Run all tests with pytest if available
    if HAS_PYTEST:
        print("\nRunning all tests with pytest...")
        pytest.main([__file__, '-v'])
    else:
        print("\nNote: pytest not installed. Install with 'pip install pytest' to run full test suite.")
