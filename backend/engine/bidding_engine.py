from engine.hand import Hand
from engine.ai.feature_extractor import extract_features
from engine.ai.decision_engine import select_bidding_module
from engine.ai.bid_explanation import BidExplanation, ExplanationLevel
from engine.ai.module_registry import ModuleRegistry
from engine.ai.validation_pipeline import ValidationPipeline
from engine.ai.sanity_checker import SanityChecker
from engine.ai.auction_context import analyze_auction_context

# Import all specialist modules (triggers auto-registration)
# ADR-0002 Phase 1: Modules now register themselves on import
from engine.opening_bids import OpeningBidsModule
from engine.responses import ResponseModule
from engine.responder_rebids import ResponderRebidModule
from engine.rebids import RebidModule
from engine.advancer_bids import AdvancerBidsModule
from engine.overcalls import OvercallModule
from engine.balancing import BalancingModule
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
from engine.ai.conventions.gerber import GerberConvention
from engine.ai.conventions.minor_suit_bust import MinorSuitBustConvention
from engine.ai.conventions.grand_slam_force import GrandSlamForceConvention

class BiddingEngine:
    def __init__(self):
        # ADR-0002 Phase 1: Use ModuleRegistry instead of manual registration
        # All modules auto-register on import, so we just get the registry
        self.modules = ModuleRegistry.get_all()

        # ADR-0002 Phase 2: Initialize validation pipeline
        self.validation_pipeline = ValidationPipeline()

        # ADR-0002 Phase 3: Initialize sanity checker
        self.sanity_checker = SanityChecker()

        # Last-computed features from get_next_bid (for belief serialization)
        self.last_features = None

        # Verify all expected modules are registered
        expected_modules = [
            'opening_bids', 'responses', 'openers_rebid', 'responder_rebid',
            'advancer_bids', 'overcalls', 'balancing', 'stayman', 'jacoby', 'preempts',
            'blackwood', 'gerber', 'grand_slam_force', 'minor_suit_bust',
            'takeout_doubles', 'negative_doubles',
            'michaels_cuebid', 'unusual_2nt', 'splinter_bids', 'fourth_suit_forcing'
        ]

        missing = [name for name in expected_modules if not ModuleRegistry.exists(name)]
        if missing:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Missing bidding modules: {missing}")
            logger.warning(f"Registered modules: {ModuleRegistry.list_modules()}")

    def get_next_bid(self, hand: Hand, auction_history: list, my_position: str, vulnerability: str,
                     explanation_level: str = "detailed", dealer: str = None):
        """
        Get the next bid from the AI.

        Args:
            hand: The hand to bid with
            auction_history: List of previous bids (starting from dealer)
            my_position: Position of this player (North/East/South/West)
            vulnerability: Vulnerability status
            explanation_level: Level of detail ("simple", "detailed", or "expert")
            dealer: Who dealt the hand (default: inferred from auction length + my_position)

        Returns:
            Tuple of (bid, explanation_string)
        """
        import time

        # Infer dealer if not provided (for backward compatibility)
        if dealer is None:
            # Dealer is determined by: auction_history[0] was made by dealer
            # Current bidder is at position len(auction_history) from dealer
            # So dealer = my_position - len(auction_history) % 4
            base_positions = ['North', 'East', 'South', 'West']
            my_idx = base_positions.index(my_position)
            dealer_idx = (my_idx - len(auction_history)) % 4
            dealer = base_positions[dealer_idx]

        # Time feature extraction
        t0 = time.time()
        features = extract_features(hand, auction_history, my_position, vulnerability, dealer)
        self.last_features = features
        t1 = time.time()
        feature_time = (t1 - t0) * 1000

        # Time module selection
        module_name = select_bidding_module(features)
        t2 = time.time()
        module_selection_time = (t2 - t1) * 1000

        # print(f"  ├─ Feature extraction: {feature_time:.1f}ms")
        # print(f"  ├─ Module selection: {module_selection_time:.1f}ms → {module_name}")

        if module_name == 'pass_by_default':
            # SAFETY NET: Check if we should override Pass due to game-forcing values
            should_override, game_bid, explanation = self._game_forcing_safety_net(hand, features, auction_history)
            if should_override:
                return (game_bid, explanation)
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
            # SAFETY NET: Check if we should override Pass due to game-forcing values
            should_override, game_bid, explanation = self._game_forcing_safety_net(hand, features, auction_history)
            if should_override:
                return (game_bid, explanation)
            return ("Pass", "No appropriate bid found.")

        # Time module evaluation
        t3 = time.time()
        result = specialist.evaluate(hand, features)
        t4 = time.time()
        evaluation_time = (t4 - t3) * 1000
        # print(f"  ├─ Module evaluation ({module_name}): {evaluation_time:.1f}ms")

        if result:
            bid_to_check = result[0]
            explanation = result[1]
            # Convention modules can optionally return metadata in 3rd tuple element
            metadata = result[2] if len(result) > 2 else None

            # ADR-0002 Phase 2: MANDATORY validation pipeline
            # This CANNOT be bypassed - all bids must pass validation
            # Metadata can request bypassing specific validators for artificial bids
            t5 = time.time()
            is_valid, validation_error = self.validation_pipeline.validate(
                bid_to_check, hand, features, auction_history, metadata
            )
            t6 = time.time()
            validation_time = (t6 - t5) * 1000
            # print(f"  ├─ Validation: {validation_time:.1f}ms")

            if not is_valid:
                # Validation failed - graceful fallback to Pass
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Validation failed for {module_name} bid '{bid_to_check}': {validation_error}"
                )
                # SAFETY NET: Check if we should override Pass due to game-forcing values
                should_override, game_bid, explanation = self._game_forcing_safety_net(hand, features, auction_history)
                if should_override:
                    return (game_bid, explanation)
                return ("Pass", "No appropriate bid found.")

            # ADR-0002 Phase 3: Sanity check layer
            # Final safety net to prevent impossible contracts
            t7 = time.time()
            should_bid, final_bid, sanity_reason = self.sanity_checker.check(
                bid_to_check, hand, features, auction_history, metadata
            )
            t8 = time.time()
            sanity_time = (t8 - t7) * 1000
            # print(f"  └─ Sanity check: {sanity_time:.1f}ms")

            if not should_bid:
                # Sanity check prevented bid - use fallback
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Sanity check prevented {module_name} bid '{bid_to_check}': {sanity_reason}"
                )
                return (final_bid, "No appropriate bid found.")

            # Legacy legality check (kept for backward compatibility)
            if self._is_bid_legal(bid_to_check, auction_history):
                # CRITICAL: If module returned Pass, check game-forcing safety net FIRST!
                # This catches cases where modules pass when they shouldn't (game forcing situations)
                if bid_to_check == 'Pass':
                    should_override, game_bid, override_explanation = self._game_forcing_safety_net(hand, features, auction_history)
                    if should_override:
                        return (game_bid, override_explanation)

                # SLAM EXPLORATION SAFETY NET (re-enabled with BiddingState)
                # Uses per-seat beliefs for accurate combined HCP — guards prevent
                # the old AuctionContext inflation issues (requires BiddingState,
                # 16+ own HCP, partner 10+ min, 33+ combined midpoint).
                if self._is_game_bid(bid_to_check) and not self._is_slam_bid(bid_to_check):
                    should_explore, slam_bid, slam_explanation = self._slam_exploration_safety_net(hand, features, auction_history, bid_to_check)
                    if should_explore:
                        return (slam_bid, slam_explanation)

                # Convert BidExplanation to string if needed
                if isinstance(explanation, BidExplanation):
                    # Format at requested level
                    try:
                        level_enum = ExplanationLevel(explanation_level)
                    except ValueError:
                        level_enum = ExplanationLevel.DETAILED
                    return (bid_to_check, explanation.format(level_enum))
                else:
                    # Legacy string explanation - strip metadata, return only (bid, explanation)
                    return (bid_to_check, explanation)
            else:
                print(f"WARNING: AI module '{module_name}' suggested illegal bid '{bid_to_check}'. Overriding to Pass.")
                # SAFETY NET: Check if we should override Pass due to game-forcing values
                should_override, game_bid, explanation = self._game_forcing_safety_net(hand, features, auction_history)
                if should_override:
                    return (game_bid, explanation)
                return ("Pass", "AI bid overridden due to illegality.")

        # Module returned None - SAFETY NET check
        should_override, game_bid, explanation = self._game_forcing_safety_net(hand, features, auction_history)
        if should_override:
            return (game_bid, explanation)
        return ("Pass", "No appropriate bid found.")

    def get_next_bid_structured(self, hand: Hand, auction_history: list, my_position: str, vulnerability: str,
                                  dealer: str = None):
        """
        Get the next bid with structured explanation data (for JSON API).

        Returns:
            Tuple of (bid, explanation_dict)
        """
        # Infer dealer if not provided (for backward compatibility)
        if dealer is None:
            base_positions = ['North', 'East', 'South', 'West']
            my_idx = base_positions.index(my_position)
            dealer_idx = (my_idx - len(auction_history)) % 4
            dealer = base_positions[dealer_idx]

        features = extract_features(hand, auction_history, my_position, vulnerability, dealer)
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

    def _game_forcing_safety_net(self, hand: Hand, features: dict, auction_history: list) -> tuple:
        """
        SAFETY NET: Prevent Pass when game-forcing values are established.

        This is the LAST RESORT when all modules return None or Pass.
        If the partnership has established game values (25+ combined HCP or
        game_forcing flag is set), we MUST bid something toward game.

        Works for BOTH responder AND opener:
        - If I'm responder: Check if we have 25+ combined or game_forcing
        - If I'm opener: Check if partner's response shows enough for game, or if 2♣ opening

        Returns:
            (should_override, bid, explanation) - bid to make instead of Pass
        """
        import logging
        logger = logging.getLogger(__name__)

        auction = features.get('auction_features', {})
        opener_rel = auction.get('opener_relationship')
        
        # Only applies to partnership auctions (I opened or partner opened)
        if opener_rel not in ['Partner', 'Me']:
            return (False, None, None)

        # Check if game is already reached
        for bid in auction_history:
            if self._is_game_bid(bid):
                return (False, None, None)  # Game already reached

        # Analyze auction context for game-forcing status
        try:
            positions = features.get('positions', ['North', 'East', 'South', 'West'])
            my_index = features.get('my_index', 0)
            context = analyze_auction_context(auction_history, positions, my_index)

            # CORRECT CALCULATION: Use my ACTUAL HCP instead of my range midpoint
            my_hcp = hand.hcp
            
            # Get partner's estimated HCP
            if opener_rel == 'Me':
                # I am opener, partner is responder
                partner_min, partner_max = context.ranges.responder_hcp
            else:
                # I am responder, partner is opener
                partner_min, partner_max = context.ranges.opener_hcp
                
            # Cap partner's specific max for estimation purposes if they are unlimited
            # (Prevent assuming 23 HCP just because range is 6-40)
            calc_partner_max = min(partner_max, 20)  # Cap at 20 for estimation
            
            partner_midpoint = (partner_min + calc_partner_max) / 2
            combined_pts = int(my_hcp + partner_midpoint)
            
            game_forcing = context.ranges.game_forcing
            opening_bid = auction.get('opening_bid', '')

            # SPECIAL CASE: 2♣ opening is ALWAYS game-forcing until game is reached (usually)
            if opener_rel == 'Me' and opening_bid == '2♣':
                partner_responded = any(bid != 'Pass' for i, bid in enumerate(auction_history) 
                                       if i % 2 == 1)
                if partner_responded:
                    game_forcing = True
            
            # SPECIAL CASE: Partner's 2NT response shows 11-12 HCP
            # Only after suit openings (1♣/1♦/1♥/1♠) — NOT after 1NT/2NT openings
            # where 2NT is an invitation (8-9 HCP), not a game-force
            if (opener_rel == 'Me' and auction.get('partner_last_bid') == '2NT'
                    and opening_bid not in ['1NT', '2NT', '3NT']):
                if my_hcp >= 14:  # 14 + 11 = 25
                    combined_pts = max(combined_pts, 25)

            # Only intervene if game values are present
            if not game_forcing and combined_pts < 25:
                return (False, None, None)

            logger.info(f"GAME SAFETY NET: combined={combined_pts}, game_forcing={game_forcing}, opener_rel={opener_rel}")

            # Find the best game bid to make
            game_bid = self._find_best_game_bid(hand, features, auction_history, context)

            if game_bid and self._is_bid_legal(game_bid, auction_history):
                # Suppress high-level bids without slam values
                game_bid_level = int(game_bid[0]) if game_bid[0].isdigit() else 0
                if game_bid_level >= 5 and combined_pts < 33:
                    logger.info(f"GAME SAFETY NET: Suppressed {game_bid} (5+ level needs 33, have {combined_pts})")
                    return (False, None, None)
                if game_bid == '4NT' and combined_pts < 33:
                    logger.info(f"GAME SAFETY NET: Suppressed 4NT (slam exploration needs 33, have {combined_pts})")
                    return (False, None, None)

                explanation = f"Game safety net: Partnership has ~{combined_pts} combined points, must reach game."
                logger.info(f"GAME SAFETY NET: Overriding Pass with {game_bid}")
                return (True, game_bid, explanation)

        except Exception as e:
            logger.debug(f"Error in game safety net: {e}")

        return (False, None, None)

    def _find_best_game_bid(self, hand: Hand, features: dict, auction_history: list, context) -> str:
        """Find the best game contract to bid."""
        auction = features.get('auction_features', {})
        opener_rel = auction.get('opener_relationship')
        partner_suit = None
        my_suit = None

        # Check if partner showed a suit
        partner_last = auction.get('partner_last_bid', '')
        if partner_last and len(partner_last) >= 2 and partner_last[1] in '♠♥♦♣':
            partner_suit = partner_last[1]

        # Check my opening suit (if I'm opener)
        opening_bid = auction.get('opening_bid', '')
        if opener_rel == 'Me' and opening_bid and len(opening_bid) >= 2 and opening_bid[1] in '♠♥♦♣':
            my_suit = opening_bid[1]

        # If I opened a major and partner supported it
        if my_suit in ['♥', '♠']:
            # Check if partner raised
            if partner_last and len(partner_last) >= 2 and partner_last[1] == my_suit:
                game_bid = f"4{my_suit}"
                if self._is_bid_legal(game_bid, auction_history):
                    return game_bid
            # Even without explicit raise, bid my major if long enough
            if hand.suit_lengths.get(my_suit, 0) >= 6:
                game_bid = f"4{my_suit}"
                if self._is_bid_legal(game_bid, auction_history):
                    return game_bid

        # If partner showed a major and we have support, bid game in that major
        if partner_suit in ['♥', '♠']:
            support = hand.suit_lengths.get(partner_suit, 0)
            if support >= 2:
                game_bid = f"4{partner_suit}"
                if self._is_bid_legal(game_bid, auction_history):
                    return game_bid

        # Check our own longest major (5+ cards)
        if hand.suit_lengths.get('♠', 0) >= 5:
            if self._is_bid_legal('4♠', auction_history):
                return '4♠'
        if hand.suit_lengths.get('♥', 0) >= 5:
            if self._is_bid_legal('4♥', auction_history):
                return '4♥'

        # Default to 3NT for game
        if self._is_bid_legal('3NT', auction_history):
            return '3NT'

        # If 3NT isn't legal (auction is higher), DON'T escalate to 4NT/5m
        # from the safety net — those levels require slam values which are
        # checked separately. The safety net's job is to reach game, not push past it.
        return None

    def _is_game_bid(self, bid: str) -> bool:
        """Check if a bid is at game level or higher."""
        if not bid or bid in ['Pass', 'X', 'XX']:
            return False
        try:
            level = int(bid[0])
            strain = bid[1:] if len(bid) > 1 else ''
            if level >= 5:
                return True
            if level == 4 and strain in ['♥', '♠', 'NT']:
                return True
            if level >= 3 and strain == 'NT':
                return True
        except (ValueError, IndexError):
            return False
        return False

    def _is_slam_bid(self, bid: str) -> bool:
        """Check if a bid is at slam level (6 or 7)."""
        if not bid or bid in ['Pass', 'X', 'XX']:
            return False
        try:
            level = int(bid[0])
            return level >= 6
        except (ValueError, IndexError):
            return False

    def _slam_exploration_safety_net(self, hand: Hand, features: dict, auction_history: list, original_bid: str = '3NT') -> tuple:
        """
        SLAM EXPLORATION SAFETY NET: Intercept game bids when slam values exist.

        Uses BiddingState per-seat beliefs for accurate combined HCP estimation.
        Only triggers when BiddingState is available — no fallback to AuctionContext
        (which had inflated estimates causing inappropriate Blackwood).

        Requirements for slam exploration:
        1. BiddingState available with per-seat beliefs
        2. Combined HCP midpoint >= 33
        3. Own hand has 16+ HCP
        4. Partner has shown 10+ HCP minimum
        5. Blackwood hasn't already been used
        6. 4NT is a legal bid (or direct slam with 2+ aces)

        Args:
            original_bid: The game bid that was about to be made

        Returns:
            (should_explore, bid, explanation) - bid to make instead of game
        """
        import logging
        logger = logging.getLogger(__name__)

        auction = features.get('auction_features', {})
        opener_rel = auction.get('opener_relationship')

        # Only applies to partnership auctions (I opened or partner opened)
        if opener_rel not in ['Partner', 'Me']:
            return (False, None, None)

        # Check if Blackwood has already been used
        if '4NT' in auction_history:
            return (False, None, None)

        # Check if slam has already been reached
        for bid in auction_history:
            if bid and len(bid) >= 1 and bid[0].isdigit():
                try:
                    level = int(bid[0])
                    if level >= 6:
                        return (False, None, None)
                except ValueError:
                    pass

        # Require BiddingState for accurate estimation (no AuctionContext fallback)
        bidding_state = features.get('bidding_state')
        if bidding_state is None:
            return (False, None, None)

        positions = features.get('positions', [])
        my_index = features.get('my_index')
        if not positions or my_index is None:
            return (False, None, None)

        from utils.seats import normalize
        my_seat = normalize(positions[my_index])
        partner_belief = bidding_state.partner_of(my_seat)
        partner_mid = (partner_belief.hcp[0] + partner_belief.hcp[1]) // 2
        combined_hcp = hand.hcp + partner_mid

        # Must have 16+ own HCP to trigger slam exploration
        if hand.hcp < 16:
            return (False, None, None)

        # Partner must have shown 10+ HCP minimum (prevents triggering over weak responses)
        if partner_belief.hcp[0] < 10:
            return (False, None, None)

        # When partner range is wide, use a higher threshold
        # because the midpoint is unreliable — partner could easily be near minimum
        # spread 0-5: reliable, use 33; spread 6-7: use 34; spread 8+: use 35
        partner_spread = partner_belief.hcp[1] - partner_belief.hcp[0]
        if partner_spread >= 8:
            slam_threshold = 35
        elif partner_spread >= 6:
            slam_threshold = 34
        else:
            slam_threshold = 33

        # Combined HCP midpoint must meet slam threshold
        if combined_hcp < slam_threshold:
            return (False, None, None)

        # Check if 4NT is legal → explore via Blackwood
        if self._is_bid_legal('4NT', auction_history):
            logger.info(f"SLAM SAFETY NET: combined={combined_hcp}, my_hcp={hand.hcp}, partner~{partner_mid} - exploring slam instead of {original_bid}")
            explanation = (f"Slam safety net: {combined_hcp} combined HCP "
                          f"(my {hand.hcp} + partner ~{partner_mid}). "
                          f"Exploring slam with Blackwood instead of {original_bid}.")
            return (True, '4NT', explanation)

        # Past 4NT → bid 6-level directly if we have 2+ aces
        trump_suit = original_bid[1:] if len(original_bid) > 1 else 'NT'
        slam_bid = f"6{trump_suit}"
        if self._is_bid_legal(slam_bid, auction_history):
            my_aces = sum(1 for card in hand.cards if card.rank == 'A')
            if my_aces >= 2:
                logger.info(f"SLAM SAFETY NET: combined={combined_hcp}, my_hcp={hand.hcp}, {my_aces} aces - bidding {slam_bid} directly")
                explanation = (f"Slam safety net: {combined_hcp} combined HCP "
                              f"with {my_aces} aces. Bidding {slam_bid} directly.")
                return (True, slam_bid, explanation)

        return (False, None, None)