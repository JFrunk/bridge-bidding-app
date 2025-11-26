"""
Mistake Pattern Analyzer - Aggregates errors and provides insights

Manages:
- Aggregating individual errors into patterns
- Calculating improvement rates
- Determining pattern status (active, improving, resolved, needs_attention)
- Generating growth-focused insights
- Creating personalized practice recommendations
- Tracking pattern resolution

Part of the Common Mistake Detection System
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Database abstraction layer for SQLite/PostgreSQL compatibility
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db import get_connection


@dataclass
class MistakePattern:
    """Represents an aggregated mistake pattern"""
    id: Optional[int]
    user_id: int
    convention_id: Optional[str]
    error_category: str
    error_subcategory: Optional[str]
    total_occurrences: int
    recent_occurrences: int
    first_seen: datetime
    last_seen: datetime
    attempts_in_category: int
    correct_in_category: int
    current_accuracy: float
    previous_accuracy: float
    improvement_rate: float
    trend: str
    status: str
    recommended_practice_hands: Optional[int]
    practice_hands_completed: int
    last_analysis: Optional[datetime]


@dataclass
class InsightSummary:
    """Summary of user's learning insights"""
    user_id: int
    total_patterns: int
    active_patterns: int
    improving_patterns: int
    resolved_patterns: int
    needs_attention_patterns: int
    overall_trend: str
    top_growth_areas: List[Dict]
    recent_wins: List[Dict]
    recommended_focus: Optional[str]


class MistakeAnalyzer:
    """Analyzes mistake patterns and provides learning insights"""

    def __init__(self, db_path: str = 'backend/bridge.db'):
        self.db_path = db_path  # Kept for backward compatibility
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Verify required tables exist - handled by db initialization"""
        pass

    def analyze_practice_hand(self, user_id: int, practice_id: int) -> Optional[int]:
        """
        Analyze a practice hand and update mistake patterns

        Args:
            user_id: User ID
            practice_id: ID from practice_history table

        Returns:
            Pattern ID or None
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Get practice record
            cursor.execute("""
                SELECT * FROM practice_history
                WHERE id = ? AND user_id = ?
            """, (practice_id, user_id))

            practice = cursor.fetchone()
            if not practice:
                return None

            # Only analyze errors (not correct answers)
            if practice['was_correct']:
                # Still update accuracy for this category
                self._update_category_accuracy(
                    user_id,
                    practice['convention_id'],
                    practice['error_category'],
                    True,
                    cursor
                )
                conn.commit()
                return None

            # Check if pattern exists
            cursor.execute("""
                SELECT id FROM mistake_patterns
                WHERE user_id = ?
                  AND convention_id IS ?
                  AND error_category = ?
                  AND (error_subcategory IS ? OR (error_subcategory IS NULL AND ? IS NULL))
            """, (
                user_id,
                practice['convention_id'],
                practice['error_category'],
                practice['error_subcategory'],
                practice['error_subcategory']
            ))

            existing = cursor.fetchone()

            if existing:
                # Update existing pattern
                pattern_id = existing['id']
                self._update_pattern(pattern_id, cursor)
            else:
                # Create new pattern
                pattern_id = self._create_pattern(
                    user_id,
                    practice['convention_id'],
                    practice['error_category'],
                    practice['error_subcategory'],
                    cursor
                )

            conn.commit()
            return pattern_id

        except Exception as e:
            conn.rollback()
            print(f"Error analyzing practice hand: {e}")
            return None
        finally:
            conn.close()

    def _create_pattern(self, user_id: int, convention_id: Optional[str],
                       error_category: str, error_subcategory: Optional[str],
                       cursor: Any) -> int:
        """Create a new mistake pattern"""
        cursor.execute("""
            INSERT INTO mistake_patterns (
                user_id, convention_id, error_category, error_subcategory,
                total_occurrences, recent_occurrences,
                first_seen, last_seen,
                attempts_in_category, correct_in_category,
                current_accuracy, previous_accuracy,
                improvement_rate, trend, status,
                recommended_practice_hands, practice_hands_completed,
                last_analysis
            ) VALUES (?, ?, ?, ?, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                     0, 0, 0.0, 0.0, 0.0, 'new', 'active', 10, 0, CURRENT_TIMESTAMP)
        """, (user_id, convention_id, error_category, error_subcategory))

        return cursor.lastrowid

    def _update_pattern(self, pattern_id: int, cursor: Any):
        """Update an existing mistake pattern"""
        # Get current pattern
        cursor.execute("""
            SELECT * FROM mistake_patterns WHERE id = ?
        """, (pattern_id,))

        pattern = cursor.fetchone()
        if not pattern:
            return

        # Calculate recent occurrences (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM practice_history
            WHERE user_id = ?
              AND convention_id IS ?
              AND error_category = ?
              AND was_correct = FALSE
              AND timestamp >= datetime('now', '-30 days')
        """, (pattern['user_id'], pattern['convention_id'], pattern['error_category']))

        recent_count = cursor.fetchone()['count']

        # Update pattern
        cursor.execute("""
            UPDATE mistake_patterns
            SET total_occurrences = total_occurrences + 1,
                recent_occurrences = ?,
                last_seen = CURRENT_TIMESTAMP,
                last_analysis = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (recent_count, pattern_id))

    def _update_category_accuracy(self, user_id: int, convention_id: Optional[str],
                                  error_category: Optional[str], was_correct: bool,
                                  cursor: Any):
        """Update accuracy tracking for a category"""
        if not error_category:
            return

        # Get or create pattern for accuracy tracking
        cursor.execute("""
            SELECT id, attempts_in_category, correct_in_category, current_accuracy
            FROM mistake_patterns
            WHERE user_id = ?
              AND convention_id IS ?
              AND error_category = ?
        """, (user_id, convention_id, error_category))

        pattern = cursor.fetchone()

        if not pattern:
            # Create pattern if it doesn't exist
            cursor.execute("""
                INSERT INTO mistake_patterns (
                    user_id, convention_id, error_category,
                    total_occurrences, recent_occurrences,
                    attempts_in_category, correct_in_category,
                    current_accuracy, previous_accuracy,
                    trend, status,
                    first_seen, last_seen, last_analysis
                ) VALUES (?, ?, ?, 0, 0, 1, ?, ?, 0.0, 'new', 'active',
                         CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (user_id, convention_id, error_category,
                  1 if was_correct else 0,
                  1.0 if was_correct else 0.0))
        else:
            # Update existing pattern
            new_attempts = pattern['attempts_in_category'] + 1
            new_correct = pattern['correct_in_category'] + (1 if was_correct else 0)
            new_accuracy = new_correct / new_attempts if new_attempts > 0 else 0.0

            cursor.execute("""
                UPDATE mistake_patterns
                SET attempts_in_category = ?,
                    correct_in_category = ?,
                    previous_accuracy = current_accuracy,
                    current_accuracy = ?,
                    last_analysis = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_attempts, new_correct, new_accuracy, pattern['id']))

    def calculate_pattern_status(self, pattern_id: int) -> bool:
        """
        Calculate and update pattern status based on accuracy and improvement

        Status definitions:
        - 'active': Recently seen, not yet improving
        - 'improving': Showing positive improvement trend
        - 'resolved': High accuracy (90%+), pattern mastered
        - 'needs_attention': Frequent errors, not improving

        Returns:
            True if successful
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM mistake_patterns WHERE id = ?
            """, (pattern_id,))

            pattern = cursor.fetchone()
            if not pattern:
                return False

            # Calculate improvement rate
            if pattern['previous_accuracy'] > 0:
                improvement_rate = (
                    (pattern['current_accuracy'] - pattern['previous_accuracy'])
                    / pattern['previous_accuracy']
                )
            else:
                improvement_rate = 0.0

            # Determine trend
            if pattern['attempts_in_category'] < 5:
                trend = 'new'
            elif improvement_rate > 0.1:  # 10%+ improvement
                trend = 'improving'
            elif improvement_rate < -0.1:  # 10%+ regression
                trend = 'regressing'
            else:
                trend = 'stable'

            # Determine status
            if pattern['current_accuracy'] >= 0.9 and pattern['attempts_in_category'] >= 10:
                status = 'resolved'
            elif trend == 'improving':
                status = 'improving'
            elif pattern['recent_occurrences'] >= 5 and pattern['current_accuracy'] < 0.6:
                status = 'needs_attention'
            else:
                status = 'active'

            # Calculate recommended practice hands
            if status == 'resolved':
                recommended_hands = 0
            elif status == 'needs_attention':
                recommended_hands = 20
            elif status == 'improving':
                recommended_hands = 10
            else:
                recommended_hands = 15

            # Update pattern
            cursor.execute("""
                UPDATE mistake_patterns
                SET improvement_rate = ?,
                    trend = ?,
                    status = ?,
                    recommended_practice_hands = ?,
                    last_analysis = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (improvement_rate, trend, status, recommended_hands, pattern_id))

            conn.commit()

            # Check if we should celebrate pattern resolution
            if status == 'resolved' and pattern['status'] != 'resolved':
                self._create_resolution_celebration(pattern, cursor)
                conn.commit()

            return True

        except Exception as e:
            conn.rollback()
            print(f"Error calculating pattern status: {e}")
            return False
        finally:
            conn.close()

    def _create_resolution_celebration(self, pattern: Any, cursor: Any):
        """Create a celebration for resolving a pattern"""
        # Import here to avoid circular dependency
        from engine.learning.celebration_manager import get_celebration_manager

        # Get category friendly name
        cursor.execute("""
            SELECT friendly_name FROM error_categories
            WHERE category_id = ?
        """, (pattern['error_category'],))

        category_row = cursor.fetchone()
        category_name = category_row['friendly_name'] if category_row else pattern['error_category']

        celebration_manager = get_celebration_manager(self.db_path)
        celebration_manager.create_pattern_resolved_milestone(
            pattern['user_id'],
            pattern['error_category'],
            category_name,
            pattern['previous_accuracy'],
            pattern['current_accuracy']
        )

    def get_user_patterns(self, user_id: int, status_filter: Optional[str] = None) -> List[MistakePattern]:
        """
        Get all mistake patterns for a user

        Args:
            user_id: User ID
            status_filter: Optional status to filter by ('active', 'improving', 'resolved', 'needs_attention')

        Returns:
            List of MistakePattern objects
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            if status_filter:
                cursor.execute("""
                    SELECT * FROM mistake_patterns
                    WHERE user_id = ? AND status = ?
                    ORDER BY recent_occurrences DESC, last_seen DESC
                """, (user_id, status_filter))
            else:
                cursor.execute("""
                    SELECT * FROM mistake_patterns
                    WHERE user_id = ?
                    ORDER BY recent_occurrences DESC, last_seen DESC
                """, (user_id,))

            patterns = []
            for row in cursor.fetchall():
                patterns.append(self._row_to_pattern(row))

            return patterns

        finally:
            conn.close()

    def _row_to_pattern(self, row: Any) -> MistakePattern:
        """Convert database row to MistakePattern object"""
        return MistakePattern(
            id=row['id'],
            user_id=row['user_id'],
            convention_id=row['convention_id'],
            error_category=row['error_category'],
            error_subcategory=row['error_subcategory'],
            total_occurrences=row['total_occurrences'],
            recent_occurrences=row['recent_occurrences'],
            first_seen=datetime.fromisoformat(row['first_seen']),
            last_seen=datetime.fromisoformat(row['last_seen']),
            attempts_in_category=row['attempts_in_category'],
            correct_in_category=row['correct_in_category'],
            current_accuracy=row['current_accuracy'],
            previous_accuracy=row['previous_accuracy'],
            improvement_rate=row['improvement_rate'],
            trend=row['trend'],
            status=row['status'],
            recommended_practice_hands=row['recommended_practice_hands'],
            practice_hands_completed=row['practice_hands_completed'],
            last_analysis=datetime.fromisoformat(row['last_analysis']) if row['last_analysis'] else None
        )

    def get_insight_summary(self, user_id: int) -> InsightSummary:
        """
        Generate comprehensive insight summary for user

        Returns:
            InsightSummary with top growth areas, recent wins, and recommendations
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Get pattern counts by status
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'improving' THEN 1 ELSE 0 END) as improving,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                    SUM(CASE WHEN status = 'needs_attention' THEN 1 ELSE 0 END) as needs_attention
                FROM mistake_patterns
                WHERE user_id = ?
            """, (user_id,))

            counts = cursor.fetchone()

            # Handle None values from SUM() when no data exists
            total = counts['total'] or 0
            active = counts['active'] or 0
            improving = counts['improving'] or 0
            resolved = counts['resolved'] or 0
            needs_attention = counts['needs_attention'] or 0

            # Determine overall trend
            if improving > active + needs_attention:
                overall_trend = 'improving'
            elif needs_attention > improving:
                overall_trend = 'needs_attention'
            elif total > 0 and resolved > total * 0.6:
                overall_trend = 'mastering'
            else:
                overall_trend = 'learning'

            # Get top growth areas (needs attention or active with high occurrence)
            cursor.execute("""
                SELECT
                    mp.error_category,
                    ec.friendly_name as category_name,
                    mp.recent_occurrences,
                    mp.current_accuracy,
                    mp.status,
                    mp.recommended_practice_hands
                FROM mistake_patterns mp
                LEFT JOIN error_categories ec ON mp.error_category = ec.category_id
                WHERE mp.user_id = ?
                  AND mp.status IN ('needs_attention', 'active')
                ORDER BY mp.recent_occurrences DESC, mp.current_accuracy ASC
                LIMIT 3
            """, (user_id,))

            top_growth_areas = []
            for row in cursor.fetchall():
                top_growth_areas.append({
                    'category': row['error_category'],
                    'category_name': row['category_name'],
                    'recent_occurrences': row['recent_occurrences'],
                    'accuracy': row['current_accuracy'],
                    'status': row['status'],
                    'recommended_hands': row['recommended_practice_hands']
                })

            # Get recent wins (recently resolved or significantly improved)
            cursor.execute("""
                SELECT
                    mp.error_category,
                    ec.friendly_name as category_name,
                    mp.current_accuracy,
                    mp.improvement_rate,
                    mp.status
                FROM mistake_patterns mp
                LEFT JOIN error_categories ec ON mp.error_category = ec.category_id
                WHERE mp.user_id = ?
                  AND (mp.status = 'resolved' OR (mp.status = 'improving' AND mp.improvement_rate > 0.2))
                ORDER BY
                    CASE WHEN mp.status = 'resolved' THEN 1 ELSE 2 END,
                    mp.improvement_rate DESC
                LIMIT 3
            """, (user_id,))

            recent_wins = []
            for row in cursor.fetchall():
                recent_wins.append({
                    'category': row['error_category'],
                    'category_name': row['category_name'],
                    'accuracy': row['current_accuracy'],
                    'improvement_rate': row['improvement_rate'],
                    'status': row['status']
                })

            # Determine recommended focus
            recommended_focus = None
            if top_growth_areas:
                recommended_focus = top_growth_areas[0]['category_name']

            return InsightSummary(
                user_id=user_id,
                total_patterns=total,
                active_patterns=active,
                improving_patterns=improving,
                resolved_patterns=resolved,
                needs_attention_patterns=needs_attention,
                overall_trend=overall_trend,
                top_growth_areas=top_growth_areas,
                recent_wins=recent_wins,
                recommended_focus=recommended_focus
            )

        finally:
            conn.close()

    def get_practice_recommendations(self, user_id: int, max_recommendations: int = 5) -> List[Dict]:
        """
        Get personalized practice recommendations

        Args:
            user_id: User ID
            max_recommendations: Maximum number of recommendations

        Returns:
            List of recommendation dictionaries with category, convention, and priority
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Prioritize patterns that need attention
            cursor.execute("""
                SELECT
                    mp.convention_id,
                    mp.error_category,
                    ec.friendly_name as category_name,
                    mp.recommended_practice_hands,
                    mp.practice_hands_completed,
                    mp.status,
                    mp.current_accuracy,
                    mp.recent_occurrences,
                    CASE
                        WHEN mp.status = 'needs_attention' THEN 1
                        WHEN mp.status = 'active' THEN 2
                        WHEN mp.status = 'improving' THEN 3
                        ELSE 4
                    END as priority
                FROM mistake_patterns mp
                LEFT JOIN error_categories ec ON mp.error_category = ec.category_id
                WHERE mp.user_id = ?
                  AND mp.status != 'resolved'
                  AND (mp.recommended_practice_hands - mp.practice_hands_completed) > 0
                ORDER BY priority ASC, mp.recent_occurrences DESC, mp.current_accuracy ASC
                LIMIT ?
            """, (user_id, max_recommendations))

            recommendations = []
            for row in cursor.fetchall():
                remaining_hands = row['recommended_practice_hands'] - row['practice_hands_completed']

                recommendations.append({
                    'convention_id': row['convention_id'],
                    'error_category': row['error_category'],
                    'category_name': row['category_name'],
                    'recommended_hands': remaining_hands,
                    'status': row['status'],
                    'accuracy': row['current_accuracy'],
                    'priority': row['priority'],
                    'reason': self._get_recommendation_reason(row)
                })

            return recommendations

        finally:
            conn.close()

    def _get_recommendation_reason(self, pattern: Any) -> str:
        """Generate encouraging reason for practice recommendation"""
        category_name = pattern['category_name']
        accuracy_pct = int(pattern['current_accuracy'] * 100)

        if pattern['status'] == 'needs_attention':
            return f"Let's work on {category_name} - you're at {accuracy_pct}% and improving!"
        elif pattern['status'] == 'active':
            return f"Keep practicing {category_name} to build consistency (currently {accuracy_pct}%)"
        elif pattern['status'] == 'improving':
            return f"You're doing great with {category_name}! A bit more practice to master it ({accuracy_pct}%)"
        else:
            return f"Practice {category_name} to strengthen your skills"

    def run_full_analysis(self, user_id: int) -> Dict:
        """
        Run complete analysis for user and update all patterns

        Returns:
            Summary of analysis results
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Get all patterns for user
            cursor.execute("""
                SELECT id FROM mistake_patterns
                WHERE user_id = ?
            """, (user_id,))

            pattern_ids = [row['id'] for row in cursor.fetchall()]

            # Update status for each pattern
            patterns_updated = 0
            patterns_resolved = 0

            for pattern_id in pattern_ids:
                # Note: calculate_pattern_status opens its own connection
                # This is fine for now, but could be optimized
                success = self.calculate_pattern_status(pattern_id)
                if success:
                    patterns_updated += 1

            # Get updated counts
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved
                FROM mistake_patterns
                WHERE user_id = ?
            """, (user_id,))

            counts = cursor.fetchone()

            return {
                'user_id': user_id,
                'patterns_analyzed': patterns_updated,
                'total_patterns': counts['total'],
                'resolved_patterns': counts['resolved'],
                'analysis_timestamp': datetime.now().isoformat()
            }

        finally:
            conn.close()


# Singleton instance
_mistake_analyzer_instance = None

def get_mistake_analyzer(db_path: str = 'bridge.db') -> MistakeAnalyzer:
    """Get singleton MistakeAnalyzer instance"""
    global _mistake_analyzer_instance
    if _mistake_analyzer_instance is None:
        _mistake_analyzer_instance = MistakeAnalyzer(db_path)
    return _mistake_analyzer_instance
