#!/usr/bin/env python3
"""
Initialize authentication tables for MVP user management
Adds phone column to users table if it doesn't exist
"""

import sys
from pathlib import Path

# Add backend dir to path so we can import db module
script_dir = Path(__file__).parent.resolve()
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from db import get_connection


def init_auth_tables():
    """Add phone column to users table"""

    print("Initializing auth tables (PostgreSQL)")

    with get_connection() as conn:
        cursor = conn.cursor()

        try:
            # Check if users table exists
            cursor.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename = 'users'
            """)

            if not cursor.fetchone():
                print("Users table doesn't exist. Please run init_all_tables.py first.")
                return False

            # Check if phone column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'users'
            """)
            columns = [row['column_name'] for row in cursor.fetchall()]

            if 'phone' not in columns:
                print("Adding 'phone' column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
                print("Phone column added successfully")
            else:
                print("Phone column already exists")

            # Verify the change
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            columns = [row['column_name'] for row in cursor.fetchall()]
            print(f"\nUsers table columns: {', '.join(columns)}")

            # Show existing users (without sensitive data)
            cursor.execute("SELECT id, username, email, phone, display_name FROM users")
            users = cursor.fetchall()

            if users:
                print(f"\nExisting users: {len(users)}")
                for user in users:
                    contact = user['email'] or user['phone'] or 'no contact'
                    print(f"   - ID {user['id']}: {user['username']} ({contact})")
            else:
                print("\nNo existing users")

            print("\nDatabase ready for authentication!")
            return True

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = init_auth_tables()
    sys.exit(0 if success else 1)
