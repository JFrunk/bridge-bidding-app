"""
Regression test for player rotation bug discovered 2025-10-29

BUG: Frontend useEffect captured stale nextPlayerIndex state, causing
same player (North) to bid 4 times consecutively instead of rotating
through East -> South -> West

ROOT CAUSE: useEffect deps on [auction, nextPlayerIndex], but useEffect
runs immediately after setAuction() before nextPlayerIndex state updates,
so it captures OLD nextPlayerIndex value and sends wrong current_player

EXPECTED: Dealer opens, then rotation advances through all 4 players
ACTUAL: North bid 1NT four times because frontend kept sending current_player='North'

Reference: backend/review_requests/hand_2025-10-29_13-49-57.json

FIX: Frontend should calculate current_player from auction.length and dealer,
not rely on nextPlayerIndex state variable which can be stale
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from engine.bidding_engine import BiddingEngine
from engine.hand import Hand, Card


def calculate_current_player_from_auction(dealer: str, auction_length: int) -> str:
    """
    Helper function that mimics correct player rotation calculation
    This is what the frontend SHOULD use instead of relying on stale state
    """
    players = ['North', 'East', 'South', 'West']
    dealer_index = players.index(dealer)
    current_index = (dealer_index + auction_length) % 4
    return players[current_index]


def test_player_rotation_advances_correctly():
    """
    Test that simulates the correct way to determine current player:
    Calculate from auction length + dealer, NOT from stale state variable
    """

    # Create hands from the bug report
    north_cards = [
        Card('A', '♠'), Card('7', '♠'), Card('5', '♠'),
        Card('A', '♥'), Card('Q', '♥'), Card('6', '♥'), Card('5', '♥'),
        Card('3', '♦'), Card('2', '♦'),
        Card('A', '♣'), Card('K', '♣'), Card('7', '♣'), Card('3', '♣')
    ]

    east_cards = [
        Card('Q', '♠'), Card('9', '♠'), Card('6', '♠'), Card('3', '♠'),
        Card('7', '♥'), Card('2', '♥'),
        Card('T', '♦'), Card('5', '♦'), Card('4', '♦'),
        Card('J', '♣'), Card('T', '♣'), Card('5', '♣'), Card('4', '♣')
    ]

    south_cards = [
        Card('K', '♠'), Card('J', '♠'), Card('4', '♠'),
        Card('J', '♥'), Card('9', '♥'), Card('4', '♥'),
        Card('A', '♦'), Card('K', '♦'), Card('7', '♦'),
        Card('Q', '♣'), Card('8', '♣'), Card('6', '♣'), Card('2', '♣')
    ]

    west_cards = [
        Card('T', '♠'), Card('8', '♠'), Card('2', '♠'),
        Card('K', '♥'), Card('T', '♥'), Card('8', '♥'), Card('3', '♥'),
        Card('Q', '♦'), Card('J', '♦'), Card('9', '♦'), Card('8', '♦'), Card('6', '♦'),
        Card('9', '♣')
    ]

    hands = {
        'North': Hand(north_cards),
        'East': Hand(east_cards),
        'South': Hand(south_cards),
        'West': Hand(west_cards)
    }

    engine = BiddingEngine()

    # Start auction with North as dealer
    auction_history = []  # Just bid strings for backend API
    auction_full = []  # Full entries with player info
    dealer = 'North'
    vulnerability = 'None'

    # Bid 1: North opens
    current_player = calculate_current_player_from_auction(dealer, len(auction_history))
    assert current_player == 'North', f"First player should be dealer (North), got {current_player}"

    bid1, explanation1 = engine.get_next_bid(
        hands[current_player], auction_history, current_player, vulnerability
    )
    auction_history.append(bid1)
    auction_full.append({'bid': bid1, 'explanation': explanation1, 'player': current_player})

    assert bid1 == '1NT', f"North should open 1NT with 17 HCP balanced, got {bid1}"
    assert auction_full[0]['player'] == 'North', "First bid should be by North (dealer)"

    # Bid 2: East responds - THIS IS WHERE BUG OCCURRED (frontend sent 'North' again)
    current_player = calculate_current_player_from_auction(dealer, len(auction_history))
    assert current_player == 'East', f"Second player should be East, got {current_player}"

    bid2, explanation2 = engine.get_next_bid(
        hands[current_player], auction_history, current_player, vulnerability
    )
    auction_history.append(bid2)
    auction_full.append({'bid': bid2, 'explanation': explanation2, 'player': current_player})

    # CRITICAL: Second bid must be by East, not North again
    assert auction_full[1]['player'] == 'East', "Second bid must be by East, not North"
    assert bid2 == 'Pass', f"East should pass with 3 HCP, got {bid2}"

    # Bid 3: South responds
    current_player = calculate_current_player_from_auction(dealer, len(auction_history))
    assert current_player == 'South', f"Third player should be South, got {current_player}"

    bid3, explanation3 = engine.get_next_bid(
        hands[current_player], auction_history, current_player, vulnerability
    )
    auction_history.append(bid3)
    auction_full.append({'bid': bid3, 'explanation': explanation3, 'player': current_player})

    # CRITICAL: Third bid must be by South
    assert auction_full[2]['player'] == 'South', "Third bid must be by South"
    # South has 14 HCP opposite 1NT - should respond (not pass)
    assert bid3 != 'Pass', f"South should respond with 14 HCP opposite 1NT, got {bid3}"

    # Bid 4: West responds
    current_player = calculate_current_player_from_auction(dealer, len(auction_history))
    assert current_player == 'West', f"Fourth player should be West, got {current_player}"

    bid4, explanation4 = engine.get_next_bid(
        hands[current_player], auction_history, current_player, vulnerability
    )
    auction_history.append(bid4)
    auction_full.append({'bid': bid4, 'explanation': explanation4, 'player': current_player})

    # CRITICAL: Fourth bid must be by West
    assert auction_full[3]['player'] == 'West', "Fourth bid must be by West"

    # Verify no player bid twice in a row
    for i in range(1, len(auction_full)):
        assert auction_full[i]['player'] != auction_full[i-1]['player'], \
            f"Players should alternate, but {auction_full[i]['player']} bid twice in a row"

    # Verify proper rotation order
    expected_order = ['North', 'East', 'South', 'West']
    actual_order = [bid_entry['player'] for bid_entry in auction_full[:4]]
    assert actual_order == expected_order, \
        f"Expected rotation {expected_order}, got {actual_order}"

    print(f"✅ Player rotation test passed - all 4 players bid in correct order")


def test_player_calculation_function():
    """Test that the player calculation function works correctly for all dealers"""

    test_cases = [
        ('North', 0, 'North'),  # Dealer bids first
        ('North', 1, 'East'),   # Next player after dealer
        ('North', 2, 'South'),
        ('North', 3, 'West'),
        ('North', 4, 'North'),  # Wraps around
        ('East', 0, 'East'),    # East dealer
        ('East', 1, 'South'),
        ('East', 2, 'West'),
        ('East', 3, 'North'),
        ('South', 0, 'South'),  # South dealer
        ('South', 1, 'West'),
        ('South', 2, 'North'),
        ('West', 0, 'West'),    # West dealer
        ('West', 1, 'North'),
        ('West', 2, 'East'),
    ]

    for dealer, auction_length, expected_player in test_cases:
        actual_player = calculate_current_player_from_auction(dealer, auction_length)
        assert actual_player == expected_player, \
            f"Dealer={dealer}, auction_length={auction_length}: " \
            f"expected {expected_player}, got {actual_player}"

    print(f"✅ Player calculation function test passed - all {len(test_cases)} cases correct")


if __name__ == '__main__':
    # Run with verbose output
    pytest.main([__file__, '-v'])
