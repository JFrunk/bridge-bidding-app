"""
User Management System for Learning Analytics

Handles user creation, authentication, settings, and basic user operations.
Foundation for mistake detection and progress tracking.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
import json
import sys
from pathlib import Path

# Database abstraction layer for SQLite/PostgreSQL compatibility
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db import get_connection


@dataclass
class User:
    """User data model"""
    id: int
    username: str
    email: Optional[str]
    display_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    last_activity: Optional[datetime]
    timezone: str = 'UTC'
    preferences: Optional[Dict] = None
    phone: Optional[str] = None


@dataclass
class UserStats:
    """User gamification statistics"""
    user_id: int
    total_xp: int
    current_level: int
    xp_to_next_level: int
    current_streak_days: int
    longest_streak_days: int
    total_hands_practiced: int
    overall_accuracy: float
    recent_accuracy: float


class UserManager:
    """
    Manages user accounts and basic operations
    """

    def __init__(self, db_path: str = 'bridge.db'):
        self.db_path = db_path  # Kept for backward compatibility

    def _get_connection(self):
        """Get database connection using abstraction layer"""
        return get_connection()

    # ========================================================================
    # USER CRUD OPERATIONS
    # ========================================================================

    def create_user(self, username: str, email: Optional[str] = None,
                   display_name: Optional[str] = None, phone: Optional[str] = None) -> int:
        """
        Create a new user with default settings

        Args:
            username: Unique username (min 3 chars)
            email: Optional email
            display_name: Optional display name
            phone: Optional phone number

        Returns:
            user_id: ID of newly created user

        Raises:
            ValueError: If username exists or invalid
        """
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Check if phone column exists, if not create it
            from db import USE_POSTGRES
            if USE_POSTGRES:
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'users'"
                )
                columns = [row['column_name'] for row in cursor.fetchall()]
            else:
                cursor.execute("PRAGMA table_info(users)")
                columns = [row[1] for row in cursor.fetchall()]
            if 'phone' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
                conn.commit()

            # Create user
            cursor.execute("""
                INSERT INTO users (username, email, display_name, phone, last_login, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (username, email, display_name, phone))

            user_id = cursor.lastrowid

            # Create default settings
            cursor.execute("""
                INSERT INTO user_settings (user_id) VALUES (?)
            """, (user_id,))

            # Create gamification record
            cursor.execute("""
                INSERT INTO user_gamification (user_id) VALUES (?)
            """, (user_id,))

            conn.commit()
            return user_id

        except sqlite3.IntegrityError as e:
            conn.rollback()
            if 'username' in str(e):
                raise ValueError(f"Username '{username}' already exists")
            elif 'email' in str(e):
                raise ValueError(f"Email '{email}' already exists")
            raise

        finally:
            conn.close()

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID

        Returns:
            User object or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            display_name=row['display_name'],
            created_at=datetime.fromisoformat(row['created_at']),
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
            timezone=row['timezone'],
            preferences=json.loads(row['preferences']) if row['preferences'] else None,
            phone=row['phone'] if 'phone' in row.keys() else None
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users WHERE username = ?
        """, (username,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            display_name=row['display_name'],
            created_at=datetime.fromisoformat(row['created_at']),
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
            timezone=row['timezone'],
            preferences=json.loads(row['preferences']) if row['preferences'] else None,
            phone=row['phone'] if 'phone' in row.keys() else None
        )

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        if not email:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            display_name=row['display_name'],
            created_at=datetime.fromisoformat(row['created_at']),
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
            timezone=row['timezone'],
            preferences=json.loads(row['preferences']) if row['preferences'] else None,
            phone=row['phone'] if 'phone' in row.keys() else None
        )

    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number"""
        if not phone:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users WHERE phone = ?
        """, (phone,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            display_name=row['display_name'],
            created_at=datetime.fromisoformat(row['created_at']),
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
            timezone=row['timezone'],
            preferences=json.loads(row['preferences']) if row['preferences'] else None,
            phone=row['phone'] if 'phone' in row.keys() else None
        )

    def update_user_activity(self, user_id: int):
        """Update user's last activity timestamp"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET last_activity = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))

        conn.commit()
        conn.close()

    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP, last_activity = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))

        conn.commit()
        conn.close()

    # ========================================================================
    # USER SETTINGS
    # ========================================================================

    def get_user_settings(self, user_id: int) -> Dict:
        """Get user settings"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM user_settings WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {}

        return dict(row)

    def update_user_settings(self, user_id: int, settings: Dict):
        """
        Update user settings

        Args:
            user_id: User ID
            settings: Dict of settings to update
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic UPDATE query
        set_clauses = []
        values = []

        for key, value in settings.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)

        if not set_clauses:
            return

        values.append(user_id)

        query = f"""
            UPDATE user_settings
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """

        cursor.execute(query, values)
        conn.commit()
        conn.close()

    # ========================================================================
    # USER STATISTICS
    # ========================================================================

    def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Get user gamification statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM user_gamification WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return UserStats(
            user_id=row['user_id'],
            total_xp=row['total_xp'],
            current_level=row['current_level'],
            xp_to_next_level=row['xp_to_next_level'],
            current_streak_days=row['current_streak_days'],
            longest_streak_days=row['longest_streak_days'],
            total_hands_practiced=row['total_hands_practiced'],
            overall_accuracy=row['overall_accuracy'],
            recent_accuracy=row['recent_accuracy']
        )

    def update_streak(self, user_id: int):
        """
        Update user's practice streak

        Call this whenever user completes a practice hand.
        Handles streak increment, reset, and longest streak tracking.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get current streak info
        cursor.execute("""
            SELECT current_streak_days, longest_streak_days, last_practice_date
            FROM user_gamification
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        current_streak = row['current_streak_days']
        longest_streak = row['longest_streak_days']
        last_practice = row['last_practice_date']

        today = date.today()
        today_str = today.isoformat()

        # Determine new streak
        if not last_practice:
            # First practice ever
            new_streak = 1
        elif last_practice == today_str:
            # Already practiced today, no change
            new_streak = current_streak
        else:
            last_date = date.fromisoformat(last_practice)
            days_since = (today - last_date).days

            if days_since == 1:
                # Consecutive day
                new_streak = current_streak + 1
            else:
                # Streak broken
                new_streak = 1

        # Update longest streak if needed
        new_longest = max(longest_streak, new_streak)

        # Update database
        cursor.execute("""
            UPDATE user_gamification
            SET current_streak_days = ?,
                longest_streak_days = ?,
                last_practice_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_streak, new_longest, today_str, user_id))

        conn.commit()
        conn.close()

        # Check for streak milestones
        self._check_streak_milestone(user_id, new_streak)

    def _check_streak_milestone(self, user_id: int, streak_days: int):
        """Check if user hit a streak milestone and create celebration"""
        from engine.learning.celebration_manager import CelebrationManager

        milestones = {
            3: 'streak_3day',
            7: 'streak_7day',
            14: 'streak_14day',
            30: 'streak_30day',
            60: 'streak_60day',
            100: 'streak_100day'
        }

        if streak_days in milestones:
            celebration_mgr = CelebrationManager(self.db_path)
            celebration_mgr.create_milestone(
                user_id=user_id,
                milestone_type='streak_milestone',
                template_id=milestones[streak_days],
                context={'streak_days': streak_days}
            )

    def add_xp(self, user_id: int, xp_amount: int):
        """
        Add XP to user and handle level ups

        Args:
            user_id: User ID
            xp_amount: Amount of XP to add
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get current stats
        cursor.execute("""
            SELECT total_xp, current_level, xp_to_next_level
            FROM user_gamification
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        current_xp = row['total_xp']
        current_level = row['current_level']
        xp_to_next = row['xp_to_next_level']

        # Add XP
        new_xp = current_xp + xp_amount
        new_level = current_level

        # Check for level up
        while new_xp >= xp_to_next:
            new_level += 1
            new_xp -= xp_to_next
            xp_to_next = self._calculate_xp_for_level(new_level + 1)

            # Create level up milestone
            self._create_level_up_milestone(user_id, new_level)

        # Update database
        cursor.execute("""
            UPDATE user_gamification
            SET total_xp = ?,
                current_level = ?,
                xp_to_next_level = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_xp, new_level, xp_to_next, user_id))

        conn.commit()
        conn.close()

    def _calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required for a given level"""
        # Progressive XP curve: level 1->2 = 500, 2->3 = 700, 3->4 = 1000, etc.
        base = 500
        return int(base * (1 + (level - 1) * 0.4))

    def _create_level_up_milestone(self, user_id: int, new_level: int):
        """Create milestone for leveling up"""
        from engine.learning.celebration_manager import CelebrationManager

        celebration_mgr = CelebrationManager(self.db_path)
        celebration_mgr.create_milestone(
            user_id=user_id,
            milestone_type='level_up',
            context={'new_level': new_level}
        )

    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================

    def get_or_create_guest_user(self) -> int:
        """
        Get or create a default 'guest' user for single-user mode

        Returns:
            user_id of guest user
        """
        user = self.get_user_by_username('guest')
        if user:
            return user.id

        return self.create_user(
            username='guest',
            display_name='Guest User'
        )

    def user_exists(self, username: str) -> bool:
        """Check if username exists"""
        return self.get_user_by_username(username) is not None


# Singleton instance
_user_manager_instance = None


def get_user_manager(db_path: str = 'bridge.db') -> UserManager:
    """Get singleton UserManager instance"""
    global _user_manager_instance
    if _user_manager_instance is None:
        _user_manager_instance = UserManager(db_path)
    return _user_manager_instance
