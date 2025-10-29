#!/usr/bin/env python3
"""
Database Cleanup Script
Removes test/old data to provide fresh user experience

Options:
  1. Complete reset - Delete all user data (recommended for dev)
  2. Selective cleanup - Remove only old test data
  3. User separation - Keep test data, create fresh user
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = 'bridge.db'


def print_current_state(conn):
    """Show current database state"""
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("CURRENT DATABASE STATE")
    print("=" * 60)

    tables = [
        ('bidding_decisions', 'timestamp'),
        ('session_hands', 'played_at'),
        ('game_sessions', 'started_at'),
        ('ai_play_log', 'timestamp'),
        ('hand_analyses', None)
    ]

    for table, timestamp_col in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:30} {count:5} records")

        if count > 0 and timestamp_col:
            cursor.execute(f"SELECT MIN({timestamp_col}), MAX({timestamp_col}) FROM {table}")
            min_ts, max_ts = cursor.fetchone()
            print(f"  → Date range: {min_ts} to {max_ts}")

    print("=" * 60 + "\n")


def option1_complete_reset(conn):
    """
    Option 1: Complete Database Reset
    Deletes ALL user data for a fresh start
    """
    print("\n🗑️  OPTION 1: Complete Database Reset")
    print("This will delete ALL data from the following tables:")
    print("  - bidding_decisions")
    print("  - session_hands")
    print("  - game_sessions")
    print("  - ai_play_log")
    print("  - hand_analyses")
    print()

    response = input("Are you sure? Type 'YES' to confirm: ")
    if response != 'YES':
        print("Cancelled.")
        return False

    cursor = conn.cursor()

    # Delete in order (respecting foreign keys)
    tables_to_clear = [
        'hand_analyses',
        'ai_play_log',
        'session_hands',
        'game_sessions',
        'bidding_decisions'
    ]

    for table in tables_to_clear:
        cursor.execute(f"DELETE FROM {table}")
        deleted = cursor.rowcount
        print(f"✓ Deleted {deleted} records from {table}")

    conn.commit()
    print("\n✅ Complete reset successful!")
    return True


def option2_selective_cleanup(conn):
    """
    Option 2: Selective Cleanup
    Removes only test data from October 17
    """
    print("\n🧹 OPTION 2: Selective Cleanup")
    print("This will delete:")
    print("  - Bidding decisions from before Oct 24, 2025")
    print("  - Game sessions started before Oct 24, 2025 (if no hands played)")
    print()

    response = input("Proceed? Type 'yes' to confirm: ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return False

    cursor = conn.cursor()

    # Delete old bidding decisions
    cursor.execute("DELETE FROM bidding_decisions WHERE DATE(timestamp) < '2025-10-24'")
    deleted_bids = cursor.rowcount
    print(f"✓ Deleted {deleted_bids} old bidding decisions")

    # Delete old AI play logs
    cursor.execute("DELETE FROM ai_play_log WHERE DATE(timestamp) < '2025-10-24'")
    deleted_ai = cursor.rowcount
    print(f"✓ Deleted {deleted_ai} old AI play logs")

    # Check for old sessions with no hands played
    cursor.execute("""
        DELETE FROM game_sessions
        WHERE DATE(started_at) < '2025-10-24'
        AND hands_completed = 0
    """)
    deleted_sessions = cursor.rowcount
    print(f"✓ Deleted {deleted_sessions} empty old sessions")

    conn.commit()
    print("\n✅ Selective cleanup successful!")
    return True


def option3_user_separation(conn):
    """
    Option 3: User ID Separation
    Keeps test data under user_id=1, creates fresh user_id=2
    """
    print("\n👤 OPTION 3: User Separation")
    print("This will:")
    print("  - Keep all existing data under user_id=1 (test user)")
    print("  - Create a fresh user_id=2 for actual gameplay")
    print("  - Dashboard for user_id=2 will be empty")
    print()
    print("Note: Frontend needs to be updated to use user_id=2")
    print()

    response = input("Proceed? Type 'yes' to confirm: ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return False

    cursor = conn.cursor()

    # Check if user_id=2 already exists
    cursor.execute("SELECT COUNT(*) FROM game_sessions WHERE user_id = 2")
    if cursor.fetchone()[0] > 0:
        print("⚠️  User ID 2 already has data")
        return False

    print("✓ User ID 2 is ready for fresh data")
    print("\n📝 To use user_id=2:")
    print("   1. Update frontend/src/App.js")
    print("   2. Change all instances of 'user_id: 1' to 'user_id: 2'")
    print("   3. Or add a login system to dynamically set user_id")
    print("\n✅ User separation ready!")
    return True


def show_preview(conn):
    """Show what data would be deleted"""
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("DATA PREVIEW")
    print("=" * 60)

    # Old bidding decisions
    cursor.execute("""
        SELECT id, timestamp, user_bid, optimal_bid, correctness
        FROM bidding_decisions
        WHERE DATE(timestamp) < '2025-10-24'
        ORDER BY timestamp
    """)
    old_bids = cursor.fetchall()
    if old_bids:
        print(f"\n📊 Old Bidding Decisions ({len(old_bids)} to delete):")
        for row in old_bids:
            print(f"  ID {row[0]:2}: {row[1]} | {row[2]:5} vs {row[3]:5} ({row[4]})")

    # Recent data to keep
    cursor.execute("""
        SELECT id, timestamp, user_bid, optimal_bid, correctness
        FROM bidding_decisions
        WHERE DATE(timestamp) >= '2025-10-24'
        ORDER BY timestamp
    """)
    new_bids = cursor.fetchall()
    if new_bids:
        print(f"\n✅ Recent Bidding Decisions ({len(new_bids)} to keep):")
        for row in new_bids:
            print(f"  ID {row[0]:2}: {row[1]} | {row[2]:5} vs {row[3]:5} ({row[4]})")

    print("=" * 60 + "\n")


def main():
    """Main cleanup script"""
    print("\n" + "=" * 60)
    print("DATABASE CLEANUP SCRIPT")
    print("=" * 60)

    # Connect to database
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return 1

    # Show current state
    print_current_state(conn)

    # Show data preview
    show_preview(conn)

    # Ask user which option
    print("\nCLEANUP OPTIONS:")
    print("  1. Complete Reset - Delete ALL data (recommended for dev)")
    print("  2. Selective Cleanup - Remove old test data only")
    print("  3. User Separation - Keep test data, create fresh user_id")
    print("  4. Cancel - Exit without changes")
    print()

    choice = input("Choose an option (1-4): ").strip()

    if choice == '1':
        success = option1_complete_reset(conn)
    elif choice == '2':
        success = option2_selective_cleanup(conn)
    elif choice == '3':
        success = option3_user_separation(conn)
    else:
        print("Cancelled.")
        conn.close()
        return 0

    if success:
        print("\n" + "=" * 60)
        print("FINAL STATE")
        print("=" * 60)
        print_current_state(conn)

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
