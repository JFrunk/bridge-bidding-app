from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.overcalls import OvercallModule
from engine.ai.conventions.takeout_doubles import TakeoutDoubleConvention
# from engine.ai.conventions.negative_doubles import NegativeDoubleConvention # Temporarily commented out

def select_bidding_module(features):
    """
    Looks at the features and returns the NAME of the specialist module to use.
    """
    
    specialists = {
        'blackwood': BlackwoodConvention(),
        'preempts': PreemptConvention(),
        # 'negative_doubles': NegativeDoubleConvention(), # Temporarily commented out
        'stayman': StaymanConvention(),
        'jacoby': JacobyConvention(),
        'overcalls': OvercallModule(),
        'takeout_doubles': TakeoutDoubleConvention()
    }

    for name, instance in specialists.items():
        if hasattr(instance, 'evaluate') and instance.evaluate(features['hand'], features):
            return name

    auction_features = features['auction_features']
    my_position_str = features['positions'][features['my_index']]
    my_bids = [bid for i, bid in enumerate(features['auction_history']) if features['positions'][i % 4] == my_position_str]

    if not auction_features['opener']:
        return 'opening_bids'
    
    if auction_features['opener_relationship'] == 'Me':
        return 'openers_rebid'
    
    if auction_features['opener_relationship'] == 'Opponent':
        return 'advancer_bids'

    if auction_features['opener_relationship'] == 'Partner':
        return 'responses'
            
    return 'pass_by_default'