from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.overcalls import OvercallModule
from engine.ai.conventions.takeout_doubles import TakeoutDoubleConvention

def select_bidding_module(features):
    # Instantiate all specialists
    specialists = {
        'blackwood': BlackwoodConvention(), 'preempts': PreemptConvention(),
        'stayman': StaymanConvention(), 'jacoby': JacobyConvention(),
        'overcalls': OvercallModule(), 'takeout_doubles': TakeoutDoubleConvention()
    }

    # Check high-priority conventional bids
    for name, instance in specialists.items():
        if instance.evaluate(features['hand'], features):
            return name

    # Determine natural bidding situation
    auction = features['auction_features']
    my_bids = [bid for i, bid in enumerate(features['auction_history']) if features['positions'][i % 4] == features['my_index']]

    if not auction['opener']: return 'opening_bids'
    if auction['opener_relationship'] == 'Me': return 'openers_rebid'
    if auction['opener_relationship'] == 'Opponent': return 'advancer_bids'
    if auction['opener_relationship'] == 'Partner': return 'responses'
            
    return 'pass_by_default'