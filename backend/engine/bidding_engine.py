from engine.hand import Hand
from engine.opening_bids import get_opening_bid
from engine.responses import get_response_bid
from engine.overcalls import get_overcall
from engine.rebids import get_openers_rebid
from engine.ai.feature_extractor import extract_features
from engine.ai.decision_engine import select_bidding_module

class BiddingEngine:
    def get_next_bid(self, hand: Hand, auction_history: list, my_position: str):
        
        features = extract_features(hand, auction_history, my_position)
        decision_type, action = select_bidding_module(features)
        
        # If the decision was to make a specific conventional bid
        if decision_type == 'convention_bid':
            return action # action is already the (bid, explanation) tuple

        # If the decision was to use a natural bidding module
        if decision_type == 'natural_bid':
            module_to_use = action
            if module_to_use == 'opening_bids': return get_opening_bid(hand)
            if module_to_use == 'overcalls': return get_overcall(hand, auction_history)
            if module_to_use == 'openers_rebid': return get_openers_rebid(hand, auction_history)
            if module_to_use == 'responses':
                partner_opening_bid = features['auction_features']['opening_bid']
                return get_response_bid(hand, partner_opening_bid)
        
        return ("Pass", "No clear action defined.")