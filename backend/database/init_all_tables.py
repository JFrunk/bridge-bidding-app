#!/usr/bin/env python3
"""
Initialize ALL database tables for Bridge Bidding App
This script ensures all tables, views, and indexes exist in the database.

Uses the db.py abstraction layer (PostgreSQL via psycopg2).

Usage:
    python3 backend/database/init_all_tables.py

This script is safe to run multiple times (uses CREATE IF NOT EXISTS).
"""

import sys
from pathlib import Path

# Add backend dir to path so we can import db module
script_dir = Path(__file__).parent.resolve()
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from db import init_database, get_connection


def init_postgresql():
    """Initialize PostgreSQL database using db.py's init_database()"""
    print("  Database: PostgreSQL")
    print()

    # db.init_database() handles schema + migrations
    init_database()

    # Verify critical tables
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = [row['tablename'] for row in cursor.fetchall()]

    print(f"\nTables ({len(tables)}):")
    for table in tables:
        print(f"  - {table}")

    return verify_critical_tables(tables)


def verify_critical_tables(tables):
    """Verify all critical tables exist"""
    critical_tables = [
        'users',
        'user_gamification',
        'game_sessions',
        'session_hands',
        'bidding_decisions',
        'play_decisions',
        'hand_analyses',
        'conventions',
        'error_categories',
    ]

    print("\nVerifying critical tables...")
    missing = []
    for table_name in critical_tables:
        if table_name in tables:
            print(f"  {table_name}")
        else:
            print(f"  {table_name} - MISSING!")
            missing.append(table_name)

    if missing:
        print(f"\nWARNING: {len(missing)} critical table(s) missing: {missing}")
        return False

    print("\nAll critical tables verified.")
    return True


def main():
    print()
    print("=" * 60)
    print("Bridge Bidding App - Database Initialization")
    print("  Database type: PostgreSQL")
    print("=" * 60)
    print()

    success = init_postgresql()

    print()
    if success:
        print("Database initialization complete!")
        sys.exit(0)
    else:
        print("Database initialization incomplete - check errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
