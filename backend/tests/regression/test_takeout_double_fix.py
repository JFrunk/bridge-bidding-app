"""
Test to verify the takeout double fix.
Ensures we don't double a suit where we have 4+ cards.

Scenario from hand_2025-10-11_14-28-29.json:
- Auction: Pass - Pass - 1♦ - Pass - 1♥ - ?
- East has: ♠KQ97 ♥AT42 ♦QJ ♣832 (12 HCP, 4 hearts)
- East should NOT make a takeout double of 1♥ because they have 4 hearts
"""

from engine.hand import Hand, Card
from engine.ai.conventions.takeout_doubles import TakeoutDoubleConvention

def test_no_takeout_double_with_four_card_holding():
    """
    East should NOT double 1♥ when holding 4 hearts.
    """
    # Create East's hand from the problematic game
    east_hand = Hand([
        Card('K', '♠'),
        Card('Q', '♠'),
        Card('9', '♠'),
        Card('7', '♠'),
        Card('A', '♥'),
        Card('T', '♥'),
        Card('4', '♥'),
        Card('2', '♥'),
        Card('Q', '♦'),
        Card('J', '♦'),
        Card('8', '♣'),
        Card('3', '♣'),
        Card('2', '♣'),
    ])

    # Simulate the auction: Pass - Pass - 1♦ - Pass - 1♥ - ?
    # East is in position to bid after North's 1♥ response
    # Positions cycle: N(0), E(1), S(2), W(3), N(0), E(1)...
    features = {
        'auction_history': ['Pass', 'Pass', '1♦', 'Pass', '1♥'],
        'positions': ['N', 'E', 'S', 'W', 'N'],  # N passed, E passed, S opened 1♦, W passed, N bid 1♥
        'my_index': 1,  # East is at index 1 in the position cycle
        'hand': east_hand,
        'auction_features': {
            'opener': 'S',
            'opening_bid': '1♦',
            'opener_relationship': 'Opponent',
            'partner_last_bid': 'Pass',
        }
    }

    # Test the takeout double convention
    takeout_double = TakeoutDoubleConvention()

    print("Testing East's hand after 1♦ - Pass - 1♥:")
    print(f"  Spades: {east_hand.suit_lengths['♠']} cards")
    print(f"  Hearts: {east_hand.suit_lengths['♥']} cards")
    print(f"  Diamonds: {east_hand.suit_lengths['♦']} cards")
    print(f"  Clubs: {east_hand.suit_lengths['♣']} cards")
    print(f"  HCP: {east_hand.hcp}")
    print()

    result = takeout_double.evaluate(east_hand, features)

    if result is None:
        print("✅ CORRECT: Takeout double convention returns None (no double)")
        print("   Reason: East has 4 hearts, cannot double a suit with 4-card holding")
        return True
    else:
        print("❌ INCORRECT: Takeout double convention returned:", result)
        print("   East should NOT double with 4 hearts!")
        return False


def test_valid_takeout_double():
    """
    Test a valid takeout double scenario where we have proper shape.
    After 1♥ opening, double with: ♠KQJ9 ♥2 ♦AJ87 ♣K943 (13 HCP, singleton heart)
    """
    hand = Hand([
        Card('K', '♠'),
        Card('Q', '♠'),
        Card('J', '♠'),
        Card('9', '♠'),
        Card('2', '♥'),
        Card('A', '♦'),
        Card('J', '♦'),
        Card('8', '♦'),
        Card('7', '♦'),
        Card('K', '♣'),
        Card('9', '♣'),
        Card('4', '♣'),
        Card('3', '♣'),
    ])

    features = {
        'auction_history': ['1♥'],
        'positions': ['E', 'S'],
        'my_index': 1,  # South's turn
        'hand': hand,
        'auction_features': {
            'opener': 'E',
            'opening_bid': '1♥',
            'opener_relationship': 'Opponent',
            'partner_last_bid': None,
        }
    }

    takeout_double = TakeoutDoubleConvention()

    print("\nTesting valid takeout double after 1♥:")
    print(f"  Spades: {hand.suit_lengths['♠']} cards")
    print(f"  Hearts: {hand.suit_lengths['♥']} cards (singleton)")
    print(f"  Diamonds: {hand.suit_lengths['♦']} cards")
    print(f"  Clubs: {hand.suit_lengths['♣']} cards")
    print(f"  HCP: {hand.hcp}")
    print()

    result = takeout_double.evaluate(hand, features)

    if result and result[0] == 'X':
        print("✅ CORRECT: Takeout double suggested with proper shape (singleton in opponent's suit)")
        return True
    else:
        print("❌ INCORRECT: Should suggest takeout double with this hand")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("TAKEOUT DOUBLE FIX VERIFICATION")
    print("=" * 70)
    print()

    test1_passed = test_no_takeout_double_with_four_card_holding()
    test2_passed = test_valid_takeout_double()

    print()
    print("=" * 70)
    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)
