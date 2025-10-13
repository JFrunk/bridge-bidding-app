"""
Tests for Phase 3 Convention Implementations:
- Michaels Cuebid
- Unusual 2NT
- Splinter Bids
- Fourth Suit Forcing
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.hand import Hand, Card
from engine.ai.conventions.michaels_cuebid import MichaelsCuebidConvention
from engine.ai.conventions.unusual_2nt import Unusual2NTConvention
from engine.ai.conventions.splinter_bids import SplinterBidsConvention
from engine.ai.conventions.fourth_suit_forcing import FourthSuitForcingConvention


def create_hand(spades, hearts, diamonds, clubs):
    """Helper to create hand from string notation like 'AKJ76'"""
    cards = []
    for rank in spades:
        cards.append(Card(rank, '♠'))
    for rank in hearts:
        cards.append(Card(rank, '♥'))
    for rank in diamonds:
        cards.append(Card(rank, '♦'))
    for rank in clubs:
        cards.append(Card(rank, '♣'))
    return Hand(cards)


# ============================================================================
# MICHAELS CUEBID TESTS
# ============================================================================

def test_michaels_over_minor_shows_majors():
    """Test Michaels cuebid over 1♣ showing both majors"""
    hand = create_hand("AKJ76", "QJ854", "32", "4")

    features = {
        'hand': hand,
        'auction_history': ['1♣'],  # Opponent opened, now it's my turn
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 1,  # East position
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Opponent',
            'opening_bid': '1♣',
            'partner_last_bid': None
        }
    }

    convention = MichaelsCuebidConvention()
    result = convention.evaluate(hand, features)

    assert result is not None, "Should make Michaels cuebid with 5-5 majors"
    assert result[0] == "2♣", f"Should bid 2♣ (Michaels), got {result[0]}"
    assert "majors" in result[1].lower(), "Explanation should mention both majors"


def test_michaels_over_1heart_shows_spades_and_minor():
    """Test Michaels cuebid over 1♥ showing spades + minor"""
    hand = create_hand("KQJ87", "4", "AQJ65", "32")

    features = {
        'hand': hand,
        'auction_history': ['1♥'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 1,
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Opponent',
            'opening_bid': '1♥',
            'partner_last_bid': None
        }
    }

    convention = MichaelsCuebidConvention()
    result = convention.evaluate(hand, features)

    assert result is not None, "Should make Michaels cuebid"
    assert result[0] == "2♥", f"Should bid 2♥ (Michaels), got {result[0]}"
    assert "spades" in result[1].lower() and "minor" in result[1].lower()


def test_michaels_response_to_major_suit():
    """Test Michaels cuebid strength requirements"""
    # Test that hand needs 8+ HCP for Michaels
    weak_hand = create_hand("QJ876", "JT954", "32", "4")  # 6 HCP - too weak

    features = {
        'hand': weak_hand,
        'auction_history': ['1♦'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 1,
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Opponent',
            'opening_bid': '1♦',
            'partner_last_bid': None
        }
    }

    convention = MichaelsCuebidConvention()
    result = convention.evaluate(weak_hand, features)

    assert result is None, f"Should not bid Michaels with only {weak_hand.hcp} HCP (need 8+)"


# ============================================================================
# UNUSUAL 2NT TESTS
# ============================================================================

def test_unusual_2nt_over_major():
    """Test Unusual 2NT over 1♠ showing both minors"""
    hand = create_hand("4", "32", "AQJ87", "KJT65")

    features = {
        'hand': hand,
        'auction_history': ['1♠'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 1,
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Opponent',
            'opening_bid': '1♠',
            'partner_last_bid': None
        }
    }

    convention = Unusual2NTConvention()
    result = convention.evaluate(hand, features)

    assert result is not None, "Should bid Unusual 2NT with 5-5 minors"
    assert result[0] == "2NT", f"Should bid 2NT, got {result[0]}"
    assert "minors" in result[1].lower(), "Explanation should mention minors"


def test_unusual_2nt_response():
    """Test Unusual 2NT with too strong hand (12-16 HCP)"""
    # Test that middle-range hands (12-16 HCP) don't use Unusual 2NT
    medium_hand = create_hand("4", "A2", "AQJ87", "KJT65")  # 15 HCP

    features = {
        'hand': medium_hand,
        'auction_history': ['1♥'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 1,
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Opponent',
            'opening_bid': '1♥',
            'partner_last_bid': None
        }
    }

    convention = Unusual2NTConvention()
    result = convention.evaluate(medium_hand, features)

    assert result is None, f"Should not bid Unusual 2NT with {medium_hand.hcp} HCP (need 6-11 or 17+)"


# ============================================================================
# SPLINTER BIDS TESTS
# ============================================================================

def test_splinter_after_major_opening():
    """Test splinter bid showing shortness and support"""
    hand = create_hand("KJ87", "AQ42", "2", "Q865")  # 13 HCP

    features = {
        'hand': hand,
        'auction_history': ['1♠'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 1,  # East (partner North opened)
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Partner',
            'opening_bid': '1♠',
            'partner_last_bid': None
        }
    }

    convention = SplinterBidsConvention()
    result = convention.evaluate(hand, features)

    assert result is not None, "Should make splinter bid with singleton and support"
    assert result[0] == "4♦", f"Should bid 4♦ (splinter), got {result[0]}"
    assert "singleton" in result[1].lower() or "shortness" in result[1].lower()


def test_no_splinter_without_support():
    """Test that splinter requires 4+ card support"""
    hand = create_hand("K87", "AQ42", "2", "KJ654")  # 13 cards: 3+4+1+5

    features = {
        'hand': hand,
        'auction_history': ['1♠'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 1,
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Partner',
            'opening_bid': '1♠',
            'partner_last_bid': None
        }
    }

    convention = SplinterBidsConvention()
    result = convention.evaluate(hand, features)

    assert result is None, "Should not splinter with only 3-card support"


def test_no_splinter_without_shortness():
    """Test that splinter requires singleton or void"""
    hand = create_hand("KJ87", "AQ4", "K32", "KJ6")

    features = {
        'hand': hand,
        'auction_history': ['1♠'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 1,
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Partner',
            'opening_bid': '1♠',
            'partner_last_bid': None
        }
    }

    convention = SplinterBidsConvention()
    result = convention.evaluate(hand, features)

    assert result is None, "Should not splinter without shortness"


# ============================================================================
# FOURTH SUIT FORCING TESTS
# ============================================================================

def test_fourth_suit_forcing_applicable():
    """Test FSF when 3 suits bid and no fit found"""
    hand = create_hand("AT6", "KJ87", "AQ42", "32")  # 3-4-4-2, no 4-card fit with partner's spades

    # Auction: 1♦ (partner) - 1♥ (me) - 1♠ (partner) - ?
    # Three suits bid: ♦, ♥, ♠. Fourth suit is ♣
    features = {
        'hand': hand,
        'auction_history': ['1♦', 'Pass', '1♥', 'Pass', '1♠', 'Pass'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 2,  # South
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Partner',
            'opening_bid': '1♦',
            'partner_last_bid': '1♠'
        }
    }

    convention = FourthSuitForcingConvention()
    result = convention.evaluate(hand, features)

    assert result is not None, "Should use FSF with 12+ HCP and no fit"
    assert result[0] == "2♣", f"Should bid 2♣ (FSF), got {result[0]}"
    assert "forcing" in result[1].lower(), "Should mention forcing"


def test_no_fsf_with_fit():
    """Test that FSF is not used when fit is found"""
    hand = create_hand("AQ65", "KJ87", "AQ42", "3")

    # Has 4-card spade support - should raise instead
    features = {
        'hand': hand,
        'auction_history': ['1♦', 'Pass', '1♥', 'Pass', '1♠', 'Pass'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 2,
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Partner',
            'opening_bid': '1♦',
            'partner_last_bid': '1♠'
        }
    }

    convention = FourthSuitForcingConvention()
    result = convention.evaluate(hand, features)

    assert result is None, "Should not use FSF when 4+ card fit exists"


def test_no_fsf_insufficient_values():
    """Test that FSF requires 12+ HCP"""
    hand = create_hand("AT65", "QJ87", "QT4", "32")  # Only 9 HCP

    features = {
        'hand': hand,
        'auction_history': ['1♦', 'Pass', '1♥', 'Pass', '1♠', 'Pass'],
        'positions': ['North', 'East', 'South', 'West'],
        'my_index': 2,
        'auction_features': {
            'opener': 'North',
            'opener_relationship': 'Partner',
            'opening_bid': '1♦',
            'partner_last_bid': '1♠'
        }
    }

    convention = FourthSuitForcingConvention()
    result = convention.evaluate(hand, features)

    assert result is None, "Should not use FSF with less than 12 HCP"


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("Running Phase 3 Convention Tests...\n")

    # Michaels Cuebid tests
    print("Testing Michaels Cuebid...")
    test_michaels_over_minor_shows_majors()
    print("  ✓ Michaels over minor shows both majors")

    test_michaels_over_1heart_shows_spades_and_minor()
    print("  ✓ Michaels over 1♥ shows spades + minor")

    test_michaels_response_to_major_suit()
    print("  ✓ Michaels strength requirements (8+ HCP)")

    # Unusual 2NT tests
    print("\nTesting Unusual 2NT...")
    test_unusual_2nt_over_major()
    print("  ✓ Unusual 2NT over major shows both minors")

    test_unusual_2nt_response()
    print("  ✓ Unusual 2NT strength requirements (6-11 or 17+)")

    # Splinter Bids tests
    print("\nTesting Splinter Bids...")
    test_splinter_after_major_opening()
    print("  ✓ Splinter shows shortness and support")

    test_no_splinter_without_support()
    print("  ✓ No splinter without 4+ support")

    test_no_splinter_without_shortness()
    print("  ✓ No splinter without shortness")

    # Fourth Suit Forcing tests
    print("\nTesting Fourth Suit Forcing...")
    test_fourth_suit_forcing_applicable()
    print("  ✓ FSF with 3 suits bid and 12+ HCP")

    test_no_fsf_with_fit()
    print("  ✓ No FSF when fit found")

    test_no_fsf_insufficient_values()
    print("  ✓ No FSF with less than 12 HCP")

    print("\n" + "="*50)
    print("All Phase 3 Convention Tests PASSED! ✅")
    print("="*50)
