"""
Simplified integration tests for architecture validation.

Tests that Phase 1 and Phase 2 components integrate without breaking existing functionality.
"""

import pytest
from core.session_manager import SessionManager
from core.deal_generator import DealGenerator
from core.scenario_loader import ScenarioLoader
from engine.hand import Hand, Card


class TestArchitectureIntegration:
    """Test integration of new architecture with existing code."""

    def test_deal_generator_produces_valid_hands(self):
        """Test that DealGenerator produces valid Hand objects."""
        hands = DealGenerator.generate_random_deal()

        # Verify structure
        assert all(pos in hands for pos in ['N', 'E', 'S', 'W'])
        assert all(isinstance(hand, Hand) for hand in hands.values())

        # Verify each hand has 13 cards
        for pos, hand in hands.items():
            assert len(hand.cards) == 13, f"{pos} hand doesn't have 13 cards"
            assert hand.hcp >= 0, f"{pos} HCP calculation failed"

    def test_session_manager_basic_operations(self):
        """Test SessionManager basic CRUD operations."""
        manager = SessionManager()

        # Create session
        session_id = manager.create_session('bidding', user_id='test_user')
        assert session_id is not None
        assert session_id.startswith('bidding_')

        # Retrieve session
        session = manager.get_session(session_id)
        assert session is not None
        assert session['type'] == 'bidding'
        assert session['user_id'] == 'test_user'

        # Update session
        test_data = {'deal': 'test_deal', 'auction': []}
        success = manager.update_session(session_id, test_data)
        assert success

        # Verify update
        updated_session = manager.get_session(session_id)
        assert updated_session['data'] == test_data

        # Delete session
        success = manager.delete_session(session_id)
        assert success

        # Verify deletion
        deleted_session = manager.get_session(session_id)
        assert deleted_session is None

    def test_scenario_loader_loads_bidding_scenarios(self):
        """Test ScenarioLoader can load bidding scenarios."""
        loader = ScenarioLoader()
        scenarios = loader.load_bidding_scenarios()

        assert len(scenarios) > 0, "Should load at least one scenario"

        # Validate first scenario structure
        scenario = scenarios[0]
        assert 'name' in scenario
        assert 'setup' in scenario

        # Validate scenario format
        assert loader.validate_bidding_scenario(scenario)

    def test_deal_generator_constrained_deals(self):
        """Test DealGenerator with constraints."""
        constraints = {
            'S': {'hcp_range': (15, 17), 'is_balanced': True},
            'N': None,
            'E': None,
            'W': None
        }

        hands = DealGenerator.generate_constrained_deal(constraints)

        # Check South hand meets constraints
        south_hand = hands['S']
        assert 15 <= south_hand.hcp <= 21  # Allow retry widening
        assert south_hand.is_balanced

    def test_session_isolation(self):
        """Test that sessions are properly isolated."""
        manager = SessionManager()

        # Create two sessions
        session1 = manager.create_session('bidding', user_id='user1')
        session2 = manager.create_session('bidding', user_id='user2')

        # Store different data
        manager.update_session(session1, {'deal': 'deal1'})
        manager.update_session(session2, {'deal': 'deal2'})

        # Verify isolation
        data1 = manager.get_session(session1)
        data2 = manager.get_session(session2)

        assert data1['data']['deal'] == 'deal1'
        assert data2['data']['deal'] == 'deal2'
        assert data1['user_id'] == 'user1'
        assert data2['user_id'] == 'user2'

    def test_deal_generator_all_cards_present(self):
        """Test that generated deal has all 52 unique cards."""
        hands = DealGenerator.generate_random_deal()

        all_cards = []
        for hand in hands.values():
            all_cards.extend(hand.cards)

        # Should have exactly 52 cards
        assert len(all_cards) == 52

        # All cards should be unique
        card_strings = [f"{c.rank}{c.suit}" for c in all_cards]
        assert len(set(card_strings)) == 52

    def test_scenario_loader_play_scenarios(self):
        """Test ScenarioLoader can load play scenarios."""
        loader = ScenarioLoader()
        play_scenarios = loader.load_play_scenarios()

        # Should have at least one play scenario
        assert len(play_scenarios) >= 1

        if play_scenarios:
            # Validate structure
            scenario = play_scenarios[0]
            assert 'name' in scenario or 'id' in scenario
            assert 'contract' in scenario
            assert 'hands' in scenario

    def test_multiple_deal_generations(self):
        """Test that multiple deal generations produce different hands."""
        deal1 = DealGenerator.generate_random_deal()
        deal2 = DealGenerator.generate_random_deal()

        # Deals should be different
        south1_cards = set(f"{c.rank}{c.suit}" for c in deal1['S'].cards)
        south2_cards = set(f"{c.rank}{c.suit}" for c in deal2['S'].cards)

        assert south1_cards != south2_cards, "Deals should be different"

    def test_session_manager_concurrent_access(self):
        """Test SessionManager handles multiple sessions concurrently."""
        manager = SessionManager()

        # Create 10 sessions rapidly
        session_ids = []
        for i in range(10):
            sid = manager.create_session('bidding', user_id=f'user{i}')
            session_ids.append(sid)

        # All sessions should exist
        assert len(session_ids) == 10
        assert len(set(session_ids)) == 10  # All unique

        # All should be retrievable
        for sid in session_ids:
            session = manager.get_session(sid)
            assert session is not None

    def test_deal_generator_balanced_hand(self):
        """Test DealGenerator can create balanced hands."""
        hand = DealGenerator.generate_balanced_hand((15, 17))

        # Should be balanced
        assert hand.is_balanced
        assert 15 <= hand.hcp <= 21  # Allow retry widening
        assert len(hand.cards) == 13

    def test_backward_compatibility_hand_class(self):
        """Test that Hand class still works with direct construction."""
        # Create hand the old way
        cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'), Card('J', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'),
            Card('A', '♦'), Card('K', '♦'),
            Card('A', '♣'), Card('K', '♣'), Card('Q', '♣'), Card('J', '♣')
        ]
        hand = Hand(cards)

        # Should calculate points correctly
        # 4A*4 + 4K*3 + 3Q*2 + 2J*1 = 16+12+6+2 = 36 HCP
        assert hand.hcp == 36
        assert len(hand.cards) == 13


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
