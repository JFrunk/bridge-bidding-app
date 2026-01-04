"""
Test Suite for Decay Curve Generation

This validates the "physics" of state reconstruction:
1. Serial Mutation: Cards are consumed in exact play order
2. Normalization: All values are from Declarer's perspective
3. Monotonicity: Potential can only decrease (or stay flat) for optimal play
4. Ghost Trick Detection: Increases indicate defensive errors, not logic bugs

The tests use mock DDS to validate logic without requiring the actual solver.
"""

import pytest
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# =============================================================================
# Test Fixtures: Hand State Representation
# =============================================================================

@dataclass
class Card:
    """A single card."""
    suit: str  # 'S', 'H', 'D', 'C'
    rank: str  # 'A', 'K', 'Q', 'J', 'T', '9', ..., '2'

    def __str__(self):
        return f"{self.suit}{self.rank}"

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.suit == other.suit and self.rank == other.rank
        return False

    def __hash__(self):
        return hash((self.suit, self.rank))


@dataclass
class PlayRecord:
    """A single play in the play history."""
    card: str  # e.g., 'SA' for Ace of Spades
    position: str  # 'N', 'E', 'S', 'W'


def parse_pbn_deal(pbn: str) -> Dict[str, List[Card]]:
    """
    Parse PBN deal format into hand dictionaries.

    Format: "N:AKQJ.T98.765.432 E:T98.765.432.AKQJ ..."
    Or: "N:AKQJ.T98.765.432" (space-separated hands in N/E/S/W order)
    """
    hands = {'N': [], 'E': [], 'S': [], 'W': []}

    # Handle both formats
    if pbn.startswith('N:') or pbn.startswith('E:') or pbn.startswith('S:') or pbn.startswith('W:'):
        # Format with position prefixes
        parts = pbn.split()
        for part in parts:
            pos, cards = part.split(':')
            hands[pos] = parse_hand_string(cards)
    else:
        # Assume N:... format for the whole string
        parts = pbn.split(':')
        if len(parts) == 2:
            # Single position format "N:cards"
            first_char = parts[0]
            if first_char in 'NESW':
                hands[first_char] = parse_hand_string(parts[1].split()[0])

    return hands


def parse_hand_string(hand_str: str) -> List[Card]:
    """
    Parse a hand string like 'AKQJ.T98.765.432' into cards.
    Order is Spades.Hearts.Diamonds.Clubs
    """
    cards = []
    suits = ['S', 'H', 'D', 'C']
    suit_cards = hand_str.split('.')

    for i, suit_str in enumerate(suit_cards):
        if i < len(suits):
            for rank in suit_str:
                if rank != '-':  # Handle empty suits
                    cards.append(Card(suits[i], rank))

    return cards


def get_partner(position: str) -> str:
    """Get partner's position."""
    partners = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
    return partners[position]


def get_next_player(position: str) -> str:
    """Get next player in clockwise order."""
    order = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}
    return order[position]


# =============================================================================
# State Reconstruction Engine (Under Test)
# =============================================================================

class StateReconstructor:
    """
    Reconstructs game state by consuming cards from play history.

    This is the "physics engine" that must be correct for decay curves.
    """

    def __init__(self, pbn_deal: str, declarer: str):
        """
        Initialize with starting deal and declarer position.

        Args:
            pbn_deal: PBN format deal string
            declarer: Position of declarer ('N', 'E', 'S', 'W')
        """
        self.initial_hands = parse_pbn_deal(pbn_deal)
        self.current_hands = {pos: list(cards) for pos, cards in self.initial_hands.items()}
        self.declarer = declarer
        self.declarer_side = {declarer, get_partner(declarer)}
        self.cards_played = 0
        self.current_trick = []
        self.tricks_won = {'NS': 0, 'EW': 0}

    def get_hand(self, position: str) -> List[Card]:
        """Get current hand for a position."""
        return self.current_hands[position]

    def get_cards_remaining(self, position: str) -> int:
        """Get number of cards remaining in a hand."""
        return len(self.current_hands[position])

    def get_total_cards_remaining(self) -> int:
        """Get total cards remaining across all hands."""
        return sum(len(h) for h in self.current_hands.values())

    def get_tricks_remaining(self) -> int:
        """Get number of complete tricks remaining."""
        return self.get_total_cards_remaining() // 4

    def play_card(self, card_str: str, position: str) -> bool:
        """
        Remove a card from a hand (simulate playing it).

        Args:
            card_str: Card string like 'SA' (Ace of Spades)
            position: Position playing the card

        Returns:
            True if card was found and removed, False otherwise
        """
        # Parse card string
        if len(card_str) < 2:
            return False

        suit = card_str[0]
        rank = card_str[1]
        target_card = Card(suit, rank)

        # Find and remove the card
        hand = self.current_hands[position]
        for i, card in enumerate(hand):
            if card == target_card:
                hand.pop(i)
                self.cards_played += 1
                self.current_trick.append((position, target_card))

                # Complete trick after 4 cards
                if len(self.current_trick) == 4:
                    self._complete_trick()

                return True

        return False

    def _complete_trick(self):
        """Process completed trick and determine winner."""
        # For testing, we don't need actual trick evaluation
        # Just reset the current trick
        self.current_trick = []

    def is_declarer_side_on_lead(self, leader: str) -> bool:
        """Check if declarer's side is on lead."""
        return leader in self.declarer_side

    def normalize_tricks(self, dds_result: int, leader: str) -> int:
        """
        Normalize DDS result to declarer's perspective.

        Args:
            dds_result: Max tricks DDS says leader's side can take
            leader: Position currently on lead

        Returns:
            Max tricks declarer's side can take
        """
        tricks_remaining = self.get_tricks_remaining()

        if self.is_declarer_side_on_lead(leader):
            # DDS result is already from declarer's perspective
            return dds_result
        else:
            # DDS result is from defense's perspective
            # Declarer's potential = Total tricks - Defense's potential
            return tricks_remaining - dds_result

    def validate_state(self) -> Tuple[bool, str]:
        """
        Validate current state is consistent.

        Returns:
            (is_valid, error_message)
        """
        # Check all hands have same number of cards
        hand_sizes = [len(h) for h in self.current_hands.values()]
        if len(set(hand_sizes)) > 1:
            return False, f"Unequal hand sizes: {hand_sizes}"

        # Check total cards is divisible by 4
        total = sum(hand_sizes)
        if total % 4 != 0:
            return False, f"Total cards ({total}) not divisible by 4"

        # Check no duplicate cards
        all_cards = []
        for hand in self.current_hands.values():
            all_cards.extend(hand)

        if len(all_cards) != len(set(all_cards)):
            return False, "Duplicate cards detected"

        return True, ""


# =============================================================================
# Mock DDS for Testing
# =============================================================================

class MockDDS:
    """
    Mock DDS solver for testing state reconstruction logic.

    Allows setting expected results for specific states.
    """

    def __init__(self):
        self.results = {}  # {(cards_remaining, leader): tricks}
        self.call_history = []

    def set_result(self, cards_remaining: int, leader: str, tricks: int):
        """Set expected result for a state."""
        self.results[(cards_remaining, leader)] = tricks

    def solve(self, reconstructor: StateReconstructor, leader: str) -> int:
        """
        Mock DDS solve - returns configured result or a sensible default.
        """
        cards_remaining = reconstructor.get_total_cards_remaining()
        self.call_history.append({
            'cards_remaining': cards_remaining,
            'leader': leader,
            'hands': {p: len(h) for p, h in reconstructor.current_hands.items()}
        })

        key = (cards_remaining, leader)
        if key in self.results:
            return self.results[key]

        # Default: assume roughly half the tricks
        tricks_remaining = cards_remaining // 4
        return tricks_remaining // 2


# =============================================================================
# Decay Curve Generator (Under Test)
# =============================================================================

class DecayCurveGenerator:
    """
    Generates decay curves from play history.

    The decay curve tracks declarer's trick potential at each card played.
    """

    def __init__(self, dds_solver):
        """
        Args:
            dds_solver: DDS solver (real or mock)
        """
        self.dds = dds_solver

    def generate(
        self,
        pbn_deal: str,
        play_history: List[Dict],
        declarer: str
    ) -> List[int]:
        """
        Generate decay curve for a hand.

        Args:
            pbn_deal: Initial deal in PBN format
            play_history: List of {'card': 'SA', 'position': 'W'}
            declarer: Declarer's position

        Returns:
            List of trick potentials (one per card played)
        """
        reconstructor = StateReconstructor(pbn_deal, declarer)
        decay_points = []

        for i, play in enumerate(play_history):
            card = play['card']
            position = play['position']

            # Query DDS BEFORE removing the card
            dds_result = self.dds.solve(reconstructor, position)

            # Normalize to declarer's perspective
            normalized = reconstructor.normalize_tricks(dds_result, position)
            decay_points.append(normalized)

            # Mutate state: remove the played card
            success = reconstructor.play_card(card, position)
            if not success:
                raise ValueError(f"Card {card} not found in {position}'s hand at play {i}")

        return decay_points

    def detect_errors(
        self,
        decay_curve: List[int],
        play_history: List[Dict],
        declarer: str,
        threshold: int = 1
    ) -> List[Dict]:
        """
        Detect major errors from decay curve.

        An error is when the potential drops by more than threshold.

        Args:
            decay_curve: Generated decay curve
            play_history: Original play history
            declarer: Declarer's position
            threshold: Minimum trick loss to flag as error

        Returns:
            List of error records
        """
        declarer_side = {declarer, get_partner(declarer)}
        errors = []

        for i in range(1, len(decay_curve)):
            delta = decay_curve[i] - decay_curve[i-1]

            if delta < -threshold:
                # Potential dropped - someone made an error
                play = play_history[i]
                position = play['position']

                # Determine whose error it was
                if position in declarer_side:
                    error_type = 'declarer_error'
                else:
                    error_type = 'defensive_gift'  # Defense gave away tricks

                errors.append({
                    'card_index': i,
                    'card': play['card'],
                    'position': position,
                    'loss': abs(delta),
                    'error_type': error_type,
                    'potential_before': decay_curve[i-1],
                    'potential_after': decay_curve[i]
                })

            elif delta > 0:
                # Potential increased - defense leaked a trick
                play = play_history[i]
                position = play['position']

                if position not in declarer_side:
                    errors.append({
                        'card_index': i,
                        'card': play['card'],
                        'position': position,
                        'gain': delta,
                        'error_type': 'defensive_leak',
                        'potential_before': decay_curve[i-1],
                        'potential_after': decay_curve[i]
                    })

        return errors


# =============================================================================
# Unit Tests
# =============================================================================

class TestStateReconstructor:
    """Tests for state reconstruction logic."""

    def test_parse_simple_hand(self):
        """Test parsing a simple hand string."""
        cards = parse_hand_string('AKQJ.T98.765.432')
        assert len(cards) == 13
        assert Card('S', 'A') in cards
        assert Card('H', 'T') in cards
        assert Card('D', '7') in cards
        assert Card('C', '2') in cards

    def test_parse_hand_with_voids(self):
        """Test parsing hands with void suits."""
        cards = parse_hand_string('AKQJT98765432...')
        assert len(cards) == 13
        # All spades
        for card in cards:
            assert card.suit == 'S'

    def test_initial_state_has_52_cards(self):
        """Test that initial state has exactly 52 cards."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        reconstructor = StateReconstructor(pbn, 'N')
        assert reconstructor.get_total_cards_remaining() == 52

    def test_play_card_removes_from_hand(self):
        """Test that playing a card removes it from the correct hand."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        reconstructor = StateReconstructor(pbn, 'N')

        initial_north = reconstructor.get_cards_remaining('N')
        assert initial_north == 13

        success = reconstructor.play_card('SA', 'N')
        assert success
        assert reconstructor.get_cards_remaining('N') == 12
        assert reconstructor.get_total_cards_remaining() == 51

    def test_play_nonexistent_card_fails(self):
        """Test that playing a card not in hand fails."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        reconstructor = StateReconstructor(pbn, 'N')

        # SA is in North's hand, not South's
        success = reconstructor.play_card('SA', 'S')
        assert not success

    def test_declarer_side_detection(self):
        """Test declarer side detection."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"

        # North is declarer
        reconstructor = StateReconstructor(pbn, 'N')
        assert reconstructor.is_declarer_side_on_lead('N')
        assert reconstructor.is_declarer_side_on_lead('S')
        assert not reconstructor.is_declarer_side_on_lead('E')
        assert not reconstructor.is_declarer_side_on_lead('W')

    def test_normalize_tricks_declarer_leading(self):
        """Test normalization when declarer's side is on lead."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        reconstructor = StateReconstructor(pbn, 'N')

        # DDS says North can take 9 tricks, North is leading
        # Result should be 9 (already from declarer's perspective)
        normalized = reconstructor.normalize_tricks(9, 'N')
        assert normalized == 9

    def test_normalize_tricks_defense_leading(self):
        """Test normalization when defense is on lead."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        reconstructor = StateReconstructor(pbn, 'N')

        # DDS says East can take 4 tricks, East is leading
        # Declarer's potential = 13 - 4 = 9
        normalized = reconstructor.normalize_tricks(4, 'E')
        assert normalized == 9

    def test_state_validation_equal_hands(self):
        """Test state validation with equal hand sizes."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        reconstructor = StateReconstructor(pbn, 'N')

        valid, msg = reconstructor.validate_state()
        assert valid, msg

    def test_state_after_complete_trick(self):
        """Test state remains valid after a complete trick."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        reconstructor = StateReconstructor(pbn, 'N')

        # Play one complete trick
        reconstructor.play_card('SA', 'N')
        reconstructor.play_card('ST', 'E')
        reconstructor.play_card('S6', 'S')
        reconstructor.play_card('S3', 'W')

        valid, msg = reconstructor.validate_state()
        assert valid, msg
        assert reconstructor.get_total_cards_remaining() == 48


class TestDecayCurveGenerator:
    """Tests for decay curve generation."""

    def test_simple_decay_curve(self):
        """Test generating a simple decay curve."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"

        mock_dds = MockDDS()
        # Set up mock results - tricks remaining decreases as cards are played
        # At 52 cards: 13 tricks remain, at 51: 12 tricks, at 50: 12, at 49: 12
        mock_dds.set_result(52, 'N', 9)  # Initial: N can take 9 of 13
        mock_dds.set_result(51, 'E', 4)  # After 1 card: E can take 4 of 12 -> declarer=8
        mock_dds.set_result(50, 'S', 9)  # After 2 cards: S can take 9 of 12
        mock_dds.set_result(49, 'W', 4)  # After 3 cards: W can take 4 of 12 -> declarer=8

        generator = DecayCurveGenerator(mock_dds)

        play_history = [
            {'card': 'SA', 'position': 'N'},
            {'card': 'ST', 'position': 'E'},
            {'card': 'S6', 'position': 'S'},
            {'card': 'S3', 'position': 'W'},
        ]

        curve = generator.generate(pbn, play_history, 'N')

        assert len(curve) == 4
        # Normalization depends on tricks remaining AND who is leading
        assert curve[0] == 9   # N leading, DDS=9, declarer side
        assert curve[1] == 8   # E leading, 12-4=8 (51 cards = 12 tricks)
        assert curve[2] == 9   # S leading, DDS=9, declarer side
        assert curve[3] == 8   # W leading, 12-4=8 (49 cards = 12 tricks)

    def test_decay_curve_monotonicity_optimal_play(self):
        """Test that optimal play produces flat or decreasing curve."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"

        mock_dds = MockDDS()
        # Simulate optimal play - declarer maintains 9 tricks throughout
        # Key: when defense leads, we set their max tricks so that:
        # tricks_remaining - defense_tricks = declarer_tricks
        #
        # Card 0 (52 cards, 13 tricks): N leads, declarer can take 9
        # Card 1 (51 cards, 12 tricks): E leads, defense can take 3 -> declarer=9
        # Card 2 (50 cards, 12 tricks): S leads, declarer can take 9
        # Card 3 (49 cards, 12 tricks): W leads, defense can take 3 -> declarer=9
        # Card 4 (48 cards, 12 tricks): N leads, declarer can take 9
        # etc.

        mock_dds.set_result(52, 'N', 9)
        mock_dds.set_result(51, 'E', 3)  # 12-3=9
        mock_dds.set_result(50, 'S', 9)
        mock_dds.set_result(49, 'W', 3)  # 12-3=9
        mock_dds.set_result(48, 'N', 9)
        mock_dds.set_result(47, 'E', 3)  # 11-3=8... hmm, this drops
        mock_dds.set_result(46, 'S', 8)
        mock_dds.set_result(45, 'W', 3)  # 11-3=8

        generator = DecayCurveGenerator(mock_dds)

        play_history = [
            {'card': 'SA', 'position': 'N'},
            {'card': 'ST', 'position': 'E'},
            {'card': 'S6', 'position': 'S'},
            {'card': 'S3', 'position': 'W'},
            {'card': 'SK', 'position': 'N'},
            {'card': 'S9', 'position': 'E'},
            {'card': 'S5', 'position': 'S'},
            {'card': 'S2', 'position': 'W'},
        ]

        curve = generator.generate(pbn, play_history, 'N')

        # Expected: [9, 9, 9, 9, 9, 8, 8, 8] - decreases after trick 1
        # Verify curve is monotonically non-increasing
        for i in range(1, len(curve)):
            assert curve[i] <= curve[i-1], f"Curve increased at index {i}: {curve[i-1]} -> {curve[i]}"

    def test_error_detection_declarer_mistake(self):
        """Test detection of declarer's mistakes."""
        mock_dds = MockDDS()
        # Scenario: Declarer has 10 tricks potential, but South makes a mistake
        # Card 0 (52 cards, 13 tricks): N leads, declarer can take 10
        # Card 1 (51 cards, 12 tricks): E leads, defense can take 2 -> declarer=10
        # Card 2 (50 cards, 12 tricks): S leads, but now only can take 8 (mistake!)
        # Card 3 (49 cards, 12 tricks): W leads, defense can take 4 -> declarer=8
        mock_dds.set_result(52, 'N', 10)
        mock_dds.set_result(51, 'E', 2)   # 12-2=10
        mock_dds.set_result(50, 'S', 8)   # Declarer dropped from 10 to 8!
        mock_dds.set_result(49, 'W', 4)   # 12-4=8

        generator = DecayCurveGenerator(mock_dds)

        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        play_history = [
            {'card': 'SA', 'position': 'N'},
            {'card': 'ST', 'position': 'E'},
            {'card': 'S6', 'position': 'S'},  # This is the mistake
            {'card': 'S3', 'position': 'W'},
        ]

        curve = generator.generate(pbn, play_history, 'N')
        # Expected curve: [10, 10, 8, 8]
        assert curve == [10, 10, 8, 8], f"Unexpected curve: {curve}"

        errors = generator.detect_errors(curve, play_history, 'N', threshold=1)

        # Should detect an error at position 2 (South's play dropped from 10 to 8)
        declarer_errors = [e for e in errors if e['error_type'] == 'declarer_error']
        assert len(declarer_errors) >= 1
        assert declarer_errors[0]['card_index'] == 2
        assert declarer_errors[0]['loss'] == 2

    def test_defensive_leak_detection(self):
        """Test detection of defensive leaks (tricks given back)."""
        mock_dds = MockDDS()
        # Scenario: East's play gives declarer an extra trick
        # Card 0 (52 cards, 13 tricks): N leads, declarer can take 9
        # Card 1 (51 cards, 12 tricks): E leads, defense can only take 2 now
        #   -> declarer = 12-2 = 10 (gained 1 trick!)
        mock_dds.set_result(52, 'N', 9)
        mock_dds.set_result(51, 'E', 2)  # Defense leaked: 12-2=10, up from 9

        generator = DecayCurveGenerator(mock_dds)

        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        play_history = [
            {'card': 'SA', 'position': 'N'},
            {'card': 'ST', 'position': 'E'},  # Defense leaks a trick
        ]

        curve = generator.generate(pbn, play_history, 'N')
        # Expected: [9, 10] - potential increased!
        assert curve == [9, 10], f"Unexpected curve: {curve}"

        errors = generator.detect_errors(curve, play_history, 'N', threshold=0)

        # Should detect a defensive leak at index 1
        leaks = [e for e in errors if e['error_type'] == 'defensive_leak']
        assert len(leaks) >= 1
        assert leaks[0]['card_index'] == 1
        assert leaks[0]['gain'] == 1


class TestNormalizationPhysics:
    """
    Tests for the "physics" of normalization.

    These validate that the normalization logic correctly handles
    the perspective shift between declarer and defense.
    """

    def test_full_hand_normalization(self):
        """Test normalization throughout an entire hand."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        reconstructor = StateReconstructor(pbn, 'N')

        # At start: 13 tricks available
        # If DDS says E can take 5, declarer can take 8
        normalized = reconstructor.normalize_tricks(5, 'E')
        assert normalized == 8

        # After 4 cards (1 trick): 12 tricks remaining
        for card, pos in [('SA', 'N'), ('ST', 'E'), ('S6', 'S'), ('S3', 'W')]:
            reconstructor.play_card(card, pos)

        assert reconstructor.get_tricks_remaining() == 12

        # If DDS says W can take 4, declarer can take 8
        normalized = reconstructor.normalize_tricks(4, 'W')
        assert normalized == 8

    def test_normalization_symmetry(self):
        """Test that NS and EW perspectives are symmetric."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"

        # North declarer
        recon_n = StateReconstructor(pbn, 'N')
        # East declarer (for comparison)
        recon_e = StateReconstructor(pbn, 'E')

        # Same DDS result (5 tricks for the side on lead)
        # should give opposite normalized results
        n_perspective = recon_n.normalize_tricks(5, 'N')  # N leading, N declarer
        e_perspective = recon_e.normalize_tricks(5, 'N')  # N leading, E declarer

        # N leading with 5 tricks: N as declarer sees 5, E as declarer sees 13-5=8
        assert n_perspective == 5
        assert e_perspective == 8
        assert n_perspective + e_perspective == 13


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_play_history(self):
        """Test with no plays."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        mock_dds = MockDDS()
        generator = DecayCurveGenerator(mock_dds)

        curve = generator.generate(pbn, [], 'N')
        assert curve == []

    def test_single_card_play(self):
        """Test with just one card played."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        mock_dds = MockDDS()
        mock_dds.set_result(52, 'N', 9)

        generator = DecayCurveGenerator(mock_dds)

        play_history = [{'card': 'SA', 'position': 'N'}]
        curve = generator.generate(pbn, play_history, 'N')

        assert len(curve) == 1
        assert curve[0] == 9

    def test_invalid_card_raises_error(self):
        """Test that playing an invalid card raises an error."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"
        mock_dds = MockDDS()
        mock_dds.set_result(52, 'N', 9)

        generator = DecayCurveGenerator(mock_dds)

        # Try to play a card that's not in the hand
        play_history = [{'card': 'HA', 'position': 'N'}]  # North doesn't have HA

        with pytest.raises(ValueError):
            generator.generate(pbn, play_history, 'N')

    def test_all_same_suit(self):
        """Test with hands that are all one suit."""
        # North has all spades
        pbn = "N:AKQJT98765432... E:-.AKQJT987654.32. S:-.32.AKQJT987654. W:-...AKQJT9876543"
        reconstructor = StateReconstructor(pbn, 'N')

        assert reconstructor.get_cards_remaining('N') == 13
        # All cards should be spades
        for card in reconstructor.get_hand('N'):
            assert card.suit == 'S'


class TestDatabaseSerialization:
    """Tests for JSON serialization of decay curves."""

    def test_decay_curve_json_serializable(self):
        """Test that decay curves can be serialized to JSON."""
        curve = [10, 10, 10, 8, 8, 7, 7, 6, 6, 6]

        json_str = json.dumps(curve)
        restored = json.loads(json_str)

        assert restored == curve

    def test_error_records_json_serializable(self):
        """Test that error records can be serialized to JSON."""
        errors = [
            {
                'card_index': 4,
                'card': 'SQ',
                'position': 'S',
                'loss': 2,
                'error_type': 'declarer_error',
                'potential_before': 10,
                'potential_after': 8
            }
        ]

        json_str = json.dumps(errors)
        restored = json.loads(json_str)

        assert restored == errors
        assert restored[0]['loss'] == 2


# =============================================================================
# Integration Test: Full Hand Simulation
# =============================================================================

class TestFullHandSimulation:
    """
    Integration tests simulating complete hands.

    These test the entire pipeline from PBN to decay curve.
    """

    def test_complete_trick_sequence(self):
        """Test processing a complete sequence of tricks."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"

        mock_dds = MockDDS()
        # Set up results for a 2-trick sequence
        # Trick 1: North leads, declarer takes the trick
        mock_dds.set_result(52, 'N', 9)
        mock_dds.set_result(51, 'E', 4)
        mock_dds.set_result(50, 'S', 9)
        mock_dds.set_result(49, 'W', 4)
        # Trick 2: North leads again
        mock_dds.set_result(48, 'N', 8)
        mock_dds.set_result(47, 'E', 4)
        mock_dds.set_result(46, 'S', 8)
        mock_dds.set_result(45, 'W', 4)

        generator = DecayCurveGenerator(mock_dds)

        play_history = [
            # Trick 1
            {'card': 'SA', 'position': 'N'},
            {'card': 'ST', 'position': 'E'},
            {'card': 'S6', 'position': 'S'},
            {'card': 'S3', 'position': 'W'},
            # Trick 2
            {'card': 'SK', 'position': 'N'},
            {'card': 'S9', 'position': 'E'},
            {'card': 'S5', 'position': 'S'},
            {'card': 'S2', 'position': 'W'},
        ]

        curve = generator.generate(pbn, play_history, 'N')

        assert len(curve) == 8
        # Verify DDS was called 8 times
        assert len(mock_dds.call_history) == 8

    def test_dds_call_order(self):
        """Verify DDS is called BEFORE each card is removed."""
        pbn = "N:AKQJ.T98.765.432 E:T987.AKQ.J98.765 S:654.765.AKQ.JT98 W:32.J432.T432.AKQ"

        mock_dds = MockDDS()
        generator = DecayCurveGenerator(mock_dds)

        play_history = [
            {'card': 'SA', 'position': 'N'},
            {'card': 'ST', 'position': 'E'},
        ]

        generator.generate(pbn, play_history, 'N')

        # First call should have 52 cards
        assert mock_dds.call_history[0]['cards_remaining'] == 52
        # Second call should have 51 cards (after first play)
        assert mock_dds.call_history[1]['cards_remaining'] == 51


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
