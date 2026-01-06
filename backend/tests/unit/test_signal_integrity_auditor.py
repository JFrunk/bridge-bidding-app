"""
Tests for the Signal Integrity Auditor.

Tests cover:
- Basic scoring calculations
- Deduction confidence levels
- Violation breakdown by heuristic type
- Recommendation generation
- Edge cases (empty data, all optimal, all violations)
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.feedback.signal_integrity_auditor import (
    SignalIntegrityAuditor,
    SignalIntegrityReport,
    DeductionConfidence,
    analyze_signal_integrity,
    get_signal_integrity_auditor
)


class TestSignalIntegrityAuditor:
    """Test suite for SignalIntegrityAuditor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.auditor = SignalIntegrityAuditor()

    # =========================================================================
    # Basic Functionality Tests
    # =========================================================================

    def test_empty_feedbacks_returns_perfect_score(self):
        """Empty feedback list should return perfect score with no data message."""
        report = self.auditor.analyze([])

        assert report.signal_integrity_score == 100.0
        assert report.deduction_confidence == 'expert'
        assert report.total_signals == 0
        assert report.optimal_signals == 0
        assert len(report.recommendations) == 1
        assert 'No signaling situations' in report.recommendations[0]

    def test_all_optimal_signals_returns_expert(self):
        """All optimal signals should return expert rating."""
        feedbacks = [
            {
                'trick_number': i,
                'user_card': f'{i}♠',
                'signal_heuristic': 'min_of_equals',
                'signal_context': 'SECOND_HAND_FOLLOW',
                'signal_reason': '2nd Hand Low',
                'is_signal_optimal': True
            }
            for i in range(1, 6)
        ]

        report = self.auditor.analyze(feedbacks)

        assert report.signal_integrity_score == 100.0
        assert report.deduction_confidence == 'expert'
        assert report.total_signals == 5
        assert report.optimal_signals == 5
        assert len(report.violation_breakdown) == 0

    def test_all_violations_returns_chaotic(self):
        """All signal violations should return chaotic rating."""
        feedbacks = [
            {
                'trick_number': i,
                'user_card': f'{i}♠',
                'signal_heuristic': 'min_of_equals',
                'signal_context': 'SECOND_HAND_FOLLOW',
                'signal_reason': '2nd Hand Low',
                'is_signal_optimal': False
            }
            for i in range(1, 6)
        ]

        report = self.auditor.analyze(feedbacks)

        assert report.signal_integrity_score == 0.0
        assert report.deduction_confidence == 'chaotic'
        assert report.total_signals == 5
        assert report.optimal_signals == 0
        assert report.violation_breakdown.get('min_of_equals') == 5

    # =========================================================================
    # Score Threshold Tests
    # =========================================================================

    def test_expert_threshold_exactly_90(self):
        """90% should be expert."""
        feedbacks = self._create_mixed_feedbacks(optimal=9, violations=1)
        report = self.auditor.analyze(feedbacks)

        assert report.signal_integrity_score == 90.0
        assert report.deduction_confidence == 'expert'

    def test_competent_threshold_exactly_70(self):
        """70% should be competent."""
        feedbacks = self._create_mixed_feedbacks(optimal=7, violations=3)
        report = self.auditor.analyze(feedbacks)

        assert report.signal_integrity_score == 70.0
        assert report.deduction_confidence == 'competent'

    def test_inconsistent_threshold_exactly_50(self):
        """50% should be inconsistent."""
        feedbacks = self._create_mixed_feedbacks(optimal=5, violations=5)
        report = self.auditor.analyze(feedbacks)

        assert report.signal_integrity_score == 50.0
        assert report.deduction_confidence == 'inconsistent'

    def test_chaotic_threshold_below_50(self):
        """Below 50% should be chaotic."""
        feedbacks = self._create_mixed_feedbacks(optimal=4, violations=6)
        report = self.auditor.analyze(feedbacks)

        assert report.signal_integrity_score == 40.0
        assert report.deduction_confidence == 'chaotic'

    def test_competent_range_89_percent(self):
        """89% should still be competent (not expert)."""
        feedbacks = self._create_mixed_feedbacks(optimal=89, violations=11)
        report = self.auditor.analyze(feedbacks)

        assert 89.0 <= report.signal_integrity_score < 90.0
        assert report.deduction_confidence == 'competent'

    # =========================================================================
    # Violation Breakdown Tests
    # =========================================================================

    def test_violation_breakdown_counts_by_heuristic(self):
        """Violations should be counted by heuristic type."""
        feedbacks = [
            {'trick_number': 1, 'user_card': '7♠', 'signal_heuristic': 'min_of_equals',
             'signal_context': 'SECOND_HAND', 'signal_reason': 'test', 'is_signal_optimal': False},
            {'trick_number': 2, 'user_card': '8♠', 'signal_heuristic': 'min_of_equals',
             'signal_context': 'SECOND_HAND', 'signal_reason': 'test', 'is_signal_optimal': False},
            {'trick_number': 3, 'user_card': '9♠', 'signal_heuristic': 'max_of_equals',
             'signal_context': 'THIRD_HAND', 'signal_reason': 'test', 'is_signal_optimal': False},
            {'trick_number': 4, 'user_card': 'T♠', 'signal_heuristic': 'attitude_signal',
             'signal_context': 'DISCARD', 'signal_reason': 'test', 'is_signal_optimal': True},
        ]

        report = self.auditor.analyze(feedbacks)

        assert report.violation_breakdown.get('min_of_equals') == 2
        assert report.violation_breakdown.get('max_of_equals') == 1
        assert 'attitude_signal' not in report.violation_breakdown  # Optimal, not a violation

    def test_only_violations_in_breakdown(self):
        """Breakdown should only contain violated heuristics, not optimal ones."""
        feedbacks = [
            {'trick_number': 1, 'user_card': '7♠', 'signal_heuristic': 'min_of_equals',
             'signal_context': 'X', 'signal_reason': 'test', 'is_signal_optimal': True},
            {'trick_number': 2, 'user_card': '8♠', 'signal_heuristic': 'max_of_equals',
             'signal_context': 'X', 'signal_reason': 'test', 'is_signal_optimal': True},
        ]

        report = self.auditor.analyze(feedbacks)

        assert len(report.violation_breakdown) == 0

    # =========================================================================
    # Recommendation Tests
    # =========================================================================

    def test_recommendations_for_top_violations(self):
        """Recommendations should address the most frequent violations."""
        feedbacks = [
            {'trick_number': i, 'user_card': f'{i}♠', 'signal_heuristic': 'min_of_equals',
             'signal_context': 'X', 'signal_reason': 'test', 'is_signal_optimal': False}
            for i in range(1, 4)
        ] + [
            {'trick_number': i, 'user_card': f'{i}♠', 'signal_heuristic': 'attitude_signal',
             'signal_context': 'X', 'signal_reason': 'test', 'is_signal_optimal': False}
            for i in range(4, 6)
        ]

        report = self.auditor.analyze(feedbacks)

        # Should have recommendations for both heuristics
        recommendation_text = ' '.join(report.recommendations)
        assert '2nd hand low' in recommendation_text.lower() or 'second hand' in recommendation_text.lower()
        assert 'attitude' in recommendation_text.lower()

    def test_expert_gets_positive_recommendation(self):
        """Expert level should receive positive feedback."""
        feedbacks = self._create_mixed_feedbacks(optimal=10, violations=0)
        report = self.auditor.analyze(feedbacks)

        assert any('excellent' in rec.lower() or 'trust' in rec.lower()
                   for rec in report.recommendations)

    def test_chaotic_gets_urgent_recommendation(self):
        """Chaotic level should receive urgent improvement message."""
        feedbacks = self._create_mixed_feedbacks(optimal=2, violations=8)
        report = self.auditor.analyze(feedbacks)

        assert any('confusing' in rec.lower() or 'focus' in rec.lower()
                   for rec in report.recommendations)

    # =========================================================================
    # Signal Details Tests
    # =========================================================================

    def test_signal_details_includes_all_signals(self):
        """Signal details should include all signal-relevant plays."""
        feedbacks = [
            {'trick_number': 1, 'user_card': '7♠', 'signal_heuristic': 'min_of_equals',
             'signal_context': 'SECOND_HAND_FOLLOW', 'signal_reason': 'Test reason', 'is_signal_optimal': True},
            {'trick_number': 2, 'user_card': 'Q♠', 'signal_heuristic': 'max_of_equals',
             'signal_context': 'THIRD_HAND_FOLLOW', 'signal_reason': 'Test reason 2', 'is_signal_optimal': False},
        ]

        report = self.auditor.analyze(feedbacks)

        assert len(report.signal_details) == 2
        assert report.signal_details[0]['trick_number'] == 1
        assert report.signal_details[0]['card'] == '7♠'
        assert report.signal_details[0]['followed_convention'] is True
        assert report.signal_details[1]['followed_convention'] is False

    def test_signal_details_has_display_names(self):
        """Signal details should use human-readable signal type names."""
        feedbacks = [
            {'trick_number': 1, 'user_card': '7♠', 'signal_heuristic': 'min_of_equals',
             'signal_context': 'SECOND_HAND', 'signal_reason': 'test', 'is_signal_optimal': True},
        ]

        report = self.auditor.analyze(feedbacks)

        # Should use display name, not raw heuristic
        assert report.signal_details[0]['signal_type'] == '2nd Hand Low'

    # =========================================================================
    # Edge Case Tests
    # =========================================================================

    def test_feedbacks_without_signal_heuristic_ignored(self):
        """Plays without signal_heuristic should be ignored."""
        feedbacks = [
            {'trick_number': 1, 'user_card': '7♠', 'signal_heuristic': None,
             'signal_context': None, 'signal_reason': None, 'is_signal_optimal': True},
            {'trick_number': 2, 'user_card': '8♠', 'signal_heuristic': 'min_of_equals',
             'signal_context': 'X', 'signal_reason': 'test', 'is_signal_optimal': True},
        ]

        report = self.auditor.analyze(feedbacks)

        assert report.total_signals == 1  # Only one had heuristic

    def test_mixed_object_and_dict_feedbacks(self):
        """Should handle both dict and object-like feedbacks."""
        # Create a mock object with attributes
        class MockFeedback:
            def __init__(self):
                self.trick_number = 1
                self.user_card = '7♠'
                self.signal_heuristic = 'min_of_equals'
                self.signal_context = 'SECOND_HAND'
                self.signal_reason = 'test'
                self.is_signal_optimal = True

        feedbacks = [
            MockFeedback(),
            {'trick_number': 2, 'user_card': '8♠', 'signal_heuristic': 'max_of_equals',
             'signal_context': 'THIRD_HAND', 'signal_reason': 'test', 'is_signal_optimal': False},
        ]

        report = self.auditor.analyze(feedbacks)

        assert report.total_signals == 2
        assert report.optimal_signals == 1

    def test_unknown_heuristic_type_handled(self):
        """Unknown heuristic types should be handled gracefully."""
        feedbacks = [
            {'trick_number': 1, 'user_card': '7♠', 'signal_heuristic': 'unknown_heuristic_xyz',
             'signal_context': 'X', 'signal_reason': 'test', 'is_signal_optimal': False},
        ]

        report = self.auditor.analyze(feedbacks)

        assert report.total_signals == 1
        assert 'unknown_heuristic_xyz' in report.violation_breakdown
        # Should still generate a recommendation
        assert len(report.recommendations) > 0

    # =========================================================================
    # Report Serialization Tests
    # =========================================================================

    def test_to_dict_returns_serializable(self):
        """to_dict should return JSON-serializable data."""
        import json

        feedbacks = self._create_mixed_feedbacks(optimal=8, violations=2)
        report = self.auditor.analyze(feedbacks)

        # Should not raise
        serialized = json.dumps(report.to_dict())
        assert isinstance(serialized, str)

        # Verify structure
        data = report.to_dict()
        assert 'signal_integrity_score' in data
        assert 'deduction_confidence' in data
        assert 'total_signals' in data
        assert 'optimal_signals' in data
        assert 'violation_breakdown' in data
        assert 'recommendations' in data

    def test_score_rounded_in_to_dict(self):
        """Score should be rounded to 1 decimal in to_dict."""
        feedbacks = self._create_mixed_feedbacks(optimal=7, violations=3)
        report = self.auditor.analyze(feedbacks)

        data = report.to_dict()
        # 70% should be exactly 70.0
        assert data['signal_integrity_score'] == 70.0

    # =========================================================================
    # Convenience Function Tests
    # =========================================================================

    def test_analyze_signal_integrity_function(self):
        """Convenience function should work correctly."""
        feedbacks = self._create_mixed_feedbacks(optimal=8, violations=2)
        report = analyze_signal_integrity(feedbacks)

        assert isinstance(report, SignalIntegrityReport)
        assert report.signal_integrity_score == 80.0

    def test_get_signal_integrity_auditor_function(self):
        """Convenience function should return auditor instance."""
        auditor = get_signal_integrity_auditor()
        assert isinstance(auditor, SignalIntegrityAuditor)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _create_mixed_feedbacks(self, optimal: int, violations: int) -> list:
        """Create a list of feedbacks with specified optimal and violation counts."""
        feedbacks = []

        for i in range(optimal):
            feedbacks.append({
                'trick_number': i + 1,
                'user_card': f'{i % 10}♠',
                'signal_heuristic': 'min_of_equals',
                'signal_context': 'SECOND_HAND_FOLLOW',
                'signal_reason': 'Test',
                'is_signal_optimal': True
            })

        for i in range(violations):
            feedbacks.append({
                'trick_number': optimal + i + 1,
                'user_card': f'{(optimal + i) % 10}♥',
                'signal_heuristic': 'max_of_equals',
                'signal_context': 'THIRD_HAND_FOLLOW',
                'signal_reason': 'Test violation',
                'is_signal_optimal': False
            })

        return feedbacks


class TestDeductionConfidenceEnum:
    """Tests for the DeductionConfidence enum."""

    def test_enum_values(self):
        """Verify enum values match expected strings."""
        assert DeductionConfidence.EXPERT.value == 'expert'
        assert DeductionConfidence.COMPETENT.value == 'competent'
        assert DeductionConfidence.INCONSISTENT.value == 'inconsistent'
        assert DeductionConfidence.CHAOTIC.value == 'chaotic'

    def test_all_levels_exist(self):
        """Verify all four confidence levels exist."""
        assert len(DeductionConfidence) == 4
