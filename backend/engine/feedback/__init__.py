"""
Gameplay Feedback System

Provides real-time and post-game feedback on bidding and card play decisions.

Bidding Feedback: Evaluates bids against SAYC conventions
Play Feedback: Uses DDS (Double Dummy Solver) for optimal play analysis
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
    'get_play_feedback_generator'
]
