from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.overcalls import OvercallModule
from engine.ai.conventions.takeout_doubles import TakeoutDoubleConvention

def select_bidding_module(features):
    """
    Looks at the features and returns the NAME of the specialist module to use.
    This version has a more robust, state-based logic.
    """
    auction = features['auction_features']
    my_pos_str = features['positions'][features['my_index']]
    my_bids = [bid for i, bid in enumerate(features['auction_history']) if features['positions'][i % 4] == my_pos_str]

    # --- STATE 1: Is this an OPENING situation? ---
    if not auction['opener']:
        # Priority for opening is to check for a preempt first.
        preempt_specialist = PreemptConvention()
        if preempt_specialist.evaluate(features['hand'], features):
            return 'preempts'
        return 'opening_bids'

    # --- STATE 2: Is this a COMPETITIVE situation? ---
    if auction['opener_relationship'] == 'Opponent':
        # If it's my first bid after an opponent opened, I can overcall or double.
        if len(my_bids) == 0:
            overcall_specialist = OvercallModule()
            if overcall_specialist.evaluate(features['hand'], features): return 'overcalls'
            
            takeout_double_specialist = TakeoutDoubleConvention()
            if takeout_double_specialist.evaluate(features['hand'], features): return 'takeout_doubles'
        else: # It's my second bid, I am the "advancer"
            return 'advancer_bids'

    # --- STATE 3: This is an UNCONTESTED PARTNERSHIP auction ---
    if auction['opener_relationship'] == 'Partner': # My partner opened
        # Check for conventions over 1NT first
        if auction['opening_bid'] == '1NT':
            jacoby = JacobyConvention()
            if jacoby.evaluate(features['hand'], features): return 'jacoby'
            stayman = StaymanConvention()
            if stayman.evaluate(features['hand'], features): return 'stayman'
        # Fallback to natural responses
        return 'responses'

    if auction['opener_relationship'] == 'Me': # I opened
        # Check for slam conventions
        blackwood = BlackwoodConvention()
        if blackwood.evaluate(features['hand'], features):
            return 'blackwood'
        # Fallback to natural rebids
        return 'openers_rebid'
            
    return 'pass_by_default'