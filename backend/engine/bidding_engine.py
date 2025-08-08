from engine.hand import Hand
from engine.opening_bids import get_opening_bid
from engine.responses import get_response_bid
from engine.overcalls import get_overcall
from engine.rebids import get_openers_rebid
from engine.ai.feature_extractor import extract_features
from engine.ai.decision_engine import select_bidding_module
from engine.ai.conventions.jacoby_transfers import get_jacoby_transfer_bid
from engine.ai.conventions.transfer_responses import get_transfer_completion_bid

class BiddingEngine:
    def get_next_bid(self, hand: Hand, auction_history: list, my_position: str):
        features = extract_features(hand, auction_history, my_position)
        module_to_use = select_bidding_module(features)
        
        if module_to_use == 'opening_bids': return get_opening_bid(hand)
        if module_to_use == 'overcalls': return get_overcall(hand, auction_history)
        if module_to_use == 'jacoby_transfers': return get_jacoby_transfer_bid(hand)
        if module_to_use == 'transfer_completion':
            partner_bid = features['auction_features']['partner_last_bid']
            return get_transfer_completion_bid(partner_bid)
        if module_to_use == 'stayman_response': return get_response_bid(hand, "1NT")
        
        if module_to_use == 'openers_rebid':
            # CORRECTED: Pass the full auction history for context
            return get_openers_rebid(hand, auction_history)
            
        if module_to_use == 'responses':
            partner_opening_bid = features['auction_features']['opening_bid']
            return get_response_bid(hand, partner_opening_bid)
            
        return ("Pass", "No clear action defined.")