
from engine.hand import Hand, Card
from engine.bidding_engine_v2 import BiddingEngineV2
import logging
import sys

# Configure logging to stdout
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def test_5nt_bug():
    print("--- Reproducing 5NT Bug (Hand 2) ---")
    # Shape 2425: 2 Spades, 4 Hearts, 2 Diamonds, 5 Clubs
    # HCP: 5
    # Let's construct a hand:
    # S: 85
    # H: 9876
    # D: 43
    # C: JT982
    # Total HCP: 0? No, need 5.
    # S: K5 (3)
    # H: Q876 (2)
    # D: 43
    # C: J9872 (1) -> 6 HCP. Close enough.
    
    # Let's try to pass in cards manually to match shape exactly roughly
    # S: 85
    # H: Qxxx
    # D: xx
    # C: KQxxx
    
    # Using PBN for a weak hand with 5 clubs
    # PBN: S.H.D.C
    pbn = "85.Q876.43.KQ872" # S:85 H:Q876 D:43 C:KQ872 (HCP: Q+K+Q = 2+3+2 = 7)
    hand = Hand.from_pbn(pbn)
    print(f"Hand: {hand.to_pbn()} HCP: {hand.hcp}")
    
    engine = BiddingEngineV2()
    # Auction context from log wasn't clear, but likely Partner opened something or it's a competitive auction?
    # The log said "North bid 5NT"
    # Let's try a few scenarios.
    
    scenarios = [
        [], 
        ["1H"], ["1S"], ["1C"], ["1D"], ["1NT"], ["2NT"], ["2C"],
        ["1C", "Pass", "1H", "Pass"], # 4th seat
        ["1S", "Pass", "2S"], # Competitive
        ["1NT", "Pass"],
        ["2NT", "Pass"],
        # Check for conventions gone wrong
        ["1NT", "Pass", "2C", "Pass"], # After Stayman
        ["1NT", "Pass", "2D", "Pass"], # After Transfer
        ["1H", "Pass", "4NT", "Pass"], # RKC?
        ["1S", "Pass", "4NT", "Pass"],
        ["2NT", "Pass", "3NT", "Pass", "4NT", "Pass"], # Quantitative sequence?
        ["2NT", "Pass", "3NT", "Pass", "5NT", "Pass"], # Partner bids 5NT?
    ]
    
    for auction in scenarios:
        print(f"\nScenario: {auction}")
        try:
            # If auction length is even (0, 2), it's South's turn (if South deals).
            # If auction length is odd (1, 3), it's West's turn... wait.
            # Dealer: South.
            # 0: South
            # 1: West
            # 2: North
            # 3: East
            # We want North to bid. So we need 2 bids (e.g. 1NT, Pass).
            
            # Let's standardize: Dealer = South. We want to test North's response.
            # We need to provide auctions where it is North's turn.
            # 1H (South), Pass (West) -> North.
            
            # Filter scenarios that don't make sense for North acting as Responder to South
            # or North acting as Opener (if auction empty)
            
            final_auction = list(auction)
            position = "North"
            if len(final_auction) == 0:
                 bid, expl = engine.get_next_bid(hand, final_auction, "North", vulnerability="None", dealer="North")
            else:
                 # Assume South opened.
                 if len(final_auction) % 2 != 0:
                     final_auction.append("Pass")
                 
                 # Derive proper position based on turn
                 # Dealer South (0).
                 turn_idx = len(final_auction) % 4
                 positions = ["South", "West", "North", "East"]
                 position = positions[turn_idx]
                 
                 bid, expl = engine.get_next_bid(hand, final_auction, position, vulnerability="None", dealer="South")
            
            print(f"Bid ({position}): {bid} ({expl})")
            if "5NT" in bid or "3NT" in bid:
                print("FOUND IT! 🚨")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_5nt_bug()
