"""
Signal Integrity Auditor (SIR) - Deduction Confidence Scoring

Analyzes signaling consistency across a hand to generate a "Deduction Confidence"
score that tells users how well they're communicating with their AI partner
through standard bridge signals.

The Problem:
- Bridge signaling (attitude, count, suit preference) requires CONSISTENCY
- A single wrong signal can mislead partner for the entire hand
- Users need feedback on their overall signaling quality, not just individual plays

The Solution:
- Track signal consistency across all plays in a hand
- Generate a Signal Integrity Score (0-100%)
- Provide a Deduction Confidence rating (Expert/Competent/Inconsistent/Chaotic)
- Identify which signal types are most often violated
- Give specific recommendations for improvement

Usage:
    from engine.feedback.signal_integrity_auditor import SignalIntegrityAuditor, SignalIntegrityReport

    # Get play feedback objects for a hand
    feedbacks = [play_feedback_1, play_feedback_2, ...]

    # Generate report
    auditor = SignalIntegrityAuditor()
    report = auditor.analyze(feedbacks)

    print(f"Score: {report.signal_integrity_score}%")
    print(f"Rating: {report.deduction_confidence}")
    print(f"Recommendations: {report.recommendations}")
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum


class DeductionConfidence(Enum):
    """
    Deduction confidence levels based on signal integrity.

    These ratings tell users how well their partner can trust their signals.
    """
    EXPERT = "expert"           # 90-100%: Partner can trust signals completely
    COMPETENT = "competent"     # 70-89%: Partner can mostly rely on signals
    INCONSISTENT = "inconsistent"  # 50-69%: Partner is confused by mixed signals
    CHAOTIC = "chaotic"         # <50%: Partner cannot deduce anything from signals


@dataclass
class SignalIntegrityReport:
    """
    Report on signaling consistency across a hand.

    This report summarizes how well the user followed standard bridge
    signaling conventions, enabling partner deduction analysis.
    """

    # Core metrics
    signal_integrity_score: float  # 0-100 percentage
    deduction_confidence: str      # "expert", "competent", "inconsistent", "chaotic"

    # Raw counts
    total_signals: int             # Total plays where signaling applied
    optimal_signals: int           # Plays that followed conventions

    # Breakdown by signal type
    violation_breakdown: Dict[str, int] = field(default_factory=dict)
    # Maps heuristic type (e.g., "MIN_OF_EQUALS", "ATTITUDE_SIGNAL") to violation count

    # Recommendations for improvement
    recommendations: List[str] = field(default_factory=list)

    # Detailed signal data (optional, for UI display)
    signal_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return {
            'signal_integrity_score': round(self.signal_integrity_score, 1),
            'deduction_confidence': self.deduction_confidence,
            'total_signals': self.total_signals,
            'optimal_signals': self.optimal_signals,
            'violation_breakdown': self.violation_breakdown,
            'recommendations': self.recommendations,
            'signal_details': self.signal_details
        }


class SignalIntegrityAuditor:
    """
    Auditor that analyzes signaling consistency across plays.

    This class is STATELESS - it takes a list of PlayFeedback objects
    and generates a SignalIntegrityReport. It does not store any state
    between calls.
    """

    # Thresholds for deduction confidence levels
    EXPERT_THRESHOLD = 90.0
    COMPETENT_THRESHOLD = 70.0
    INCONSISTENT_THRESHOLD = 50.0

    # Signal heuristic display names for user-friendly output
    HEURISTIC_DISPLAY_NAMES = {
        'min_of_equals': '2nd Hand Low',
        'max_of_equals': '3rd Hand High',
        'top_of_sequence': 'Top of Sequence',
        'bottom_of_sequence': 'Bottom of Sequence',
        'attitude_signal': 'Attitude Signal',
        'count_signal': 'Count Signal',
        'cheapest_winner': 'Win Cheaply',
        'protect_stoppers': 'Protect Stoppers',
        'discard_from_length': 'Discard from Length',
        'declarer_conserve': 'Conserve Winners',
        'defensive_defer': 'Defer to Partner'
    }

    # Recommendations based on violation patterns
    RECOMMENDATIONS = {
        'min_of_equals': "Practice 2nd hand low: When playing second to a trick, preserve your high cards for when they're needed.",
        'max_of_equals': "Work on 3rd hand high: When playing third, use your high cards to force declarer or win the trick.",
        'top_of_sequence': "Lead top of touching honors: When leading from KQJ or QJT, lead the highest to show the sequence.",
        'bottom_of_sequence': "Follow with bottom of sequence: When following suit from a sequence, play the lower card to signal the higher ones.",
        'attitude_signal': "Improve attitude signals: High cards encourage partner to lead the suit, low cards discourage.",
        'count_signal': "Practice count signals: High-low shows even count, low-high shows odd count.",
        'cheapest_winner': "Win with your cheapest card: When winning a trick, use the lowest card that gets the job done.",
        'protect_stoppers': "Protect your stoppers: Don't discard the only high card guarding a suit.",
        'discard_from_length': "Discard from long suits: Keep cards in short suits where high cards are more valuable.",
        'declarer_conserve': "Conserve as declarer: When your side is already winning, play low to save high cards for later.",
        'defensive_defer': "Support your partner's winners: Don't waste your high cards when partner is already winning."
    }

    def analyze(self, play_feedbacks: List[Any]) -> SignalIntegrityReport:
        """
        Analyze a collection of play feedbacks for signal consistency.

        Args:
            play_feedbacks: List of PlayFeedback objects or dicts with signal fields.
                           Can be from PlayFeedback dataclass or database rows.

        Returns:
            SignalIntegrityReport with analysis results

        Note: This method is stateless and can be called multiple times
        with different feedback sets.
        """
        # Extract signal-relevant plays
        signal_plays = self._extract_signal_plays(play_feedbacks)

        if not signal_plays:
            # No signals to analyze - return perfect score with no data
            return SignalIntegrityReport(
                signal_integrity_score=100.0,
                deduction_confidence=DeductionConfidence.EXPERT.value,
                total_signals=0,
                optimal_signals=0,
                violation_breakdown={},
                recommendations=["No signaling situations occurred in this hand."],
                signal_details=[]
            )

        # Count optimal vs violated signals
        total_signals = len(signal_plays)
        optimal_signals = sum(1 for p in signal_plays if p['is_signal_optimal'])
        violated_signals = total_signals - optimal_signals

        # Calculate integrity score
        signal_integrity_score = (optimal_signals / total_signals) * 100.0 if total_signals > 0 else 100.0

        # Determine confidence level
        deduction_confidence = self._calculate_confidence_level(signal_integrity_score)

        # Build violation breakdown
        violation_breakdown = self._build_violation_breakdown(signal_plays)

        # Generate recommendations
        recommendations = self._generate_recommendations(violation_breakdown, signal_integrity_score)

        # Build signal details for UI
        signal_details = self._build_signal_details(signal_plays)

        return SignalIntegrityReport(
            signal_integrity_score=signal_integrity_score,
            deduction_confidence=deduction_confidence,
            total_signals=total_signals,
            optimal_signals=optimal_signals,
            violation_breakdown=violation_breakdown,
            recommendations=recommendations,
            signal_details=signal_details
        )

    def _extract_signal_plays(self, play_feedbacks: List[Any]) -> List[Dict]:
        """
        Extract plays where signaling conventions applied.

        A play is signal-relevant if:
        1. signal_heuristic is not None (a convention was identified)
        2. The play was in the user's position (not AI plays)

        Args:
            play_feedbacks: List of PlayFeedback objects or dicts

        Returns:
            List of dicts with signal-relevant fields
        """
        signal_plays = []

        for feedback in play_feedbacks:
            # Handle both PlayFeedback objects and dicts
            if hasattr(feedback, 'signal_heuristic'):
                # PlayFeedback dataclass
                heuristic = feedback.signal_heuristic
                is_optimal = feedback.is_signal_optimal
                context = feedback.signal_context
                reason = feedback.signal_reason
                user_card = feedback.user_card
                trick_number = feedback.trick_number
            elif isinstance(feedback, dict):
                # Dict from database
                heuristic = feedback.get('signal_heuristic')
                is_optimal = feedback.get('is_signal_optimal', True)
                context = feedback.get('signal_context')
                reason = feedback.get('signal_reason')
                user_card = feedback.get('user_card')
                trick_number = feedback.get('trick_number')
            else:
                # Unknown format, skip
                continue

            # Only include plays where a signal heuristic was identified
            if heuristic:
                signal_plays.append({
                    'heuristic': heuristic,
                    'is_signal_optimal': is_optimal,
                    'context': context,
                    'reason': reason,
                    'user_card': user_card,
                    'trick_number': trick_number
                })

        return signal_plays

    def _calculate_confidence_level(self, score: float) -> str:
        """
        Determine deduction confidence level based on score.

        Args:
            score: Signal integrity score (0-100)

        Returns:
            Confidence level string
        """
        if score >= self.EXPERT_THRESHOLD:
            return DeductionConfidence.EXPERT.value
        elif score >= self.COMPETENT_THRESHOLD:
            return DeductionConfidence.COMPETENT.value
        elif score >= self.INCONSISTENT_THRESHOLD:
            return DeductionConfidence.INCONSISTENT.value
        else:
            return DeductionConfidence.CHAOTIC.value

    def _build_violation_breakdown(self, signal_plays: List[Dict]) -> Dict[str, int]:
        """
        Count violations by heuristic type.

        Args:
            signal_plays: List of signal-relevant plays

        Returns:
            Dict mapping heuristic type to violation count
        """
        breakdown = {}

        for play in signal_plays:
            if not play['is_signal_optimal']:
                heuristic = play['heuristic']
                breakdown[heuristic] = breakdown.get(heuristic, 0) + 1

        return breakdown

    def _generate_recommendations(self, violation_breakdown: Dict[str, int],
                                   score: float) -> List[str]:
        """
        Generate improvement recommendations based on violation patterns.

        Args:
            violation_breakdown: Dict of heuristic -> violation count
            score: Overall signal integrity score

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Sort violations by frequency (most common first)
        sorted_violations = sorted(
            violation_breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Add recommendations for top 3 most frequent violations
        for heuristic, count in sorted_violations[:3]:
            if heuristic in self.RECOMMENDATIONS:
                recommendations.append(self.RECOMMENDATIONS[heuristic])
            else:
                # Fallback for unknown heuristic types
                display_name = self.HEURISTIC_DISPLAY_NAMES.get(heuristic, heuristic)
                recommendations.append(f"Review {display_name} conventions for more consistent signaling.")

        # Add general recommendations based on score
        if score >= self.EXPERT_THRESHOLD:
            if not recommendations:
                recommendations.append("Excellent signaling! Your partner can fully trust your conventions.")
        elif score >= self.COMPETENT_THRESHOLD:
            recommendations.append("Good signaling overall. Focus on the areas above to reach expert level.")
        elif score >= self.INCONSISTENT_THRESHOLD:
            recommendations.append("Your signals are sending mixed messages. Practice the conventions above.")
        else:
            recommendations.insert(0, "Your signaling is confusing your partner. Focus on learning one signal type at a time.")

        return recommendations

    def _build_signal_details(self, signal_plays: List[Dict]) -> List[Dict]:
        """
        Build detailed signal information for UI display.

        Args:
            signal_plays: List of signal-relevant plays

        Returns:
            List of dicts with signal details for each play
        """
        details = []

        for play in signal_plays:
            heuristic = play['heuristic']
            display_name = self.HEURISTIC_DISPLAY_NAMES.get(heuristic, heuristic)

            details.append({
                'trick_number': play['trick_number'],
                'card': play['user_card'],
                'signal_type': display_name,
                'followed_convention': play['is_signal_optimal'],
                'expected_signal': play['reason'] if not play['is_signal_optimal'] else None,
                'context': play['context']
            })

        return details


# Convenience function for external use
def get_signal_integrity_auditor() -> SignalIntegrityAuditor:
    """Get a SignalIntegrityAuditor instance."""
    return SignalIntegrityAuditor()


def analyze_signal_integrity(play_feedbacks: List[Any]) -> SignalIntegrityReport:
    """
    Convenience function to analyze signal integrity.

    Args:
        play_feedbacks: List of PlayFeedback objects or dicts

    Returns:
        SignalIntegrityReport with analysis
    """
    auditor = SignalIntegrityAuditor()
    return auditor.analyze(play_feedbacks)


# Self-test
if __name__ == '__main__':
    print("Signal Integrity Auditor - Self Test")
    print("=" * 50)

    # Create mock play feedback data
    mock_feedbacks = [
        {
            'trick_number': 1,
            'user_card': '7♠',
            'signal_heuristic': 'min_of_equals',
            'signal_context': 'SECOND_HAND_FOLLOW',
            'signal_reason': '2nd Hand Low: Preserving higher honors.',
            'is_signal_optimal': True
        },
        {
            'trick_number': 2,
            'user_card': 'Q♠',
            'signal_heuristic': 'max_of_equals',
            'signal_context': 'THIRD_HAND_FOLLOW',
            'signal_reason': '3rd Hand High: Forcing declarer.',
            'is_signal_optimal': False  # Violation!
        },
        {
            'trick_number': 3,
            'user_card': '3♥',
            'signal_heuristic': 'attitude_signal',
            'signal_context': 'DISCARD_FIRST',
            'signal_reason': 'Attitude Signal: Discouraging hearts.',
            'is_signal_optimal': True
        },
        {
            'trick_number': 4,
            'user_card': 'K♦',
            'signal_heuristic': 'top_of_sequence',
            'signal_context': 'LEAD_FROM_HONOR_SEQUENCE',
            'signal_reason': 'Top of Sequence: Leading K from KQJ.',
            'is_signal_optimal': False  # Violation!
        },
        {
            'trick_number': 5,
            'user_card': '5♣',
            'signal_heuristic': 'min_of_equals',
            'signal_context': 'SECOND_HAND_FOLLOW',
            'signal_reason': '2nd Hand Low.',
            'is_signal_optimal': True
        }
    ]

    auditor = SignalIntegrityAuditor()
    report = auditor.analyze(mock_feedbacks)

    print(f"\nSignal Integrity Score: {report.signal_integrity_score:.1f}%")
    print(f"Deduction Confidence: {report.deduction_confidence}")
    print(f"Total Signals: {report.total_signals}")
    print(f"Optimal Signals: {report.optimal_signals}")
    print(f"\nViolation Breakdown:")
    for heuristic, count in report.violation_breakdown.items():
        print(f"  {heuristic}: {count}")
    print(f"\nRecommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")

    # Verify expected results
    assert report.total_signals == 5, f"Expected 5 signals, got {report.total_signals}"
    assert report.optimal_signals == 3, f"Expected 3 optimal, got {report.optimal_signals}"
    assert report.signal_integrity_score == 60.0, f"Expected 60%, got {report.signal_integrity_score}%"
    assert report.deduction_confidence == 'inconsistent', f"Expected 'inconsistent', got {report.deduction_confidence}"
    assert 'max_of_equals' in report.violation_breakdown
    assert 'top_of_sequence' in report.violation_breakdown

    print("\n" + "=" * 50)
    print("All self-tests passed!")
