"""
Regression test for single-player dummy control bug

Bug History:
- Original working code (commit 2b0948a): User controlled both N and S when NS declaring
- Bug introduced (commit f5a8b7a): Added check that returned empty set if user is dummy
- Bug impact: User could not play when they were dummy in NS declaring hands
- Bug fixed (2025-10-31): Removed the incorrect dummy check

This test ensures that the SINGLE-PLAYER MODE behavior is maintained:
- In single-player digital bridge, user controls BOTH declarer and dummy when NS declaring
- This is DIFFERENT from 4-player bridge where dummy is passive

Test Case Source: backend/review_requests/hand_2025-10-31_15-32-54.json
User reported: "I could not play my hand"
"""

import pytest
from engine.bridge_rules_engine import BridgeRulesEngine, GameState


class TestSinglePlayerDummyControl:
    """
    Regression tests for single-player dummy control

    These tests ensure that the single-player mode behavior is maintained
    where the user controls BOTH North and South when NS is declaring,
    even when the user's position (South) is dummy.
    """

    def test_user_controls_both_when_south_is_dummy(self):
        """
        REGRESSION TEST: User can play when South is dummy

        Scenario from hand_2025-10-31_15-32-54.json:
        - Contract: 2♦ by North
        - Declarer: North
        - Dummy: South (user position)
        - User reported: "I could not play my hand"

        Expected: User controls BOTH N and S (single-player mode)
        """
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            next_to_play='S',  # South (dummy) is next to play
            opening_lead_made=True,
            dummy_revealed=True
        )

        # User should control both positions
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        assert controllable == {'N', 'S'}, \
            f"User should control both N and S, got {controllable}"

        # It should be user's turn
        assert BridgeRulesEngine.is_user_turn(state) is True, \
            "Should be user's turn when South (dummy) plays in NS declaring"

        # User can play from dummy position
        assert BridgeRulesEngine.can_user_play_from_position(state, 'S') is True, \
            "User should be able to play from dummy (South)"

        # User can also play from declarer position
        assert BridgeRulesEngine.can_user_play_from_position(state, 'N') is True, \
            "User should be able to play from declarer (North)"

    def test_user_controls_both_when_north_is_dummy(self):
        """
        Test the opposite case: North is dummy, South is declarer

        Expected: User still controls both N and S
        """
        state = GameState(
            declarer='S',
            dummy='N',
            user_position='S',
            next_to_play='N',  # North (dummy) is next to play
            opening_lead_made=True,
            dummy_revealed=True
        )

        # User should control both positions
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        assert controllable == {'N', 'S'}, \
            f"User should control both N and S, got {controllable}"

        # It should be user's turn (playing from dummy)
        assert BridgeRulesEngine.is_user_turn(state) is True, \
            "Should be user's turn when North (dummy) plays in NS declaring"

    def test_user_only_controls_south_when_ew_declaring(self):
        """
        Verify defense case: User only controls South when defending

        When EW is declaring, user is defending and should only control South
        """
        state = GameState(
            declarer='E',
            dummy='W',
            user_position='S',
            next_to_play='S',
            opening_lead_made=True,
            dummy_revealed=True
        )

        # User should only control South (defense)
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        assert controllable == {'S'}, \
            f"User should only control S when defending, got {controllable}"

    def test_before_opening_lead_only_leader_can_play(self):
        """
        Before opening lead, only the opening leader can act

        Even in single-player mode, user must wait for AI to make opening lead
        if opening leader is East or West
        """
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            next_to_play='E',  # East is opening leader
            opening_lead_made=False,
            dummy_revealed=False
        )

        # User should not control any positions (waiting for opening lead)
        controllable = BridgeRulesEngine.get_controllable_positions(state)
        assert controllable == set(), \
            f"User should control nothing before opening lead by AI, got {controllable}"

        # AI should play
        assert BridgeRulesEngine.should_ai_play(state) is True

    def test_ui_display_info_when_user_is_dummy(self):
        """
        Test UI display information for dummy scenario

        UI should show that user can play even though role is 'dummy'
        """
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            next_to_play='S',
            opening_lead_made=True,
            dummy_revealed=True
        )

        ui_info = BridgeRulesEngine.get_ui_display_info(state)

        assert ui_info['user_role'] == 'dummy', \
            "User role should be 'dummy'"

        assert ui_info['is_user_turn'] is True, \
            "UI should indicate it's user's turn"

        assert set(ui_info['controllable_positions']) == {'N', 'S'}, \
            "UI should show user controls both N and S"

        assert set(ui_info['visible_hands']) == {'S', 'N'}, \
            "UI should show both N and S hands visible"

    def test_complete_hand_progression_south_as_dummy(self):
        """
        Test a complete hand where South is dummy

        Simulates the progression of the problematic hand:
        1. East makes opening lead
        2. South (dummy) plays
        3. West plays
        4. North (declarer) plays
        """
        # After opening lead by East
        state = GameState(
            declarer='N',
            dummy='S',
            user_position='S',
            next_to_play='S',
            opening_lead_made=True,
            dummy_revealed=True
        )

        # 1. South's turn (user plays from dummy)
        assert BridgeRulesEngine.is_user_turn(state) is True
        assert 'S' in BridgeRulesEngine.get_controllable_positions(state)

        # 2. West's turn (AI plays)
        state.next_to_play = 'W'
        assert BridgeRulesEngine.is_user_turn(state) is False
        assert BridgeRulesEngine.should_ai_play(state) is True

        # 3. North's turn (user plays from declarer)
        state.next_to_play = 'N'
        assert BridgeRulesEngine.is_user_turn(state) is True
        assert 'N' in BridgeRulesEngine.get_controllable_positions(state)

        # 4. East's turn (AI plays)
        state.next_to_play = 'E'
        assert BridgeRulesEngine.is_user_turn(state) is False
        assert BridgeRulesEngine.should_ai_play(state) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
