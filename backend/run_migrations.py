"""
Database Migration Runner

Automatically runs SQL migration files from the migrations/ directory.
Tracks which migrations have been applied using a migrations_applied table.

Usage:
    python run_migrations.py [db_path]

    Or import and call:
    from run_migrations import run_migrations
    run_migrations('bridge.db')
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Tuple
import sys


def get_migration_files(migrations_dir: str = 'migrations') -> List[Tuple[str, str]]:
    """
    Get all .sql migration files in order.

    Returns:
        List of (filename, filepath) tuples sorted by filename
    """
    migrations_path = Path(migrations_dir)

    if not migrations_path.exists():
        print(f"Warning: Migrations directory '{migrations_dir}' not found")
        return []

    sql_files = list(migrations_path.glob('*.sql'))
    # Sort by filename (assumes numbered like 001_, 002_, etc.)
    sql_files.sort(key=lambda p: p.name)

    return [(f.name, str(f)) for f in sql_files]


def init_migrations_table(conn: sqlite3.Connection):
    """Create migrations tracking table if it doesn't exist"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations_applied (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def is_migration_applied(conn: sqlite3.Connection, migration_name: str) -> bool:
    """Check if a migration has already been applied"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM migrations_applied WHERE migration_name = ?",
        (migration_name,)
    )
    count = cursor.fetchone()[0]
    return count > 0


def apply_migration(conn: sqlite3.Connection, migration_name: str, filepath: str):
    """
    Apply a single migration file.

    Reads the SQL file and executes it within a transaction.
    Records the migration in migrations_applied table.
    """
    print(f"  Applying migration: {migration_name}")

    try:
        # Read migration file
        with open(filepath, 'r') as f:
            sql_content = f.read()

        # Execute migration
        cursor = conn.cursor()
        cursor.executescript(sql_content)

        # Record migration as applied
        cursor.execute(
            "INSERT INTO migrations_applied (migration_name) VALUES (?)",
            (migration_name,)
        )

        conn.commit()
        print(f"  ✓ Successfully applied: {migration_name}")

    except Exception as e:
        conn.rollback()
        print(f"  ✗ Failed to apply {migration_name}: {e}")
        raise


def run_migrations(db_path: str = 'bridge.db', migrations_dir: str = 'migrations'):
    """
    Run all pending database migrations.

    Args:
        db_path: Path to SQLite database file
        migrations_dir: Directory containing migration .sql files

    Returns:
        Number of migrations applied
    """
    # Ensure we're in the backend directory for relative paths
    if os.path.basename(os.getcwd()) != 'backend':
        if os.path.exists('backend'):
            os.chdir('backend')

    print(f"\n{'='*60}")
    print(f"Database Migration Runner")
    print(f"{'='*60}")
    print(f"Database: {db_path}")
    print(f"Migrations directory: {migrations_dir}")

    # Connect to database
    conn = sqlite3.connect(db_path)

    try:
        # Initialize migrations tracking table
        init_migrations_table(conn)

        # Get all migration files
        migrations = get_migration_files(migrations_dir)

        if not migrations:
            print("\nNo migration files found.")
            return 0

        print(f"\nFound {len(migrations)} migration file(s)")

        # Apply each migration that hasn't been applied yet
        applied_count = 0
        skipped_count = 0

        for migration_name, filepath in migrations:
            if is_migration_applied(conn, migration_name):
                print(f"  Skipping (already applied): {migration_name}")
                skipped_count += 1
            else:
                apply_migration(conn, migration_name, filepath)
                applied_count += 1

        print(f"\n{'='*60}")
        print(f"Migration Summary:")
        print(f"  Applied: {applied_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total: {len(migrations)}")
        print(f"{'='*60}\n")

        return applied_count

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        raise

    finally:
        conn.close()


def list_applied_migrations(db_path: str = 'bridge.db'):
    """List all applied migrations"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()

        # Check if migrations table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='migrations_applied'
        """)

        if not cursor.fetchone():
            print("No migrations have been applied yet (migrations_applied table does not exist)")
            return

        cursor.execute("""
            SELECT migration_name, applied_at
            FROM migrations_applied
            ORDER BY applied_at
        """)

        rows = cursor.fetchall()

        print("\nApplied Migrations:")
        print("-" * 60)
        for row in rows:
            print(f"  {row['migration_name']:<50} {row['applied_at']}")
        print(f"\nTotal: {len(rows)} migration(s) applied")

    finally:
        conn.close()


if __name__ == '__main__':
    # Allow database path as command line argument
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'bridge.db'

    # Check if --list flag is provided
    if '--list' in sys.argv:
        list_applied_migrations(db_path)
    else:
        try:
            run_migrations(db_path)
        except Exception as e:
            print(f"\nFatal error: {e}")
            sys.exit(1)
