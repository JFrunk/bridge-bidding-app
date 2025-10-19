"""
Celebration Manager - Handles milestone celebrations and achievements

Manages:
- Creating improvement milestones
- Loading celebration templates
- Formatting celebration messages with context
- Marking celebrations as shown
- XP rewards for achievements

Part of the Common Mistake Detection System
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Milestone:
    """Represents an achievement milestone"""
    id: Optional[int]
    user_id: int
    milestone_type: str
    milestone_subtype: Optional[str]
    convention_id: Optional[str]
    error_category: Optional[str]
    previous_value: Optional[float]
    new_value: Optional[float]
    improvement_amount: Optional[float]
    improvement_percentage: Optional[float]
    title: str
    message: str
    celebration_emoji: Optional[str]
    achieved_at: datetime
    shown_to_user: bool
    acknowledged_at: Optional[datetime]
    xp_reward: int
    badge_id: Optional[str]


@dataclass
class CelebrationTemplate:
    """Template for celebration messages"""
    id: int
    template_id: str
    milestone_type: str
    title_template: str
    message_template: str
    emoji: Optional[str]
    trigger_conditions: Optional[Dict]
    xp_reward: int
    active: bool


class CelebrationManager:
    """Manages milestone celebrations and achievement rewards"""

    def __init__(self, db_path: str = 'backend/bridge.db'):
        self.db_path = db_path
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Verify celebration tables exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('improvement_milestones', 'celebration_templates')
        """)

        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        if 'improvement_milestones' not in tables or 'celebration_templates' not in tables:
            raise RuntimeError(
                "Required tables not found. Please run schema_user_management.sql first."
            )

    def create_milestone(self, user_id: int, milestone_type: str,
                        context: Dict, xp_reward: Optional[int] = None) -> Optional[int]:
        """
        Create a new milestone celebration

        Args:
            user_id: User ID
            milestone_type: Type of milestone (e.g., 'pattern_resolved', 'streak_achieved')
            context: Context data for formatting message
            xp_reward: Optional custom XP reward (uses template default if None)

        Returns:
            Milestone ID or None if creation failed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get appropriate celebration template
            template = self._get_template(milestone_type, context)

            if not template:
                return None

            # Format title and message
            title = self._format_message(template.title_template, context)
            message = self._format_message(template.message_template, context)

            # Use custom XP or template XP
            reward = xp_reward if xp_reward is not None else template.xp_reward

            # Extract context values
            milestone_subtype = context.get('subtype')
            convention_id = context.get('convention_id')
            error_category = context.get('error_category')
            previous_value = context.get('previous_value')
            new_value = context.get('new_value')
            improvement_amount = context.get('improvement_amount')
            improvement_percentage = context.get('improvement_percentage')
            badge_id = context.get('badge_id')

            # Insert milestone
            cursor.execute("""
                INSERT INTO improvement_milestones (
                    user_id, milestone_type, milestone_subtype,
                    convention_id, error_category,
                    previous_value, new_value,
                    improvement_amount, improvement_percentage,
                    title, message, celebration_emoji,
                    xp_reward, badge_id,
                    achieved_at, shown_to_user
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, FALSE)
            """, (
                user_id, milestone_type, milestone_subtype,
                convention_id, error_category,
                previous_value, new_value,
                improvement_amount, improvement_percentage,
                title, message, template.emoji,
                reward, badge_id
            ))

            milestone_id = cursor.lastrowid
            conn.commit()

            # Award XP to user
            if reward > 0:
                self._award_xp(user_id, reward, cursor)
                conn.commit()

            return milestone_id

        except Exception as e:
            conn.rollback()
            print(f"Error creating milestone: {e}")
            return None
        finally:
            conn.close()

    def _get_template(self, milestone_type: str, context: Dict) -> Optional[CelebrationTemplate]:
        """Get appropriate celebration template"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Try to find specific subtype template first
            subtype = context.get('subtype')

            if subtype:
                cursor.execute("""
                    SELECT * FROM celebration_templates
                    WHERE milestone_type = ?
                      AND template_id LIKE ?
                      AND active = TRUE
                    LIMIT 1
                """, (milestone_type, f"%{subtype}%"))

                row = cursor.fetchone()
                if row:
                    return self._row_to_template(row)

            # Fall back to general template for this type
            cursor.execute("""
                SELECT * FROM celebration_templates
                WHERE milestone_type = ?
                  AND active = TRUE
                ORDER BY id
                LIMIT 1
            """, (milestone_type,))

            row = cursor.fetchone()
            if row:
                return self._row_to_template(row)

            return None

        finally:
            conn.close()

    def _row_to_template(self, row: sqlite3.Row) -> CelebrationTemplate:
        """Convert database row to CelebrationTemplate"""
        return CelebrationTemplate(
            id=row['id'],
            template_id=row['template_id'],
            milestone_type=row['milestone_type'],
            title_template=row['title_template'],
            message_template=row['message_template'],
            emoji=row['emoji'],
            trigger_conditions=None,  # Would parse JSON if needed
            xp_reward=row['xp_reward'],
            active=bool(row['active'])
        )

    def _format_message(self, template: str, context: Dict) -> str:
        """
        Format message template with context variables

        Supported placeholders:
        - {convention}: Convention name
        - {category}: Error category friendly name
        - {old_accuracy}, {new_accuracy}: Accuracy percentages
        - {accuracy}: Current accuracy
        - {improvement}: Improvement amount
        - {streak_days}: Number of streak days
        - {hands}: Number of hands
        """
        message = template

        # Replace all context variables
        replacements = {
            '{convention}': context.get('convention_name', ''),
            '{category}': context.get('category_name', ''),
            '{old_accuracy}': str(int(context.get('previous_value', 0) * 100)) if context.get('previous_value') else '',
            '{new_accuracy}': str(int(context.get('new_value', 0) * 100)) if context.get('new_value') else '',
            '{accuracy}': str(int(context.get('accuracy', 0) * 100)) if context.get('accuracy') else '',
            '{improvement}': str(int(context.get('improvement_percentage', 0))) if context.get('improvement_percentage') else '',
            '{streak_days}': str(context.get('streak_days', 0)),
            '{hands}': str(context.get('hands_count', 0))
        }

        for placeholder, value in replacements.items():
            if placeholder in message:
                message = message.replace(placeholder, value)

        return message

    def _award_xp(self, user_id: int, xp_amount: int, cursor: sqlite3.Cursor):
        """Award XP to user (internal method with existing cursor)"""
        # Get current XP and level
        cursor.execute("""
            SELECT total_xp, current_level, xp_to_next_level
            FROM user_gamification
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            return

        total_xp, current_level, xp_to_next_level = row

        # Add XP
        new_total_xp = total_xp + xp_amount

        # Check for level up
        new_level = current_level
        new_xp_to_next = xp_to_next_level

        while new_total_xp >= xp_to_next_level:
            new_level += 1
            # Progressive XP curve: each level requires more XP
            new_xp_to_next = int(500 + (new_level - 1) * 200)

        # Update user gamification
        cursor.execute("""
            UPDATE user_gamification
            SET total_xp = ?,
                current_level = ?,
                xp_to_next_level = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_total_xp, new_level, new_xp_to_next, user_id))

    def get_pending_celebrations(self, user_id: int) -> List[Milestone]:
        """
        Get all pending (unshown) celebrations for user

        Returns:
            List of Milestone objects ordered by achievement date (newest first)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM improvement_milestones
                WHERE user_id = ?
                  AND shown_to_user = FALSE
                ORDER BY achieved_at DESC
            """, (user_id,))

            milestones = []
            for row in cursor.fetchall():
                milestones.append(self._row_to_milestone(row))

            return milestones

        finally:
            conn.close()

    def get_recent_celebrations(self, user_id: int, limit: int = 10) -> List[Milestone]:
        """
        Get recent celebrations for user (shown or not)

        Args:
            user_id: User ID
            limit: Maximum number of celebrations to return

        Returns:
            List of Milestone objects ordered by achievement date (newest first)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM improvement_milestones
                WHERE user_id = ?
                ORDER BY achieved_at DESC
                LIMIT ?
            """, (user_id, limit))

            milestones = []
            for row in cursor.fetchall():
                milestones.append(self._row_to_milestone(row))

            return milestones

        finally:
            conn.close()

    def mark_celebration_shown(self, milestone_id: int) -> bool:
        """
        Mark a celebration as shown to user

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE improvement_milestones
                SET shown_to_user = TRUE
                WHERE id = ?
            """, (milestone_id,))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            print(f"Error marking celebration shown: {e}")
            return False
        finally:
            conn.close()

    def acknowledge_celebration(self, milestone_id: int) -> bool:
        """
        Mark a celebration as acknowledged by user

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE improvement_milestones
                SET shown_to_user = TRUE,
                    acknowledged_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (milestone_id,))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            print(f"Error acknowledging celebration: {e}")
            return False
        finally:
            conn.close()

    def _row_to_milestone(self, row: sqlite3.Row) -> Milestone:
        """Convert database row to Milestone object"""
        return Milestone(
            id=row['id'],
            user_id=row['user_id'],
            milestone_type=row['milestone_type'],
            milestone_subtype=row['milestone_subtype'],
            convention_id=row['convention_id'],
            error_category=row['error_category'],
            previous_value=row['previous_value'],
            new_value=row['new_value'],
            improvement_amount=row['improvement_amount'],
            improvement_percentage=row['improvement_percentage'],
            title=row['title'],
            message=row['message'],
            celebration_emoji=row['celebration_emoji'],
            achieved_at=datetime.fromisoformat(row['achieved_at']),
            shown_to_user=bool(row['shown_to_user']),
            acknowledged_at=datetime.fromisoformat(row['acknowledged_at']) if row['acknowledged_at'] else None,
            xp_reward=row['xp_reward'],
            badge_id=row['badge_id']
        )

    def create_streak_milestone(self, user_id: int, streak_days: int) -> Optional[int]:
        """
        Create a streak milestone celebration

        Args:
            user_id: User ID
            streak_days: Number of consecutive days

        Returns:
            Milestone ID or None
        """
        # Only celebrate specific streak milestones
        milestone_thresholds = {
            3: 'streak_3day',
            7: 'streak_7day',
            14: 'streak_14day',
            30: 'streak_30day',
            60: 'streak_60day',
            100: 'streak_100day'
        }

        if streak_days not in milestone_thresholds:
            return None

        context = {
            'subtype': milestone_thresholds[streak_days],
            'streak_days': streak_days
        }

        return self.create_milestone(user_id, 'streak_milestone', context)

    def create_accuracy_milestone(self, user_id: int, accuracy: float,
                                  convention_id: Optional[str] = None) -> Optional[int]:
        """
        Create an accuracy achievement milestone

        Args:
            user_id: User ID
            accuracy: Accuracy percentage (0.0 to 1.0)
            convention_id: Optional specific convention

        Returns:
            Milestone ID or None
        """
        # Celebrate specific accuracy thresholds
        accuracy_pct = int(accuracy * 100)

        milestone_thresholds = [70, 80, 90, 95]

        # Find the highest threshold reached
        for threshold in reversed(milestone_thresholds):
            if accuracy_pct >= threshold:
                context = {
                    'accuracy': accuracy,
                    'convention_id': convention_id,
                    'subtype': f'accuracy_{threshold}'
                }

                return self.create_milestone(user_id, 'accuracy_achievement', context)

        return None

    def create_pattern_resolved_milestone(self, user_id: int, error_category: str,
                                         category_name: str, old_accuracy: float,
                                         new_accuracy: float) -> Optional[int]:
        """
        Create a pattern resolved milestone (user mastered a mistake pattern)

        Args:
            user_id: User ID
            error_category: Category ID (e.g., 'wrong_level')
            category_name: Friendly name (e.g., 'Bid Level')
            old_accuracy: Previous accuracy (0.0 to 1.0)
            new_accuracy: New accuracy (0.0 to 1.0)

        Returns:
            Milestone ID or None
        """
        improvement_amount = new_accuracy - old_accuracy
        improvement_percentage = improvement_amount * 100

        context = {
            'error_category': error_category,
            'category_name': category_name,
            'previous_value': old_accuracy,
            'new_value': new_accuracy,
            'improvement_amount': improvement_amount,
            'improvement_percentage': improvement_percentage
        }

        return self.create_milestone(user_id, 'pattern_milestone', context)

    def create_hands_milestone(self, user_id: int, hands_count: int) -> Optional[int]:
        """
        Create a hands practiced milestone

        Args:
            user_id: User ID
            hands_count: Total hands practiced

        Returns:
            Milestone ID or None
        """
        # Celebrate specific hand count milestones
        milestone_thresholds = {
            10: 'hands_milestone_10',
            25: 'hands_milestone_25',
            50: 'hands_milestone_50',
            100: 'hands_milestone_100',
            250: 'hands_milestone_250',
            500: 'hands_milestone_500',
            1000: 'hands_milestone_1000'
        }

        if hands_count not in milestone_thresholds:
            return None

        context = {
            'subtype': milestone_thresholds[hands_count],
            'hands_count': hands_count
        }

        return self.create_milestone(user_id, 'hands_milestone', context)

    def create_improvement_milestone(self, user_id: int, category_name: str,
                                    improvement_pct: float) -> Optional[int]:
        """
        Create an improvement milestone (significant improvement in category)

        Args:
            user_id: User ID
            category_name: Friendly category name
            improvement_pct: Improvement percentage (e.g., 20.0 for 20%)

        Returns:
            Milestone ID or None
        """
        # Only celebrate significant improvements
        if improvement_pct < 15:  # Less than 15% improvement
            return None

        context = {
            'category_name': category_name,
            'improvement_percentage': improvement_pct
        }

        return self.create_milestone(user_id, 'improvement_milestone', context)


# Singleton instance
_celebration_manager_instance = None

def get_celebration_manager(db_path: str = 'bridge.db') -> CelebrationManager:
    """Get singleton CelebrationManager instance"""
    global _celebration_manager_instance
    if _celebration_manager_instance is None:
        _celebration_manager_instance = CelebrationManager(db_path)
    return _celebration_manager_instance
