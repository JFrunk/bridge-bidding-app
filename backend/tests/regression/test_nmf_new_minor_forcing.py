"""
Regression Test: New Minor Forcing (NMF)

Tests the complete NMF bidding sequence:
1. Partner opens 1m, I respond 1M, partner rebids 1NT
2. I bid the unbid minor (NMF) with 11+ HCP to probe for best contract
3. Partner responds showing major support, other major, or NT range
4. I place the contract based on partner's response

NMF solves the "game-forcing gap" where responder has invitational+ values
but no way to describe their hand without guessing the final contract.
"""

import pytest
from engine.hand import Hand, Card
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema
from engine.v2.features.enhanced_extractor import extract_flat_features


def make_hand(spades: str, hearts: str, diamonds: str, clubs: str) -> Hand:
    """Create a Hand from suit strings like 'AKQ32' for each suit."""
    cards = []
    for suit, holding in [('♠', spades), ('♥', hearts), ('♦', diamonds), ('♣', clubs)]:
        for rank in holding:
            cards.append(Card(rank, suit))
    if len(cards) != 13:
        raise ValueError(f"Hand must have 13 cards, got {len(cards)}")
    return Hand(cards)


class TestNMFFeatureExtraction:
    """Test that the feature extractor correctly identifies NMF situations."""

    def test_nmf_situation_after_1c_1h_1nt(self):
        """After 1♣-1♥-1NT, responder should see is_nmf_situation=True."""
        # Partner(North) opened 1♣, I(South) responded 1♥, Partner rebid 1NT
        hand = make_hand("K32", "AQT54", "K32", "43")  # 13 HCP, 5 hearts
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        assert features['is_nmf_situation'] is True
        assert features['nmf_suit'] == '♦', "NMF suit should be ♦ (unbid minor when partner opened ♣)"
        assert features['nmf_bid'] == '2♦'
        assert features['partner_opening_minor'] == '♣'

    def test_nmf_situation_after_1d_1s_1nt(self):
        """After 1♦-1♠-1NT, responder should see NMF bid as 2♣."""
        hand = make_hand("AQJ54", "K32", "43", "K32")  # 13 HCP, 5 spades
        auction = ["1♦", "Pass", "1♠", "Pass", "1NT", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        assert features['is_nmf_situation'] is True
        assert features['nmf_suit'] == '♣', "NMF suit should be ♣ (unbid minor when partner opened ♦)"
        assert features['nmf_bid'] == '2♣'

    def test_no_nmf_when_contested(self):
        """NMF should not trigger when opponents have bid."""
        hand = make_hand("K32", "AQT54", "K32", "43")
        # Partner opened 1♣, opponent overcalled, I bid 1♥, opponent bid again, partner bid 1NT
        auction = ["1♣", "1♦", "1♥", "Pass", "1NT", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        # is_contested should be True, blocking NMF
        assert features['is_contested'] is True
        assert features['is_nmf_situation'] is False

    def test_no_nmf_when_partner_opened_major(self):
        """NMF does not apply when partner opened a major."""
        hand = make_hand("K32", "43", "AQT54", "K32")
        auction = ["1♥", "Pass", "1♠", "Pass", "1NT", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        assert features['is_nmf_situation'] is False

    def test_no_nmf_weak_hand(self):
        """NMF situation detected but engine should not bid NMF with <11 HCP."""
        hand = make_hand("K32", "QT754", "932", "43")  # 7 HCP — too weak
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        # Feature detection works regardless of HCP
        assert features['is_nmf_situation'] is True
        # But the schema rule requires 11+ HCP — engine should not bid NMF


class TestNMFOpenerDetection:
    """Test that opener correctly detects partner's NMF bid."""

    def test_opener_detects_nmf_2d_after_1c(self):
        """Opener should detect partner's 2♦ as NMF after 1♣-1♥-1NT-2♦."""
        # I(North) opened 1♣, partner(South) bid 1♥, I rebid 1NT, partner bid 2♦
        hand = make_hand("Q43", "K32", "AJ5", "KQ43")  # 15 HCP balanced
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass", "2♦", "Pass"]

        features = extract_flat_features(hand, auction, "North", "None", "North")

        assert features['partner_bid_nmf'] is True
        assert features['nmf_responder_major'] == '♥'

    def test_opener_detects_nmf_2c_after_1d(self):
        """Opener should detect partner's 2♣ as NMF after 1♦-1♠-1NT-2♣."""
        hand = make_hand("K32", "AJ5", "KQ43", "Q43")  # 15 HCP balanced
        auction = ["1♦", "Pass", "1♠", "Pass", "1NT", "Pass", "2♣", "Pass"]

        features = extract_flat_features(hand, auction, "North", "None", "North")

        assert features['partner_bid_nmf'] is True
        assert features['nmf_responder_major'] == '♠'


class TestNMFContinuationFeatures:
    """Test responder's continuation features after opener responds to NMF."""

    def test_partner_showed_support(self):
        """After NMF, opener bid 2♥ showing support for my hearts."""
        # N: 1♣, S: 1♥, N: 1NT, S: 2♦(NMF), N: 2♥(support)
        hand = make_hand("K32", "AQT54", "K32", "43")  # 13 HCP, 5 hearts
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass", "2♦", "Pass", "2♥", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        assert features['partner_responded_to_my_nmf'] is True
        assert features['partner_nmf_showed_support'] is True
        assert features['my_nmf_major'] == '♥'

    def test_partner_showed_other_major(self):
        """After NMF, opener bid 2♠ showing 4 spades (I bid hearts)."""
        hand = make_hand("KJ32", "AQT54", "32", "43")  # 12 HCP, 5H 4S
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass", "2♦", "Pass", "2♠", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        assert features['partner_responded_to_my_nmf'] is True
        assert features['partner_nmf_showed_other_major'] is True

    def test_partner_showed_minimum_2nt(self):
        """After NMF, opener bid 2NT showing minimum without major fit."""
        hand = make_hand("K32", "AQT54", "K32", "43")
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass", "2♦", "Pass", "2NT", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        assert features['partner_responded_to_my_nmf'] is True
        assert features['partner_nmf_minimum'] is True

    def test_partner_showed_maximum_3nt(self):
        """After NMF, opener bid 3NT showing maximum without major fit."""
        hand = make_hand("K32", "AQT54", "K32", "43")
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass", "2♦", "Pass", "3NT", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        assert features['partner_responded_to_my_nmf'] is True
        assert features['partner_nmf_maximum'] is True


class TestNMFEngineIntegration:
    """Full engine tests for NMF bidding sequences."""

    @pytest.fixture
    def engine(self):
        return BiddingEngineV2Schema()

    def test_responder_bids_nmf_with_invitational_hand(self, engine):
        """Responder with 12 HCP and 5 hearts should bid NMF (2♦) after 1♣-1♥-1NT."""
        hand = make_hand("K32", "AQT54", "K32", "43")  # 13 HCP, 5 hearts
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass"]

        bid, explanation = engine.get_next_bid(
            hand=hand, auction_history=auction,
            my_position="South", vulnerability="None", dealer="North"
        )

        assert bid == "2♦", f"Expected NMF 2♦, got {bid} ({explanation})"
        assert "New Minor Forcing" in explanation or "NMF" in explanation or "minor" in explanation.lower()

    def test_responder_bids_nmf_2c_after_1d(self, engine):
        """After 1♦-1♠-1NT, responder should bid 2♣ (NMF)."""
        hand = make_hand("AQJ54", "K32", "43", "K32")  # 13 HCP, 5 spades
        auction = ["1♦", "Pass", "1♠", "Pass", "1NT", "Pass"]

        bid, explanation = engine.get_next_bid(
            hand=hand, auction_history=auction,
            my_position="South", vulnerability="None", dealer="North"
        )

        assert bid == "2♣", f"Expected NMF 2♣, got {bid} ({explanation})"

    def test_opener_shows_heart_support_after_nmf(self, engine):
        """After NMF, opener with 3+ hearts should bid 2♥."""
        hand = make_hand("Q43", "K32", "AJ5", "KQ43")  # 15 HCP, 3 hearts
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass", "2♦", "Pass"]

        bid, explanation = engine.get_next_bid(
            hand=hand, auction_history=auction,
            my_position="North", vulnerability="None", dealer="North"
        )

        assert bid == "2♥", f"Expected 2♥ showing heart support, got {bid} ({explanation})"

    def test_opener_shows_4_spades_after_nmf(self, engine):
        """After 1♣-1♥-1NT-2♦, opener with 4 spades but <3 hearts should bid 2♠."""
        hand = make_hand("KQ43", "J5", "AJ5", "KQ43")  # 16 HCP, 4S 2H
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass", "2♦", "Pass"]

        bid, explanation = engine.get_next_bid(
            hand=hand, auction_history=auction,
            my_position="North", vulnerability="None", dealer="North"
        )

        assert bid == "2♠", f"Expected 2♠ showing 4 spades, got {bid} ({explanation})"

    def test_opener_bids_2nt_minimum_no_major_fit(self, engine):
        """After NMF, opener with minimum (12-13) and no major fit should bid 2NT."""
        hand = make_hand("Q43", "J5", "AJ52", "KQ43")  # 13 HCP, no major fit
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass", "2♦", "Pass"]

        bid, explanation = engine.get_next_bid(
            hand=hand, auction_history=auction,
            my_position="North", vulnerability="None", dealer="North"
        )

        assert bid == "2NT", f"Expected 2NT (minimum, no major), got {bid} ({explanation})"

    def test_opener_bids_3nt_maximum_no_major_fit(self, engine):
        """After NMF, opener with maximum (14+) and no major fit should bid 3NT."""
        hand = make_hand("Q43", "J5", "AKJ5", "KQ43")  # 16 HCP, no major fit
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass", "2♦", "Pass"]

        bid, explanation = engine.get_next_bid(
            hand=hand, auction_history=auction,
            my_position="North", vulnerability="None", dealer="North"
        )

        assert bid == "3NT", f"Expected 3NT (maximum, no major), got {bid} ({explanation})"

    def test_weak_responder_does_not_nmf(self, engine):
        """Responder with <11 HCP should NOT bid NMF."""
        hand = make_hand("K32", "QT754", "932", "43")  # 7 HCP — too weak
        auction = ["1♣", "Pass", "1♥", "Pass", "1NT", "Pass"]

        bid, explanation = engine.get_next_bid(
            hand=hand, auction_history=auction,
            my_position="South", vulnerability="None", dealer="North"
        )

        # Should pass or bid 2♥ (weak signoff), NOT 2♦ (NMF)
        assert bid != "2♦" or "New Minor" not in explanation, \
            f"Weak hand should not use NMF, got {bid} ({explanation})"
