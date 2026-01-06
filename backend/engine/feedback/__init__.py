"""
Gameplay Feedback System

Provides real-time and post-game feedback on bidding and card play decisions.

Bidding Feedback: Evaluates bids against SAYC conventions
Play Feedback: Uses DDS (Double Dummy Solver) for optimal play analysis
Signal Integrity: Analyzes signaling consistency for partner deduction
"""

from engine.feedback.bidding_feedback import (
    BiddingFeedback,
    BiddingFeedbackGenerator,
    CorrectnessLevel,
    ImpactLevel
)

from engine.feedback.play_feedback import (
    PlayFeedback,
    PlayFeedbackGenerator,
    PlayCorrectnessLevel,
    PlayCategory,
    get_play_feedback_generator
)

from engine.feedback.signal_integrity_auditor import (
    SignalIntegrityAuditor,
    SignalIntegrityReport,
    DeductionConfidence,
    analyze_signal_integrity,
    get_signal_integrity_auditor
)

__all__ = [
    # Bidding feedback
    'BiddingFeedback',
    'BiddingFeedbackGenerator',
    'CorrectnessLevel',
    'ImpactLevel',
    # Play feedback
    'PlayFeedback',
    'PlayFeedbackGenerator',
    'PlayCorrectnessLevel',
    'PlayCategory',
    'get_play_feedback_generator',
    # Signal integrity
    'SignalIntegrityAuditor',
    'SignalIntegrityReport',
    'DeductionConfidence',
    'analyze_signal_integrity',
    'get_signal_integrity_auditor'
]
