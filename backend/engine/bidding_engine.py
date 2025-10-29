from engine.hand import Hand
from engine.ai.feature_extractor import extract_features
from engine.ai.decision_engine import select_bidding_module
from engine.ai.bid_explanation import BidExplanation, ExplanationLevel
from engine.ai.module_registry import ModuleRegistry
from engine.ai.validation_pipeline import ValidationPipeline

# Import all specialist modules (triggers auto-registration)
# ADR-0002 Phase 1: Modules now register themselves on import
from engine.opening_bids import OpeningBidsModule
from engine.responses import ResponseModule
from engine.responder_rebids import ResponderRebidModule
from engine.rebids import RebidModule
from engine.advancer_bids import AdvancerBidsModule
from engine.overcalls import OvercallModule
from engine.ai.conventions.stayman import StaymanConvention
from engine.ai.conventions.jacoby_transfers import JacobyConvention
from engine.ai.conventions.preempts import PreemptConvention
from engine.ai.conventions.blackwood import BlackwoodConvention
from engine.ai.conventions.takeout_doubles import TakeoutDoubleConvention
from engine.ai.conventions.negative_doubles import NegativeDoubleConvention
from engine.ai.conventions.michaels_cuebid import MichaelsCuebidConvention
from engine.ai.conventions.unusual_2nt import Unusual2NTConvention
from engine.ai.conventions.splinter_bids import SplinterBidsConvention
from engine.ai.conventions.fourth_suit_forcing import FourthSuitForcingConvention

class BiddingEngine:
    def __init__(self):
        # ADR-0002 Phase 1: Use ModuleRegistry instead of manual registration
        # All modules auto-register on import, so we just get the registry
        self.modules = ModuleRegistry.get_all()

        # ADR-0002 Phase 2: Initialize validation pipeline
        self.validation_pipeline = ValidationPipeline()

        # Verify all expected modules are registered
        expected_modules = [
            'opening_bids', 'responses', 'openers_rebid', 'responder_rebid',
            'advancer_bids', 'overcalls', 'stayman', 'jacoby', 'preempts',
            'blackwood', 'takeout_doubles', 'negative_doubles',
            'michaels_cuebid', 'unusual_2nt', 'splinter_bids', 'fourth_suit_forcing'
        ]

        missing = [name for name in expected_modules if not ModuleRegistry.exists(name)]
        if missing:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Missing bidding modules: {missing}")
            logger.warning(f"Registered modules: {ModuleRegistry.list_modules()}")

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

        # ADR-0002 Phase 1: Use ModuleRegistry for safe module lookup
        specialist = ModuleRegistry.get(module_name)
        if specialist is None:
            # Graceful fallback when module not found
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Module '{module_name}' not found in registry. "
                f"Available: {ModuleRegistry.list_modules()}"
            )
            return ("Pass", "No appropriate bid found.")

        result = specialist.evaluate(hand, features)
        if result:
            bid_to_check = result[0]
            explanation = result[1]

            # ADR-0002 Phase 2: MANDATORY validation pipeline
            # This CANNOT be bypassed - all bids must pass validation
            is_valid, validation_error = self.validation_pipeline.validate(
                bid_to_check, hand, features, auction_history
            )

            if not is_valid:
                # Validation failed - graceful fallback to Pass
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Validation failed for {module_name} bid '{bid_to_check}': {validation_error}"
                )
                return ("Pass", "No appropriate bid found.")

            # Legacy legality check (kept for backward compatibility)
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

        return ("Pass", "No appropriate bid found.")

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