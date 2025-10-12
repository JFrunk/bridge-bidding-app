"""
Test to reproduce the first hand bug where all players bid 1NT illegally
"""
from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine

# Recreate the exact hands from the review request
north_cards = [
    Card('A', '♠'), Card('9', '♠'),
    Card('K', '♥'), Card('J', '♥'), Card('T', '♥'), Card('9', '♥'),
    Card('A', '♦'), Card('J', '♦'), Card('6', '♦'),
    Card('A', '♣'), Card('T', '♣'), Card('6', '♣'), Card('4', '♣')
]

east_cards = [
    Card('8', '♠'), Card('7', '♠'), Card('6', '♠'),
    Card('A', '♥'), Card('Q', '♥'), Card('2', '♥'),
    Card('K', '♦'), Card('9', '♦'), Card('8', '♦'), Card('7', '♦'), Card('5', '♦'),
    Card('9', '♣'), Card('2', '♣')
]

south_cards = [
    Card('K', '♠'), Card('Q', '♠'), Card('T', '♠'), Card('4', '♠'),
    Card('8', '♥'), Card('7', '♥'), Card('6', '♥'), Card('3', '♥'),
    Card('3', '♦'),
    Card('K', '♣'), Card('8', '♣'), Card('5', '♣'), Card('3', '♣')
]

west_cards = [
    Card('J', '♠'), Card('5', '♠'), Card('3', '♠'), Card('2', '♠'),
    Card('5', '♥'), Card('4', '♥'),
    Card('Q', '♦'), Card('T', '♦'), Card('4', '♦'), Card('2', '♦'),
    Card('Q', '♣'), Card('J', '♣'), Card('7', '♣')
]

north_hand = Hand(north_cards)
east_hand = Hand(east_cards)
south_hand = Hand(south_cards)
west_hand = Hand(west_cards)

print("=== HAND ANALYSIS ===")
print(f"North: {north_hand.hcp} HCP, balanced={north_hand.is_balanced}, {north_hand.suit_lengths}")
print(f"East: {east_hand.hcp} HCP, balanced={east_hand.is_balanced}, {east_hand.suit_lengths}")
print(f"South: {south_hand.hcp} HCP, balanced={south_hand.is_balanced}, {south_hand.suit_lengths}")
print(f"West: {west_hand.hcp} HCP, balanced={west_hand.is_balanced}, {west_hand.suit_lengths}")
print()

# Create bidding engine
engine = BiddingEngine()
vulnerability = "EW"

# Simulate the auction
auction = []
positions = ['North', 'East', 'South', 'West']
hands = [north_hand, east_hand, south_hand, west_hand]

print("=== SIMULATED AUCTION ===")
for i in range(4):  # First 4 bids
    position = positions[i]
    hand = hands[i]

    print(f"\n--- {position}'s turn (auction so far: {auction}) ---")

    # Extract features to see what decision engine sees
    from engine.ai.feature_extractor import extract_features
    features = extract_features(hand, auction, position, vulnerability)

    print(f"  opener: {features['auction_features']['opener']}")
    print(f"  opener_relationship: {features['auction_features']['opener_relationship']}")

    # Get next bid
    bid, explanation = engine.get_next_bid(hand, auction, position, vulnerability)

    print(f"  BID: {bid}")
    print(f"  Explanation: {explanation[:100]}...")

    # Check if bid is legal
    is_legal = engine._is_bid_legal(bid, auction)
    print(f"  Legal: {is_legal}")

    auction.append(bid)

print("\n=== FINAL AUCTION ===")
print(auction)
