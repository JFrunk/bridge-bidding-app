"""
BiddingEngineV2 - Refactored Bidding Engine with Explicit State Machine

This is a ground-up reimplementation of the bidding engine designed to address
the architectural issues identified in the SAYC improvement analysis:

1. EXPLICIT STATE MACHINE - Clear bidding states instead of implicit if/else chains
2. FORCING SEQUENCE TRACKING - First-class support for game-forcing and one-round forcing
3. BALANCING SEAT HANDLING - Proper HCP adjustments for pass-out positions
4. SEPARATED CONCERNS - applies() vs evaluate() to avoid double evaluation
5. GROUND TRUTH VALIDATION - Built-in hooks for SAYC compliance testing

Usage:
    # Can be used as drop-in replacement for BiddingEngine
    from engine.bidding_engine_v2 import BiddingEngineV2

    engine = BiddingEngineV2()
    bid, explanation = engine.get_next_bid(hand, auction_history, position, vulnerability)

Configuration:
    Set USE_V2_BIDDING_ENGINE=true environment variable to enable in production.

Comparison Mode:
    engine = BiddingEngineV2(comparison_mode=True)
    # Will log discrepancies with V1 for analysis

Author: Claude Code
Date: 2026-01-03
"""

import logging
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any

from engine.hand import Hand
from engine.ai.feature_extractor import extract_features
from engine.ai.bid_explanation import BidExplanation

logger = logging.getLogger(__name__)


# =============================================================================
# BIDDING STATE MACHINE
# =============================================================================

class BiddingState(Enum):
    """
    Explicit states in the bidding auction.

    This replaces the implicit state detection in decision_engine.py
    with clear, documented states.
    """
    # Opening states
    OPENING = auto()              # No one has bid yet, considering opening

    # Responder states (partner opened)
    RESPONDING = auto()           # Partner opened, my first response
    RESPONDER_REBID = auto()      # Partner opened, my second+ bid

    # Opener states (I opened)
    OPENER_REBID = auto()         # I opened, making my rebid
    OPENER_THIRD_BID = auto()     # I opened, making third+ bid

    # Competitive states (opponent opened)
    DIRECT_SEAT = auto()          # Opponent opened, I'm in direct position
    BALANCING_SEAT = auto()       # Opponent opened, two passes, I'm in passout seat
    ADVANCING = auto()            # Partner overcalled/doubled, I'm advancing

    # Special states
    GAME_FORCING = auto()         # Auction is game-forcing, must reach game
    SLAM_EXPLORATION = auto()     # Exploring slam possibilities
    SIGNOFF = auto()              # Trying to end the auction

    # Terminal
    PASSED_OUT = auto()           # Four passes, auction over


class ForcingStatus(Enum):
    """Forcing nature of the current auction."""
    NON_FORCING = auto()
    ONE_ROUND_FORCING = auto()
    GAME_FORCING = auto()
    SLAM_FORCING = auto()


@dataclass
class AuctionState:
    """
    Complete state of the auction for decision making.

    This is computed once and passed to all modules, avoiding
    the repeated computation in the current architecture.
    """
    # Current state in the state machine
    state: BiddingState

    # Forcing status
    forcing: ForcingStatus
    forcing_source: Optional[str] = None
    must_bid: bool = False
    minimum_level: int = 0

    # Partnership info
    opener_relationship: Optional[str] = None  # 'Me', 'Partner', 'Opponent', None
    agreed_suit: Optional[str] = None
    fit_confirmed: bool = False

    # Balancing adjustments
    is_balancing: bool = False
    hcp_adjustment: int = 0

    # Bid counts
    my_bid_count: int = 0
    partner_bid_count: int = 0

    # Key bids
    opening_bid: Optional[str] = None
    partner_last_bid: Optional[str] = None
    my_last_bid: Optional[str] = None

    # Raw features (for modules that need detailed access)
    features: Dict = field(default_factory=dict)


# =============================================================================
# BIDDING ENGINE V2
# =============================================================================

class BiddingEngineV2:
    """
    Refactored bidding engine with explicit state machine.

    Key improvements over V1:
    1. State is computed once, not repeatedly
    2. Clear state machine instead of nested if/else
    3. Modules are selected based on state, not re-evaluated
    4. Forcing sequences are tracked explicitly
    5. Comparison mode for safe migration
    """

    def __init__(self, comparison_mode: bool = False):
        """
        Initialize the V2 bidding engine.

        Args:
            comparison_mode: If True, also runs V1 and logs discrepancies
        """
        self.comparison_mode = comparison_mode
        self._v1_engine = None  # Lazy load for comparison mode

        # Module registry - will be populated with V2-compatible modules
        self.modules: Dict[str, Any] = {}

        # Statistics for monitoring
        self.stats = {
            'total_bids': 0,
            'v1_matches': 0,
            'v1_discrepancies': 0,
            'state_distribution': {},
            'avg_time_ms': 0,
        }

        # Initialize modules
        self._initialize_modules()

    def _initialize_modules(self):
        """
        Initialize bidding modules.

        For now, we reuse V1 modules but with proper state-based routing.
        Future: Create V2-native modules with applies() methods.
        """
        # Import V1 modules for initial compatibility
        from engine.ai.module_registry import ModuleRegistry
        
        # Explicitly import modules to trigger auto-registration
        import engine.opening_bids
        import engine.responses
        import engine.rebids
        import engine.responder_rebids
        import engine.overcalls
        import engine.advancer_bids
        import engine.balancing
        import engine.bid_safety

        # Import Conventions
        import engine.ai.conventions.blackwood
        import engine.ai.conventions.stayman
        import engine.ai.conventions.jacoby_transfers
        import engine.ai.conventions.preempts
        import engine.ai.conventions.michaels_cuebid
        import engine.ai.conventions.unusual_2nt
        import engine.ai.conventions.takeout_doubles
        import engine.ai.conventions.fourth_suit_forcing
        import engine.ai.conventions.gerber
        import engine.ai.conventions.grand_slam_force
        import engine.ai.conventions.minor_suit_bust
        import engine.ai.conventions.negative_doubles
        import engine.ai.conventions.splinter_bids
        
        self.modules = ModuleRegistry.get_all()

        logger.info(f"BiddingEngineV2 initialized with {len(self.modules)} modules")

    def get_next_bid(
        self,
        hand: Hand,
        auction_history: list,
        my_position: str,
        vulnerability: str,
        explanation_level: str = "detailed",
        dealer: str = None
    ) -> Tuple[str, str]:
        """
        Get the next bid from the AI.

        This is the main entry point, compatible with BiddingEngine V1.

        Args:
            hand: The hand to bid with
            auction_history: List of previous bids (starting from dealer)
            my_position: Position of this player (North/East/South/West)
            vulnerability: Vulnerability status
            explanation_level: Level of detail ("simple", "detailed", or "expert")
            dealer: Who dealt the hand (default: inferred from auction length)

        Returns:
            Tuple of (bid, explanation_string)
        """
        start_time = time.time()

        # Infer dealer if not provided
        if dealer is None:
            dealer = self._infer_dealer(my_position, len(auction_history))

        # Step 1: Extract features (reuse V1 feature extractor)
        features = extract_features(hand, auction_history, my_position, vulnerability, dealer)

        # Step 2: Compute auction state (NEW - explicit state machine)
        auction_state = self._compute_auction_state(hand, features)

        # Log state for debugging
        logger.debug(
            f"\n🎯 BIDDING ENGINE V2:\n"
            f"   State: {auction_state.state.name}\n"
            f"   Forcing: {auction_state.forcing.name}\n"
            f"   Opener: {auction_state.opener_relationship}\n"
            f"   Balancing: {auction_state.is_balancing} (adj: {auction_state.hcp_adjustment})\n"
            f"   Auction: {auction_history}"
        )

        # Step 3: Select module based on state
        module_name = self._select_module_for_state(auction_state, hand)

        # Step 4: Get bid from module
        bid, explanation = self._get_bid_from_module(module_name, hand, features, auction_history)

        # Step 5: Apply safety nets
        bid, explanation = self._apply_safety_nets(bid, explanation, hand, auction_state, auction_history)

        # Step 6: Validate bid
        if not self._is_bid_legal(bid, auction_history):
            logger.warning(f"Illegal bid {bid} from {module_name}, falling back to Pass")
            bid, explanation = "Pass", "No legal bid found."

        # Step 7: Comparison mode (if enabled)
        if self.comparison_mode:
            self._compare_with_v1(hand, auction_history, my_position, vulnerability, dealer, bid)

        # Update statistics
        elapsed_ms = (time.time() - start_time) * 1000
        self._update_stats(auction_state, elapsed_ms)

        return (bid, explanation)

    def get_next_bid_structured(
        self,
        hand: Hand,
        auction_history: list,
        my_position: str,
        vulnerability: str,
        dealer: str = None
    ) -> Tuple[str, Dict]:
        """
        Get the next bid with structured explanation data (for JSON API).

        Returns:
            Tuple of (bid, explanation_dict)
        """
        # Infer dealer if not provided
        if dealer is None:
            dealer = self._infer_dealer(my_position, len(auction_history))

        # Steps 1-3: Features, State, Module Selection
        features = extract_features(hand, auction_history, my_position, vulnerability, dealer)
        auction_state = self._compute_auction_state(hand, features)
        module_name = self._select_module_for_state(auction_state, hand)

        # Step 4: Get bid from module
        bid = "Pass"
        explanation_obj = "No appropriate bid found."
        
        if module_name != 'pass_by_default':
            module = self.modules.get(module_name)
            if module:
                try:
                    result = module.evaluate(hand, features)
                    if result:
                        bid = result[0]
                        explanation_obj = result[1]
                except Exception as e:
                    logger.error(f"Error in module {module_name}: {e}")

        # Step 5: Apply safety nets
        bid, explanation_final = self._apply_safety_nets(bid, explanation_obj, hand, auction_state, auction_history)

        # Step 6: Validate
        if not self._is_bid_legal(bid, auction_history):
             bid = "Pass"
             explanation_final = "No legal bid found (illegal bid was suggested)."

        # Format explanation for return
        explanation_dict = {}
        if isinstance(explanation_final, BidExplanation):
            explanation_dict = explanation_final.to_dict()
        elif isinstance(explanation_final, dict):
             explanation_dict = explanation_final
        else:
            explanation_dict = {
                "bid": bid,
                "primary_reason": str(explanation_final)
            }
            
        return (bid, explanation_dict)

    def _infer_dealer(self, my_position: str, auction_length: int) -> str:
        """Infer dealer from position and auction length."""
        positions = ['North', 'East', 'South', 'West']
        my_idx = positions.index(my_position)
        dealer_idx = (my_idx - auction_length) % 4
        return positions[dealer_idx]

    def _compute_auction_state(self, hand: Hand, features: Dict) -> AuctionState:
        """
        Compute the complete auction state.

        This is the CORE of V2 - explicit state computation instead of
        scattered if/else checks throughout the code.
        """
        auction = features.get('auction_features', {})

        # Get forcing status from features (now computed in feature_extractor)
        forcing_info = auction.get('forcing_status', {})
        forcing_type = forcing_info.get('forcing_type', 'non_forcing')

        if forcing_type == 'game_forcing':
            forcing = ForcingStatus.GAME_FORCING
        elif forcing_type == 'one_round_forcing':
            forcing = ForcingStatus.ONE_ROUND_FORCING
        else:
            forcing = ForcingStatus.NON_FORCING

        # Get balancing info
        balancing_info = auction.get('balancing', {})
        is_balancing = balancing_info.get('is_balancing', False)
        hcp_adjustment = balancing_info.get('hcp_adjustment', 0)

        # Get agreed suit info
        agreed_info = auction.get('agreed_suit', {})

        # Get bid counts
        bid_counts = auction.get('bid_counts', {})

        # Determine state based on auction context
        state = self._determine_state(
            auction.get('opener_relationship'),
            auction.get('opening_bid'),
            bid_counts.get('my_bid_count', 0),
            bid_counts.get('partner_bid_count', 0),
            is_balancing,
            forcing
        )

        return AuctionState(
            state=state,
            forcing=forcing,
            forcing_source=forcing_info.get('forcing_source'),
            must_bid=forcing_info.get('must_bid', False),
            minimum_level=forcing_info.get('minimum_level', 0),
            opener_relationship=auction.get('opener_relationship'),
            agreed_suit=agreed_info.get('agreed_suit'),
            fit_confirmed=agreed_info.get('fit_known', False),
            is_balancing=is_balancing,
            hcp_adjustment=hcp_adjustment,
            my_bid_count=bid_counts.get('my_bid_count', 0),
            partner_bid_count=bid_counts.get('partner_bid_count', 0),
            opening_bid=auction.get('opening_bid'),
            partner_last_bid=auction.get('partner_last_bid'),
            my_last_bid=None,  # TODO: Track this
            features=features
        )

    def _determine_state(
        self,
        opener_relationship: Optional[str],
        opening_bid: Optional[str],
        my_bid_count: int,
        partner_bid_count: int,
        is_balancing: bool,
        forcing: ForcingStatus
    ) -> BiddingState:
        """
        Determine the bidding state based on auction context.

        This is the STATE MACHINE - clear, testable logic.
        """
        # Game forcing overrides other states — but only for the opening partnership
        if forcing == ForcingStatus.GAME_FORCING and opener_relationship in ('Me', 'Partner'):
            return BiddingState.GAME_FORCING

        # No opener yet = opening position
        if opener_relationship is None:
            return BiddingState.OPENING

        # I opened
        if opener_relationship == 'Me':
            if my_bid_count == 1:
                return BiddingState.OPENER_REBID
            else:
                return BiddingState.OPENER_THIRD_BID

        # Partner opened
        if opener_relationship == 'Partner':
            if my_bid_count == 0:
                return BiddingState.RESPONDING
            else:
                return BiddingState.RESPONDER_REBID

        # Opponent opened
        if opener_relationship == 'Opponent':
            if is_balancing:
                return BiddingState.BALANCING_SEAT
            if my_bid_count == 0 and partner_bid_count == 0:
                return BiddingState.DIRECT_SEAT
            if partner_bid_count > 0:
                return BiddingState.ADVANCING
            return BiddingState.DIRECT_SEAT

        # Fallback
        return BiddingState.OPENING

    def _select_module_for_state(self, state: AuctionState, hand: Hand) -> str:
        """
        Select the appropriate module based on auction state.

        This replaces the complex if/else chain in decision_engine.py
        with a clean state-to-module mapping.
        """
        # State to module mapping
        STATE_MODULE_MAP = {
            BiddingState.OPENING: self._select_opening_module,
            BiddingState.RESPONDING: self._select_response_module,
            BiddingState.RESPONDER_REBID: self._select_responder_rebid_module,
            BiddingState.OPENER_REBID: self._select_opener_rebid_module,
            BiddingState.OPENER_THIRD_BID: self._select_opener_rebid_module,
            BiddingState.DIRECT_SEAT: self._select_competitive_module,
            BiddingState.BALANCING_SEAT: self._select_balancing_module,
            BiddingState.ADVANCING: self._select_advancer_module,
            BiddingState.GAME_FORCING: self._select_game_forcing_module,
        }

        selector = STATE_MODULE_MAP.get(state.state)
        if selector:
            return selector(state, hand)

        return 'pass_by_default'

    def _select_opening_module(self, state: AuctionState, hand: Hand) -> str:
        """Select module for opening bid."""
        # Check for preempt first
        if self._should_preempt(hand):
            return 'preempts'
        return 'opening_bids'

    def _select_response_module(self, state: AuctionState, hand: Hand) -> str:
        """Select module for responding to partner's opening."""
        features = state.features
        opening_bid = state.opening_bid

        # Check conventions first (in priority order)
        if opening_bid in ['1NT', '2NT']:
            # Jacoby transfers
            if self._should_transfer(hand, opening_bid):
                return 'jacoby'
            # Stayman
            if self._should_stayman(hand, opening_bid):
                return 'stayman'

        # Check for Blackwood response
        if state.partner_last_bid == '4NT':
            return 'blackwood'

        # Default to natural responses
        return 'responses'

    def _select_competitive_module(self, state: AuctionState, hand: Hand) -> str:
        """Select module for competitive bidding (opponent opened)."""
        features = state.features

        # Check for two-suited bids
        if self._has_michaels_shape(hand, state):
            return 'michaels_cuebid'

        if self._has_unusual_2nt_shape(hand, state):
            return 'unusual_2nt'

        # Check for overcall
        if self._can_overcall(hand, state):
            return 'overcalls'

        # Check for takeout double
        if self._can_takeout_double(hand, state):
            return 'takeout_doubles'

        return 'pass_by_default'

    def _select_responder_rebid_module(self, state: AuctionState, hand: Hand) -> str:
        """Select module for responder's rebid."""
        # Check for Blackwood response
        if state.partner_last_bid == '4NT':
            return 'blackwood'
        if state.partner_last_bid == '5NT': # King ask or GSF
             return 'blackwood'
             
        return 'responder_rebid'

    def _select_opener_rebid_module(self, state: AuctionState, hand: Hand) -> str:
        """Select module for opener's rebid."""
        # Check for Blackwood response
        if state.partner_last_bid == '4NT':
            return 'blackwood'
        if state.partner_last_bid == '5NT':
             return 'blackwood'
             
        return 'openers_rebid'

    def _select_advancer_module(self, state: AuctionState, hand: Hand) -> str:
        """Select module for advancer (partner of overcaller)."""
        # Check for Blackwood response
        if state.partner_last_bid == '4NT':
            return 'blackwood'
            
        return 'advancer_bids'

    def _select_balancing_module(self, state: AuctionState, hand: Hand) -> str:
        """Select module for balancing seat."""
        # In balancing seat, can bid with lighter values
        # The HCP adjustment is already in state.hcp_adjustment

        if self._can_overcall(hand, state):
            return 'overcalls'

        if self._can_takeout_double(hand, state):
            return 'takeout_doubles'

        return 'pass_by_default'

    def _select_game_forcing_module(self, state: AuctionState, hand: Hand) -> str:
        """Select module when game-forcing is established."""
        # Must reach game - select appropriate continuation
        if state.agreed_suit:
            # Suit agreed - head for game in that suit or explore slam
            if hand.hcp >= 15:  # Slam interest
                return 'blackwood'
            return 'responses'  # Will bid game

        # No suit agreed yet
        if state.opener_relationship == 'Me':
            return 'openers_rebid'
        else:
            return 'responder_rebid'

    # ==========================================================================
    # HELPER METHODS FOR MODULE SELECTION
    # ==========================================================================

    def _should_preempt(self, hand: Hand) -> bool:
        """Check if hand qualifies for preempt."""
        # Basic preempt criteria: 6+ card suit, < 12 HCP
        if hand.hcp >= 12:
            return False
        for suit in ['♠', '♥', '♦', '♣']:
            if hand.suit_lengths.get(suit, 0) >= 6:
                return True
        return False

    def _should_transfer(self, hand: Hand, opening: str) -> bool:
        """Check if should make Jacoby transfer."""
        # Need 5+ major
        return hand.suit_lengths.get('♥', 0) >= 5 or hand.suit_lengths.get('♠', 0) >= 5

    def _should_stayman(self, hand: Hand, opening: str) -> bool:
        """Check if should bid Stayman."""
        # Need 4-card major and invitational+ values
        has_4_major = hand.suit_lengths.get('♥', 0) >= 4 or hand.suit_lengths.get('♠', 0) >= 4
        has_values = hand.hcp >= 8
        return has_4_major and has_values

    def _has_michaels_shape(self, hand: Hand, state: AuctionState) -> bool:
        """Check for Michaels cuebid shape (5-5 in two suits)."""
        lengths = sorted(hand.suit_lengths.values(), reverse=True)
        return lengths[0] >= 5 and lengths[1] >= 5

    def _has_unusual_2nt_shape(self, hand: Hand, state: AuctionState) -> bool:
        """Check for Unusual 2NT shape (5-5 minors)."""
        return hand.suit_lengths.get('♣', 0) >= 5 and hand.suit_lengths.get('♦', 0) >= 5

    def _can_overcall(self, hand: Hand, state: AuctionState) -> bool:
        """Check if can make an overcall."""
        # Adjusted HCP for balancing
        effective_hcp = hand.hcp + state.hcp_adjustment

        # Need 8+ HCP (5+ in balancing) and 5+ card suit
        min_hcp = 5 if state.is_balancing else 8
        if effective_hcp < min_hcp:
            return False

        # Need a 5+ card suit
        for suit in ['♠', '♥', '♦', '♣']:
            if hand.suit_lengths.get(suit, 0) >= 5:
                return True
        return False

    def _can_takeout_double(self, hand: Hand, state: AuctionState) -> bool:
        """Check if can make takeout double."""
        effective_hcp = hand.hcp + state.hcp_adjustment

        # Need 12+ HCP (9+ in balancing) and support for unbid suits
        min_hcp = 9 if state.is_balancing else 12
        return effective_hcp >= min_hcp

    # ==========================================================================
    # BID GENERATION
    # ==========================================================================

    def _get_bid_from_module(
        self,
        module_name: str,
        hand: Hand,
        features: Dict,
        auction_history: list
    ) -> Tuple[str, str]:
        """Get bid from the selected module."""
        if module_name == 'pass_by_default':
            return ('Pass', 'No appropriate bid found.')

        module = self.modules.get(module_name)
        if not module:
            logger.warning(f"Module '{module_name}' not found")
            return ('Pass', 'Module not found.')

        try:
            result = module.evaluate(hand, features)
            if result:
                return (result[0], result[1] if len(result) > 1 else '')
        except Exception as e:
            logger.error(f"Error in module {module_name}: {e}")

        return ('Pass', 'Module returned no bid.')

    def _apply_safety_nets(
        self,
        bid: str,
        explanation: str,
        hand: Hand,
        state: AuctionState,
        auction_history: list
    ) -> Tuple[str, str]:
        """Apply safety nets for game-forcing and slam exploration."""

        # Safety nets only apply to partnership auctions (I opened or partner opened)
        if state.opener_relationship not in ('Me', 'Partner'):
            return (bid, explanation)

        # Safety net 1: Game-forcing must not pass below game
        if state.forcing == ForcingStatus.GAME_FORCING and bid == 'Pass':
            game_bid = self._find_game_bid(hand, state, auction_history)
            if game_bid:
                return (game_bid, f"Game-forcing auction - must reach game. {explanation}")

        # Safety net 2: Don't pass when must_bid is True
        if state.must_bid and bid == 'Pass':
            # Find any legal bid
            legal_bid = self._find_any_legal_bid(hand, state, auction_history)
            if legal_bid:
                return (legal_bid, f"Forcing auction - cannot pass. {explanation}")

        return (bid, explanation)

    def _find_game_bid(self, hand: Hand, state: AuctionState, auction_history: list) -> Optional[str]:
        """Find an appropriate game bid."""
        # If suit is agreed, bid game in that suit
        if state.agreed_suit:
            if state.agreed_suit in ['♥', '♠']:
                game = f'4{state.agreed_suit}'
            else:
                game = f'5{state.agreed_suit}'
            if self._is_bid_legal(game, auction_history):
                return game

        # Try 3NT
        if self._is_bid_legal('3NT', auction_history):
            return '3NT'

        # Try 4 of a major
        for suit in ['♠', '♥']:
            if hand.suit_lengths.get(suit, 0) >= 4:
                game = f'4{suit}'
                if self._is_bid_legal(game, auction_history):
                    return game

        return None

    def _find_any_legal_bid(self, hand: Hand, state: AuctionState, auction_history: list) -> Optional[str]:
        """Find any legal bid when we must bid."""
        # Try cheapest NT
        for level in range(1, 8):
            if self._is_bid_legal(f'{level}NT', auction_history):
                return f'{level}NT'

        # Try longest suit
        longest_suit = max(hand.suit_lengths, key=hand.suit_lengths.get)
        for level in range(1, 8):
            bid = f'{level}{longest_suit}'
            if self._is_bid_legal(bid, auction_history):
                return bid

        return None

    def _is_bid_legal(self, bid: str, auction_history: list) -> bool:
        """Check if a bid is legal given the auction history."""
        if bid in ['Pass', 'X', 'XX']:
            return True

        last_real_bid = None
        for b in reversed(auction_history):
            if b not in ['Pass', 'X', 'XX']:
                last_real_bid = b
                break

        if not last_real_bid:
            return True

        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}

        try:
            my_level = int(bid[0])
            my_suit = bid[1:]
            last_level = int(last_real_bid[0])
            last_suit = last_real_bid[1:]

            if my_level > last_level:
                return True
            if my_level == last_level and suit_rank.get(my_suit, 0) > suit_rank.get(last_suit, 0):
                return True
        except (ValueError, IndexError):
            return False

        return False

    # ==========================================================================
    # COMPARISON MODE
    # ==========================================================================

    def _compare_with_v1(
        self,
        hand: Hand,
        auction_history: list,
        my_position: str,
        vulnerability: str,
        dealer: str,
        v2_bid: str
    ):
        """Compare V2 result with V1 and log discrepancies."""
        if self._v1_engine is None:
            from engine.bidding_engine import BiddingEngine
            self._v1_engine = BiddingEngine()

        try:
            v1_bid, v1_explanation = self._v1_engine.get_next_bid(
                hand, auction_history, my_position, vulnerability,
                dealer=dealer
            )

            if v1_bid != v2_bid:
                self.stats['v1_discrepancies'] += 1
                logger.info(
                    f"V1/V2 DISCREPANCY:\n"
                    f"  Auction: {auction_history}\n"
                    f"  V1: {v1_bid}\n"
                    f"  V2: {v2_bid}\n"
                    f"  Hand HCP: {hand.hcp}"
                )
            else:
                self.stats['v1_matches'] += 1

        except Exception as e:
            logger.error(f"Error comparing with V1: {e}")

    def _update_stats(self, state: AuctionState, elapsed_ms: float):
        """Update engine statistics."""
        self.stats['total_bids'] += 1

        # Update state distribution
        state_name = state.state.name
        self.stats['state_distribution'][state_name] = \
            self.stats['state_distribution'].get(state_name, 0) + 1

        # Update average time (rolling average)
        n = self.stats['total_bids']
        self.stats['avg_time_ms'] = (self.stats['avg_time_ms'] * (n-1) + elapsed_ms) / n

    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return self.stats.copy()

    def reset_stats(self):
        """Reset engine statistics."""
        self.stats = {
            'total_bids': 0,
            'v1_matches': 0,
            'v1_discrepancies': 0,
            'state_distribution': {},
            'avg_time_ms': 0,
        }
