"""
Unit tests for GamePhase state machine

Tests the explicit state machine implementation for game phases.
"""

import pytest
from engine.play_engine import GamePhase, PlayState, Contract
from engine.hand import Hand, Card


class TestGamePhaseEnum:
    """Test GamePhase enum properties and helpers"""

    def test_phase_string_representation(self):
        """Test that phases convert to strings correctly"""
        assert str(GamePhase.SETUP) == "setup"
        assert str(GamePhase.BIDDING) == "bidding"
        assert str(GamePhase.PLAY_IN_PROGRESS) == "play_in_progress"

    def test_is_play_phase(self):
        """Test is_play_phase property"""
        assert GamePhase.PLAY_STARTING.is_play_phase
        assert GamePhase.PLAY_IN_PROGRESS.is_play_phase
        assert GamePhase.PLAY_COMPLETE.is_play_phase

        assert not GamePhase.BIDDING.is_play_phase
        assert not GamePhase.SCORING.is_play_phase

    def test_is_bidding_phase(self):
        """Test is_bidding_phase property"""
        assert GamePhase.BIDDING.is_bidding_phase
        assert GamePhase.BIDDING_COMPLETE.is_bidding_phase

        assert not GamePhase.PLAY_STARTING.is_bidding_phase
        assert not GamePhase.SETUP.is_bidding_phase

    def test_allows_card_play(self):
        """Test allows_card_play property"""
        assert GamePhase.PLAY_STARTING.allows_card_play
        assert GamePhase.PLAY_IN_PROGRESS.allows_card_play

        assert not GamePhase.BIDDING.allows_card_play
        assert not GamePhase.PLAY_COMPLETE.allows_card_play
        assert not GamePhase.SCORING.allows_card_play

    def test_allows_bidding(self):
        """Test allows_bidding property"""
        assert GamePhase.BIDDING.allows_bidding

        assert not GamePhase.BIDDING_COMPLETE.allows_bidding
        assert not GamePhase.PLAY_STARTING.allows_bidding
        assert not GamePhase.SETUP.allows_bidding


class TestPlayStatePhaseTransitions:
    """Test PlayState phase transition validation"""

    def create_test_play_state(self, phase: GamePhase = GamePhase.PLAY_STARTING) -> PlayState:
        """Helper to create a test PlayState"""
        contract = Contract(level=3, strain='NT', declarer='S')

        # Create proper 13-card hands
        north_cards = [Card(r, '♠') for r in 'AKQJT98765432']
        east_cards = [Card(r, '♥') for r in 'AKQJT98765432']
        south_cards = [Card(r, '♦') for r in 'AKQJT98765432']
        west_cards = [Card(r, '♣') for r in 'AKQJT98765432']

        hands = {
            'N': Hand(north_cards),
            'E': Hand(east_cards),
            'S': Hand(south_cards),
            'W': Hand(west_cards)
        }

        return PlayState(
            contract=contract,
            hands=hands,
            current_trick=[],
            tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
            trick_history=[],
            next_to_play='W',
            dummy_revealed=False,
            phase=phase
        )

    def test_valid_transitions(self):
        """Test all valid phase transitions"""
        # SETUP → DEALING
        state = self.create_test_play_state(GamePhase.SETUP)
        state.transition_to(GamePhase.DEALING)
        assert state.phase == GamePhase.DEALING

        # DEALING → BIDDING
        state = self.create_test_play_state(GamePhase.DEALING)
        state.transition_to(GamePhase.BIDDING)
        assert state.phase == GamePhase.BIDDING

        # BIDDING → BIDDING_COMPLETE
        state = self.create_test_play_state(GamePhase.BIDDING)
        state.transition_to(GamePhase.BIDDING_COMPLETE)
        assert state.phase == GamePhase.BIDDING_COMPLETE

        # BIDDING_COMPLETE → PLAY_STARTING
        state = self.create_test_play_state(GamePhase.BIDDING_COMPLETE)
        state.transition_to(GamePhase.PLAY_STARTING)
        assert state.phase == GamePhase.PLAY_STARTING

        # PLAY_STARTING → PLAY_IN_PROGRESS
        state = self.create_test_play_state(GamePhase.PLAY_STARTING)
        state.transition_to(GamePhase.PLAY_IN_PROGRESS)
        assert state.phase == GamePhase.PLAY_IN_PROGRESS

        # PLAY_IN_PROGRESS → PLAY_IN_PROGRESS (stays in progress)
        state = self.create_test_play_state(GamePhase.PLAY_IN_PROGRESS)
        state.transition_to(GamePhase.PLAY_IN_PROGRESS)
        assert state.phase == GamePhase.PLAY_IN_PROGRESS

        # PLAY_IN_PROGRESS → PLAY_COMPLETE
        state = self.create_test_play_state(GamePhase.PLAY_IN_PROGRESS)
        state.transition_to(GamePhase.PLAY_COMPLETE)
        assert state.phase == GamePhase.PLAY_COMPLETE

        # PLAY_COMPLETE → SCORING
        state = self.create_test_play_state(GamePhase.PLAY_COMPLETE)
        state.transition_to(GamePhase.SCORING)
        assert state.phase == GamePhase.SCORING

        # SCORING → ROUND_COMPLETE
        state = self.create_test_play_state(GamePhase.SCORING)
        state.transition_to(GamePhase.ROUND_COMPLETE)
        assert state.phase == GamePhase.ROUND_COMPLETE

        # ROUND_COMPLETE → SETUP (new round)
        state = self.create_test_play_state(GamePhase.ROUND_COMPLETE)
        state.transition_to(GamePhase.SETUP)
        assert state.phase == GamePhase.SETUP

        # ROUND_COMPLETE → DEALING (new round, skip setup)
        state = self.create_test_play_state(GamePhase.ROUND_COMPLETE)
        state.transition_to(GamePhase.DEALING)
        assert state.phase == GamePhase.DEALING

    def test_invalid_transitions(self):
        """Test that invalid transitions raise ValueError"""
        # Cannot go from BIDDING to PLAY_STARTING (must go through BIDDING_COMPLETE)
        state = self.create_test_play_state(GamePhase.BIDDING)
        with pytest.raises(ValueError, match="Invalid phase transition"):
            state.transition_to(GamePhase.PLAY_STARTING)

        # Cannot go backwards from PLAY_IN_PROGRESS to PLAY_STARTING
        state = self.create_test_play_state(GamePhase.PLAY_IN_PROGRESS)
        with pytest.raises(ValueError, match="Invalid phase transition"):
            state.transition_to(GamePhase.PLAY_STARTING)

        # Cannot go from PLAY_STARTING to SCORING
        state = self.create_test_play_state(GamePhase.PLAY_STARTING)
        with pytest.raises(ValueError, match="Invalid phase transition"):
            state.transition_to(GamePhase.SCORING)

        # Cannot go from SCORING to BIDDING
        state = self.create_test_play_state(GamePhase.SCORING)
        with pytest.raises(ValueError, match="Invalid phase transition"):
            state.transition_to(GamePhase.BIDDING)

    def test_can_play_card_method(self):
        """Test can_play_card() method"""
        assert self.create_test_play_state(GamePhase.PLAY_STARTING).can_play_card()
        assert self.create_test_play_state(GamePhase.PLAY_IN_PROGRESS).can_play_card()

        assert not self.create_test_play_state(GamePhase.BIDDING).can_play_card()
        assert not self.create_test_play_state(GamePhase.PLAY_COMPLETE).can_play_card()
        assert not self.create_test_play_state(GamePhase.SCORING).can_play_card()

    def test_update_phase_after_card_first_card(self):
        """Test that phase updates from PLAY_STARTING to PLAY_IN_PROGRESS after first card"""
        state = self.create_test_play_state(GamePhase.PLAY_STARTING)
        assert state.phase == GamePhase.PLAY_STARTING

        # Simulate playing first card
        state.current_trick.append((Card('A', '♠'), 'W'))
        state.update_phase_after_card()

        assert state.phase == GamePhase.PLAY_IN_PROGRESS

    def test_update_phase_after_card_stays_in_progress(self):
        """Test that phase stays PLAY_IN_PROGRESS during play"""
        state = self.create_test_play_state(GamePhase.PLAY_IN_PROGRESS)

        # Simulate playing cards (not all 13 tricks)
        state.current_trick.append((Card('A', '♠'), 'W'))
        state.update_phase_after_card()

        assert state.phase == GamePhase.PLAY_IN_PROGRESS

    def test_update_phase_after_card_complete(self):
        """Test that phase updates to PLAY_COMPLETE when all tricks done"""
        state = self.create_test_play_state(GamePhase.PLAY_IN_PROGRESS)

        # Simulate all 13 tricks won
        state.tricks_won = {'N': 7, 'E': 0, 'S': 0, 'W': 6}
        state.update_phase_after_card()

        assert state.phase == GamePhase.PLAY_COMPLETE


class TestGamePhaseIntegration:
    """Integration tests for phase tracking during actual play"""

    def test_full_play_sequence_phases(self):
        """Test that phases update correctly through a full play sequence"""
        from engine.play_engine import PlayEngine

        # Create play state (simulates start-play endpoint)
        contract = Contract(level=3, strain='NT', declarer='S')

        # Create minimal 13-card hands for testing
        north_cards = [Card(r, '♠') for r in 'AKQJT98765432']
        east_cards = [Card(r, '♥') for r in 'AKQJT98765432']
        south_cards = [Card(r, '♦') for r in 'AKQJT98765432']
        west_cards = [Card(r, '♣') for r in 'AKQJT98765432']

        hands = {
            'N': Hand(north_cards),
            'E': Hand(east_cards),
            'S': Hand(south_cards),
            'W': Hand(west_cards)
        }

        state = PlayState(
            contract=contract,
            hands=hands,
            current_trick=[],
            tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
            trick_history=[],
            next_to_play='W',
            dummy_revealed=False,
            phase=GamePhase.PLAY_STARTING
        )

        # Initially in PLAY_STARTING
        assert state.phase == GamePhase.PLAY_STARTING
        assert state.can_play_card()

        # Play first card of first trick
        state.current_trick.append((Card('2', '♣'), 'W'))
        state.update_phase_after_card()

        # Should transition to PLAY_IN_PROGRESS after first card
        assert state.phase == GamePhase.PLAY_IN_PROGRESS

        # Complete first trick (play 3 more cards)
        state.current_trick.append((Card('2', '♠'), 'N'))
        state.update_phase_after_card()
        assert state.phase == GamePhase.PLAY_IN_PROGRESS

        state.current_trick.append((Card('2', '♥'), 'E'))
        state.update_phase_after_card()
        assert state.phase == GamePhase.PLAY_IN_PROGRESS

        state.current_trick.append((Card('2', '♦'), 'S'))

        # Still in progress after one trick (need 13 tricks total)
        state.tricks_won['N'] = 1
        state.update_phase_after_card()
        assert state.phase == GamePhase.PLAY_IN_PROGRESS

        # Simulate completing all 13 tricks
        state.tricks_won = {'N': 7, 'E': 3, 'S': 0, 'W': 3}
        state.update_phase_after_card()

        # Should transition to PLAY_COMPLETE after all 13 tricks
        assert state.phase == GamePhase.PLAY_COMPLETE
        assert not state.can_play_card()  # Can't play cards anymore

    def test_phase_validation_prevents_invalid_play(self):
        """Test that phase validation prevents play in wrong phases"""
        contract = Contract(level=3, strain='NT', declarer='S')

        # Create proper 13-card hands
        north_cards = [Card(r, '♠') for r in 'AKQJT98765432']
        east_cards = [Card(r, '♥') for r in 'AKQJT98765432']
        south_cards = [Card(r, '♦') for r in 'AKQJT98765432']
        west_cards = [Card(r, '♣') for r in 'AKQJT98765432']

        hands = {
            'N': Hand(north_cards),
            'E': Hand(east_cards),
            'S': Hand(south_cards),
            'W': Hand(west_cards)
        }

        # Try to play in BIDDING phase
        state = PlayState(
            contract=contract,
            hands=hands,
            current_trick=[],
            tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
            trick_history=[],
            next_to_play='W',
            dummy_revealed=False,
            phase=GamePhase.BIDDING
        )

        assert not state.can_play_card()

        # Try to play in PLAY_COMPLETE phase
        state.phase = GamePhase.PLAY_COMPLETE
        assert not state.can_play_card()

        # Try to play in SCORING phase
        state.phase = GamePhase.SCORING
        assert not state.can_play_card()
