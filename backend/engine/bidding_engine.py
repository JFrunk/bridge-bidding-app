from engine.hand import Hand
from engine.opening_bids import get_opening_bid
from engine.responses import get_response_bid, get_responder_rebid # NEW IMPORT
from engine.overcalls import OvercallModule
from engine.rebids import get_openers_rebid
from engine.ai.feature_extractor import extract_features
from engine.ai.decision_engine import select_bidding_module

class BiddingEngine:
    def get_next_bid(self, hand: Hand, auction_history: list, my_position: str):
        features = extract_features(hand, auction_history, my_position)
        decision_type, action = select_bidding_module(features)
        
        if decision_type == 'convention_bid': return action 
        if decision_type == 'natural_bid':
            module_to_use = action
            if module_to_use == 'opening_bids': return get_opening_bid(hand)
            if module_to_use == 'overcalls': 
                overcall_specialist = OvercallModule()
                return overcall_specialist.evaluate(hand, features)
            if module_to_use == 'openers_rebid': return get_openers_rebid(hand, auction_history)
            if module_to_use == 'responses':
                partner_opening_bid = features['auction_features']['opening_bid']
                return get_response_bid(hand, partner_opening_bid)
            if module_to_use == 'responder_rebid': # NEW ACTION
                return get_responder_rebid(hand, features)
        
        return ("Pass", "No clear action defined.")