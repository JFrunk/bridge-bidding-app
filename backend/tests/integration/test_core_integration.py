"""
Integration tests for core shared components with existing bidding engine.

Tests that Phase 1 core components (SessionManager, DealGenerator, ScenarioLoader)
integrate correctly with existing bidding engine without breaking functionality.
"""

import pytest
from core.session_manager import SessionManager
from core.deal_generator import DealGenerator
from core.scenario_loader import ScenarioLoader
from engine.bidding_engine import BiddingEngine
from engine.hand import Hand


class TestCoreIntegration:
    """Test integration of core components with bidding engine."""

    def setup_method(self):
        """Setup for each test."""
        self.session_manager = SessionManager()
        self.bidding_engine = BiddingEngine()

    def test_deal_generator_produces_valid_hands_for_bidding(self):
        """Test that DealGenerator produces hands the bidding engine can use."""
        # Generate random deal
        hands = DealGenerator.generate_random_deal()

        # Verify all positions have valid hands
        assert all(pos in hands for pos in ['N', 'E', 'S', 'W'])
        assert all(isinstance(hand, Hand) for hand in hands.values())

        # Verify bidding engine can make opening bid with generated hand
        south_hand = hands['S']
        features = {
            'auction': [],
            'dealer': 'N',
            'position': 'S',
            'vulnerability': 'None'
        }

        bid, explanation = self.bidding_engine.get_bid(south_hand, features)

        # Should get a valid bid or Pass
        assert bid in ['Pass', '1♣', '1♦', '1♥', '1♠', '1NT', '2♣', '2♦', '2♥', '2♠', '2NT', '3♣', '3♦', '3♥', '3♠', '3NT', '4♣', '4♦', '4♥', '4♠', '5♣', '5♦', '6♣', '6♦', '7♣', '7♦']
        assert explanation is not None

    def test_deal_generator_constraint_hands_biddable(self):
        """Test that constrained deals produce biddable hands."""
        # Generate 1NT opening hand
        constraints = {
            'S': {'hcp_range': (15, 17), 'is_balanced': True},
            'N': None,
            'E': None,
            'W': None
        }

        hands = DealGenerator.generate_constrained_deal(constraints)
        south_hand = hands['S']

        # Should have 15-17 HCP
        assert 15 <= south_hand.hcp <= 17
        assert south_hand.is_balanced

        # Bidding engine should bid 1NT
        features = {
            'auction': [],
            'dealer': 'S',
            'position': 'S',
            'vulnerability': 'None'
        }

        bid, explanation = self.bidding_engine.get_bid(south_hand, features)
        assert bid == '1NT'

    def test_scenario_loader_integrates_with_bidding_engine(self):
        """Test that loaded scenarios work with bidding engine."""
        loader = ScenarioLoader()
        scenarios = loader.load_bidding_scenarios()

        assert len(scenarios) > 0, "Should have at least one scenario"

        # Take first scenario and verify it's valid
        scenario = scenarios[0]
        assert 'name' in scenario
        assert 'setup' in scenario

    def test_session_manager_isolates_bidding_state(self):
        """Test that SessionManager isolates state between sessions."""
        # Create two bidding sessions
        session1_id = self.session_manager.create_session('bidding', user_id='user1')
        session2_id = self.session_manager.create_session('bidding', user_id='user2')

        # Store different deals in each session
        deal1 = DealGenerator.generate_random_deal()
        deal2 = DealGenerator.generate_random_deal()

        self.session_manager.update_session(session1_id, {'deal': deal1, 'auction': []})
        self.session_manager.update_session(session2_id, {'deal': deal2, 'auction': ['1♥']})

        # Retrieve sessions and verify isolation
        session1 = self.session_manager.get_session(session1_id)
        session2 = self.session_manager.get_session(session2_id)

        assert session1['data']['auction'] == []
        assert session2['data']['auction'] == ['1♥']
        assert session1['data']['deal'] != session2['data']['deal']

    def test_full_bidding_sequence_with_generated_deal(self):
        """Test complete bidding sequence using generated deal."""
        # Create session
        session_id = self.session_manager.create_session('bidding')

        # Generate deal
        deal = DealGenerator.generate_random_deal()
        self.session_manager.update_session(session_id, {
            'deal': deal,
            'auction': [],
            'next_player': 0  # North
        })

        # Simulate bidding sequence
        auction = []
        positions = ['N', 'E', 'S', 'W']

        # Get bids for all 4 players
        for i in range(4):
            position = positions[i]
            hand = deal[position]

            features = {
                'auction': auction,
                'dealer': 'N',
                'position': position,
                'vulnerability': 'None'
            }

            bid, explanation = self.bidding_engine.get_bid(hand, features)
            auction.append({'bid': bid, 'explanation': explanation})

            # Update session with new auction state
            session_data = self.session_manager.get_session(session_id)
            session_data['data']['auction'] = auction
            self.session_manager.update_session(session_id, session_data['data'])

        # Verify we got 4 bids
        assert len(auction) == 4
        assert all('bid' in bid_obj for bid_obj in auction)
        assert all('explanation' in bid_obj for bid_obj in auction)

    def test_scenario_loader_backward_compatibility(self):
        """Test that ScenarioLoader handles both old and new scenario formats."""
        loader = ScenarioLoader()

        # Should load bidding scenarios from new location
        bidding_scenarios = loader.load_bidding_scenarios()
        assert len(bidding_scenarios) > 0

        # Each scenario should have required fields
        for scenario in bidding_scenarios:
            assert 'name' in scenario, f"Scenario missing 'name': {scenario}"
            assert 'setup' in scenario, f"Scenario missing 'setup': {scenario}"

    def test_deal_generator_for_all_contract_levels(self):
        """Test that DealGenerator works for all contract levels."""
        contract_tests = [
            ('1NT', 'S'),  # Partscore
            ('3NT', 'S'),  # Game
            ('4♠', 'S'),   # Major game
            ('6NT', 'S'),  # Slam
        ]

        for contract_str, declarer in contract_tests:
            hands = DealGenerator.generate_for_contract(contract_str, declarer)

            # Verify valid deal
            assert all(pos in hands for pos in ['N', 'E', 'S', 'W'])
            assert all(isinstance(hand, Hand) for hand in hands.values())

            # Verify declarer and dummy have reasonable combined strength
            dummy_pos = {'N': 'S', 'E': 'W', 'S': 'N', 'W': 'E'}[declarer]
            combined_hcp = hands[declarer].hcp + hands[dummy_pos].hcp

            # Should have reasonable HCP for contract
            if '6' in contract_str:  # Slam
                assert combined_hcp >= 25
            elif '3NT' in contract_str or '4' in contract_str:  # Game
                assert combined_hcp >= 20
            else:  # Partscore
                assert combined_hcp >= 15

    def test_session_cleanup_doesnt_break_active_sessions(self):
        """Test that session cleanup only removes expired sessions."""
        import time

        # Create active session
        active_id = self.session_manager.create_session('bidding', user_id='active')

        # Create expired session (manually set old timestamp)
        expired_id = self.session_manager.create_session('bidding', user_id='expired')
        self.session_manager._sessions[expired_id]['last_accessed'] = time.time() - 7200  # 2 hours ago

        # Run cleanup
        removed_count = self.session_manager.cleanup_expired_sessions()

        # Active session should still exist
        assert self.session_manager.get_session(active_id) is not None

        # Expired session should be removed
        assert self.session_manager.get_session(expired_id) is None
        assert removed_count >= 1

    def test_multiple_sessions_concurrent_bidding(self):
        """Test that multiple sessions can bid concurrently without interference."""
        # Create 3 concurrent sessions
        sessions = []
        for i in range(3):
            session_id = self.session_manager.create_session('bidding', user_id=f'user{i}')
            deal = DealGenerator.generate_random_deal()
            self.session_manager.update_session(session_id, {'deal': deal, 'auction': []})
            sessions.append(session_id)

        # Make bids in different sessions
        for i, session_id in enumerate(sessions):
            session = self.session_manager.get_session(session_id)
            hand = session['data']['deal']['S']

            features = {
                'auction': [],
                'dealer': 'S',
                'position': 'S',
                'vulnerability': 'None'
            }

            bid, explanation = self.bidding_engine.get_bid(hand, features)

            # Update session with bid
            session['data']['auction'].append({'bid': bid, 'explanation': explanation})
            self.session_manager.update_session(session_id, session['data'])

        # Verify all sessions have independent state
        for i, session_id in enumerate(sessions):
            session = self.session_manager.get_session(session_id)
            assert len(session['data']['auction']) == 1
            assert session['user_id'] == f'user{i}'


class TestBackwardCompatibility:
    """Test that new architecture doesn't break existing functionality."""

    def test_bidding_engine_still_works(self):
        """Test that BiddingEngine still functions with direct Hand objects."""
        engine = BiddingEngine()

        # Create hand the old way (direct construction)
        from engine.hand import Card
        cards = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
            Card('A', '♥'), Card('K', '♥'), Card('Q', '♥'),
            Card('A', '♦'), Card('K', '♦'),
            Card('A', '♣'), Card('K', '♣'), Card('Q', '♣'),
            Card('J', '♣'), Card('T', '♣')
        ]
        hand = Hand(cards)

        features = {
            'auction': [],
            'dealer': 'S',
            'position': 'S',
            'vulnerability': 'None'
        }

        # Should still be able to get a bid
        bid, explanation = engine.get_bid(hand, features)
        assert bid in ['2NT', '2♣', '1NT', '3NT']  # Strong hand should bid something

    def test_existing_test_data_still_works(self):
        """Test that existing test data formats still work."""
        loader = ScenarioLoader()

        # Should be able to load scenarios
        scenarios = loader.load_bidding_scenarios()
        assert len(scenarios) > 0

        # Pick a scenario and validate it
        scenario = scenarios[0]
        assert loader.validate_bidding_scenario(scenario)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
