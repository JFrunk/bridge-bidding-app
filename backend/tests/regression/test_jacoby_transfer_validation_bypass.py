"""
Regression test for Jacoby Transfer validation bypass bug.

Bug: Jacoby Transfer initiation (2♦ for hearts, 2♥ for spades) was being rejected
by the SuitLengthValidator because it checked the bid suit instead of recognizing
the artificial nature of the transfer.

Example: With 5 spades and 1 heart, bidding 2♥ (transfer to spades) was rejected
because the validator saw only 1 heart card.

Fix: Added bypass_suit_length metadata to Jacoby Transfer initiation bids.

Date: 2025-11-26
Related: User report about 1NT response evaluation marking Pass as correct
"""

import pytest
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


class TestJacobyTransferValidationBypass:
    """Test that Jacoby Transfer bids bypass suit length validation."""

    def test_transfer_to_spades_with_short_hearts(self):
        """
        With 5 spades and 1 heart, AI should bid 2♥ (transfer to spades).
        This tests the bypass_suit_length metadata is working.
        """
        # South's hand: ♠JT985 ♥4 ♦KJ42 ♣A63 (9 HCP, 5 spades, 1 heart)
        south_cards = [
            Card('J', '♠'), Card('T', '♠'), Card('9', '♠'), Card('8', '♠'), Card('5', '♠'),
            Card('4', '♥'),
            Card('K', '♦'), Card('J', '♦'), Card('4', '♦'), Card('2', '♦'),
            Card('A', '♣'), Card('6', '♣'), Card('3', '♣')
        ]
        south_hand = Hand(south_cards)
        
        # Auction: 1NT - Pass - ?
        auction = ['1NT', 'Pass']
        
        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None', 'detailed')
        
        # Should bid 2♥ (Jacoby Transfer to spades), NOT Pass
        assert bid == '2♥', f"Expected 2♥ (Jacoby Transfer to spades), got {bid}"
        assert 'Transfer' in explanation or 'transfer' in explanation.lower(), \
            f"Expected transfer explanation, got: {explanation}"

    def test_transfer_to_hearts_with_short_diamonds(self):
        """
        With 5 hearts and 2 diamonds, AI should bid 2♦ (transfer to hearts).
        """
        # South's hand: ♠K32 ♥QJ985 ♦A4 ♣753 (10 HCP, 5 hearts, 2 diamonds)
        south_cards = [
            Card('K', '♠'), Card('3', '♠'), Card('2', '♠'),
            Card('Q', '♥'), Card('J', '♥'), Card('9', '♥'), Card('8', '♥'), Card('5', '♥'),
            Card('A', '♦'), Card('4', '♦'),
            Card('7', '♣'), Card('5', '♣'), Card('3', '♣')
        ]
        south_hand = Hand(south_cards)
        
        # Auction: 1NT - Pass - ?
        auction = ['1NT', 'Pass']
        
        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None', 'detailed')
        
        # Should bid 2♦ (Jacoby Transfer to hearts), NOT Pass
        assert bid == '2♦', f"Expected 2♦ (Jacoby Transfer to hearts), got {bid}"
        assert 'Transfer' in explanation or 'transfer' in explanation.lower(), \
            f"Expected transfer explanation, got: {explanation}"


class TestStaymanValidationBypass:
    """Test that Stayman bid bypasses suit length validation."""

    def test_stayman_with_short_clubs(self):
        """
        With 4-4 in majors and 2 clubs, AI should bid 2♣ (Stayman).
        The 2♣ is artificial and doesn't promise clubs.
        """
        # South's hand: ♠KQ84 ♥AJ73 ♦952 ♣T6 (11 HCP, 4-4 majors, 2 clubs)
        south_cards = [
            Card('K', '♠'), Card('Q', '♠'), Card('8', '♠'), Card('4', '♠'),
            Card('A', '♥'), Card('J', '♥'), Card('7', '♥'), Card('3', '♥'),
            Card('9', '♦'), Card('5', '♦'), Card('2', '♦'),
            Card('T', '♣'), Card('6', '♣')
        ]
        south_hand = Hand(south_cards)
        
        # Auction: 1NT - Pass - ?
        auction = ['1NT', 'Pass']
        
        engine = BiddingEngine()
        bid, explanation = engine.get_next_bid(south_hand, auction, 'South', 'None', 'detailed')
        
        # Should bid 2♣ (Stayman), NOT Pass
        assert bid == '2♣', f"Expected 2♣ (Stayman), got {bid}"
        assert 'Stayman' in explanation, f"Expected Stayman explanation, got: {explanation}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
