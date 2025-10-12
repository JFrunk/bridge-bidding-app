from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.overcalls import OvercallModule
from engine.ai.conventions.takeout_doubles import TakeoutDoubleConvention
from engine.ai.conventions.negative_doubles import NegativeDoubleConvention
from engine.ai.conventions.michaels_cuebid import MichaelsCuebidConvention
from engine.ai.conventions.unusual_2nt import Unusual2NTConvention
from engine.ai.conventions.splinter_bids import SplinterBidsConvention
from engine.ai.conventions.fourth_suit_forcing import FourthSuitForcingConvention

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
        # Check if I'm the advancer (partner made an overcall or double)
        # This can be my first OR subsequent bid
        # Only advance if partner is NOT the opener (i.e., partner overcalled/doubled)
        partner_last_bid = auction['partner_last_bid']
        if (partner_last_bid and partner_last_bid not in ['Pass', 'XX'] and
            auction['opener_relationship'] != 'Partner'):
            # Partner overcalled or doubled - I'm the advancer
            return 'advancer_bids'

        # If it's my first bid after an opponent opened, I can overcall or double.
        if len(my_bids) == 0:
            # Check for Michaels Cuebid (5-5 two suits)
            michaels = MichaelsCuebidConvention()
            if michaels.evaluate(features['hand'], features): return 'michaels_cuebid'

            # Check for Unusual 2NT (5-5 both minors)
            unusual_2nt = Unusual2NTConvention()
            if unusual_2nt.evaluate(features['hand'], features): return 'unusual_2nt'

            overcall_specialist = OvercallModule()
            if overcall_specialist.evaluate(features['hand'], features): return 'overcalls'

            takeout_double_specialist = TakeoutDoubleConvention()
            if takeout_double_specialist.evaluate(features['hand'], features): return 'takeout_doubles'
        else: # My second+ bid in a competitive auction

            # Check if I'm in balancing seat (pass-out seat)
            # Last 2 bids were Pass, and my Pass would end the auction
            auction_history = features['auction_history']
            if len(auction_history) >= 2 and auction_history[-1] == 'Pass' and auction_history[-2] == 'Pass':
                # I'm in balancing/pass-out seat
                # Try to balance with an overcall or takeout double
                overcall_specialist = OvercallModule()
                if overcall_specialist.evaluate(features['hand'], features): return 'overcalls'

                takeout_double_specialist = TakeoutDoubleConvention()
                if takeout_double_specialist.evaluate(features['hand'], features): return 'takeout_doubles'

            # Otherwise, I passed initially and now competing
            # Can still try to overcall or double
            overcall_specialist = OvercallModule()
            if overcall_specialist.evaluate(features['hand'], features): return 'overcalls'

            takeout_double_specialist = TakeoutDoubleConvention()
            if takeout_double_specialist.evaluate(features['hand'], features): return 'takeout_doubles'

    # --- STATE 3: This is an UNCONTESTED PARTNERSHIP auction ---
    if auction['opener_relationship'] == 'Partner': # My partner opened
        # Check for slam conventions first
        blackwood = BlackwoodConvention()
        if blackwood.evaluate(features['hand'], features):
            return 'blackwood'

        # Check for Splinter bids (slam interest with shortness)
        splinter = SplinterBidsConvention()
        if splinter.evaluate(features['hand'], features):
            return 'splinter_bids'

        # Check for Fourth Suit Forcing
        fsf = FourthSuitForcingConvention()
        if fsf.evaluate(features['hand'], features):
            return 'fourth_suit_forcing'

        # Check for negative doubles (partner opened, opponent interfered)
        negative_double = NegativeDoubleConvention()
        if negative_double.evaluate(features['hand'], features):
            return 'negative_doubles'

        # Check for conventions over 1NT
        if auction['opening_bid'] == '1NT':
            jacoby = JacobyConvention()
            if jacoby.evaluate(features['hand'], features): return 'jacoby'
            stayman = StaymanConvention()
            if stayman.evaluate(features['hand'], features): return 'stayman'
        # Fallback to natural responses
        return 'responses'

    if auction['opener_relationship'] == 'Me': # I opened
        # Check for 1NT convention completions FIRST (before natural rebids)
        if auction['opening_bid'] == '1NT':
            jacoby = JacobyConvention()
            if jacoby.evaluate(features['hand'], features): return 'jacoby'
            stayman = StaymanConvention()
            if stayman.evaluate(features['hand'], features): return 'stayman'

        # Check for slam conventions
        blackwood = BlackwoodConvention()
        if blackwood.evaluate(features['hand'], features):
            return 'blackwood'
        # Fallback to natural rebids
        return 'openers_rebid'
            
    return 'pass_by_default'