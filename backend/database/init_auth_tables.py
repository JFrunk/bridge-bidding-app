#!/usr/bin/env python3
"""
Initialize authentication tables for MVP user management
Adds phone column to users table if it doesn't exist
"""

import sqlite3
import os
import sys

def init_auth_tables(db_path='bridge.db'):
    """Add phone column to users table"""

    # Make sure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    db_full_path = os.path.join(backend_dir, db_path)

    print(f"Initializing auth tables in: {db_full_path}")

    if not os.path.exists(db_full_path):
        print(f"❌ Database not found at {db_full_path}")
        print("   Creating new database...")

    conn = sqlite3.connect(db_full_path)
    cursor = conn.cursor()

    try:
        # Check if users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='users'
        """)

        if not cursor.fetchone():
            print("❌ Users table doesn't exist. Please run schema_user_management.sql first.")
            return False

        # Check if phone column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'phone' not in columns:
            print("➕ Adding 'phone' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            conn.commit()
            print("✅ Phone column added successfully")
        else:
            print("✓ Phone column already exists")

        # Verify the change
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"\n📋 Users table columns: {', '.join(columns)}")

        # Show existing users (without sensitive data)
        cursor.execute("SELECT id, username, email, phone, display_name FROM users")
        users = cursor.fetchall()

        if users:
            print(f"\n👥 Existing users: {len(users)}")
            for user in users:
                user_id, username, email, phone, display_name = user
                print(f"   - ID {user_id}: {username} ({email or phone or 'no contact'})")
        else:
            print("\n👥 No existing users")

        print("\n✅ Database ready for authentication!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'bridge.db'
    success = init_auth_tables(db_path)
    sys.exit(0 if success else 1)
