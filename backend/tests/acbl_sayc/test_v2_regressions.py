
import pytest
from engine.hand import Hand
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema

# Test helpers
def make_hand(spades, hearts, diamonds, clubs):
    """Create a hand from pbn-style strings."""
    cards = []
    # Simple mapping for test creation
    rank_map = {'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': 'T', 
                '9': '9', '8': '8', '7': '7', '6': '6', '5': '5', '4': '4', '3': '3', '2': '2'}
    
    for suit_char, holding in [('♠', spades), ('♥', hearts), ('♦', diamonds), ('♣', clubs)]:
        for rank_char in holding:
            # We construct a real Hand object using from_pbn or similar would be easier, 
            # but let's stick to the pattern used in other tests if possible, 
            # or just use the pbn string which Hand.from_pbn supports.
            pass
            
    # Actually, let's just use Hand.from_pbn for simplicity if the class supports it
    pbn = f"{spades}.{hearts}.{diamonds}.{clubs}"
    return Hand.from_pbn(pbn)

@pytest.fixture
def engine():
    return BiddingEngineV2Schema(use_v1_fallback=False)

class TestV2Regressions:
    """
    Test suite specifically for regressions found in V1 that might exist in V2.
    """

    def test_weak_hand_game_force(self, engine):
        """
        Regression: 5 HCP hand should NOT bid 4H (Game) in response to 1H.
        This was the original 'fragility' bug.
        """
        # ♠ 8743 ♥ 763 ♦ T85 ♣ J32 (1+0+0+1 = 2 HCP) - Extremely weak
        # Partner opens 1H. We should Pass.
        hand = make_hand("8743", "763", "T85", "J32")
        auction = ["1♥"]
        
        bid, explanation = engine.get_next_bid(hand, auction, "South")
        
        # Should be Pass. Definitely NOT 4H or 2H.
        assert bid == "Pass", f"Weak hand (2 HCP) against 1H should Pass, but bid {bid}. Expl: {explanation}"

    def test_responder_preference_legality(self, engine):
        """
        Regression: Giving preference should not return the current bid (illegal).
        Auction: 1D - Pass - 1S - Pass - 2D - Pass - ?
        Responder has 2 diamonds, should Pass (satisfied with contract).
        """
        # ♠ KJ732 ♥ J54 ♦ 85 ♣ Q72 (3+1+0+2=6 HCP)
        hand = make_hand("KJ732", "J54", "85", "Q72")
        auction = ["1♦", "Pass", "1♠", "Pass", "2♦", "Pass"]
        
        bid, explanation = engine.get_next_bid(hand, auction, "South")
        
        assert bid == "Pass", f"Should Pass 2D rebid with preference, but bid {bid}. Expl: {explanation}"

    def test_opener_rebid_minimum_vs_medium(self, engine):
        """
        Regression: 13-15 HCP opener should not jump raise partner's suit or invite aggressively.
        Auction: 1D - Pass - 1S - Pass - ?
        """
        # 14 HCP: ♠ KJ32 ♥ K2 ♦ AQJ32 ♣ 32
        hand = make_hand("KJ32", "K2", "AQJ32", "32")
        auction = ["1♦", "Pass", "1♠", "Pass"]
        
        # South must be dealer to be Opener
        bid, explanation = engine.get_next_bid(hand, auction, "South", dealer="South")
        
        # Should be 2S (Simple Raise), NOT 3S (Invite) or 4S (Game)
        assert bid == "2♠", f"14 HCP opener with fit should bid 2S, but bid {bid}. Expl: {explanation}"

    def test_opener_rebid_strong_vs_medium(self, engine):
        """
        Regression: 17 HCP opener should validly invite or Reverse, but correct range is key.
        Checks boundaries for Medium/Strong.
        """
        # 18 HCP is updated 'Strong' threshold.
        # 17 HCP: ♠ AQ32 ♥ K2 ♦ AKJ32 ♣ 32
        hand = make_hand("AQ32", "K2", "AKJ32", "32")
        auction = ["1♦", "Pass", "1♠", "Pass"]
        
        # South must be dealer
        bid, explanation = engine.get_next_bid(hand, auction, "South", dealer="South")
        
        # With 17HCP + fit + shape, this is a very strong hand.
        # In V1 we adjusted this. Let's see what V2 does.
        # Ideally 3S (Strong Invite) or 4S depending on aggression.
        # V2 Scheme check.
        assert bid in ["3♠", "4♠"], f"17 HCP strong hand should raise aggressively, but bid {bid}: {explanation}"

