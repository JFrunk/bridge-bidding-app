"""
Test Deference & Unblocking Logic in TacticalPlayFilter

Tests the defensive logic where:
1. DEFER when partner is winning and we have length (3+ cards)
2. UNBLOCK when partner leads and we have doubleton honor

Key scenarios:
- Partner leads K, we have A-x-x (3+ cards) → DEFER (play x)
- Partner leads K, we have A-x (doubleton) → UNBLOCK (play A)
- Partner leads J, we have Q-x-x (3+ cards) → DEFER (play x)
- Partner leads J, we have Q-x (doubleton) → UNBLOCK (play Q)

Note: The card in equivalence set must be HIGHER than partner's card
for deference/unblocking to apply. If we can't overtake, it's just
regular follow-suit logic.
"""

import pytest
from engine.play.ai.play_signal_overlay import TacticalPlayFilter, SignalHeuristic
from engine.hand import Card, Hand


class MockContract:
    """Mock contract for testing"""
    def __init__(self, declarer='S', trump_suit=None):
        self.declarer = declarer
        self.trump_suit = trump_suit


class MockGameState:
    """Mock game state for testing"""
    def __init__(self, current_trick=None, contract=None):
        self.current_trick = current_trick or []
        self.contract = contract


def make_hand(cards_str: str) -> Hand:
    """Create a Hand from a simple string like 'A73' for clubs"""
    suit = '♣'
    cards = []
    for rank in cards_str:
        cards.append(Card(rank, suit))
    # Pad with other suits to make 13 cards
    other_suits = ['♠', '♥', '♦']
    other_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T']
    idx = 0
    while len(cards) < 13:
        cards.append(Card(other_ranks[idx % len(other_ranks)],
                         other_suits[idx % len(other_suits)]))
        idx += 1
    return Hand(cards)


class TestDeferenceWithLength:
    """Test deference when we have 3+ cards (should defer, not unblock)"""

    def test_defer_with_ace_tripleton(self):
        """Partner leads K, we have A-7-3. Should defer (play low)."""
        tpf = TacticalPlayFilter()

        # West leads K♣, East has A-7-3♣ (3 cards)
        # Contract: South declares, so East and West are defenders
        # (North is dummy - opposite of declarer South)
        contract = MockContract(declarer='S', trump_suit=None)

        # West (E's partner) leads K♣
        current_trick = [
            (Card('K', '♣'), 'W'),  # Partner leads K
        ]

        game_state = MockGameState(current_trick=current_trick, contract=contract)

        # East has A♣ and 7♣ in equivalence set (both DDS-equivalent)
        # Full hand has A-7-3 in clubs (3 cards = should defer)
        hand = make_hand('A73')
        equivalence_set = [Card('A', '♣'), Card('7', '♣')]

        # Check should_defer_to_partner (East = 'E', partner is West)
        should_defer = tpf._should_defer_to_partner(
            game_state, 'E', equivalence_set, hand
        )

        assert should_defer is True, "Should defer with 3+ cards - not unblock"

        # If we actually selected, we'd play low
        if should_defer:
            result = tpf._select_defensive_deference(equivalence_set, game_state)
            assert result.card.rank == '7', f"Should play 7, not {result.card.rank}"


class TestUnblockingWithDoubleton:
    """Test unblocking when we have exactly 2 cards (should unblock)"""

    def test_unblock_with_ace_doubleton(self):
        """Partner leads K, we have A-x. Should unblock (play A)."""
        tpf = TacticalPlayFilter()

        # West leads K♣, East has A-7♣ (doubleton)
        # South declares, so East and West are defenders
        contract = MockContract(declarer='S', trump_suit=None)

        current_trick = [
            (Card('K', '♣'), 'W'),  # Partner leads K
        ]

        game_state = MockGameState(current_trick=current_trick, contract=contract)

        # Hand has exactly 2 clubs (A-7 doubleton)
        hand = make_hand('A7')
        equivalence_set = [Card('A', '♣'), Card('7', '♣')]

        # Check should_defer - should be FALSE because we need to unblock
        should_defer = tpf._should_defer_to_partner(
            game_state, 'E', equivalence_set, hand
        )

        # Should NOT defer - need to unblock with doubleton
        assert should_defer is False, "Should NOT defer with doubleton honor - need to unblock!"

        # Verify unblock check directly
        should_unblock = tpf._should_unblock(equivalence_set, hand, '♣')
        assert should_unblock is True, "Should unblock with A-x doubleton"


class TestUnblockingWithQueen:
    """Test unblocking with Q-x doubleton when partner leads J"""

    def test_unblock_queen_doubleton_on_jack(self):
        """Partner leads J, we have Q-x doubleton. Should unblock (play Q)."""
        tpf = TacticalPlayFilter()

        # West leads J♣, East has Q-7♣ (doubleton)
        # Q > J so we CAN overtake - this is a real deference/unblock decision
        # South declares, so East and West are defenders
        contract = MockContract(declarer='S', trump_suit=None)

        current_trick = [
            (Card('J', '♣'), 'W'),  # Partner leads J
        ]

        game_state = MockGameState(current_trick=current_trick, contract=contract)

        # Hand has exactly 2 clubs (Q-7 doubleton)
        hand = make_hand('Q7')
        equivalence_set = [Card('Q', '♣'), Card('7', '♣')]

        # Check should_defer - should be FALSE because we need to unblock
        should_defer = tpf._should_defer_to_partner(
            game_state, 'E', equivalence_set, hand
        )

        assert should_defer is False, "Should NOT defer with Q-x doubleton - need to unblock!"

        # Verify unblock check directly
        should_unblock = tpf._should_unblock(equivalence_set, hand, '♣')
        assert should_unblock is True, "Should unblock with Q-x doubleton"


class TestDeferenceWithQueenTripleton:
    """Test deference with Q-x-x (3 cards) when partner leads J"""

    def test_defer_queen_tripleton_on_jack(self):
        """Partner leads J, we have Q-7-3. Should defer (play low)."""
        tpf = TacticalPlayFilter()

        # West leads J♣, East has Q-7-3♣ (3 cards)
        # South declares, so East and West are defenders
        contract = MockContract(declarer='S', trump_suit=None)

        current_trick = [
            (Card('J', '♣'), 'W'),  # Partner leads J
        ]

        game_state = MockGameState(current_trick=current_trick, contract=contract)

        # Hand has 3 clubs (Q-7-3 tripleton)
        hand = make_hand('Q73')
        equivalence_set = [Card('Q', '♣'), Card('7', '♣')]

        # Check should_defer - should be TRUE with 3+ cards
        should_defer = tpf._should_defer_to_partner(
            game_state, 'E', equivalence_set, hand
        )

        assert should_defer is True, "Should defer with Q-x-x (3+ cards)"

        # If we actually selected, we'd play low
        if should_defer:
            result = tpf._select_defensive_deference(equivalence_set, game_state)
            assert result.card.rank == '7', f"Should play 7, not {result.card.rank}"


class TestNoDecisionWhenCantOvertake:
    """Test that no deference decision when we can't overtake anyway"""

    def test_no_defer_when_cant_beat_partner(self):
        """Partner leads K, we have Q-7-3. Q < K so no overtake possible."""
        tpf = TacticalPlayFilter()

        # West leads K♣, East has Q-7-3♣
        # Q(12) < K(13), so we can't overtake - not a deference scenario
        # South declares, so East and West are defenders
        contract = MockContract(declarer='S', trump_suit=None)

        current_trick = [
            (Card('K', '♣'), 'W'),  # Partner leads K
        ]

        game_state = MockGameState(current_trick=current_trick, contract=contract)

        hand = make_hand('Q73')
        equivalence_set = [Card('Q', '♣'), Card('7', '♣')]

        # Check should_defer - should be FALSE because Q < K
        should_defer = tpf._should_defer_to_partner(
            game_state, 'E', equivalence_set, hand
        )

        # When we can't overtake, deference doesn't apply
        # (the logic returns False because can_overtake = False)
        assert should_defer is False, "No deference decision when Q < K (can't overtake)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
