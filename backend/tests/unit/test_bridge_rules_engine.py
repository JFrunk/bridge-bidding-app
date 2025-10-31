"""
Comprehensive test suite for BridgeRulesEngine

Tests all scenarios for hand visibility and control according to bridge rules.
Covers all combinations of:
- User position (N, E, S, W)
- Declarer position (N, E, S, W)
- User role (declarer, dummy, defender)
- Game state (before/after opening lead)
"""

import pytest
from engine.bridge_rules_engine import BridgeRulesEngine, GameState, PlayerRole


class TestDummyPosition:
    """Test dummy position calculation (partnerships)"""

    def test_north_declarer_has_south_dummy(self):
        assert BridgeRulesEngine.get_dummy_position('N') == 'S'

    def test_south_declarer_has_north_dummy(self):
        assert BridgeRulesEngine.get_dummy_position('S') == 'N'

    def test_east_declarer_has_west_dummy(self):
        assert BridgeRulesEngine.get_dummy_position('E') == 'W'

    def test_west_declarer_has_east_dummy(self):
        assert BridgeRulesEngine.get_dummy_position('W') == 'E'


class TestPlayerRole:
    """Test player role determination"""

    def test_declarer_role(self):
        role = BridgeRulesEngine.get_player_role('S', declarer='S', dummy='N')
        assert role == PlayerRole.DECLARER

    def test_dummy_role(self):
        role = BridgeRulesEngine.get_player_role('N', declarer='S', dummy='N')
        assert role == PlayerRole.DUMMY

    def test_defender_role_east(self):
        role = BridgeRulesEngine.get_player_role('E', declarer='S', dummy='N')
        assert role == PlayerRole.DEFENDER

    def test_defender_role_west(self):
        role = BridgeRulesEngine.get_player_role('W', declarer='S', dummy='N')
        assert role == PlayerRole.DEFENDER


class TestVisibleHandsUserIsDeclarer:
    """Test hand visibility when user (South) is declarer"""

    def test_before_opening_lead_user_declarer(self):
        """Before opening lead, declarer sees only their own hand (standard bridge protocol)"""
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            opening_lead_made=False,
            dummy_revealed=False
        )
        visible = BridgeRulesEngine.get_visible_hands(state)
        # Standard bridge: dummy is revealed AFTER opening lead, not before
        assert visible == {'S'}

    def test_after_opening_lead_user_declarer(self):
        """After opening lead, declarer sees own hand + dummy"""
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            opening_lead_made=True,
            dummy_revealed=True
        )
        visible = BridgeRulesEngine.get_visible_hands(state)
        assert visible == {'S', 'N'}


class TestVisibleHandsUserIsDummy:
    """Test hand visibility when user (South) is dummy"""

    def test_before_opening_lead_user_dummy(self):
        """When user is dummy before opening lead, they see only their own hand (standard bridge protocol)"""
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            opening_lead_made=False,
            dummy_revealed=False
        )
        visible = BridgeRulesEngine.get_visible_hands(state)
        # Standard bridge: dummy is laid down AFTER opening lead
        # Before lead, dummy (user at South) sees only their own hand
        assert visible == {'S'}

    def test_after_opening_lead_user_dummy(self):
        """After opening lead, dummy sees declarer's hand"""
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            opening_lead_made=True,
            dummy_revealed=True
        )
        visible = BridgeRulesEngine.get_visible_hands(state)
        assert visible == {'S', 'N'}


class TestVisibleHandsUserIsDefender:
    """Test hand visibility when user (South) is defender"""

    def test_before_opening_lead_user_defender(self):
        """Before opening lead, defender sees only their own hand"""
        state = GameState(
            declarer='E',
            dummy='W',
            user_position='S',
            opening_lead_made=False,
            dummy_revealed=False
        )
        visible = BridgeRulesEngine.get_visible_hands(state)
        # Only own hand before dummy revealed
        assert visible == {'S'}

    def test_after_opening_lead_user_defender(self):
        """After opening lead, defender sees own hand + dummy"""
        state = GameState(
            declarer='E',
            dummy='W',
            user_position='S',
            opening_lead_made=True,
            dummy_revealed=True
        )
        visible = BridgeRulesEngine.get_visible_hands(state)
        assert visible == {'S', 'W'}


class TestControllablePositionsUserIsDeclarer:
    """Test position control when user (South) is declarer"""

    def test_user_declarer_controls_both(self):
        """Declarer controls both declarer and dummy positions AFTER opening lead (standard bridge protocol)"""
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            opening_lead_made=True  # Must be after opening lead
        )
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        assert controllable == {'S', 'N'}

    def test_user_declarer_different_dummy(self):
        """Test with East-West partnership (but user is South, not West - testing defensive case)"""
        state = GameState(
            declarer='W',
            dummy='E',
            user_position='S',  # User is South (defender), not declarer
            opening_lead_made=True
        )
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        # User (South) is defender, only controls own position
        assert controllable == {'S'}


class TestControllablePositionsUserIsDummy:
    """Test position control when user (South) is dummy"""

    def test_user_dummy_controls_nothing(self):
        """SINGLE-PLAYER MODE: User controls both N and S even when S is dummy"""
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            opening_lead_made=True  # After opening lead, user controls both
        )
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        # SINGLE-PLAYER MODE: User controls both N and S when NS is declaring
        assert controllable == {'N', 'S'}


class TestControllablePositionsUserIsDefender:
    """Test position control when user (South) is defender"""

    def test_user_defender_controls_only_self(self):
        """Defender controls only their own position"""
        state = GameState(
            declarer='E',
            dummy='W',
            user_position='S'
        )
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        assert controllable == {'S'}

    def test_user_defender_partner_is_dummy(self):
        """Defender cannot control partner even if partner is dummy"""
        state = GameState(
            declarer='E',
            dummy='W',
            user_position='S'  # South is defender, North is partner
        )
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        assert controllable == {'S'}  # Cannot control North


class TestIsUserTurn:
    """Test turn determination"""

    def test_user_turn_as_declarer(self):
        """It's user's turn when next_to_play is user's position (after opening lead)"""
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='S',
            opening_lead_made=True  # After opening lead, user controls S
        )
        assert BridgeRulesEngine.is_user_turn(state) is True

    def test_user_turn_as_declarer_playing_dummy(self):
        """It's user's turn when declarer plays from dummy (after opening lead)"""
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='N',  # Dummy's turn, but user is declarer
            opening_lead_made=True  # After opening lead, user controls both S and N
        )
        assert BridgeRulesEngine.is_user_turn(state) is True

    def test_not_user_turn_as_declarer(self):
        """Not user's turn when defender plays"""
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='E'  # East's turn (defender)
        )
        assert BridgeRulesEngine.is_user_turn(state) is False

    def test_user_turn_as_defender(self):
        """It's user's turn when defender plays from own hand"""
        state = GameState(
            declarer='E',
            dummy='W',
            user_position='S',
            next_to_play='S'
        )
        assert BridgeRulesEngine.is_user_turn(state) is True

    def test_not_user_turn_as_defender(self):
        """Not user's turn when other positions play"""
        state = GameState(
            declarer='E',
            dummy='W',
            user_position='S',
            next_to_play='E'
        )
        assert BridgeRulesEngine.is_user_turn(state) is False

    def test_never_user_turn_when_dummy(self):
        """SINGLE-PLAYER MODE: User plays even when dummy in NS declaring"""
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            next_to_play='S',  # Dummy's position
            opening_lead_made=True  # After opening lead
        )
        # SINGLE-PLAYER MODE: User controls both N and S
        assert BridgeRulesEngine.is_user_turn(state) is True


class TestShouldAIPlay:
    """Test AI play determination (inverse of user turn)"""

    def test_ai_plays_when_not_user_turn(self):
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='E'
        )
        assert BridgeRulesEngine.should_ai_play(state) is True

    def test_ai_does_not_play_when_user_turn(self):
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='S',
            opening_lead_made=True  # After opening lead, user controls S
        )
        assert BridgeRulesEngine.should_ai_play(state) is False

    def test_ai_plays_all_positions_when_user_is_dummy(self):
        """SINGLE-PLAYER MODE: User plays when dummy in NS declaring"""
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            next_to_play='S',  # Dummy's turn
            opening_lead_made=True
        )
        # SINGLE-PLAYER MODE: User controls both N and S
        assert BridgeRulesEngine.should_ai_play(state) is False


class TestCanUserPlayFromPosition:
    """Test position-specific play permission"""

    def test_declarer_can_play_from_declarer_position(self):
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            opening_lead_made=True  # After opening lead, user controls S
        )
        assert BridgeRulesEngine.can_user_play_from_position(state, 'S') is True

    def test_declarer_can_play_from_dummy_position(self):
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            opening_lead_made=True  # After opening lead, user controls N (dummy)
        )
        assert BridgeRulesEngine.can_user_play_from_position(state, 'N') is True

    def test_declarer_cannot_play_from_defender_position(self):
        state = GameState(declarer='S', dummy='N', user_position='S')
        assert BridgeRulesEngine.can_user_play_from_position(state, 'E') is False

    def test_defender_can_play_from_own_position(self):
        state = GameState(declarer='E', dummy='W', user_position='S')
        assert BridgeRulesEngine.can_user_play_from_position(state, 'S') is True

    def test_defender_cannot_play_from_partner_position(self):
        state = GameState(declarer='E', dummy='W', user_position='S')
        assert BridgeRulesEngine.can_user_play_from_position(state, 'N') is False

    def test_dummy_cannot_play_from_any_position(self):
        """SINGLE-PLAYER MODE: User can play from both N and S when NS declares"""
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            opening_lead_made=True
        )
        # SINGLE-PLAYER MODE: User controls both N and S
        assert BridgeRulesEngine.can_user_play_from_position(state, 'S') is True
        assert BridgeRulesEngine.can_user_play_from_position(state, 'N') is True


class TestNextPlayer:
    """Test clockwise player progression"""

    def test_next_player_north_to_east(self):
        assert BridgeRulesEngine.get_next_player('N') == 'E'

    def test_next_player_east_to_south(self):
        assert BridgeRulesEngine.get_next_player('E') == 'S'

    def test_next_player_south_to_west(self):
        assert BridgeRulesEngine.get_next_player('S') == 'W'

    def test_next_player_west_to_north(self):
        assert BridgeRulesEngine.get_next_player('W') == 'N'


class TestOpeningLeader:
    """Test opening leader determination (LHO of declarer)"""

    def test_opening_leader_north_declarer(self):
        """North declares, East (LHO) leads"""
        assert BridgeRulesEngine.get_opening_leader('N') == 'E'

    def test_opening_leader_east_declarer(self):
        """East declares, South (LHO) leads"""
        assert BridgeRulesEngine.get_opening_leader('E') == 'S'

    def test_opening_leader_south_declarer(self):
        """South declares, West (LHO) leads"""
        assert BridgeRulesEngine.get_opening_leader('S') == 'W'

    def test_opening_leader_west_declarer(self):
        """West declares, North (LHO) leads"""
        assert BridgeRulesEngine.get_opening_leader('W') == 'N'


class TestValidatePlayRequest:
    """Test play request validation"""

    def test_valid_user_turn(self):
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='S'
        )
        valid, error = BridgeRulesEngine.validate_play_request(state, 'S')
        assert valid is True
        assert error is None

    def test_valid_ai_turn(self):
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='E'
        )
        valid, error = BridgeRulesEngine.validate_play_request(state, 'E')
        assert valid is True
        assert error is None

    def test_invalid_not_position_turn(self):
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='E'
        )
        valid, error = BridgeRulesEngine.validate_play_request(state, 'S')
        assert valid is False
        assert "Not S's turn" in error


class TestUIDisplayInfo:
    """Test comprehensive UI display information"""

    def test_ui_info_user_declarer(self):
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='S',
            opening_lead_made=True,
            dummy_revealed=True
        )
        info = BridgeRulesEngine.get_ui_display_info(state)

        assert set(info['visible_hands']) == {'S', 'N'}
        assert set(info['controllable_positions']) == {'S', 'N'}
        assert info['is_user_turn'] is True
        assert info['user_role'] == 'declarer'
        assert info['declarer'] == 'S'
        assert info['dummy'] == 'N'

    def test_ui_info_user_dummy(self):
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            next_to_play='N',
            opening_lead_made=True,
            dummy_revealed=True
        )
        info = BridgeRulesEngine.get_ui_display_info(state)

        assert set(info['visible_hands']) == {'S', 'N'}
        # SINGLE-PLAYER MODE: User controls both N and S when NS is declaring
        assert set(info['controllable_positions']) == {'N', 'S'}
        assert info['is_user_turn'] is True  # User plays from North's hand
        assert info['user_role'] == 'dummy'  # Role is dummy, but user still controls both

    def test_ui_info_user_defender(self):
        state = GameState(
            declarer='E',
            dummy='W',
            user_position='S',
            next_to_play='S',
            opening_lead_made=True,
            dummy_revealed=True
        )
        info = BridgeRulesEngine.get_ui_display_info(state)

        assert set(info['visible_hands']) == {'S', 'W'}
        assert set(info['controllable_positions']) == {'S'}
        assert info['is_user_turn'] is True
        assert info['user_role'] == 'defender'


class TestRealWorldScenarios:
    """Test complete game scenarios from start to finish"""

    def test_scenario_south_declarer_complete_trick(self):
        """
        Scenario: South is declarer, North is dummy
        Test complete first trick progression
        """
        # Opening lead - West leads (LHO of South)
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='W',
            opening_lead_made=False,
            dummy_revealed=False
        )

        # West's turn (AI plays opening lead)
        assert BridgeRulesEngine.should_ai_play(state) is True
        # Standard bridge: declarer sees ONLY own hand before opening lead
        assert BridgeRulesEngine.get_visible_hands(state) == {'S'}

        # After opening lead, dummy revealed
        state.opening_lead_made = True
        state.dummy_revealed = True
        state.next_to_play = 'N'

        # North's turn (user plays from dummy)
        assert BridgeRulesEngine.is_user_turn(state) is True
        assert BridgeRulesEngine.get_visible_hands(state) == {'S', 'N'}

        # East's turn
        state.next_to_play = 'E'
        assert BridgeRulesEngine.should_ai_play(state) is True

        # South's turn (user plays from own hand)
        state.next_to_play = 'S'
        assert BridgeRulesEngine.is_user_turn(state) is True

    def test_scenario_south_is_dummy(self):
        """
        Scenario: North is declarer, South is dummy
        SINGLE-PLAYER MODE: User controls both N and S (even when S is dummy)
        """
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            next_to_play='E',  # Opening lead
            opening_lead_made=False,
            dummy_revealed=False
        )

        # Opening lead - East leads, so AI plays
        assert BridgeRulesEngine.should_ai_play(state) is True

        # After opening lead, it's South's turn (dummy position)
        # In SINGLE-PLAYER mode, user plays from dummy when NS is declaring
        state.opening_lead_made = True
        state.dummy_revealed = True
        state.next_to_play = 'S'

        # SINGLE-PLAYER MODE: User controls both N and S
        assert BridgeRulesEngine.is_user_turn(state) is True  # User plays from dummy
        assert BridgeRulesEngine.should_ai_play(state) is False  # User controls
        assert BridgeRulesEngine.get_controllable_positions(state) == {'N', 'S'}

    def test_scenario_south_defender_opening_lead(self):
        """
        Scenario: South is defender and makes opening lead
        East is declarer, West is dummy
        """
        state = GameState(
            declarer='E',
            dummy='W',
            user_position='S',
            next_to_play='S',  # South leads (LHO of East)
            opening_lead_made=False,
            dummy_revealed=False
        )

        # South's turn to lead
        assert BridgeRulesEngine.is_user_turn(state) is True
        assert BridgeRulesEngine.get_visible_hands(state) == {'S'}  # Only own hand

        # After opening lead
        state.opening_lead_made = True
        state.dummy_revealed = True
        state.next_to_play = 'W'

        # Now sees dummy
        assert BridgeRulesEngine.get_visible_hands(state) == {'S', 'W'}
        # But cannot control dummy
        assert BridgeRulesEngine.is_user_turn(state) is False
