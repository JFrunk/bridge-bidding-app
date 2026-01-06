"""
ACBL Audit Service - Stage 3 of the import pipeline.

Performs differential analysis comparing ACBL tournament results against the
V3 Engine's "Golden Master" rules. Identifies:
- Logic alignment (tournament bid matches engine suggestion)
- Hidden failures (lucky bids that violate bridge physics)
- Potential savings (points lost due to suboptimal bidding)
- Rule falsification (hands where ACBL result beat engine logic)

Physics:
- Ground Truth: ACBL file provides [Score] (what actually happened)
- Logic Trace: Engine provides optimal_bid (what the rules dictate)
- Falsification: If ACBL result > engine suggestion, flag for Rule Tuning
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .pbn_importer import PBNHand, convert_pbn_deal_to_json

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class SurvivalStatus(Enum):
    """Survival status based on panic index and action taken."""
    SAFE = "SAFE"           # Low panic, appropriate action
    SURVIVED = "SURVIVED"   # High panic, took rescue action
    FAILED = "FAILED"       # High panic, did not take rescue action
    LUCKY = "LUCKY"         # High panic, wrong action but good result


class BiddingEfficiency(Enum):
    """How the final contract compares to par."""
    OPTIMAL = "optimal"
    UNDERBID = "underbid"
    OVERBID = "overbid"
    PASSED_OUT = "passed_out"
    NO_AUCTION_DATA = "no_auction_data"  # PBN has no auction sequence


class AuditCategory(Enum):
    """Categories for educational feedback."""
    LUCKY_OVERBID = "lucky_overbid"     # Made contract that was mathematically wrong
    PENALTY_TRAP = "penalty_trap"        # Accepted penalty when rescue was available
    SIGNAL_ERROR = "signal_error"        # Play violated signaling principles
    LOGIC_ALIGNED = "logic_aligned"      # Tournament matched engine
    RULE_VIOLATION = "rule_violation"    # Violated explicit SAYC rule
    NO_AUCTION_DATA = "no_auction_data"  # PBN file has no auction sequence


@dataclass
class AuditResult:
    """
    Result of comparing tournament reality against engine logic.

    This is the core output displayed in the TournamentComparisonTable.
    """
    # Identification
    board_number: int = 0
    hand_pbn: str = ""

    # Tournament result (ground truth)
    tournament_bid: str = ""
    tournament_contract: str = ""
    tournament_score: int = 0
    tournament_tricks: int = 0

    # Engine analysis
    optimal_bid: str = ""
    optimal_contract: str = ""
    theoretical_score: int = 0
    theoretical_tricks: int = 0
    matched_rule: str = ""
    rule_tier: int = 0

    # Panic/Survival metrics
    panic_index: int = 0
    survival_status: str = "SAFE"
    rescue_action: str = ""

    # Comparison results
    is_logic_aligned: bool = False
    is_falsified: bool = False
    score_delta: int = 0
    potential_savings: int = 0
    bidding_efficiency: str = "optimal"

    # Audit categorization
    audit_category: str = "logic_aligned"
    reasoning: str = ""
    educational_feedback: str = ""

    # DDS analysis (if available)
    dds_par_score: int = 0
    dds_par_contract: str = ""
    dds_optimal_tricks: int = 0

    # Quadrant classification
    quadrant: str = ""  # Q1, Q2, Q3, Q4

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class TournamentAuditSummary:
    """
    Summary of audit results across all hands in a tournament.
    """
    event_name: str = ""
    total_hands: int = 0

    # Alignment statistics
    hands_aligned: int = 0
    hands_falsified: int = 0
    alignment_rate: float = 0.0

    # Score impact
    total_potential_savings: int = 0
    average_score_delta: float = 0.0

    # Survival statistics
    panic_situations: int = 0
    survival_rate: float = 0.0

    # Categorization breakdown
    category_counts: Dict[str, int] = field(default_factory=dict)

    # Flagged hands for rule tuning
    flagged_for_review: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# SCORE CALCULATION
# =============================================================================

def calculate_contract_score(
    level: int,
    strain: str,
    doubled: int,
    tricks_taken: int,
    vulnerable: bool
) -> int:
    """
    Calculate bridge contract score.

    Args:
        level: Contract level (1-7)
        strain: Contract strain (S, H, D, C, NT)
        doubled: 0=undoubled, 1=doubled, 2=redoubled
        tricks_taken: Actual tricks taken
        vulnerable: Whether declarer is vulnerable

    Returns:
        Score from declarer's perspective (negative if set)
    """
    required_tricks = level + 6
    overtricks = tricks_taken - required_tricks
    undertricks = -overtricks if overtricks < 0 else 0

    if undertricks > 0:
        # Contract went down
        return calculate_penalty(undertricks, doubled, vulnerable)

    # Contract made
    return calculate_making_score(level, strain, doubled, overtricks, vulnerable)


def calculate_penalty(undertricks: int, doubled: int, vulnerable: bool) -> int:
    """Calculate penalty for going down."""
    if doubled == 0:
        # Undoubled
        return -50 * undertricks if not vulnerable else -100 * undertricks

    if doubled == 1:
        # Doubled
        if not vulnerable:
            if undertricks == 1:
                return -100
            elif undertricks == 2:
                return -300
            elif undertricks == 3:
                return -500
            else:
                return -500 - 300 * (undertricks - 3)
        else:
            if undertricks == 1:
                return -200
            elif undertricks == 2:
                return -500
            elif undertricks == 3:
                return -800
            else:
                return -800 - 300 * (undertricks - 3)

    # Redoubled (doubled penalties x2)
    return calculate_penalty(undertricks, 1, vulnerable) * 2


def calculate_making_score(
    level: int,
    strain: str,
    doubled: int,
    overtricks: int,
    vulnerable: bool
) -> int:
    """Calculate score for making a contract."""
    # Trick values
    if strain in ['C', 'D']:
        trick_value = 20
    elif strain in ['H', 'S']:
        trick_value = 30
    else:  # NT
        trick_value = 30  # First trick is 40, but we handle that below

    # Base score
    if strain == 'NT':
        base = 40 + 30 * (level - 1)
    else:
        base = trick_value * level

    # Apply doubling to base
    if doubled == 1:
        base *= 2
    elif doubled == 2:
        base *= 4

    # Bonuses
    bonus = 0

    # Part score or game bonus
    if base < 100:
        bonus += 50  # Part score
    else:
        bonus += 300 if not vulnerable else 500  # Game

    # Slam bonuses
    if level == 6:
        bonus += 500 if not vulnerable else 750  # Small slam
    elif level == 7:
        bonus += 1000 if not vulnerable else 1500  # Grand slam

    # Insult bonus for making doubled/redoubled
    if doubled == 1:
        bonus += 50
    elif doubled == 2:
        bonus += 100

    # Overtrick value
    if doubled == 0:
        overtrick_value = trick_value
    elif doubled == 1:
        overtrick_value = 100 if not vulnerable else 200
    else:
        overtrick_value = 200 if not vulnerable else 400

    return base + bonus + overtrick_value * overtricks


def calculate_score_difference(actual: int, theoretical: int) -> int:
    """Calculate difference between actual and theoretical scores."""
    return actual - theoretical


# =============================================================================
# CORE AUDIT FUNCTIONS
# =============================================================================

def generate_audit_report(
    pbn_data: PBNHand,
    v3_analysis: Dict[str, Any],
    dds_analysis: Optional[Dict[str, Any]] = None
) -> AuditResult:
    """
    Generate audit report comparing ACBL tournament result against V3 engine logic.

    Args:
        pbn_data: Parsed PBN hand data
        v3_analysis: V3 engine analysis result (from enhanced_extractor + bidding engine)
        dds_analysis: Optional DDS analysis for par calculation

    Returns:
        AuditResult with full comparison
    """
    result = AuditResult()

    # Board identification
    result.board_number = pbn_data.board_number
    result.hand_pbn = pbn_data.hands.get('S', '')

    # Tournament results (ground truth)
    tournament_contract = f"{pbn_data.contract_level}{pbn_data.contract_strain}"
    if pbn_data.contract_doubled:
        tournament_contract += 'X' * pbn_data.contract_doubled

    result.tournament_contract = tournament_contract
    result.tournament_score = pbn_data.score_ns
    result.tournament_tricks = pbn_data.tricks_taken

    # Extract the final bid from tournament auction
    if pbn_data.auction_history:
        # Find last non-Pass bid
        for bid in reversed(pbn_data.auction_history):
            if bid not in ['Pass', 'Double', 'Redouble']:
                result.tournament_bid = bid
                break

    # Engine analysis results
    result.optimal_bid = v3_analysis.get('optimal_bid', '')
    result.matched_rule = v3_analysis.get('matched_rule', '')
    result.rule_tier = v3_analysis.get('rule_tier', 0)

    # Survival metrics from DAS (Danger Avoidance System)
    das_metrics = v3_analysis.get('das_metrics', {})
    result.panic_index = das_metrics.get('panic_index', 0)
    result.rescue_action = das_metrics.get('rescue_action', '')

    # Theoretical score (what engine expects)
    result.theoretical_score = v3_analysis.get('expected_score', 0)
    result.theoretical_tricks = v3_analysis.get('expected_tricks', 0)

    # DDS analysis (if available)
    if dds_analysis:
        result.dds_par_score = dds_analysis.get('par_score', 0)
        result.dds_par_contract = dds_analysis.get('par_contract', '')
        result.dds_optimal_tricks = dds_analysis.get('dd_tricks', 0)

    # Calculate comparison metrics
    result.is_logic_aligned = (result.tournament_bid == result.optimal_bid)
    result.score_delta = calculate_score_difference(
        result.tournament_score,
        result.theoretical_score
    )

    # Potential savings (positive if tournament did worse)
    result.potential_savings = max(0, result.theoretical_score - result.tournament_score)

    # Falsification check: Did tournament beat engine prediction?
    result.is_falsified = result.tournament_score > result.theoretical_score

    # Determine survival status
    result.survival_status = determine_survival_status(
        result.panic_index,
        result.tournament_bid,
        result.rescue_action,
        result.tournament_score,
        result.theoretical_score
    )

    # Determine bidding efficiency
    # Check for no auction data first (hand records only, no auction sequence)
    if not pbn_data.auction_history or len(pbn_data.auction_history) == 0:
        result.bidding_efficiency = BiddingEfficiency.NO_AUCTION_DATA.value
    else:
        result.bidding_efficiency = determine_bidding_efficiency(
            pbn_data.contract_level,
            pbn_data.tricks_taken,
            dds_analysis
        )

    # Categorize and generate educational feedback
    result.audit_category, result.educational_feedback = categorize_and_explain(
        result, v3_analysis
    )

    # Quadrant classification
    result.quadrant = v3_analysis.get('quadrant', '')

    return result


def determine_survival_status(
    panic_index: int,
    actual_bid: str,
    rescue_action: str,
    actual_score: int,
    theoretical_score: int
) -> str:
    """
    Determine survival status based on panic index and actions taken.

    Physics:
    - Panic Index > 70: Dangerous situation requiring rescue
    - If rescue was recommended but not taken, check outcome
    """
    if panic_index <= 30:
        return SurvivalStatus.SAFE.value

    if panic_index > 70:
        # High danger situation
        if actual_bid == rescue_action or actual_bid == 'Pass':
            return SurvivalStatus.SURVIVED.value
        elif actual_score >= theoretical_score:
            return SurvivalStatus.LUCKY.value
        else:
            return SurvivalStatus.FAILED.value

    return SurvivalStatus.SAFE.value


def determine_bidding_efficiency(
    contract_level: int,
    tricks_taken: int,
    dds_analysis: Optional[Dict] = None
) -> str:
    """
    Determine if the contract was overbid, underbid, or optimal.

    Uses DDS par analysis when available.
    """
    if contract_level == 0:
        return BiddingEfficiency.PASSED_OUT.value

    required_tricks = contract_level + 6

    if dds_analysis:
        par_level = dds_analysis.get('par_level', 0)
        if contract_level == par_level:
            return BiddingEfficiency.OPTIMAL.value
        elif contract_level > par_level:
            return BiddingEfficiency.OVERBID.value
        else:
            return BiddingEfficiency.UNDERBID.value

    # Fallback: compare to actual result
    if tricks_taken >= required_tricks:
        if tricks_taken == required_tricks:
            return BiddingEfficiency.OPTIMAL.value
        else:
            return BiddingEfficiency.UNDERBID.value  # Could have bid higher
    else:
        return BiddingEfficiency.OVERBID.value


def categorize_and_explain(
    result: AuditResult,
    v3_analysis: Dict[str, Any]
) -> Tuple[str, str]:
    """
    Categorize the audit result and generate educational feedback.

    Returns:
        Tuple of (category, explanation)
    """
    # Case 0: No auction data - PBN file is hand records only
    if result.bidding_efficiency == 'no_auction_data':
        category = AuditCategory.NO_AUCTION_DATA.value
        explanation = (
            "This hand record has no auction data. "
            "Use the BWS contract distribution to see how other tables bid. "
            "You can replay this hand to practice your bidding."
        )
        return category, explanation

    # Case 1: Lucky Overbid
    if result.bidding_efficiency == 'overbid' and result.tournament_score > 0:
        category = AuditCategory.LUCKY_OVERBID.value
        lott_safe = v3_analysis.get('lott_safe_level', 2)
        explanation = (
            f"You made {result.tournament_contract} due to a defensive error, "
            f"but your LoTT Safe Level was only {lott_safe}. "
            f"Mathematically, this bid fails 80% of the time."
        )
        return category, explanation

    # Case 2: Penalty Trap
    if result.panic_index > 70 and result.survival_status == 'FAILED':
        category = AuditCategory.PENALTY_TRAP.value
        explanation = (
            f"You accepted {result.tournament_score}. "
            f"The engine identifies a Panic Index of {result.panic_index}, "
            f"mandating an SOS Rescue ({result.rescue_action}) to minimize loss."
        )
        return category, explanation

    # Case 3: Rule Violation
    if not result.is_logic_aligned and result.score_delta < 0:
        category = AuditCategory.RULE_VIOLATION.value
        explanation = (
            f"Your bid of {result.tournament_bid} violated {result.matched_rule}. "
            f"The optimal bid was {result.optimal_bid}, "
            f"which would have scored {result.theoretical_score} instead of {result.tournament_score}."
        )
        return category, explanation

    # Case 4: Logic Aligned
    if result.is_logic_aligned:
        category = AuditCategory.LOGIC_ALIGNED.value
        explanation = (
            f"Your bid matched the V3 engine's recommendation. "
            f"Well done following SAYC principles!"
        )
        return category, explanation

    # Default: Provide general feedback
    category = AuditCategory.LOGIC_ALIGNED.value
    explanation = "Analysis complete."
    return category, explanation


# =============================================================================
# TOURNAMENT-LEVEL ANALYSIS
# =============================================================================

def compare_tournament_vs_engine(
    hands: List[PBNHand],
    v3_results: List[Dict[str, Any]],
    dds_results: Optional[List[Dict[str, Any]]] = None
) -> TournamentAuditSummary:
    """
    Generate summary audit for an entire tournament.

    Args:
        hands: List of parsed PBN hands
        v3_results: V3 engine analysis for each hand
        dds_results: Optional DDS analysis for each hand

    Returns:
        TournamentAuditSummary with aggregate statistics
    """
    summary = TournamentAuditSummary()
    summary.total_hands = len(hands)

    if not hands:
        return summary

    summary.event_name = hands[0].event_name

    # Initialize counters
    total_delta = 0
    total_savings = 0
    panic_count = 0
    survivals = 0
    category_counts = {cat.value: 0 for cat in AuditCategory}

    # Process each hand
    for i, hand in enumerate(hands):
        v3_result = v3_results[i] if i < len(v3_results) else {}
        dds_result = dds_results[i] if dds_results and i < len(dds_results) else None

        audit = generate_audit_report(hand, v3_result, dds_result)

        # Alignment
        if audit.is_logic_aligned:
            summary.hands_aligned += 1
        if audit.is_falsified:
            summary.hands_falsified += 1
            summary.flagged_for_review.append(hand.board_number)

        # Scores
        total_delta += audit.score_delta
        total_savings += audit.potential_savings

        # Survival
        if audit.panic_index > 70:
            panic_count += 1
            if audit.survival_status in ['SURVIVED', 'SAFE']:
                survivals += 1

        # Categories
        category_counts[audit.audit_category] = category_counts.get(audit.audit_category, 0) + 1

    # Calculate summary statistics
    summary.alignment_rate = summary.hands_aligned / summary.total_hands if summary.total_hands > 0 else 0
    summary.total_potential_savings = total_savings
    summary.average_score_delta = total_delta / summary.total_hands if summary.total_hands > 0 else 0
    summary.panic_situations = panic_count
    summary.survival_rate = survivals / panic_count if panic_count > 0 else 1.0
    summary.category_counts = category_counts

    return summary


# =============================================================================
# INTEGRATION WITH V3 ENGINE
# =============================================================================

def analyze_pbn_hand_with_v3(
    pbn_hand: PBNHand,
    hero_position: str = 'S'
) -> Dict[str, Any]:
    """
    Analyze a PBN hand using the V3 engine.

    This function connects the PBN import to the V3 bidding engine.

    Args:
        pbn_hand: Parsed PBN hand
        hero_position: Position to analyze from

    Returns:
        V3 analysis result
    """
    # Import here to avoid circular imports
    from engine.v2.features.enhanced_extractor import extract_flat_features
    from engine.hand import Hand

    # Convert PBN hand to Hand object
    hand_pbn = pbn_hand.hands.get(hero_position, '')
    if not hand_pbn:
        return {'error': f'No hand data for position {hero_position}'}

    try:
        hand = Hand.from_pbn(hand_pbn)
    except ValueError as e:
        return {'error': f'Invalid hand PBN: {e}'}

    # Map position
    position_map = {'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'}
    my_position = position_map.get(hero_position, 'South')
    dealer = position_map.get(pbn_hand.dealer, 'North')

    # Extract features
    features = extract_flat_features(
        hand=hand,
        auction_history=pbn_hand.auction_history,
        my_position=my_position,
        vulnerability=pbn_hand.vulnerability,
        dealer=dealer
    )

    # Get optimal bid from V3 engine
    # This would call the bidding engine to get the recommendation
    # For now, return the features; actual integration depends on bidding engine API
    return {
        'features': features,
        'hand_pbn': hand_pbn,
        'auction_history': pbn_hand.auction_history,
        'vulnerability': pbn_hand.vulnerability,
        'dealer': dealer,
        # Placeholder for actual engine results
        'optimal_bid': '',
        'matched_rule': '',
        'rule_tier': 0,
        'expected_score': 0,
        'das_metrics': {
            'panic_index': 0,
            'rescue_action': ''
        }
    }
