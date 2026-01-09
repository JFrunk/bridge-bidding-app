"""
V3 Logic Stack Bidding Tests

Runs test cases from v3_logic_test_suite.json against the bidding engine.
Uses Actual HCP values (V3 principle) rather than midpoint estimates.

Usage:
    pytest tests/v3/test_v3_bidding.py -v
    pytest tests/v3/test_v3_bidding.py -k "level_1" -v
    pytest tests/v3/test_v3_bidding.py -k "stayman" -v
"""

import json
import pytest
from pathlib import Path
from typing import Dict, List, Optional

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine
from engine.ai.feature_extractor import extract_features


# Load test suite
TEST_SUITE_PATH = Path(__file__).parent / "v3_logic_test_suite.json"


def load_test_suite() -> Dict:
    """Load the V3 test suite JSON."""
    with open(TEST_SUITE_PATH) as f:
        return json.load(f)


def parse_hand_string(hand_str: str) -> Hand:
    """
    Parse a hand string like '♠AKJ76 ♥Q43 ♦K32 ♣65' into a Hand object.
    """
    # Split by suit symbols
    suits = {'♠': [], '♥': [], '♦': [], '♣': []}
    current_suit = None

    for char in hand_str:
        if char in suits:
            current_suit = char
        elif char.isalnum() and current_suit:
            # Convert 10 to T
            if char == '1':
                continue  # Skip '1' in '10'
            elif char == '0':
                suits[current_suit].append('T')
            else:
                suits[current_suit].append(char.upper())
        elif char == ' ':
            continue

    # Build card list as Card namedtuples
    cards = []

    for suit_symbol, ranks in suits.items():
        for rank in ranks:
            cards.append(Card(rank=rank, suit=suit_symbol))

    return Hand(cards)


def create_features(hand: Hand, auction: List[str], position: str = "responder") -> Dict:
    """Create feature dictionary for bidding evaluation."""
    # extract_features(hand, auction_history, my_position, vulnerability, dealer)
    features = extract_features(
        hand=hand,
        auction_history=auction,
        my_position='South',
        vulnerability='None',
        dealer='North'
    )

    return features


def get_bid_from_engine(engine: BiddingEngine, hand: Hand, auction: List[str]) -> str:
    """Get bid from engine using the correct API."""
    bid, _, _ = engine.get_next_bid(
        hand=hand,
        auction_history=auction,
        my_position='South',
        vulnerability='None',
        dealer='North'
    )
    return bid


class TestV3Level1BasicBidding:
    """Tests for Level 1: Basic Bidding Actions"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = BiddingEngine()
        self.test_suite = load_test_suite()
        self.level1_tests = self.test_suite['test_categories']['level_1_basic_bidding']['tests']

    def test_when_to_pass_weak_hand(self):
        """Pass with weak hand (< 12 HCP) in opening seat."""
        test = self.level1_tests['when_to_pass'][0]
        hand = parse_hand_string(test['hand'])

        # Hand should have weak HCP (under opening strength)
        assert hand.hcp < 12, f"Test hand should be weak, got {hand.hcp} HCP"

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_opening_one_spade(self):
        """Open 1♠ with 5+ spades and 12-21 HCP."""
        test = self.level1_tests['opening_one_major'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_opening_one_heart(self):
        """Open 1♥ with 5+ hearts and 12+ HCP."""
        test = self.level1_tests['opening_one_major'][1]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_opening_one_diamond(self):
        """Open 1♦ with no 5-card major and longer diamonds."""
        test = self.level1_tests['opening_one_minor'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_opening_1nt_balanced(self):
        """Open 1NT with 15-17 HCP balanced."""
        test = self.level1_tests['opening_1nt'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_single_raise(self):
        """Raise partner's major with minimum values."""
        test = self.level1_tests['single_raise'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_limit_raise(self):
        """Limit raise with 10-12 HCP and 4-card support."""
        test = self.level1_tests['limit_raise'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_new_suit_response(self):
        """Respond in new suit with 6+ HCP."""
        test = self.level1_tests['new_suit_response'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"


class TestV3Level2OpenerRebid:
    """Tests for Level 2: Opener's Rebid"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = BiddingEngine()
        self.test_suite = load_test_suite()
        self.level2_tests = self.test_suite['test_categories']['level_2_openers_rebid']['tests']

    def test_minimum_rebid_suit(self):
        """Rebid 6-card major with minimum."""
        test = self.level2_tests['minimum_rebid'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        # Allow some flexibility - rebid in own suit is acceptable
        assert bid in [test['expected_bid'], '2♠'], f"Expected {test['expected_bid']}, got {bid}"

    def test_raise_responder_minimum(self):
        """Raise responder's major with 4-card support."""
        test = self.level2_tests['raise_responder'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"


class TestV3Level4Competitive:
    """Tests for Level 4: Competitive Bidding"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = BiddingEngine()
        self.test_suite = load_test_suite()
        self.level4_tests = self.test_suite['test_categories']['level_4_competitive']['tests']

    def test_simple_overcall(self):
        """Overcall with good 5-card suit."""
        test = self.level4_tests['simple_overcall'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_takeout_double(self):
        """Takeout double with support for unbid suits."""
        test = self.level4_tests['takeout_double'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_balancing_1nt(self):
        """Balancing 1NT with Borrowed King principle."""
        test = self.level4_tests['balancing'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        # Balancing 1NT with 11-14 HCP (vs direct 15-17)
        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_balancing_double(self):
        """Balancing double with Borrowed King principle."""
        test = self.level4_tests['balancing'][1]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        # Balancing double with 8+ HCP (vs direct 12+)
        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"


class TestV3EssentialConventions:
    """Tests for Essential SAYC Conventions"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = BiddingEngine()
        self.test_suite = load_test_suite()
        self.convention_tests = self.test_suite['test_categories']['essential_conventions']['tests']

    def test_stayman_inquiry(self):
        """Use Stayman with 4-4 majors."""
        test = self.convention_tests['stayman'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_jacoby_transfer_hearts(self):
        """Transfer to hearts with 5+ hearts."""
        test = self.convention_tests['jacoby_transfers'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_jacoby_transfer_spades(self):
        """Transfer to spades with 5+ spades."""
        test = self.convention_tests['jacoby_transfers'][1]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"

    def test_blackwood_ask(self):
        """Ask for aces with slam interest."""
        test = self.convention_tests['blackwood'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        # Blackwood or cue bid are both acceptable
        assert bid in [test['expected_bid'], '4NT', '4♣'], f"Expected slam try, got {bid}"

    def test_negative_double(self):
        """Negative double showing both majors."""
        test = self.convention_tests['negative_double'][0]
        hand = parse_hand_string(test['hand'])

        bid = get_bid_from_engine(self.engine, hand, test['auction'])

        assert bid == test['expected_bid'], f"Expected {test['expected_bid']}, got {bid}"


class TestV3HandParsing:
    """Test hand string parsing for V3 test suite."""

    def test_parse_basic_hand(self):
        """Parse a basic hand string."""
        # ♠AKJ76 ♥Q43 ♦K32 ♣65: A(4)+K(3)+J(1)+Q(2)+K(3) = 13 HCP
        hand = parse_hand_string("♠AKJ76 ♥Q43 ♦K32 ♣65")

        assert hand.hcp == 13  # A=4, K=3, J=1, Q=2, K=3 = 13
        assert hand.suit_lengths['♠'] == 5
        assert hand.suit_lengths['♥'] == 3
        assert hand.suit_lengths['♦'] == 3
        assert hand.suit_lengths['♣'] == 2

    def test_parse_balanced_hand(self):
        """Parse a balanced hand."""
        hand = parse_hand_string("♠KJ4 ♥AQ7 ♦K865 ♣Q32")

        assert hand.hcp == 15
        assert hand.is_balanced == True

    def test_parse_void_hand(self):
        """Parse a hand with a void (13 cards total)."""
        # ♠AKQJ765 ♥KQJ76 ♦ ♣5 = 7+5+0+1 = 13 cards
        hand = parse_hand_string("♠AKQJ765 ♥KQJ76 ♦ ♣5")

        assert hand.suit_lengths['♦'] == 0
        assert hand.is_balanced == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
