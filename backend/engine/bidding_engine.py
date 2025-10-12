from engine.hand import Hand
from engine.ai.feature_extractor import extract_features
from engine.ai.decision_engine import select_bidding_module
from engine.ai.bid_explanation import BidExplanation, ExplanationLevel

# Import all specialist CLASSES
from engine.opening_bids import OpeningBidsModule
from engine.responses import ResponseModule
from engine.rebids import RebidModule
from engine.advancer_bids import AdvancerBidsModule
from engine.overcalls import OvercallModule
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.ai.conventions.takeout_doubles import TakeoutDoubleConvention
from engine.ai.conventions.negative_doubles import NegativeDoubleConvention

class BiddingEngine:
    def __init__(self):
        # Create an instance of every specialist and store it in a dictionary
        self.modules = {
            'opening_bids': OpeningBidsModule(),
            'responses': ResponseModule(),
            'openers_rebid': RebidModule(),
            'responder_rebid': ResponseModule(),
            'advancer_bids': AdvancerBidsModule(),
            'overcalls': OvercallModule(),
            'stayman': StaymanConvention(),
            'jacoby': JacobyConvention(),
            'preempts': PreemptConvention(),
            'blackwood': BlackwoodConvention(),
            'takeout_doubles': TakeoutDoubleConvention(),
            'negative_doubles': NegativeDoubleConvention(),
        }

    def get_next_bid(self, hand: Hand, auction_history: list, my_position: str, vulnerability: str,
                     explanation_level: str = "detailed"):
        """
        Get the next bid from the AI.

        Args:
            hand: The hand to bid with
            auction_history: List of previous bids
            my_position: Position of this player (North/East/South/West)
            vulnerability: Vulnerability status
            explanation_level: Level of detail ("simple", "detailed", or "expert")

        Returns:
            Tuple of (bid, explanation_string)
        """
        features = extract_features(hand, auction_history, my_position, vulnerability)
        module_name = select_bidding_module(features)

        if module_name == 'pass_by_default':
            return ("Pass", "No bid found by any module.")

        specialist = self.modules.get(module_name)
        if specialist:
            result = specialist.evaluate(hand, features)
            if result:
                # Universal Legality Check (Safety Net)
                bid_to_check = result[0]
                explanation = result[1]

                if self._is_bid_legal(bid_to_check, auction_history):
                    # Convert BidExplanation to string if needed
                    if isinstance(explanation, BidExplanation):
                        # Format at requested level
                        try:
                            level_enum = ExplanationLevel(explanation_level)
                        except ValueError:
                            level_enum = ExplanationLevel.DETAILED
                        return (bid_to_check, explanation.format(level_enum))
                    else:
                        # Legacy string explanation
                        return result
                else:
                    print(f"WARNING: AI module '{module_name}' suggested illegal bid '{bid_to_check}'. Overriding to Pass.")
                    return ("Pass", "AI bid overridden due to illegality.")

        return ("Pass", f"Logic error: DecisionEngine chose '{module_name}' but it was not found or returned no bid.")

    def get_next_bid_structured(self, hand: Hand, auction_history: list, my_position: str, vulnerability: str):
        """
        Get the next bid with structured explanation data (for JSON API).

        Returns:
            Tuple of (bid, explanation_dict)
        """
        features = extract_features(hand, auction_history, my_position, vulnerability)
        module_name = select_bidding_module(features)

        if module_name == 'pass_by_default':
            return ("Pass", {"bid": "Pass", "primary_reason": "No bid found by any module."})

        specialist = self.modules.get(module_name)
        if specialist:
            result = specialist.evaluate(hand, features)
            if result:
                bid_to_check = result[0]
                explanation = result[1]

                if self._is_bid_legal(bid_to_check, auction_history):
                    if isinstance(explanation, BidExplanation):
                        return (bid_to_check, explanation.to_dict())
                    else:
                        # Legacy string - wrap in simple dict
                        return (bid_to_check, {
                            "bid": bid_to_check,
                            "primary_reason": explanation
                        })
                else:
                    print(f"WARNING: AI module '{module_name}' suggested illegal bid '{bid_to_check}'. Overriding to Pass.")
                    return ("Pass", {"bid": "Pass", "primary_reason": "AI bid overridden due to illegality."})

        return ("Pass", {
            "bid": "Pass",
            "primary_reason": f"Logic error: DecisionEngine chose '{module_name}' but it was not found or returned no bid."
        })

    def _is_bid_legal(self, bid: str, auction_history: list) -> bool:
        """Universal check to ensure an AI bid is legal."""
        if bid in ['Pass', 'X', 'XX']: return True
        last_real_bid = next((b for b in reversed(auction_history) if b not in ['Pass', 'X', 'XX']), None)
        if not last_real_bid: return True
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}
        try:
            my_level, my_suit = int(bid[0]), bid[1:]
            last_level, last_suit = int(last_real_bid[0]), last_real_bid[1:]
            if my_level > last_level: return True
            if my_level == last_level and suit_rank.get(my_suit, 0) > suit_rank.get(last_suit, 0): return True
        except (ValueError, IndexError):
            return False
        return False