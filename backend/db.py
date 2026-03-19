"""
Database Layer for Bridge Bidding App

PostgreSQL database interface.

Usage:
    from db import get_connection, execute_query

    # Simple query
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        results = cursor.fetchall()

    # The connection auto-commits and closes when exiting the context

Environment:
    DATABASE_URL must be set to a PostgreSQL connection string.
"""

import os
import re
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Set it to a PostgreSQL connection string, e.g.: "
        "postgresql://user:password@localhost:5432/bridge_bidding"
    )


class CursorWrapper:
    """
    Wraps a PostgreSQL cursor to provide RealDictCursor access
    and lastrowid support via automatic RETURNING id.
    """

    def __init__(self, cursor):
        self._cursor = cursor
        self._lastrowid = None

    def execute(self, query, params=None):
        """Execute a query, auto-adding RETURNING id to INSERTs for lastrowid."""
        try:
            query_to_run = query
            if query.strip().upper().startswith('INSERT') and 'RETURNING' not in query.upper():
                query_to_run = query.rstrip(';') + ' RETURNING id'
                self._cursor.execute("SAVEPOINT _returning_id_probe")

            if params:
                self._cursor.execute(query_to_run, params)
            else:
                self._cursor.execute(query_to_run)

        except Exception as e:
            if "column \"id\" does not exist" in str(e).lower() and query_to_run != query:
                self._cursor.execute("ROLLBACK TO SAVEPOINT _returning_id_probe")

                if params:
                    self._cursor.execute(query, params)
                else:
                    self._cursor.execute(query)
            else:
                raise e

        if query.strip().upper().startswith('INSERT') and 'RETURNING' in query_to_run.upper():
            try:
                result = self._cursor.fetchone()
                if result:
                    self._lastrowid = result[0] if isinstance(result, tuple) else result.get('id')
            except:
                pass

    def executemany(self, query, params_list):
        """Execute a query multiple times with different parameters."""
        self._cursor.executemany(query, params_list)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        if size:
            return self._cursor.fetchmany(size)
        return self._cursor.fetchmany()

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class ConnectionWrapper:
    """
    Wraps a PostgreSQL connection with context manager support
    for auto-commit on success and rollback on exception.
    """

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        """Get a cursor with RealDictCursor for dict-like row access."""
        return CursorWrapper(self._conn.cursor(cursor_factory=RealDictCursor))

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def execute(self, query, params=None):
        """Convenience method to execute a query directly."""
        cursor = self.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


def get_connection():
    """
    Get a PostgreSQL database connection.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
        # Connection auto-commits on success, rolls back on exception

    Returns:
        ConnectionWrapper: A wrapped PostgreSQL connection
    """
    conn = psycopg2.connect(DATABASE_URL)
    return ConnectionWrapper(conn)


# For backwards compatibility
connect = get_connection


def execute_query(cursor, query, params=None):
    """
    Execute a query on a cursor (wrapped or raw).

    Args:
        cursor: Database cursor (CursorWrapper or raw psycopg2)
        query: SQL query with %s placeholders
        params: Query parameters (tuple or list)

    Returns:
        The cursor (for chaining)
    """
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    return cursor


def date_subtract(days):
    """
    Return SQL expression for current timestamp minus N days.

    Usage in query:
        f"timestamp >= {date_subtract(30)}"
    """
    return f"NOW() - INTERVAL '{days} days'"


def date_between(days_ago_start, days_ago_end):
    """
    Return SQL expressions for a date range (exclusive end).

    Returns tuple: (start_expr, end_expr)

    Usage:
        start, end = date_between(14, 7)  # Between 14 and 7 days ago
        f"timestamp >= {start} AND timestamp < {end}"
    """
    return (date_subtract(days_ago_start), date_subtract(days_ago_end))


def init_database():
    """
    Initialize the database schema if tables don't exist.

    Runs schema_postgresql.sql and applies all migrations.
    This should be called on application startup.
    """
    schema_dir = Path(__file__).parent / 'database'

    CRITICAL_TABLES = [
        'users',
        'user_settings',
        'user_gamification',
        'game_sessions',
        'session_hands',
        'bidding_decisions',
        'hand_analyses',
    ]

    schema_path = schema_dir / 'schema_postgresql.sql'
    if schema_path.exists():
        print(f"Initializing PostgreSQL database from {schema_path}")
        with open(schema_path, 'r') as f:
            sql = f.read()
        with get_connection() as conn:
            cursor = conn.cursor()
            _execute_script(cursor, sql)

        # Apply all migrations
        print("Checking for pending migrations...")
        migrations_dir = schema_dir.parent / 'migrations'
        if migrations_dir.exists():
            migration_files = sorted([f for f in migrations_dir.iterdir() if f.suffix == '.sql'])

            with get_connection() as conn:
                cursor = conn.cursor()
                for migration_file in migration_files:
                    print(f"Applying migration: {migration_file.name}")
                    with open(migration_file, 'r') as f:
                        sql = f.read()
                        try:
                            _execute_script(cursor, sql)
                        except Exception as e:
                            print(f"Warning skipping {migration_file.name}: {e}")

        # Verify critical tables
        print("\nVerifying critical tables...")
        with get_connection() as conn:
            cursor = conn.cursor()
            missing_tables = []
            for table in CRITICAL_TABLES:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s
                    )
                """, (table,))
                result = cursor.fetchone()
                exists = result['exists'] if isinstance(result, dict) else result[0]
                if exists:
                    print(f"  {table}")
                else:
                    print(f"  {table} - MISSING!")
                    missing_tables.append(table)

            if missing_tables:
                print(f"\nWARNING: {len(missing_tables)} critical table(s) missing: {missing_tables}")
            else:
                print("\nAll critical tables verified")

        print("PostgreSQL schema initialized successfully")
    else:
        print(f"WARNING: PostgreSQL schema not found at {schema_path}")


def _execute_script(cursor, script):
    """Execute a SQL script (multiple statements)."""
    clean_script = re.sub(r'--[^\n]*\n', '\n', script)
    clean_script = re.sub(r'/\*.*?\*/', '', clean_script, flags=re.DOTALL)

    statements = [s.strip() for s in clean_script.split(';') if s.strip()]
    success_count = 0
    error_count = 0

    for statement in statements:
        if not statement:
            continue
        try:
            cursor.execute(statement)
            success_count += 1
            if 'CREATE TABLE' in statement.upper():
                match = re.search(r'CREATE TABLE[^"\'`\s]*\s+(?:IF NOT EXISTS\s+)?["\']?(\w+)', statement, re.IGNORECASE)
                if match:
                    print(f"  Created table: {match.group(1)}")
        except Exception as e:
            error_count += 1
            error_str = str(e).lower()
            if 'already exists' not in error_str and 'duplicate' not in error_str:
                print(f"SQL Error: {e}")
                print(f"  Statement: {statement[:100]}...")

    print(f"Schema execution complete: {success_count} statements succeeded, {error_count} errors")


# Print startup message
if __name__ != '__main__':
    print("Database: PostgreSQL")
