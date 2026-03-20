"""
Regression Test: Gerber Trap — Opponent's 4♣ Must Not Trigger Gerber Response

Bug Report: Depth-8 structural audit (2026-03-19)
Fixed: 2026-03-19

Issue: When an opponent bids 4♣ (natural or preemptive) after a 1NT opening,
the engine misidentified it as Gerber and responded with an ace-showing bid
(4♦/4♥/4♠/4NT). This "Ghost Gerber" caused the engine to commit to 4-level
contracts on misfit hands, tanking the success rate.

Root Cause: The old Gerber response rules only checked `partner_last_bid == "4♣"`
without verifying WHO made the 4♣ bid. An opponent's natural 4♣ overcall matched
the pattern and triggered ace-showing responses.

Fix (schema-level defense-in-depth):
1. Feature: `last_bid_side` tracks whether the last substantive bid came from
   partner, opponent, or self — using (dealer_seat + bid_index) % 4 math.
2. Schema: Gerber responses in sayc_slam.json require `last_bid_side: "partner"`.
3. Schema: Gerber initiation rules require `is_contested: false`.

Test Case:
- North opens 1NT (15-17 HCP balanced)
- East overcalls 4♣ (natural/preemptive)
- South must NOT respond as if 4♣ were Gerber
- South should pass, double, or bid naturally — never 4♦/4♥/4♠ as ace-showing
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


class TestGerberTrapOpponent4C:
    """Regression: opponent's 4♣ must not trigger Gerber responses."""

    @pytest.fixture
    def engine(self):
        return BiddingEngineV2Schema()

    def test_last_bid_side_opponent_after_overcall(self):
        """Feature extractor correctly identifies opponent's 4♣ as 'opponent'."""
        # Auction: North(1NT) - East(4♣) - South's turn
        # Dealer=North, my_position=South
        hand = make_hand("Q432", "KQ32", "A32", "32")  # 12 HCP, 1 ace
        auction = ["1NT", "4♣"]

        features = extract_flat_features(hand, auction, "South", "None", "North")

        assert features['last_bid_side'] == 'opponent', \
            f"East's 4♣ should be 'opponent', got '{features['last_bid_side']}'"
        assert features['is_contested'] is True

    def test_last_bid_side_partner_gerber(self):
        """Feature extractor correctly identifies partner's 4♣ as 'partner'."""
        # Auction: South(1NT) - West(Pass) - North(4♣) - East(Pass) - South's turn
        # Dealer=South, my_position=South
        hand = make_hand("AQ32", "KJ32", "AQ2", "K2")  # 19 HCP, 2 aces
        auction = ["1NT", "Pass", "4♣", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "South")

        assert features['last_bid_side'] == 'partner', \
            f"North's 4♣ should be 'partner', got '{features['last_bid_side']}'"

    def test_engine_does_not_gerber_respond_to_opponent(self):
        """Full engine: South must NOT show aces when East bids 4♣."""
        engine = BiddingEngineV2Schema()

        # South has 1 ace — if Gerber triggers, engine would bid 4♦
        hand = make_hand("Q432", "KQ32", "A32", "32")  # 12 HCP, 1 ace
        # North opens 1NT, East overcalls 4♣
        auction = ["1NT", "4♣"]

        bid, explanation = engine.get_next_bid(
            hand=hand,
            auction_history=auction,
            my_position="South",
            vulnerability="None",
            dealer="North"
        )

        # Must NOT be a Gerber ace-showing response
        gerber_responses = {"4♦", "4♥", "4♠", "4NT"}
        if bid in gerber_responses:
            assert "Gerber" not in explanation and "ace" not in explanation.lower(), \
                f"Got {bid} ({explanation}) — looks like a Gerber misfire to opponent's 4♣"

    def test_engine_does_not_gerber_respond_to_opponent_with_two_aces(self):
        """Full engine: 2-ace hand must not show aces to opponent's 4♣."""
        engine = BiddingEngineV2Schema()

        # South has 2 aces — Gerber would bid 4♠
        hand = make_hand("AQ32", "KQ32", "A32", "32")  # 16 HCP, 2 aces
        auction = ["1NT", "4♣"]

        bid, explanation = engine.get_next_bid(
            hand=hand,
            auction_history=auction,
            my_position="South",
            vulnerability="None",
            dealer="North"
        )

        # 4♠ with "ace" in explanation = Gerber misfire
        if bid == "4♠":
            assert "ace" not in explanation.lower(), \
                f"Got 4♠ ({explanation}) — Gerber misfire to opponent's 4♣"

    def test_last_bid_side_self_after_rebid(self):
        """last_bid_side='self' when my bid is the last substantive bid."""
        # Auction: South(1♠) - West(Pass) - North(2♠) - East(Pass) - South(4♠) - West(Pass) - North(Pass) - East(Pass)
        # Actually, simpler: South opened, opponents passed, partner passed
        # Dealer=South: S(1♠) W(Pass) N(Pass) E(Pass) — last non-pass is 1♠ by South
        hand = make_hand("AKQ32", "KJ2", "A32", "32")
        auction = ["1♠", "Pass", "Pass", "Pass"]

        features = extract_flat_features(hand, auction, "South", "None", "South")

        assert features['last_bid_side'] == 'self', \
            f"My own 1♠ should be 'self', got '{features['last_bid_side']}'"
