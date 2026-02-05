
from engine.hand import Hand, Card
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema

def make_hand_from_pbn(pbn):
    return Hand.from_pbn(pbn)

def test_strong_hand_opening():
    print("--- Test 1: West (17 HCP) Hand 10 ---")
    # Hand 1 (17 HCP): A4.AQJ9762.Q42.A
    # PBN format: S.H.D.C
    # Spades: A4
    # Hearts: AQJ9762
    # Diamonds: Q42
    # Clubs: A
    hand = make_hand_from_pbn("A4.AQJ9762.Q42.A")
    print(f"Hand: {hand.to_pbn()} HCP: {hand.hcp}")
    
    engine = BiddingEngineV2Schema(use_v1_fallback=False)
    auction = []
    
    # West is Dealer
    bid, expl = engine.get_next_bid(hand, auction, "West", dealer="West")
    print(f"Bid: {bid} ({expl})")
    
    if bid == "Pass":
        print("FAILURE: Strong hand passed!")
        # Debug candidates
        candidates = engine.get_bid_candidates(hand, auction, "West", dealer="West")
        print("Candidates found:")
        for c in candidates:
            print(f" - {c.bid}: {c.priority} (Rule: {c.rule_id})")
    else:
        print("SUCCESS: Opened correctly.")

def test_responder_pass():
    print("\n--- Test 2: South (15 HCP) Hand 45 ---")
    # Hand 2 (15 HCP): K753.A4.74.AKJ93
    # North opened 1C
    hand = make_hand_from_pbn("K753.A4.74.AKJ93")
    print(f"Hand: {hand.to_pbn()} HCP: {hand.hcp}")
    
    engine = BiddingEngineV2Schema(use_v1_fallback=False)
    auction = ["1♣"]
    
    bid, expl = engine.get_next_bid(hand, auction, "South", dealer="North")
    print(f"Bid: {bid} ({expl})")
    
    if bid == "Pass":
        print("FAILURE: Responder passed with 15 HCP!")
        candidates = engine.get_bid_candidates(hand, auction, "South", dealer="North")
        print("Candidates found:")
        for c in candidates:
            print(f" - {c.bid}: {c.priority} (Rule: {c.rule_id})")

if __name__ == "__main__":
    test_strong_hand_opening()
    test_responder_pass()
