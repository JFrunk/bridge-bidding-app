from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.preempts import PreemptConvention
from engine.overcalls import OvercallModule

def select_bidding_module(features):
    auction_features = features.get('auction_features', {})
    
    # Instantiate specialists
    stayman = StaymanConvention()
    jacoby = JacobyConvention()
    preempt = PreemptConvention()
    overcall = OvercallModule()

    # --- COMPETITIVE LOGIC FIRST ---
    # Is it my turn to act after an opponent's overcall?
    if auction_features.get('opener_relationship') == 'Opponent':
        if features['my_index'] == (auction_features['opener_index'] + 1) % 4:
            overcall_bid = overcall.evaluate(features['hand'], features)
            if overcall_bid: return ('convention_bid', overcall_bid)
            # Takeout Double logic would go here
    
    # NEW: Am I the opener rebidding after an opponent's overcall?
    if auction_features.get('opener_relationship') == 'Me' and auction_features.get('is_contested'):
        return ('natural_bid', 'openers_rebid')

    # --- PARTNERSHIP BIDDING LOGIC ---
    preempt_bid = preempt.evaluate(features['hand'], features)
    if preempt_bid: return ('convention_bid', preempt_bid)

    stayman_bid = stayman.evaluate(features['hand'], features)
    if stayman_bid: return ('convention_bid', stayman_bid)
        
    jacoby_bid = jacoby.evaluate(features['hand'], features)
    if jacoby_bid: return ('convention_bid', jacoby_bid)

    # --- NATURAL BIDS ---
    if not auction_features['opener']:
        return ('natural_bid', 'opening_bids')
    if auction_features['opener_relationship'] == 'Me' and len(auction_features['partner_bids']) == 1:
        return ('natural_bid', 'openers_rebid')
    if auction_features['opener_relationship'] == 'Partner' and len(auction_features['partner_bids']) == 1: 
        return ('natural_bid', 'responses')
            
    return ('natural_bid', 'pass_by_default')