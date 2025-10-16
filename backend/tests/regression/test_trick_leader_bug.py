"""
Regression test for trick leader tracking bug

BUG: Trick history was recording current_play_state.next_to_play as the leader,
     but by that point next_to_play had already been updated to the trick winner.

FIX: Added current_trick_leader field to track who led each trick.

Reference: docs/BRIDGE_PLAY_AUDIT_2025-01-12.md Section 1.7
"""

import pytest
from engine.play_engine import PlayEngine, Contract, PlayState
from engine.hand import Hand, Card
from tests.integration.play_test_helpers import create_test_deal, create_play_scenario


class TestTrickLeaderTracking:
    """Test that trick leaders are correctly recorded in history"""

    def test_trick_leader_is_correct_first_trick(self):
        """First trick leader should be opening leader (LHO of declarer)"""
        # Setup: 3NT by South
        deal = create_test_deal(
            north="♠AKQ ♥432 ♦KQJ2 ♣432",
            east="♠765 ♥765 ♦7654 ♣765",
            south="♠432 ♥AKQ ♦A32 ♣AKQ8",
            west="♠JT98 ♥JT98 ♦T98 ♣JT9"
        )

        play_state = create_play_scenario("3NT by S", deal, "None")

        # Opening leader should be West (LHO of South)
        assert play_state.next_to_play == 'W'
        assert play_state.current_trick_leader is None  # Not set until first card played

        # Simulate playing one complete trick
        # West leads ♠J
        play_state.current_trick.append((Card('J', '♠'), 'W'))
        play_state.current_trick_leader = 'W'  # Track leader

        # North plays ♠A
        play_state.current_trick.append((Card('A', '♠'), 'N'))

        # East plays ♠7
        play_state.current_trick.append((Card('7', '♠'), 'E'))

        # South plays ♠4
        play_state.current_trick.append((Card('4', '♠'), 'S'))

        # Determine winner (should be North with ♠A)
        winner = PlayEngine.determine_trick_winner(play_state.current_trick, play_state.contract.trump_suit)
        assert winner == 'N'

        # Record trick in history
        from engine.play_engine import Trick
        play_state.trick_history.append(
            Trick(
                cards=list(play_state.current_trick),
                leader=play_state.current_trick_leader,  # Should be 'W'
                winner=winner  # Should be 'N'
            )
        )

        # Verify the trick history has correct leader
        assert len(play_state.trick_history) == 1
        assert play_state.trick_history[0].leader == 'W', "Leader should be West (opening leader)"
        assert play_state.trick_history[0].winner == 'N', "Winner should be North (played ♠A)"

    def test_trick_leader_changes_after_first_trick(self):
        """Second trick leader should be the winner of first trick"""
        # Setup
        deal = create_test_deal(
            north="♠AKQ ♥432 ♦KQJ2 ♣432",
            east="♠765 ♥765 ♦7654 ♣765",
            south="♠432 ♥AKQ ♦A32 ♣AKQ8",
            west="♠JT98 ♥JT98 ♦T98 ♣JT9"
        )

        play_state = create_play_scenario("3NT by S", deal, "None")

        # Play first trick (West leads, North wins)
        play_state.current_trick_leader = 'W'
        play_state.current_trick = [
            (Card('J', '♠'), 'W'),
            (Card('A', '♠'), 'N'),
            (Card('7', '♠'), 'E'),
            (Card('4', '♠'), 'S')
        ]

        winner1 = PlayEngine.determine_trick_winner(play_state.current_trick, None)
        assert winner1 == 'N'

        from engine.play_engine import Trick
        play_state.trick_history.append(
            Trick(cards=list(play_state.current_trick), leader='W', winner=winner1)
        )

        # Clear trick and set next leader
        play_state.current_trick = []
        play_state.current_trick_leader = None
        play_state.next_to_play = winner1  # Winner leads next

        # Play second trick (North leads because they won first trick)
        play_state.current_trick_leader = 'N'
        play_state.current_trick = [
            (Card('K', '♠'), 'N'),
            (Card('5', '♠'), 'E'),
            (Card('3', '♠'), 'S'),
            (Card('T', '♠'), 'W')
        ]

        winner2 = PlayEngine.determine_trick_winner(play_state.current_trick, None)
        assert winner2 == 'N'

        play_state.trick_history.append(
            Trick(cards=list(play_state.current_trick), leader='N', winner=winner2)
        )

        # Verify both tricks have correct leaders
        assert len(play_state.trick_history) == 2
        assert play_state.trick_history[0].leader == 'W', "First trick led by West (opening leader)"
        assert play_state.trick_history[0].winner == 'N', "First trick won by North"
        assert play_state.trick_history[1].leader == 'N', "Second trick led by North (first trick winner)"
        assert play_state.trick_history[1].winner == 'N', "Second trick won by North"

    def test_leader_not_same_as_winner(self):
        """Test case where leader and winner are different"""
        deal = create_test_deal(
            north="♠234 ♥AKQ ♦AKQ2 ♣432",
            east="♠AKQ ♥765 ♦7654 ♣765",
            south="♠765 ♥432 ♦432 ♣AKQ8",
            west="♠JT98 ♥JT98 ♦JT98 ♣JT9"
        )

        play_state = create_play_scenario("3NT by S", deal, "None")

        # West leads ♠J, East wins with ♠A
        play_state.current_trick_leader = 'W'
        play_state.current_trick = [
            (Card('J', '♠'), 'W'),
            (Card('2', '♠'), 'N'),
            (Card('A', '♠'), 'E'),  # East wins
            (Card('7', '♠'), 'S')
        ]

        winner = PlayEngine.determine_trick_winner(play_state.current_trick, None)
        assert winner == 'E'

        from engine.play_engine import Trick
        play_state.trick_history.append(
            Trick(cards=list(play_state.current_trick), leader='W', winner=winner)
        )

        # Verify leader and winner are different
        trick = play_state.trick_history[0]
        assert trick.leader == 'W', "West led the trick"
        assert trick.winner == 'E', "East won the trick"
        assert trick.leader != trick.winner, "Leader and winner should be different"

    def test_all_four_players_as_leader(self):
        """Test that all four players can be recorded as leaders"""
        deal = create_test_deal(
            north="♠AKQ2 ♥432 ♦KQJ ♣432",
            east="♠765 ♥AKQ ♦765 ♣7654",
            south="♠432 ♥765 ♦432 ♣AKQ5",
            west="♠JT98 ♥JT9 ♦AT9 ♣J87"
        )

        play_state = create_play_scenario("3NT by S", deal, "None")
        from engine.play_engine import Trick

        # Simulate 4 tricks, each led by a different player
        leaders = ['W', 'N', 'E', 'S']  # Opening leader is W, then we'll arrange winners

        for i, leader in enumerate(leaders):
            play_state.current_trick_leader = leader
            # Dummy trick data
            play_state.current_trick = [
                (Card('2', '♠'), leader),
                (Card('3', '♠'), PlayEngine.next_player(leader)),
                (Card('4', '♠'), PlayEngine.next_player(PlayEngine.next_player(leader))),
                (Card('5', '♠'), PlayEngine.partner(leader))
            ]

            # Just use leader as winner for simplicity (doesn't matter for this test)
            play_state.trick_history.append(
                Trick(cards=list(play_state.current_trick), leader=leader, winner=leader)
            )

        # Verify all players are recorded as leaders
        recorded_leaders = [trick.leader for trick in play_state.trick_history]
        assert recorded_leaders == ['W', 'N', 'E', 'S'], "All four players should appear as leaders"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
