"""
Bridge Analysis Engine - Comprehensive hand analysis for bidding and play.

This module provides post-game analysis to help players improve their bridge.

Features:
- Quadrant classification (bidding vs play quality)
- Bidding efficiency analysis (underbid/optimal/overbid)
- Leave-table points calculation
- Opening lead quality assessment
- Strain accuracy statistics
- Par score comparison

Performance:
- DDS analysis runs ONCE at hand completion
- Results stored in DB for instant retrieval
- All visualizations use pre-calculated data

Key Definitions (First Principles):
- "Good Bidding": Reached optimal bonus level OR no higher bonus was available
  Formula: actual_score >= (par_score - epsilon) OR optimal_contract_reached
- "Good Play": Took all available tricks (actual_tricks >= dd_tricks)
- "Decay": Loss of trick potential during play (dd_tricks drops)

Phase 1: Bidding analysis (low computation, high value)
Phase 3: Decay curve generation (high computation, requires state reconstruction)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db import get_connection

# Import DDS service
try:
    from engine.play.dds_analysis import (
        get_dds_service,
        DDSAnalysisService,
        DDTable,
        DealAnalysis,
    )
    DDS_IMPORTS_OK = True
except ImportError as e:
    print(f"Warning: DDS imports failed: {e}")
    DDS_IMPORTS_OK = False
    DDSAnalysisService = None
    DDTable = None
    DealAnalysis = None

# Import Decay Curve Generator (Phase 3)
try:
    from .decay_curve import get_decay_generator, DecayCurveResult
    DECAY_CURVE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Decay curve imports failed: {e}")
    DECAY_CURVE_AVAILABLE = False
    DecayCurveResult = None


class Quadrant(Enum):
    """
    Quadrant classification for bidding vs play quality.

    Visual Layout:
        Q2 (Yellow) | Q1 (Green)
        Bad Play    | Good Play
        Good Bid    | Good Bid
        ------------|------------
        Q3 (Red)    | Q4 (Yellow)
        Bad Play    | Good Play
        Bad Bid     | Bad Bid
    """
    Q1 = "Q1"  # Good Bidding + Good Play (Top-Right, Green)
    Q2 = "Q2"  # Good Bidding + Bad Play (Top-Left, Yellow)
    Q3 = "Q3"  # Bad Bidding + Bad Play (Bottom-Left, Red)
    Q4 = "Q4"  # Bad Bidding + Good Play (Bottom-Right, Yellow)


class BidEfficiency(Enum):
    """
    Bidding efficiency classification.

    Measures whether the partnership found the optimal contract level.
    """
    OPTIMAL = "optimal"     # Contract achieves maximum available bonus
    UNDERBID = "underbid"   # Game/slam available but not bid
    OVERBID = "overbid"     # Contract unmakeable by DD analysis


class LeadQuality(Enum):
    """
    Opening lead quality classification.

    Compares actual lead to DDS-optimal leads.
    """
    OPTIMAL = "optimal"     # Lead achieves best defense (or tied)
    NEUTRAL = "neutral"     # Within 1 trick of optimal
    LEAKING = "leaking"     # Costs 2+ tricks vs optimal


@dataclass
class MajorError:
    """
    Represents a significant mistake during play.

    Used in decay curve analysis to highlight where tricks were lost.
    """
    card_index: int      # Position in play sequence (0-51)
    trick: int           # Trick number (1-13)
    card: str            # Card played (e.g., "SQ")
    position: str        # Who made the error (N/E/S/W)
    loss: int            # Tricks lost by this play
    optimal_card: str    # What should have been played
    reasoning: str = ""  # Explanation of why it was wrong


@dataclass
class OpeningLeadAnalysis:
    """
    Analysis of the opening lead.

    The opening lead is unique because it's made without seeing dummy.
    This analysis shows how the actual lead compared to optimal.
    """
    actual_lead: str           # Card that was led (e.g., "S4")
    optimal_leads: List[str]   # Cards that achieve max defense
    tricks_with_actual: int    # Tricks declarer makes with this lead
    tricks_with_optimal: int   # Tricks declarer makes with best defense
    quality: LeadQuality       # Classification
    cost: int                  # Tricks given away (0 if optimal)


@dataclass
class HandAnalysisResult:
    """
    Complete analysis result for a single hand.

    This is the output of BridgeAnalysisEngine.analyze_hand().
    It contains all computed metrics for storage and display.
    """
    # Core classifications
    quadrant: Quadrant
    bid_efficiency: BidEfficiency

    # Bidding metrics
    points_left_on_table: int       # Points lost from underbidding
    contract_makeable: bool         # Was contract achievable by DD?
    reached_optimal_level: bool     # Did we bid to the right level?

    # Play metrics
    dd_tricks: int                  # Double-dummy tricks for contract
    actual_tricks: int              # Tricks actually taken
    tricks_delta: int               # actual - dd (positive = overtricks)

    # Par comparison
    par_score: Optional[int]        # Par score (if calculated)
    par_contract: Optional[str]     # Par contract (if calculated)
    actual_score: int               # Actual score achieved
    score_vs_par: Optional[int]     # actual - par (positive = beat par)

    # Opening lead (if applicable)
    opening_lead: Optional[OpeningLeadAnalysis] = None

    # Decay analysis (Phase 3 - may be empty)
    decay_curve: List[int] = field(default_factory=list)
    major_errors: List[MajorError] = field(default_factory=list)

    # Full DD matrix (for "what if" analysis)
    dd_matrix: Optional[Dict[str, Dict[str, int]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for DB storage."""
        result = {
            'quadrant': self.quadrant.value,
            'bid_efficiency': self.bid_efficiency.value,
            'points_left_on_table': self.points_left_on_table,
            'contract_makeable': self.contract_makeable,
            'reached_optimal_level': self.reached_optimal_level,
            'dd_tricks': self.dd_tricks,
            'actual_tricks': self.actual_tricks,
            'tricks_delta': self.tricks_delta,
            'par_score': self.par_score,
            'par_contract': self.par_contract,
            'actual_score': self.actual_score,
            'score_vs_par': self.score_vs_par,
            'decay_curve': self.decay_curve,
            'major_errors': [asdict(e) for e in self.major_errors],
            'dd_matrix': self.dd_matrix,
        }
        if self.opening_lead:
            result['opening_lead'] = {
                'actual_lead': self.opening_lead.actual_lead,
                'optimal_leads': self.opening_lead.optimal_leads,
                'tricks_with_actual': self.opening_lead.tricks_with_actual,
                'tricks_with_optimal': self.opening_lead.tricks_with_optimal,
                'quality': self.opening_lead.quality.value,
                'cost': self.opening_lead.cost,
            }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HandAnalysisResult':
        """Reconstruct from dictionary (DB retrieval)."""
        opening_lead = None
        if data.get('opening_lead'):
            ol = data['opening_lead']
            opening_lead = OpeningLeadAnalysis(
                actual_lead=ol['actual_lead'],
                optimal_leads=ol.get('optimal_leads', []),
                tricks_with_actual=ol.get('tricks_with_actual', 0),
                tricks_with_optimal=ol.get('tricks_with_optimal', 0),
                quality=LeadQuality(ol.get('quality', 'neutral')),
                cost=ol.get('cost', 0),
            )

        major_errors = [
            MajorError(**e) for e in data.get('major_errors', [])
        ]

        return cls(
            quadrant=Quadrant(data['quadrant']),
            bid_efficiency=BidEfficiency(data['bid_efficiency']),
            points_left_on_table=data.get('points_left_on_table', 0),
            contract_makeable=data.get('contract_makeable', True),
            reached_optimal_level=data.get('reached_optimal_level', True),
            dd_tricks=data.get('dd_tricks', 0),
            actual_tricks=data.get('actual_tricks', 0),
            tricks_delta=data.get('tricks_delta', 0),
            par_score=data.get('par_score'),
            par_contract=data.get('par_contract'),
            actual_score=data.get('actual_score', 0),
            score_vs_par=data.get('score_vs_par'),
            opening_lead=opening_lead,
            decay_curve=data.get('decay_curve', []),
            major_errors=major_errors,
            dd_matrix=data.get('dd_matrix'),
        )


class BridgeAnalysisEngine:
    """
    Main analysis engine for comprehensive hand evaluation.

    This engine performs post-game analysis to classify hands by
    bidding and play quality, calculate points left on table,
    and generate metrics for the dashboard.

    Usage:
        engine = BridgeAnalysisEngine()

        # Analyze a completed hand
        result = engine.analyze_hand(
            hands=hands_dict,
            contract=contract,
            play_history=play_sequence,
            actual_tricks=tricks_taken,
            actual_score=score,
            vulnerability='NS'
        )

        # Store results in database
        engine.store_analysis(session_hand_id, result)

    Key Logic (First Principles):

    1. "Good Bidding" is NOT just "contract was makeable"
       Good Bidding = reached_optimal_bonus OR no_higher_bonus_available

       Example: Bidding 1S when you can make 4S is BAD bidding,
       even though 1S is "makeable".

    2. "Good Play" = actual_tricks >= dd_tricks
       This measures execution against the theoretical maximum.

    3. Par Score is the reference point for "optimal bidding"
       If par is 4S making, and you bid 2S, you underbid.
       If par is 2S making, and you bid 4S (down), you overbid.
    """

    # ========================================================================
    # Scoring Constants
    # ========================================================================

    # Game thresholds: (level_needed, tricks_needed)
    GAME_THRESHOLDS = {
        'NT': (3, 9),   # 3NT = 9 tricks
        'S': (4, 10),   # 4S = 10 tricks
        'H': (4, 10),   # 4H = 10 tricks
        'D': (5, 11),   # 5D = 11 tricks
        'C': (5, 11),   # 5C = 11 tricks
    }

    # Small slam: 6-level (12 tricks)
    # Grand slam: 7-level (13 tricks)

    # Game bonuses (approximate, for "points left" calculation)
    GAME_BONUS_NV = 300   # Non-vulnerable game bonus
    GAME_BONUS_V = 500    # Vulnerable game bonus

    # Slam bonuses
    SMALL_SLAM_BONUS_NV = 500
    SMALL_SLAM_BONUS_V = 750
    GRAND_SLAM_BONUS_NV = 1000
    GRAND_SLAM_BONUS_V = 1500

    # Partscore bonus
    PARTSCORE_BONUS = 50

    def __init__(self, dds_service: Optional['DDSAnalysisService'] = None):
        """
        Initialize the analysis engine.

        Args:
            dds_service: DDSAnalysisService instance. If None, will get singleton.
        """
        if dds_service:
            self.dds = dds_service
        elif DDS_IMPORTS_OK:
            self.dds = get_dds_service()
        else:
            self.dds = None

        self._stats = {
            'hands_analyzed': 0,
            'dds_available': 0,
            'dds_unavailable': 0,
        }

    @property
    def is_dds_available(self) -> bool:
        """Check if DDS is available for analysis."""
        return self.dds is not None and self.dds.is_available

    # ========================================================================
    # Format Conversion Helpers
    # ========================================================================

    def _convert_hands_to_card_strings(
        self, hands: Dict[str, 'Hand']
    ) -> Dict[str, List[str]]:
        """
        Convert Hand objects to card string lists for decay curve generator.

        Args:
            hands: Dict of position -> Hand objects

        Returns:
            Dict of position -> list of card strings like ['SA', 'SK', 'HQ', ...]
        """
        # Suit symbol to letter mapping
        SUIT_TO_LETTER = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}

        result = {}
        for pos, hand in hands.items():
            card_strings = []
            for card in hand.cards:
                suit_letter = SUIT_TO_LETTER.get(card.suit, card.suit)
                card_strings.append(f"{suit_letter}{card.rank}")
            result[pos] = card_strings
        return result

    def _convert_play_history_format(
        self, play_history: List[Dict]
    ) -> List[Dict]:
        """
        Convert server play_history format to decay curve format.

        Server format: {'trick': 1, 'play_index': 0, 'position': 'W', 'rank': 'A', 'suit': '♠'}
        Decay curve format: {'card': 'SA', 'position': 'W'}
        """
        # Suit symbol to letter mapping
        SUIT_TO_LETTER = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}

        result = []
        for play in play_history:
            # Handle both formats - some may already have 'card' key
            if 'card' in play and len(play['card']) == 2:
                # Already in correct format
                result.append({
                    'card': play['card'],
                    'position': play['position']
                })
            else:
                # Convert from server format
                suit = play.get('suit', '')
                rank = play.get('rank', '')
                suit_letter = SUIT_TO_LETTER.get(suit, suit)
                card_str = f"{suit_letter}{rank}"
                result.append({
                    'card': card_str,
                    'position': play['position']
                })
        return result

    # ========================================================================
    # Main Analysis Entry Point
    # ========================================================================

    def analyze_hand(
        self,
        hands: Dict[str, 'Hand'],
        contract: 'Contract',
        play_history: List[Dict],
        actual_tricks: int,
        actual_score: int,
        vulnerability: str = 'None',
        user_position: str = 'S',
        dealer: str = 'N',
    ) -> HandAnalysisResult:
        """
        Perform complete analysis on a finished hand.

        This is the main entry point - call once when hand completes.

        Args:
            hands: Dict of position -> Hand (all 4 hands)
            contract: Contract object with level, strain, declarer
            play_history: List of plays [{card, position}, ...]
            actual_tricks: Tricks actually taken by declarer
            actual_score: Score achieved (from declarer's perspective)
            vulnerability: 'None', 'NS', 'EW', 'Both'
            user_position: Which position user played
            dealer: Dealer position

        Returns:
            HandAnalysisResult with all analysis data
        """
        self._stats['hands_analyzed'] += 1

        # Handle passed-out hands
        if contract is None or contract.level == 0:
            return self._create_passout_result()

        # Get DD analysis
        dd_analysis = None
        if self.is_dds_available:
            try:
                dd_analysis = self.dds.analyze_deal(
                    hands, dealer=dealer, vulnerability=vulnerability
                )
                if dd_analysis.is_valid:
                    self._stats['dds_available'] += 1
                else:
                    self._stats['dds_unavailable'] += 1
                    dd_analysis = None
            except Exception as e:
                print(f"DDS analysis failed: {e}")
                self._stats['dds_unavailable'] += 1
        else:
            self._stats['dds_unavailable'] += 1

        if not dd_analysis or not dd_analysis.is_valid:
            # Fallback when DDS unavailable
            return self._create_fallback_result(
                contract, actual_tricks, actual_score
            )

        # Extract key values
        strain = self._normalize_strain(contract.trump_suit)
        dd_tricks = dd_analysis.dd_table.get_tricks(contract.declarer, strain)
        tricks_needed = 6 + contract.level

        par_score = dd_analysis.par_result.score if dd_analysis.par_result else None
        par_contract = None
        if dd_analysis.par_result and dd_analysis.par_result.contracts:
            par_contract = dd_analysis.par_result.contracts[0]

        # Determine vulnerability for declarer
        is_vul = self._is_vulnerable(contract.declarer, vulnerability)

        # 1. Calculate bidding efficiency (with corrected logic)
        bid_efficiency, points_left, reached_optimal = self._calculate_bid_efficiency(
            contract=contract,
            dd_table=dd_analysis.dd_table,
            par_score=par_score,
            actual_score=actual_score,
            vulnerability=vulnerability,
        )

        # 2. Calculate quadrant (using corrected "Good Bidding" definition)
        quadrant = self._calculate_quadrant(
            actual_tricks=actual_tricks,
            dd_tricks=dd_tricks,
            reached_optimal_level=reached_optimal,
            bid_efficiency=bid_efficiency,
        )

        # 3. Analyze opening lead (if applicable)
        opening_lead = self._analyze_opening_lead(
            hands, contract, play_history, dd_analysis.dd_table
        )

        # 4. Decay curve generation (Phase 3)
        # Tracks declarer's trick potential at each card played
        decay_curve = []
        major_errors = []

        if DECAY_CURVE_AVAILABLE and play_history:
            try:
                decay_gen = get_decay_generator()

                # Only run if DDS is available (required for accurate curves)
                if decay_gen.is_available:
                    # Convert formats for decay curve generator
                    hands_as_strings = self._convert_hands_to_card_strings(hands)
                    plays_for_decay = self._convert_play_history_format(play_history)

                    # Get trump suit from contract
                    trump = self._normalize_strain(contract.trump_suit)

                    # Generate decay curve (skip_interval=1 for full resolution)
                    decay_result = decay_gen.generate(
                        hands=hands_as_strings,
                        play_history=plays_for_decay,
                        declarer=contract.declarer,
                        trump_suit=trump,
                        skip_interval=1,
                    )

                    if decay_result.is_valid:
                        decay_curve = decay_result.curve
                        # Convert decay_curve MajorErrors to analysis_engine MajorErrors
                        for err in decay_result.major_errors:
                            major_errors.append(MajorError(
                                card_index=err.card_index,
                                trick=err.trick_number,
                                card=err.card,
                                position=err.position,
                                loss=err.loss,
                                optimal_card=err.optimal_card or "",
                                reasoning=err.reasoning or "",
                            ))
                        print(f"   Decay curve: {len(decay_curve)} points, {len(major_errors)} errors")
                    else:
                        print(f"   Decay curve generation failed: {decay_result.error_message}")
            except Exception as e:
                print(f"   Decay curve error: {e}")
                # Continue with empty curve - don't fail the whole analysis

        # Build result
        return HandAnalysisResult(
            quadrant=quadrant,
            bid_efficiency=bid_efficiency,
            points_left_on_table=points_left,
            contract_makeable=(dd_tricks >= tricks_needed),
            reached_optimal_level=reached_optimal,
            dd_tricks=dd_tricks,
            actual_tricks=actual_tricks,
            tricks_delta=actual_tricks - dd_tricks,
            par_score=par_score,
            par_contract=par_contract,
            actual_score=actual_score,
            score_vs_par=(actual_score - par_score) if par_score else None,
            opening_lead=opening_lead,
            decay_curve=decay_curve,
            major_errors=major_errors,
            dd_matrix=dd_analysis.dd_table.to_dict() if dd_analysis.dd_table else None,
        )

    # ========================================================================
    # Bidding Efficiency (Corrected Logic)
    # ========================================================================

    def _calculate_bid_efficiency(
        self,
        contract: 'Contract',
        dd_table: 'DDTable',
        par_score: Optional[int],
        actual_score: int,
        vulnerability: str,
    ) -> Tuple[BidEfficiency, int, bool]:
        """
        Determine if contract was optimal, underbid, or overbid.

        CORRECTED LOGIC:
        - "Optimal" means we reached the highest available bonus level
        - "Underbid" means we left a game/slam bonus on the table
        - "Overbid" means we bid higher than the cards support

        Returns:
            (BidEfficiency, points_left_on_table, reached_optimal_level)
        """
        strain = self._normalize_strain(contract.trump_suit)
        declarer = contract.declarer
        dd_tricks = dd_table.get_tricks(declarer, strain)
        tricks_needed = 6 + contract.level
        is_vul = self._is_vulnerable(declarer, vulnerability)

        # Step 1: Check if we OVERBID (contract is unmakeable)
        if dd_tricks < tricks_needed:
            return BidEfficiency.OVERBID, 0, False

        # Step 2: Check what bonus level we could reach
        # Find the highest makeable contract in this strain
        max_makeable_level = self._find_max_makeable_level(dd_tricks)

        # Step 3: Determine what bonus was available
        available_bonus = self._get_available_bonus(max_makeable_level, strain, is_vul)

        # Step 4: Determine what bonus we actually achieved
        achieved_bonus = self._get_achieved_bonus(contract.level, strain, is_vul)

        # Step 5: Compare
        if achieved_bonus >= available_bonus:
            # We reached optimal (or higher via sacrifice/etc)
            return BidEfficiency.OPTIMAL, 0, True
        else:
            # We underbid - calculate points left
            points_left = self._calculate_points_left(
                contract, dd_tricks, actual_score, is_vul, strain
            )
            return BidEfficiency.UNDERBID, points_left, False

    def _find_max_makeable_level(self, dd_tricks: int) -> int:
        """
        Find the highest contract level makeable with given DD tricks.

        Args:
            dd_tricks: Double-dummy tricks available

        Returns:
            Highest level (1-7) that can be made
        """
        # Level N requires 6+N tricks
        # So max_level = dd_tricks - 6, capped at 7
        return min(7, max(1, dd_tricks - 6))

    def _get_available_bonus(
        self, max_level: int, strain: str, is_vul: bool
    ) -> int:
        """
        Determine what bonus was theoretically available.

        Returns a "bonus tier" for comparison:
        - 0: Partscore only
        - 1: Game available
        - 2: Small slam available
        - 3: Grand slam available
        """
        game_level, _ = self.GAME_THRESHOLDS.get(strain, (7, 13))

        if max_level >= 7:
            return 3  # Grand slam
        elif max_level >= 6:
            return 2  # Small slam
        elif max_level >= game_level:
            return 1  # Game
        else:
            return 0  # Partscore

    def _get_achieved_bonus(
        self, bid_level: int, strain: str, is_vul: bool
    ) -> int:
        """
        Determine what bonus tier we actually bid to.

        Returns same tier scale as _get_available_bonus.
        """
        game_level, _ = self.GAME_THRESHOLDS.get(strain, (7, 13))

        if bid_level >= 7:
            return 3  # Grand slam
        elif bid_level >= 6:
            return 2  # Small slam
        elif bid_level >= game_level:
            return 1  # Game
        else:
            return 0  # Partscore

    def _calculate_points_left(
        self,
        contract: 'Contract',
        dd_tricks: int,
        actual_score: int,
        is_vul: bool,
        strain: str,
    ) -> int:
        """
        Calculate points left on table from underbidding.

        This estimates the difference between:
        - What we could have scored (optimal contract making)
        - What we actually scored

        The calculation includes:
        - Contract trick score
        - Game bonus (300 NV, 500 V)
        - Slam bonus (500/750 for small, 1000/1500 for grand)
        """
        max_level = self._find_max_makeable_level(dd_tricks)
        game_level, game_tricks = self.GAME_THRESHOLDS.get(strain, (7, 13))
        bid_level = contract.level

        # Determine what bonus tier we achieved vs what was available
        achieved_tier = self._get_achieved_bonus(bid_level, strain, is_vul)
        available_tier = self._get_available_bonus(max_level, strain, is_vul)

        if achieved_tier >= available_tier:
            return 0  # No points left

        # Calculate the difference in bonuses
        # Tier 0 = partscore (50), Tier 1 = game (300/500),
        # Tier 2 = small slam (+500/750), Tier 3 = grand slam (+1000/1500)

        def get_total_bonus(tier: int, vul: bool) -> int:
            """Get cumulative bonus for a tier."""
            if tier == 0:
                return self.PARTSCORE_BONUS  # 50
            elif tier == 1:
                return self.GAME_BONUS_V if vul else self.GAME_BONUS_NV  # 500/300
            elif tier == 2:
                game_bonus = self.GAME_BONUS_V if vul else self.GAME_BONUS_NV
                slam_bonus = self.SMALL_SLAM_BONUS_V if vul else self.SMALL_SLAM_BONUS_NV
                return game_bonus + slam_bonus  # 500+750 or 300+500
            else:  # tier == 3
                game_bonus = self.GAME_BONUS_V if vul else self.GAME_BONUS_NV
                slam_bonus = self.GRAND_SLAM_BONUS_V if vul else self.GRAND_SLAM_BONUS_NV
                return game_bonus + slam_bonus  # 500+1500 or 300+1000

        available_bonus = get_total_bonus(available_tier, is_vul)
        achieved_bonus = get_total_bonus(achieved_tier, is_vul)

        # Points left is primarily the bonus difference
        # We also add trick score difference for more accuracy
        optimal_level = max_level if available_tier >= 2 else (
            game_level if available_tier == 1 else bid_level
        )
        trick_diff = self._estimate_contract_score(optimal_level, strain, is_vul, dd_tricks) - \
                     self._estimate_contract_score(bid_level, strain, is_vul, dd_tricks)

        points_left = (available_bonus - achieved_bonus) + max(0, trick_diff)
        return max(0, points_left)

    def _estimate_contract_score(
        self, level: int, strain: str, is_vul: bool, tricks: int
    ) -> int:
        """
        Estimate score for a contract making with given tricks.

        This is a simplified calculation for "points left" estimation.
        """
        tricks_needed = 6 + level
        overtricks = max(0, tricks - tricks_needed)

        # Trick values
        if strain in ['S', 'H']:
            trick_value = 30
        elif strain == 'NT':
            trick_value = 30  # (first trick is 40, simplified)
        else:  # minors
            trick_value = 20

        base_score = level * trick_value
        if strain == 'NT':
            base_score = 40 + (level - 1) * 30  # First trick worth 40

        overtrick_value = 30 if strain in ['NT', 'S', 'H'] else 20

        return base_score + (overtricks * overtrick_value)

    # ========================================================================
    # Quadrant Classification (Corrected)
    # ========================================================================

    def _calculate_quadrant(
        self,
        actual_tricks: int,
        dd_tricks: int,
        reached_optimal_level: bool,
        bid_efficiency: BidEfficiency,
    ) -> Quadrant:
        """
        Determine which quadrant this hand falls into.

        CORRECTED LOGIC:
        - "Good Bidding" = reached optimal bonus level OR bid_efficiency is OPTIMAL
          (NOT just "contract was makeable")
        - "Good Play" = actual_tricks >= dd_tricks

        Quadrants:
            Q1: Good Bidding + Good Play (Green)
            Q2: Good Bidding + Bad Play (Yellow)
            Q3: Bad Bidding + Bad Play (Red)
            Q4: Bad Bidding + Good Play (Yellow)
        """
        # Bidding quality: Did we reach the optimal bonus level?
        # Note: OVERBID is also "bad bidding" (bid too high)
        bidding_good = (
            bid_efficiency == BidEfficiency.OPTIMAL or
            reached_optimal_level
        )

        # Play quality: Did we take all available tricks?
        play_good = actual_tricks >= dd_tricks

        if bidding_good and play_good:
            return Quadrant.Q1
        elif bidding_good and not play_good:
            return Quadrant.Q2
        elif not bidding_good and not play_good:
            return Quadrant.Q3
        else:  # not bidding_good and play_good
            return Quadrant.Q4

    # ========================================================================
    # Opening Lead Analysis
    # ========================================================================

    def _analyze_opening_lead(
        self,
        hands: Dict[str, 'Hand'],
        contract: 'Contract',
        play_history: List[Dict],
        dd_table: 'DDTable',
    ) -> Optional[OpeningLeadAnalysis]:
        """
        Analyze the quality of the opening lead.

        Returns None if:
        - No play history
        - First play wasn't the opening lead
        - Can't determine leader
        """
        if not play_history:
            return None

        # Get the opening lead
        first_play = play_history[0]
        actual_lead = first_play.get('card', '')
        leader = first_play.get('position', '')

        if not actual_lead or not leader:
            return None

        # Verify leader is correct (to declarer's left)
        expected_leader = self._get_leader(contract.declarer)
        if leader != expected_leader:
            return None

        # Get DD tricks for the contract
        strain = self._normalize_strain(contract.trump_suit)
        dd_tricks = dd_table.get_tricks(contract.declarer, strain)

        # For full lead analysis, we'd need to solve with each possible lead
        # This is a simplified version - Phase 2 can enhance with full DDS

        return OpeningLeadAnalysis(
            actual_lead=actual_lead,
            optimal_leads=[],  # TODO: Calculate via DDS in Phase 2
            tricks_with_actual=dd_tricks,
            tricks_with_optimal=dd_tricks,
            quality=LeadQuality.NEUTRAL,  # Default until we calculate
            cost=0,
        )

    # ========================================================================
    # Database Storage
    # ========================================================================

    def store_analysis(
        self,
        session_hand_id: int,
        result: HandAnalysisResult,
    ) -> bool:
        """
        Store analysis results in the database.

        Updates the session_hands row with analysis columns.

        Args:
            session_hand_id: ID of the session_hands row
            result: HandAnalysisResult to store

        Returns:
            True if successful, False otherwise
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Prepare JSON fields
            decay_curve_json = json.dumps(result.decay_curve) if result.decay_curve else None
            major_errors_json = json.dumps(
                [asdict(e) for e in result.major_errors]
            ) if result.major_errors else None
            dd_matrix_json = json.dumps(result.dd_matrix) if result.dd_matrix else None

            # Opening lead fields
            opening_lead_card = None
            opening_lead_quality = None
            opening_lead_cost = 0
            if result.opening_lead:
                opening_lead_card = result.opening_lead.actual_lead
                opening_lead_quality = result.opening_lead.quality.value
                opening_lead_cost = result.opening_lead.cost

            cursor.execute("""
                UPDATE session_hands SET
                    quadrant = ?,
                    bid_efficiency = ?,
                    points_left_on_table = ?,
                    decay_curve = ?,
                    major_errors = ?,
                    dd_matrix = ?,
                    opening_lead_card = ?,
                    opening_lead_quality = ?,
                    opening_lead_cost = ?,
                    par_score = COALESCE(par_score, ?),
                    par_contract = COALESCE(par_contract, ?),
                    dd_tricks = COALESCE(dd_tricks, ?)
                WHERE id = ?
            """, (
                result.quadrant.value,
                result.bid_efficiency.value,
                result.points_left_on_table,
                decay_curve_json,
                major_errors_json,
                dd_matrix_json,
                opening_lead_card,
                opening_lead_quality,
                opening_lead_cost,
                result.par_score,
                result.par_contract,
                result.dd_tricks,
                session_hand_id,
            ))

            conn.commit()
            return True

        except Exception as e:
            print(f"Error storing analysis: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return False

        finally:
            conn.close()

    # ========================================================================
    # Aggregation Methods (for dashboard/profile views)
    # ========================================================================

    def get_user_analysis_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get aggregated analysis statistics for a user.

        Uses the v_user_analysis_stats view for efficiency.

        Args:
            user_id: User ID

        Returns:
            Dictionary with all analysis metrics
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM v_user_analysis_stats WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if not row:
                return self._empty_stats()

            # Convert row to dict
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

        except Exception as e:
            print(f"Error getting analysis stats: {e}")
            return self._empty_stats()

        finally:
            conn.close()

    def get_strain_accuracy(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Get bidding accuracy per strain (for heatmap).

        Uses the v_user_strain_accuracy view.

        Args:
            user_id: User ID

        Returns:
            Dict mapping strain -> accuracy metrics
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT strain, total_contracts, makeable_contracts,
                       bidding_accuracy_pct, execution_pct
                FROM v_user_strain_accuracy
                WHERE user_id = ?
            """, (user_id,))

            result = {}
            for row in cursor.fetchall():
                strain = row[0]
                result[strain] = {
                    'total': row[1],
                    'makeable': row[2],
                    'accuracy_pct': row[3] or 0,
                    'execution_pct': row[4] or 0,
                }

            return result

        except Exception as e:
            print(f"Error getting strain accuracy: {e}")
            return {}

        finally:
            conn.close()

    def get_recent_boards_for_quadrant(
        self, user_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent boards formatted for quadrant chart.

        Uses the v_recent_boards_for_quadrant view.

        Args:
            user_id: User ID
            limit: Max boards to return

        Returns:
            List of board data for quadrant plotting
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT hand_id, contract_display, quadrant, bid_efficiency,
                       points_left_on_table, user_was_declarer, play_delta, bid_delta
                FROM v_recent_boards_for_quadrant
                WHERE user_id = ?
                LIMIT ?
            """, (user_id, limit))

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting quadrant data: {e}")
            return []

        finally:
            conn.close()

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats dictionary."""
        return {
            'total_analyzed_hands': 0,
            'q1_count': 0, 'q2_count': 0, 'q3_count': 0, 'q4_count': 0,
            'q1_pct': 0, 'q2_pct': 0, 'q3_pct': 0, 'q4_pct': 0,
            'optimal_bids': 0, 'underbids': 0, 'overbids': 0,
            'optimal_bid_pct': 0, 'underbid_pct': 0, 'overbid_pct': 0,
            'total_points_left': 0,
            'avg_tricks_vs_dd': 0,
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _normalize_strain(self, trump_suit: Optional[str]) -> str:
        """Convert trump suit to strain code."""
        if trump_suit is None:
            return 'NT'
        strain_map = {
            '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C',
            'S': 'S', 'H': 'H', 'D': 'D', 'C': 'C',
            'NT': 'NT', 'N': 'NT',
        }
        return strain_map.get(trump_suit, 'NT')

    def _is_vulnerable(self, position: str, vulnerability: str) -> bool:
        """Check if position is vulnerable."""
        if vulnerability == 'Both' or vulnerability == 'All':
            return True
        if vulnerability == 'None':
            return False
        if vulnerability == 'NS':
            return position in ['N', 'S']
        if vulnerability == 'EW':
            return position in ['E', 'W']
        return False

    def _get_leader(self, declarer: str) -> str:
        """Get the opening leader (to declarer's left)."""
        order = ['N', 'E', 'S', 'W']
        idx = order.index(declarer)
        return order[(idx + 1) % 4]

    def _create_passout_result(self) -> HandAnalysisResult:
        """Create result for a passed-out hand."""
        return HandAnalysisResult(
            quadrant=Quadrant.Q1,  # Passout is "optimal" if nobody has game
            bid_efficiency=BidEfficiency.OPTIMAL,
            points_left_on_table=0,
            contract_makeable=True,
            reached_optimal_level=True,
            dd_tricks=0,
            actual_tricks=0,
            tricks_delta=0,
            par_score=0,
            par_contract="Pass",
            actual_score=0,
            score_vs_par=0,
        )

    def _create_fallback_result(
        self,
        contract: 'Contract',
        actual_tricks: int,
        actual_score: int,
    ) -> HandAnalysisResult:
        """Create minimal result when DDS unavailable."""
        tricks_needed = 6 + contract.level
        made = actual_tricks >= tricks_needed

        return HandAnalysisResult(
            quadrant=Quadrant.Q1 if made else Quadrant.Q3,
            bid_efficiency=BidEfficiency.OPTIMAL if made else BidEfficiency.OVERBID,
            points_left_on_table=0,
            contract_makeable=made,
            reached_optimal_level=made,
            dd_tricks=actual_tricks,  # Assume DD = actual when unavailable
            actual_tricks=actual_tricks,
            tricks_delta=0,
            par_score=None,
            par_contract=None,
            actual_score=actual_score,
            score_vs_par=None,
        )

    def get_stats(self) -> Dict[str, int]:
        """Get engine statistics."""
        return self._stats.copy()


# ============================================================================
# Singleton Instance
# ============================================================================

_engine: Optional[BridgeAnalysisEngine] = None


def get_analysis_engine() -> BridgeAnalysisEngine:
    """Get the singleton analysis engine instance."""
    global _engine
    if _engine is None:
        _engine = BridgeAnalysisEngine()
    return _engine


# ============================================================================
# Self-Test
# ============================================================================

if __name__ == '__main__':
    print("Bridge Analysis Engine - Self Test")
    print("=" * 50)

    engine = get_analysis_engine()
    print(f"DDS available: {engine.is_dds_available}")
    print(f"Engine stats: {engine.get_stats()}")

    # Test helper methods
    print(f"\nStrain normalization:")
    print(f"  '♠' -> '{engine._normalize_strain('♠')}'")
    print(f"  'H' -> '{engine._normalize_strain('H')}'")
    print(f"  None -> '{engine._normalize_strain(None)}'")

    print(f"\nVulnerability check (S, 'NS'): {engine._is_vulnerable('S', 'NS')}")
    print(f"Vulnerability check (E, 'NS'): {engine._is_vulnerable('E', 'NS')}")

    print(f"\nOpening leader for declarer S: {engine._get_leader('S')}")

    print("\nAnalysis Engine initialized successfully!")
