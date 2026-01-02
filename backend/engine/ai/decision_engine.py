from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.ai.conventions.gerber import GerberConvention
from engine.ai.conventions.minor_suit_bust import MinorSuitBustConvention
from engine.ai.conventions.grand_slam_force import GrandSlamForceConvention
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

    # DEBUG: Log decision engine routing
    print(f"\n🎯 DECISION ENGINE for {my_pos_str}:")
    print(f"   Opener: {auction.get('opener')}")
    print(f"   Opener relationship: {auction.get('opener_relationship')}")
    print(f"   Partner last bid: {auction.get('partner_last_bid')}")
    print(f"   My bids so far: {my_bids}")
    print(f"   Auction: {features['auction_history']}")

    # --- STATE 1: Is this an OPENING situation? ---
    if not auction['opener']:
        print(f"   → Routing to: opening_bids (no opener yet)")
        # Priority for opening is to check for a preempt first.
        preempt_specialist = PreemptConvention()
        if preempt_specialist.evaluate(features['hand'], features):
            return 'preempts'
        return 'opening_bids'

    # --- STATE 2: Is this a COMPETITIVE situation? ---
    if auction['opener_relationship'] == 'Opponent':
        print(f"   → Competitive auction (opponent opened)")
        # Check if I'm the advancer (partner made an overcall or double)
        # This can be my first OR subsequent bid
        # Only advance if partner is NOT the opener (i.e., partner overcalled/doubled)
        partner_last_bid = auction['partner_last_bid']
        print(f"   → Checking advancer: partner_last_bid={partner_last_bid}, not in Pass/XX: {partner_last_bid not in ['Pass', 'XX'] if partner_last_bid else False}")
        if (partner_last_bid and partner_last_bid not in ['Pass', 'XX'] and
            auction['opener_relationship'] != 'Partner'):
            # Partner overcalled or doubled - I'm the advancer
            print(f"   → Routing to: advancer_bids")
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
        # PRIORITY 1: Check for Blackwood response FIRST (before responder_rebid)
        # This is critical - if partner asked 4NT Blackwood, we MUST respond with ace count
        blackwood = BlackwoodConvention()
        blackwood_result = blackwood.evaluate(features['hand'], features)
        if blackwood_result:
            return 'blackwood'

        # Check if this is responder's SECOND+ bid
        my_index = features['my_index']
        opener_index = auction.get('opener_index', -1)

        if opener_index != -1:
            my_bids_after_opening = [
                bid for i, bid in enumerate(features['auction_history'])
                if (i % 4) == my_index and i > opener_index and bid not in ['Pass', 'X', 'XX']
            ]

            # If I've already responded, use responder rebid module
            if len(my_bids_after_opening) >= 1:
                return 'responder_rebid'

        # Check for slam conventions first
        # Grand Slam Force (5NT) - check before Blackwood
        gsf = GrandSlamForceConvention()
        if gsf.evaluate(features['hand'], features):
            return 'grand_slam_force'

        # Gerber (4♣) is used over NT openings/rebids - check before Blackwood
        gerber = GerberConvention()
        if gerber.evaluate(features['hand'], features):
            return 'gerber'

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

        # Check for conventions over 1NT or 2NT
        if auction['opening_bid'] in ['1NT', '2NT']:
            jacoby = JacobyConvention()
            if jacoby.evaluate(features['hand'], features): return 'jacoby'
            stayman = StaymanConvention()
            if stayman.evaluate(features['hand'], features): return 'stayman'
            # Minor suit bust (2♠ relay for weak hands with long minor)
            minor_bust = MinorSuitBustConvention()
            if minor_bust.evaluate(features['hand'], features): return 'minor_suit_bust'
        # Fallback to natural responses (first response only)
        return 'responses'

    if auction['opener_relationship'] == 'Me': # I opened
        print(f"   → I am the opener (opener_relationship == 'Me')")

        # Check for 1NT/2NT/3NT convention responses FIRST (before Blackwood)
        # When I opened NT and partner bids 4♣, that's GERBER asking for aces
        # I must respond with ace count, NOT ask Blackwood myself
        if auction['opening_bid'] in ['1NT', '2NT', '3NT']:
            # Check Gerber (4♣ over NT) - MUST check before Blackwood
            # Partner's 4♣ over my NT is Gerber, I respond with ace count
            gerber = GerberConvention()
            if gerber.evaluate(features['hand'], features): return 'gerber'

        # PRIORITY 2: Check Blackwood signoff
        # After I asked 4NT Blackwood and partner responded with ace count,
        # I need to sign off or continue
        blackwood = BlackwoodConvention()
        blackwood_result = blackwood.evaluate(features['hand'], features)
        if blackwood_result:
            return 'blackwood'

        # Check for other 1NT/2NT convention completions (after Gerber check)
        if auction['opening_bid'] in ['1NT', '2NT', '3NT']:
            # Check Minor suit bust (opener responding to 2♠)
            minor_bust = MinorSuitBustConvention()
            if minor_bust.evaluate(features['hand'], features): return 'minor_suit_bust'
            jacoby = JacobyConvention()
            if jacoby.evaluate(features['hand'], features): return 'jacoby'
            stayman = StaymanConvention()
            if stayman.evaluate(features['hand'], features): return 'stayman'

        # Check for slam conventions
        # Grand Slam Force (5NT) - check before other slam conventions
        gsf = GrandSlamForceConvention()
        if gsf.evaluate(features['hand'], features):
            return 'grand_slam_force'

        # Gerber for NT auctions (if not already handled above)
        gerber = GerberConvention()
        if gerber.evaluate(features['hand'], features):
            return 'gerber'
        # Fallback to natural rebids
        print(f"   → Routing to: openers_rebid")
        return 'openers_rebid'

    print(f"   → No routing found, defaulting to: pass_by_default")
    return 'pass_by_default'