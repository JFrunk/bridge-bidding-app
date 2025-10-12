"""
Test helpers for standalone card play testing

This module provides utilities for creating test hands and play scenarios
without requiring the bidding phase, making tests faster and more focused.
"""

from engine.hand import Hand, Card
from engine.play_engine import Contract, PlayState, PlayEngine
from engine.contract_utils import parse_contract, parse_vulnerability
from typing import Dict, List, Optional
import re


def create_hand_from_string(hand_str: str) -> Hand:
    """
    Create a Hand object from a readable string representation

    Format: "♠AKQ32 ♥J54 ♦KQ3 ♣A2"
    - Suits separated by spaces
    - Each suit starts with suit symbol (♠, ♥, ♦, ♣)
    - Cards within suit are rank characters (A, K, Q, J, T, 9-2)
    - Order doesn't matter (will be sorted by Hand class)

    Args:
        hand_str: String representation of hand

    Returns:
        Hand object with 13 cards

    Raises:
        ValueError: If hand doesn't have exactly 13 cards

    Examples:
        >>> hand = create_hand_from_string("♠AKQ ♥432 ♦765 ♣8765")
        >>> len(hand.cards)
        13

        >>> hand = create_hand_from_string("♠AKQJT98765432")  # 13 spades
        >>> hand.suit_lengths['♠']
        13
    """
    cards = []

    # Split by suit symbols
    suit_groups = re.split(r'([♠♥♦♣])', hand_str.strip())

    current_suit = None
    for part in suit_groups:
        part = part.strip()
        if not part:
            continue

        if part in ['♠', '♥', '♦', '♣']:
            current_suit = part
        elif current_suit:
            # Parse ranks for this suit
            for rank_char in part:
                if rank_char.upper() in 'AKQJT98765432':
                    cards.append(Card(rank=rank_char.upper(), suit=current_suit))

    if len(cards) != 13:
        raise ValueError(
            f"Hand must have exactly 13 cards, got {len(cards)}. "
            f"Hand string: '{hand_str}'"
        )

    return Hand(cards)


def create_test_deal(north: str = None, east: str = None,
                     south: str = None, west: str = None) -> Dict[str, Hand]:
    """
    Create a complete deal (4 hands) from string representations

    Args:
        north: North's hand string (optional)
        east: East's hand string (optional)
        south: South's hand string (optional)
        west: West's hand string (optional)

    Returns:
        Dictionary mapping positions to Hand objects

    Example:
        >>> deal = create_test_deal(
        ...     north="♠AKQ ♥432 ♦KQJ ♣432",
        ...     south="♠432 ♥AKQ ♦432 ♣AKQ"
        ... )
        >>> 'N' in deal and 'S' in deal
        True
    """
    deal = {}

    if north:
        deal['N'] = create_hand_from_string(north)
    if east:
        deal['E'] = create_hand_from_string(east)
    if south:
        deal['S'] = create_hand_from_string(south)
    if west:
        deal['W'] = create_hand_from_string(west)

    return deal


def create_balanced_hand(hcp: int, position: str = 'N') -> Hand:
    """
    Create a balanced hand with approximately the specified HCP

    This is useful for testing NT contracts.

    Args:
        hcp: Target high card points (approximate)
        position: Position letter (for variety in generation)

    Returns:
        Hand object with balanced distribution
    """
    # Predefined balanced hands at different HCP levels
    balanced_hands = {
        12: "♠AJ3 ♥KQ4 ♦Q95 ♣8742",
        13: "♠AJ3 ♥KQ4 ♦K95 ♣8742",
        14: "♠AJ3 ♥KQ4 ♦K95 ♣A742",
        15: "♠AQJ ♥KQ4 ♦K95 ♣A742",
        16: "♠AQJ ♥KQ4 ♦KJ5 ♣A742",
        17: "♠AQJ ♥KQJ ♦KJ5 ♣A742",
        18: "♠AKJ ♥KQJ ♦KJ5 ♣A742",
        19: "♠AKJ ♥KQJ ♦KQ5 ♣A742",
        20: "♠AKQ ♥KQJ ♦KQ5 ♣A742",
    }

    # Find closest HCP
    closest_hcp = min(balanced_hands.keys(), key=lambda x: abs(x - hcp))
    hand_str = balanced_hands[closest_hcp]

    return create_hand_from_string(hand_str)


def create_play_scenario(contract_str: str,
                         hands: Dict[str, Hand],
                         vulnerability: str = "None") -> PlayState:
    """
    Create a complete play scenario ready for testing

    This is the main entry point for creating standalone play tests.

    Args:
        contract_str: Contract string (e.g., "3NT by S")
        hands: Dictionary of hands for all 4 positions
        vulnerability: Vulnerability string ("None", "NS", "EW", "Both")

    Returns:
        PlayState ready to begin play

    Example:
        >>> deal = create_test_deal(
        ...     north="♠AKQ ♥432 ♦KQJ ♣432",
        ...     east="♠432 ♥765 ♦432 ♣765",
        ...     south="♠765 ♥AKQ ♦765 ♣AKQ",
        ...     west="♠JT98 ♥JT98 ♦JT98 ♣JT"
        ... )
        >>> state = create_play_scenario("3NT by S", deal)
        >>> state.contract.level
        3
        >>> state.next_to_play  # LHO of South is West
        'W'
    """
    contract = parse_contract(contract_str)
    vuln_dict = parse_vulnerability(vulnerability)

    return PlayEngine.create_play_session(contract, hands, vuln_dict)


def assert_play_result(play_state: PlayState,
                       expected_declarer_tricks: int,
                       expected_made: bool,
                       vulnerability: str = "None") -> None:
    """
    Assert that play result matches expectations

    Args:
        play_state: Completed PlayState
        expected_declarer_tricks: Expected tricks taken by declarer's side
        expected_made: Whether contract should be made
        vulnerability: Vulnerability for score calculation

    Raises:
        AssertionError: If expectations don't match

    Example:
        >>> # After playing out 13 tricks
        >>> assert_play_result(play_state, expected_declarer_tricks=9, expected_made=True)
    """
    assert play_state.is_complete, "Play is not complete (13 tricks not played)"

    contract = play_state.contract
    declarer = contract.declarer

    # Get tricks for declarer's side
    if declarer in ['N', 'S']:
        declarer_tricks = play_state.tricks_taken_ns
    else:
        declarer_tricks = play_state.tricks_taken_ew

    assert declarer_tricks == expected_declarer_tricks, (
        f"Expected {expected_declarer_tricks} tricks for declarer's side, "
        f"got {declarer_tricks}"
    )

    # Check if contract made
    tricks_needed = contract.tricks_needed
    made = declarer_tricks >= tricks_needed

    assert made == expected_made, (
        f"Expected contract to be {'made' if expected_made else 'defeated'}, "
        f"but it was {'made' if made else 'defeated'} "
        f"(took {declarer_tricks} tricks, needed {tricks_needed})"
    )


def print_hand_diagram(hands: Dict[str, Hand], contract: Optional[Contract] = None) -> None:
    """
    Print a visual diagram of all four hands (useful for debugging tests)

    Args:
        hands: Dictionary of hands
        contract: Optional contract to display

    Example output:
                    North
                 ♠ A K Q 3
                 ♥ 5 4
                 ♦ K J 3
                 ♣ 8 7 6

        West                    East
       ♠ J T 9                ♠ 5 4 2
       ♥ J T 9                ♥ 7 6
       ♦ T 9 8                ♦ 7 6 5 4
       ♣ J T 9                ♣ 5 4 3 2

                    South
                 ♠ 8 7 6
                 ♥ A K Q 8 3 2
                 ♦ A Q 2
                 ♣ A K Q
    """
    if contract:
        print(f"\nContract: {contract}")
    print()

    def format_suit_line(hand: Hand, suit: str) -> str:
        """Format one suit line from a hand"""
        cards = [c for c in hand.cards if c.suit == suit]
        if not cards:
            return f"{suit} —"
        ranks = ' '.join(c.rank for c in sorted(cards,
                                                 key=lambda c: PlayEngine.RANK_VALUES[c.rank],
                                                 reverse=True))
        return f"{suit} {ranks}"

    def format_hand(hand: Hand, indent: int = 0) -> List[str]:
        """Format all four suits from a hand"""
        indent_str = ' ' * indent
        return [
            indent_str + format_suit_line(hand, '♠'),
            indent_str + format_suit_line(hand, '♥'),
            indent_str + format_suit_line(hand, '♦'),
            indent_str + format_suit_line(hand, '♣')
        ]

    # North
    if 'N' in hands:
        print("            North")
        for line in format_hand(hands['N'], indent=12):
            print(line)
        print()

    # West and East side by side
    if 'W' in hands and 'E' in hands:
        west_lines = format_hand(hands['W'])
        east_lines = format_hand(hands['E'])

        print("   West                    East")
        for w_line, e_line in zip(west_lines, east_lines):
            print(f"  {w_line:20} {e_line}")
        print()

    # South
    if 'S' in hands:
        print("            South")
        for line in format_hand(hands['S'], indent=12):
            print(line)
        print()


if __name__ == '__main__':
    # Self-test
    print("Testing hand creation from string...")

    test_hand = create_hand_from_string("♠AKQ ♥432 ♦765 ♣8765")
    assert len(test_hand.cards) == 13
    assert test_hand.suit_lengths['♠'] == 3
    assert test_hand.suit_lengths['♥'] == 3
    assert test_hand.suit_lengths['♦'] == 3
    assert test_hand.suit_lengths['♣'] == 4
    print("✓ Hand creation works")

    print("\nTesting deal creation...")
    deal = create_test_deal(
        north="♠AKQ2 ♥432 ♦KQJ ♣432",
        south="♠432 ♥AKQ ♦432 ♣AKQ5"
    )
    assert 'N' in deal and 'S' in deal
    assert len(deal['N'].cards) == 13
    print("✓ Deal creation works")

    print("\nTesting play scenario creation...")
    full_deal = create_test_deal(
        north="♠AKQ2 ♥432 ♦KQJ ♣432",  # 4+3+3+3 = 13
        east="♠765 ♥765 ♦765 ♣7654",    # 3+3+3+4 = 13
        south="♠432 ♥AKQ ♦432 ♣AKQ5",  # 3+3+3+4 = 13
        west="♠JT98 ♥JT9 ♦AT9 ♣J87"    # 4+3+3+3 = 13
    )
    play_state = create_play_scenario("3NT by S", full_deal, "NS")
    assert play_state.contract.level == 3
    assert play_state.contract.strain == 'NT'
    assert play_state.contract.declarer == 'S'
    assert play_state.next_to_play == 'W'  # LHO of South
    print("✓ Play scenario creation works")

    print("\nTesting hand diagram...")
    print_hand_diagram(full_deal, play_state.contract)

    print("\n✅ All test helpers working correctly!")
