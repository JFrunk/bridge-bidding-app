#!/usr/bin/env python3
"""
Initialize ALL database tables for Bridge Bidding App
This script ensures all tables, views, and indexes exist in the database.

Usage:
    python3 backend/database/init_all_tables.py
    python3 backend/database/init_all_tables.py path/to/custom.db

This script is safe to run multiple times (uses CREATE IF NOT EXISTS).
"""

import sqlite3
import os
import sys
from pathlib import Path


def run_sql_file(cursor, sql_file_path):
    """Execute SQL from a file"""
    if not os.path.exists(sql_file_path):
        print(f"⚠️  SQL file not found: {sql_file_path}")
        return False

    with open(sql_file_path, 'r') as f:
        sql_content = f.read()

    try:
        # Execute all SQL statements
        cursor.executescript(sql_content)
        print(f"✅ Applied: {os.path.basename(sql_file_path)}")
        return True
    except Exception as e:
        print(f"❌ Error in {sql_file_path}: {e}")
        return False


def init_all_tables(db_path='bridge.db'):
    """Initialize all database tables, views, and indexes"""

    # Resolve paths
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir.parent

    # If db_path is relative, make it relative to backend dir
    if not os.path.isabs(db_path):
        db_full_path = backend_dir / db_path
    else:
        db_full_path = Path(db_path)

    print(f"🗄️  Initializing database: {db_full_path}")
    print(f"   Backend directory: {backend_dir}")
    print()

    # Create database if it doesn't exist
    db_full_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_full_path))
    cursor = conn.cursor()

    try:
        # List of schema files to apply in order
        schema_files = [
            'database/schema_user_management.sql',
            'database/schema_game_sessions.sql',
            'database/schema_convention_levels.sql',
        ]

        # List of migration files
        migration_files = [
            'migrations/001_add_bidding_feedback_tables.sql',
            'migrations/004_add_learning_mode_tables.sql',
            'migrations/005_add_play_learning_tables.sql',
            'migrations/006_add_play_decisions_table.sql',
            'migrations/007_add_dds_analysis.sql',
            'migrations/008_add_hand_number_to_play_decisions.sql',
            'migrations/009_add_hand_number_to_bidding_decisions.sql',
            'migrations/010_add_analysis_source.sql',
            'migrations/011_add_comprehensive_analysis.sql',
            'migrations/012_add_deal_data_to_bidding_decisions.sql',
        ]

        print("📋 Applying schema files...")
        print("-" * 60)

        for schema_file in schema_files:
            sql_path = backend_dir / schema_file
            run_sql_file(cursor, sql_path)

        print()
        print("🔄 Applying migrations...")
        print("-" * 60)

        for migration_file in migration_files:
            sql_path = backend_dir / migration_file
            run_sql_file(cursor, sql_path)

        conn.commit()

        print()
        print("=" * 60)
        print("📊 Database Status:")
        print("=" * 60)

        # List all tables
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        print(f"\n✅ Tables ({len(tables)}):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table:30} ({count} rows)")

        # List all views
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view'
            ORDER BY name
        """)
        views = [row[0] for row in cursor.fetchall()]

        print(f"\n✅ Views ({len(views)}):")
        for view in views:
            print(f"   - {view}")

        # Verify critical tables exist
        print()
        print("🔍 Verifying critical tables...")
        critical_tables = [
            'users',
            'game_sessions',
            'session_hands',
            'bidding_decisions',  # For bidding feedback tracking
            'play_decisions',     # For play feedback tracking (DDS-based)
            'hand_analyses',
            'conventions',
            'error_categories',
        ]

        missing_tables = []
        for table_name in critical_tables:
            if table_name in tables:
                print(f"   ✅ {table_name}")
            else:
                print(f"   ❌ {table_name} - MISSING!")
                missing_tables.append(table_name)

        if missing_tables:
            print()
            print(f"⚠️  WARNING: {len(missing_tables)} critical table(s) missing!")
            print("   This may cause errors in the application.")
            return False

        print()
        print("=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
        print()
        print(f"Database ready at: {db_full_path}")

        return True

    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        conn.close()


def main():
    """Main entry point"""
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'bridge.db'

    print()
    print("=" * 60)
    print("Bridge Bidding App - Database Initialization")
    print("=" * 60)
    print()

    success = init_all_tables(db_path)

    if success:
        print("✅ SUCCESS: Database is ready to use!")
        sys.exit(0)
    else:
        print("❌ FAILED: Database initialization incomplete")
        print("   Check error messages above for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
