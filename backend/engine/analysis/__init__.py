"""
Bridge Analysis Engine - Comprehensive hand analysis for bidding and play.

This module provides:
- BridgeAnalysisEngine: Main analysis class for post-game evaluation
- HandAnalysisResult: Structured result object for all analysis data
- Quadrant/BidEfficiency enums: Classification types

Usage:
    from engine.analysis import BridgeAnalysisEngine, get_analysis_engine

    # Get singleton engine
    engine = get_analysis_engine()

    # Analyze a completed hand
    result = engine.analyze_hand(
        hands=hands_dict,
        contract=contract,
        play_history=play_sequence,
        actual_tricks=tricks_taken,
        actual_score=score,
        vulnerability='NS'
    )

    # Store to database
    engine.store_analysis(session_hand_id, result)
"""

from .analysis_engine import (
    BridgeAnalysisEngine,
    HandAnalysisResult,
    Quadrant,
    BidEfficiency,
    LeadQuality,
    MajorError,
    OpeningLeadAnalysis,
    get_analysis_engine,
)

__all__ = [
    'BridgeAnalysisEngine',
    'HandAnalysisResult',
    'Quadrant',
    'BidEfficiency',
    'LeadQuality',
    'MajorError',
    'OpeningLeadAnalysis',
    'get_analysis_engine',
]
