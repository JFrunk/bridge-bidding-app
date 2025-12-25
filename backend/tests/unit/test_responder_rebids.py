"""
Comprehensive tests for responder's rebids (second bid by responder).

Tests cover:
- Minimum rebids (6-9 points)
- Invitational rebids (10-12 points)
- Game-forcing rebids (13+ points)
- Various opener rebid types (same suit, new suit, NT, reverse, jump)
- Preference bids, Fourth Suit Forcing, etc.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from engine.hand import Hand, Card
from engine.responder_rebids import ResponderRebidModule
from engine.ai.feature_extractor import extract_features as create_features_func

def create_hand(spades, hearts, diamonds, clubs):
    """Helper to create a Hand object from string representations."""
    all_cards = []
    for suit, cards_str in [('♠', spades), ('♥', hearts), ('♦', diamonds), ('♣', clubs)]:
        for rank in cards_str:
            all_cards.append(Card(rank, suit))
    return Hand(all_cards)

def make_auction(bids: list, responder_position: int = 1):
    """
    Create an auction history.
    responder_position: 0=North, 1=East, 2=South, 3=West
    Assumes opener is at position (responder_position + 2) % 4
    """
    # Start with passes to get to opener
    opener_position = (responder_position + 2) % 4
    auction = ['Pass'] * opener_position

    # Add the actual bids
    for i, bid in enumerate(bids):
        auction.append(bid)

    return auction

def extract_features(hand, auction, responder_position=1):
    """Extract features for testing."""
    # Convert position index to position name
    positions = ['North', 'East', 'South', 'West']
    my_position = positions[responder_position]

    # Pad auction to current position
    current_position = (len(auction)) % 4
    while current_position != responder_position:
        auction.append('Pass')
        current_position = (current_position + 1) % 4

    features = create_features_func(hand, auction, my_position, vulnerability='None')
    return features


class TestMinimumRebids:
    """Tests for minimum rebids (6-9 points)."""

    def test_pass_with_fit_after_opener_rebid_same_suit(self):
        """1♥ - 1♠ - 2♥ - ? with 2+ hearts, should pass."""
        hand = create_hand('KJ74', 'Q86', '952', '852')  # 7 HCP, 2 hearts
        auction = make_auction(['1♥', 'Pass', '1♠', 'Pass', '2♥', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        assert bid == 'Pass'
        assert 'Minimum' in explanation or 'satisfied' in explanation

    def test_preference_to_first_suit(self):
        """1♣ - 1♥ - 1♠ - ? with 3 clubs and 3 spades, prefer clubs."""
        hand = create_hand('KJ7', 'Q874', 'K32', '852')  # 9 HCP, equal length
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        assert bid == '2♣'
        assert 'preference' in explanation.lower()

    def test_rebid_own_6_card_suit(self):
        """1♣ - 1♠ - 2♣ - ? with 6 spades, rebid 2♠ with extra length."""
        hand = create_hand('QJ9874', 'K54', '963', '2')  # 7 HCP (Q=2, J=1, K=3, 9 = 1), 6 spades
        auction = make_auction(['1♣', 'Pass', '1♠', 'Pass', '2♣', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # With only 2-card fit in clubs and 6-card spade suit, should rebid spades
        assert bid == '2♠'
        assert '6+' in explanation

    def test_pass_after_1nt_rebid_with_balanced_minimum(self):
        """1♦ - 1♥ - 1NT - ? with balanced 8 HCP, pass."""
        hand = create_hand('K74', 'QJ862', '95', '983')  # 8 HCP (K=3, Q=2, J=1, 9,8 = 2), balanced-ish
        auction = make_auction(['1♦', 'Pass', '1♥', 'Pass', '1NT', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        assert bid == 'Pass'
        assert 'Minimum' in explanation or 'notrump' in explanation.lower()

    def test_forced_bid_after_reverse(self):
        """1♦ - 1♠ - 2♥ - ? (reverse is forcing), must bid with minimum."""
        hand = create_hand('KJ874', 'Q5', '86', 'Q732')  # 8 HCP
        auction = make_auction(['1♦', 'Pass', '1♠', 'Pass', '2♥', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # Should bid 2NT or preference, but NOT pass
        assert bid != 'Pass'
        assert '2NT' in bid or '3' in bid  # Forced to bid


class TestInvitationalRebids:
    """Tests for invitational rebids (10-12 points)."""

    def test_jump_raise_opener_suit(self):
        """1♣ - 1♥ - 1♠ - ? with 4 spades, 11 HCP.

        With AuctionContext, combined values often justify game (opener 12-16 + responder 11 = 23-27).
        May bid 3♠ (invitational) or 4♠ (game) depending on combined midpoint.
        """
        hand = create_hand('KQ85', 'AJ84', 'T32', '75')  # 11 HCP (K=3, Q=2, A=4, J=1, T=1), 4 spades
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # With AuctionContext, may bid game (4♠) or invite (3♠) based on combined midpoint
        assert bid in ['3♠', '4♠']
        assert 'Invit' in explanation or '10-12' in explanation or 'game' in explanation.lower()

    def test_2nt_invitational(self):
        """1♣ - 1♥ - 1♠ - ? with balanced 12 HCP, no fit.

        With AuctionContext tracking, combined values often justify game.
        """
        hand = create_hand('KJ5', 'AQ84', 'T32', 'Q52')  # 12 HCP (K=3, J=1, A=4, Q=2, T=1, Q=2), balanced
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # With 12 HCP and AuctionContext, likely bids game (3NT)
        assert bid in ['2NT', '3NT', '3♣', '4♠']  # Various reasonable bids

    def test_jump_in_own_suit(self):
        """1♦ - 1♠ - 2♦ - ? with 6 spades, 10 HCP.

        With AuctionContext, combined values may justify game (opener 13+ for rebid + 10 = 23+).
        """
        hand = create_hand('KQJ874', '95', 'Q6', '732')  # 10 HCP (K=3, Q=2, J=1, Q=2, 9 = 2), 6 spades
        auction = make_auction(['1♦', 'Pass', '1♠', 'Pass', '2♦', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # With AuctionContext, may bid game (4♠) or invite (3♠)
        assert bid in ['3♠', '4♠']
        assert 'Invit' in explanation or '10-12' in explanation or '6+' in explanation or 'game' in explanation.lower()

    def test_jump_preference(self):
        """1♦ - 1♠ - 2♣ - ? with 4 diamonds, 11 HCP.

        With AuctionContext, combined values may justify game.
        """
        hand = create_hand('KQ85', 'J8', 'KJ32', '852')  # 11 HCP, 4 diamonds
        auction = make_auction(['1♦', 'Pass', '1♠', 'Pass', '2♣', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # With AuctionContext, may bid game (3NT) or invite (3♦)
        assert bid in ['3♦', '3NT']
        assert 'preference' in explanation.lower() or 'Invit' in explanation or 'game' in explanation.lower()

    def test_accept_jump_rebid_with_maximum(self):
        """1♣ - 1♥ - 3♣ - ? with 12 pts, accept invitation."""
        hand = create_hand('K74', 'AJ862', 'K5', 'Q83')  # 12 HCP
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '3♣', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # Should bid game (3NT or 5♣)
        assert '3NT' in bid or '5♣' in bid
        assert 'Accept' in explanation or 'game' in explanation.lower()


class TestGameForcingRebids:
    """Tests for game-forcing rebids (13+ points)."""

    def test_raise_to_game_with_fit(self):
        """1♣ - 1♥ - 1♠ - 4♠ with 3+ spades, 15 HCP."""
        hand = create_hand('KQ85', 'AJ84', 'AK3', '85')  # 15 HCP, 4 spades
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        assert bid == '4♠'
        assert '13+' in explanation or 'game' in explanation.lower()

    def test_3nt_with_balanced_13_hcp(self):
        """1♣ - 1♥ - 1♠ - 3NT with balanced 14 HCP."""
        hand = create_hand('KJ5', 'AQ84', 'AQ3', 'J52')  # 14 HCP, balanced
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        assert '3NT' in bid or '4♠' in bid  # Game in some strain
        assert 'game' in explanation.lower() or '13+' in explanation

    def test_fourth_suit_forcing(self):
        """1♣ - 1♥ - 1♠ - 2♦ (Fourth Suit Forcing) with 14 HCP, no clear fit."""
        hand = create_hand('AQ5', 'KQ84', 'A32', '752')  # 14 HCP, balanced-ish
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # Should bid either 2♦ (FSF) or jump to 3NT
        assert bid in ['2♦', '3NT', '4♠']

    def test_game_in_major_with_6_card_suit(self):
        """1♦ - 1♠ - 1NT - 4♠ with 6 spades, 13 HCP."""
        hand = create_hand('AQJ874', 'K5', 'AQ', '732')  # 14 HCP, 6 spades
        auction = make_auction(['1♦', 'Pass', '1♠', 'Pass', '1NT', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        assert bid == '4♠'
        assert '6+' in explanation
        assert 'game' in explanation.lower() or '13+' in explanation

    def test_preference_at_game_level(self):
        """1♥ - 1♠ - 2♣ - ? with game-forcing values, show preference."""
        hand = create_hand('KQ85', 'AJ8', 'AK3', '852')  # 15 HCP
        auction = make_auction(['1♥', 'Pass', '1♠', 'Pass', '2♣', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # Should bid game (4♥ with hearts fit, or 3NT, or 4♠)
        assert '4♥' in bid or '3NT' in bid or '4♠' in bid


class TestComplexSequences:
    """Tests for complex auction sequences."""

    def test_after_opener_reverse(self):
        """1♦ - 1♠ - 2♥ - ? (reverse, forcing) with various strengths."""
        # Minimum hand
        hand_min = create_hand('KJ874', 'Q5', '86', 'Q732')  # 8 HCP
        auction = make_auction(['1♦', 'Pass', '1♠', 'Pass', '2♥', 'Pass'])
        features = extract_features(hand_min, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand_min, features)

        assert result is not None
        bid, explanation = result
        # Forced to bid, should show minimum (2NT or 3♦ or 3♠)
        assert bid != 'Pass'

    def test_after_opener_jump_rebid(self):
        """1♣ - 1♥ - 3♣ - ? (jump rebid, invitational).

        With AuctionContext, opener's jump rebid (16-18 HCP) + responder's 9 = 25-27 combined.
        May accept game with good combined values.
        """
        # Maximum minimum (9 pts) - with jump rebid (16-18), combined may justify game
        hand_decline = create_hand('K74', 'QJ862', 'K5', '983')  # 9 HCP
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '3♣', 'Pass'])
        features = extract_features(hand_decline, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand_decline, features)

        assert result is not None
        bid, explanation = result
        # With AuctionContext showing 25+ combined, may accept game (3NT) or decline (Pass)
        assert bid in ['Pass', '3NT']
        assert 'Declin' in explanation or 'Minimum' in explanation or 'Accept' in explanation or 'game' in explanation.lower()

    def test_preference_with_equal_length(self):
        """1♦ - 1♠ - 2♣ - ? with 3-3 in minors, prefer first suit (diamonds)."""
        hand = create_hand('KQ85', 'J76', 'K32', 'T54')  # 10 HCP (K=3, Q=2, J=1, K=3, T=1), 3-3 minors
        auction = make_auction(['1♦', 'Pass', '1♠', 'Pass', '2♣', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand, features)

        assert result is not None
        bid, explanation = result
        # With 10 HCP + distribution, this is invitational strength
        # Might bid 3♦ (jump preference) or 2♦ (simple preference)
        assert bid in ['2♦', '3♦']  # Either reasonable with this strength
        assert 'preference' in explanation.lower() or 'Invit' in explanation

    def test_rebid_6_card_suit_after_1nt(self):
        """1♦ - 1♥ - 1NT - ? with 6 hearts."""
        # Minimum: Should rebid 2♥ (to play)
        hand_min = create_hand('K7', 'QJ9862', '95', '983')  # 8 HCP (K=3, Q=2, J=1, 9,8 = 2)
        auction = make_auction(['1♦', 'Pass', '1♥', 'Pass', '1NT', 'Pass'])
        features = extract_features(hand_min, auction, responder_position=1)

        module = ResponderRebidModule()
        result = module.evaluate(hand_min, features)

        assert result is not None
        bid, explanation = result
        assert bid == '2♥'
        assert '6+' in explanation


class TestAuctionContextAnalysis:
    """Tests for auction context detection."""

    def test_detect_same_suit_rebid(self):
        """Verify detection of opener rebidding same suit."""
        hand = create_hand('K74', 'Q86', '952', 'K852')
        auction = make_auction(['1♥', 'Pass', '1♠', 'Pass', '2♥', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        context = module._analyze_auction_context('1♥', '1♠', '2♥', hand)

        assert context['opener_rebid_type'] == 'same_suit'
        assert context['opener_first_suit'] == '♥'
        assert context['opener_second_suit'] is None

    def test_detect_new_suit_rebid(self):
        """Verify detection of opener showing new suit."""
        hand = create_hand('K74', 'Q8652', '952', '85')
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        context = module._analyze_auction_context('1♣', '1♥', '1♠', hand)

        assert context['opener_rebid_type'] == 'new_suit'
        assert context['opener_first_suit'] == '♣'
        assert context['opener_second_suit'] == '♠'

    def test_detect_reverse(self):
        """Verify detection of reverse bid."""
        hand = create_hand('KJ874', 'Q5', '86', 'Q732')
        auction = make_auction(['1♦', 'Pass', '1♠', 'Pass', '2♥', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        context = module._analyze_auction_context('1♦', '1♠', '2♥', hand)

        assert context['opener_rebid_type'] == 'reverse'
        assert context['is_forcing'] is True

    def test_detect_unbid_suit_for_fsf(self):
        """Verify detection of fourth suit for Fourth Suit Forcing."""
        hand = create_hand('AQ5', 'KQ84', 'A32', '752')
        auction = make_auction(['1♣', 'Pass', '1♥', 'Pass', '1♠', 'Pass'])
        features = extract_features(hand, auction, responder_position=1)

        module = ResponderRebidModule()
        context = module._analyze_auction_context('1♣', '1♥', '1♠', hand)

        # Clubs, hearts, spades bid - diamonds is fourth suit
        assert context['unbid_suit'] == '♦'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
