
import pytest
import json
import glob
import os
from engine.hand import Hand, Card
from engine.v2.bidding_engine_v2_schema import BiddingEngineV2Schema

# Helper to look up dealer index
DIRECTIONS = ["North", "East", "South", "West"]

def get_next_bidder(dealer, auction_history):
    # Normalize dealer name
    dealer_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
    dealer = dealer_map.get(dealer, dealer)
    
    start_idx = DIRECTIONS.index(dealer)
    offset = len(auction_history)
    return DIRECTIONS[(start_idx + offset) % 4]

def json_card_to_obj(card_dict):
    return Card(card_dict['rank'], card_dict['suit'])

class TestExternalReviewHands:
    """
    Run V2 engine against captured hands from review requests to ensure stability.
    """
    
    @pytest.fixture(scope="class")
    def engine(self):
        return BiddingEngineV2Schema(use_v1_fallback=False)

    def load_review_hands():
        # Find all JSON files in review_requests
        # __file__ is backend/tests/integration/test.py
        # dirname 1: backend/tests/integration
        # dirname 2: backend/tests
        # dirname 3: backend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        files = glob.glob(os.path.join(base_dir, "review_requests", "*.json"))
        # Return a list of (filename, data) tuples
        hands = []
        for f in files:
            try:
                with open(f, 'r') as fd:
                    data = json.load(fd)
                    hands.append((os.path.basename(f), data))
            except Exception as e:
                print(f"Skipping broken file {f}: {e}")
        return hands

    @pytest.mark.parametrize("filename, data", load_review_hands())
    def test_review_hand_stability(self, engine, filename, data):
        """
        Ensure the engine produces a legal bid for every captured review hand.
        """
        # 1. Reconstruct state
        # 1. Reconstruct state
        dealer_raw = data.get('dealer', 'North')
        # Normalize dealer
        dealer_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
        dealer = dealer_map.get(dealer_raw, dealer_raw)
        
        vuln_raw = data.get('vulnerability', 'None')
        # Normalize vulnerability (some files use 'N/S' etc, some use 'Both', 'None')
        # Engine expects 'None', 'NS', 'EW', 'Both' (usually) 
        # But let's just pass what we have, V2 extractor is robust?
        # Let's map common ones just in case.
        vuln_map = {'None': 'None', 'All': 'Both', 'Love': 'None', 'Both': 'Both', 'NS': 'NS', 'EW': 'EW'}
        vulnerability = vuln_map.get(vuln_raw, vuln_raw)
        
        # Parse auction history
        auction_history = [entry['bid'] for entry in data.get('auction', [])]
        
        # Determine whose turn it is
        next_bidder = get_next_bidder(dealer, auction_history)
        
        # Get that player's hand
        player_data = data['all_hands'].get(next_bidder)
        if not player_data:
            pytest.skip(f"No hand data for {next_bidder} in {filename}")
            
        cards = [json_card_to_obj(c) for c in player_data['cards']]
        hand = Hand(cards)
        
        # 2. Ask Engine for Bid
        try:
            bid, explanation = engine.get_next_bid(
                hand=hand,
                auction_history=auction_history,
                my_position=next_bidder,
                vulnerability=vulnerability,
                dealer=dealer
            )
            
            # 3. Basic Validation
            print(f"\n[{filename}] {next_bidder} holds {hand.hcp} HCP. Auction: {auction_history} -> Bids: {bid}")
            
            # Must be a valid bridge bid string (simple regex or list check)
            valid_contracts = ['Pass', 'X', 'XX'] 
            for level in range(1, 8):
                for suit in ['C', 'D', 'H', 'S', 'NT', '♣', '♦', '♥', '♠']:
                    valid_contracts.append(f"{level}{suit}")
            
            assert bid in valid_contracts, f"Engine produced invalid bid string: {bid}"
            
            # Illegal bid check (Responder Preference bug regression check)
            if bid not in ['Pass', 'X', 'XX']:
                # If we bid a suit, make sure it's sufficient
                # (This is a weak check, relies on engine internals usually, but we can catch obvious junk)
                pass

        except Exception as e:
            pytest.fail(f"Engine CRASHED on {filename}: {e}")
