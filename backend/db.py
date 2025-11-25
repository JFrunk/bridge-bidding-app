"""
Database Abstraction Layer for Bridge Bidding App

Provides a unified interface for database operations that works with both:
- SQLite (local development)
- PostgreSQL (production on Render)

Usage:
    from db import get_connection, execute_query

    # Simple query
    with get_connection() as conn:
        cursor = conn.cursor()
        execute_query(cursor, "SELECT * FROM users WHERE id = ?", (user_id,))
        results = cursor.fetchall()

    # The connection auto-commits and closes when exiting the context

Environment:
    - If DATABASE_URL is set: Uses PostgreSQL
    - Otherwise: Uses SQLite (bridge.db)
"""

import os
import sqlite3
import re
from contextlib import contextmanager
from pathlib import Path

# Check for PostgreSQL availability
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None
    RealDictCursor = None

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
SQLITE_PATH = Path(__file__).parent / 'bridge.db'

# Detect which database to use
USE_POSTGRES = DATABASE_URL is not None and POSTGRES_AVAILABLE


def _convert_placeholders(query):
    """
    Convert SQLite-style ? placeholders to PostgreSQL-style %s placeholders.

    This allows all existing code to continue using ? placeholders,
    which get converted automatically when using PostgreSQL.

    Examples:
        "SELECT * FROM users WHERE id = ?" -> "SELECT * FROM users WHERE id = %s"
        "INSERT INTO users (name, email) VALUES (?, ?)" -> "INSERT INTO users (name, email) VALUES (%s, %s)"

    Note: This is a simple conversion that handles most cases.
    Complex queries with ? in strings might need manual handling.
    """
    if not USE_POSTGRES:
        return query

    # Replace ? with %s, but not inside quoted strings
    # This regex handles single-quoted strings
    result = []
    in_string = False
    i = 0
    while i < len(query):
        char = query[i]
        if char == "'" and (i == 0 or query[i-1] != '\\'):
            in_string = not in_string
            result.append(char)
        elif char == '?' and not in_string:
            result.append('%s')
        else:
            result.append(char)
        i += 1

    return ''.join(result)


def _convert_schema_to_postgres(sql):
    """
    Convert SQLite schema SQL to PostgreSQL-compatible SQL.

    Handles common differences:
    - INTEGER PRIMARY KEY AUTOINCREMENT -> SERIAL PRIMARY KEY
    - DATETIME -> TIMESTAMP
    - Boolean handling
    """
    if not USE_POSTGRES:
        return sql

    # Replace AUTOINCREMENT with SERIAL
    sql = re.sub(
        r'INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT',
        'SERIAL PRIMARY KEY',
        sql,
        flags=re.IGNORECASE
    )

    # Replace INTEGER PRIMARY KEY (without AUTOINCREMENT) with SERIAL PRIMARY KEY
    # Only for id columns that should auto-increment
    sql = re.sub(
        r'(\bid\b\s+)INTEGER\s+PRIMARY\s+KEY(?!\s+AUTOINCREMENT)',
        r'\1SERIAL PRIMARY KEY',
        sql,
        flags=re.IGNORECASE
    )

    # Replace DATETIME with TIMESTAMP
    sql = re.sub(r'\bDATETIME\b', 'TIMESTAMP', sql, flags=re.IGNORECASE)

    # Replace SQLite's CURRENT_TIMESTAMP syntax if needed
    # (Usually compatible, but ensure it's standard)

    return sql


class PostgresCursorWrapper:
    """
    Wraps a PostgreSQL cursor to provide SQLite-compatible interface.

    Key differences handled:
    - Converts ? placeholders to %s
    - Provides lastrowid property (PostgreSQL uses RETURNING)
    """

    def __init__(self, cursor):
        self._cursor = cursor
        self._lastrowid = None

    def execute(self, query, params=None):
        """Execute a query with automatic placeholder conversion."""
        converted_query = _convert_placeholders(query)

        # Handle INSERT with RETURNING for lastrowid
        if converted_query.strip().upper().startswith('INSERT') and 'RETURNING' not in converted_query.upper():
            # Add RETURNING id to get the inserted row's ID
            if 'id' in converted_query.lower() or 'SERIAL' in converted_query.upper():
                converted_query = converted_query.rstrip(';') + ' RETURNING id'

        if params:
            self._cursor.execute(converted_query, params)
        else:
            self._cursor.execute(converted_query)

        # Try to get lastrowid from RETURNING clause
        if converted_query.strip().upper().startswith('INSERT') and 'RETURNING' in converted_query.upper():
            try:
                result = self._cursor.fetchone()
                if result:
                    self._lastrowid = result[0] if isinstance(result, tuple) else result.get('id')
            except:
                pass

    def executemany(self, query, params_list):
        """Execute a query multiple times with different parameters."""
        converted_query = _convert_placeholders(query)
        self._cursor.executemany(converted_query, params_list)

    def executescript(self, script):
        """Execute multiple SQL statements (for schema creation)."""
        converted_script = _convert_schema_to_postgres(script)
        # PostgreSQL doesn't have executescript, so split and execute
        statements = [s.strip() for s in converted_script.split(';') if s.strip()]
        for statement in statements:
            try:
                self._cursor.execute(statement)
            except Exception as e:
                # Log but continue - some statements might fail if objects exist
                print(f"Warning: {e}")

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
    Wraps a database connection to provide consistent interface.

    Works with both SQLite and PostgreSQL connections.
    """

    def __init__(self, conn, is_postgres=False):
        self._conn = conn
        self._is_postgres = is_postgres

    def cursor(self):
        """Get a cursor, wrapped for compatibility if PostgreSQL."""
        if self._is_postgres:
            return PostgresCursorWrapper(self._conn.cursor())
        return self._conn.cursor()

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
    Get a database connection.

    Returns a ConnectionWrapper that works with both SQLite and PostgreSQL.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
        # Connection auto-commits on success, rolls back on exception

    Returns:
        ConnectionWrapper: A wrapped database connection
    """
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return ConnectionWrapper(conn, is_postgres=True)
    else:
        conn = sqlite3.connect(str(SQLITE_PATH))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return ConnectionWrapper(conn, is_postgres=False)


def get_raw_connection():
    """
    Get a raw (unwrapped) database connection.

    Use this only when you need direct access to the underlying connection,
    such as for advanced features or testing.

    Returns:
        sqlite3.Connection or psycopg2.connection
    """
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect(str(SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def execute_query(cursor, query, params=None):
    """
    Execute a query with automatic placeholder conversion.

    This is a convenience function that handles the ? to %s conversion
    for PostgreSQL automatically.

    Args:
        cursor: Database cursor (can be wrapped or raw)
        query: SQL query with ? placeholders
        params: Query parameters (tuple or list)

    Returns:
        The cursor (for chaining)
    """
    if hasattr(cursor, '_cursor'):
        # Already a wrapped cursor, execute will handle conversion
        cursor.execute(query, params)
    elif USE_POSTGRES:
        # Raw PostgreSQL cursor, need to convert
        converted_query = _convert_placeholders(query)
        if params:
            cursor.execute(converted_query, params)
        else:
            cursor.execute(converted_query)
    else:
        # SQLite cursor, no conversion needed
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

    return cursor


def get_db_type():
    """
    Get the current database type.

    Returns:
        str: 'postgresql' or 'sqlite'
    """
    return 'postgresql' if USE_POSTGRES else 'sqlite'


def is_postgres():
    """Check if using PostgreSQL."""
    return USE_POSTGRES


def is_sqlite():
    """Check if using SQLite."""
    return not USE_POSTGRES


# For backwards compatibility - allow importing like sqlite3
connect = get_connection


def init_database():
    """
    Initialize the database schema if tables don't exist.

    This should be called on application startup to ensure
    all required tables exist.
    """
    from pathlib import Path

    schema_dir = Path(__file__).parent / 'database'

    if USE_POSTGRES:
        # Use dedicated PostgreSQL schema file
        schema_path = schema_dir / 'schema_postgresql.sql'
        if schema_path.exists():
            print(f"Initializing PostgreSQL database from {schema_path}")
            with open(schema_path, 'r') as f:
                sql = f.read()
            with get_connection() as conn:
                cursor = conn.cursor()
                _execute_script(cursor, sql)
            print("PostgreSQL schema initialized successfully")
        else:
            print(f"WARNING: PostgreSQL schema not found at {schema_path}")
    else:
        # SQLite: use individual schema files
        schema_files = [
            'schema_user_management.sql',
            'schema_game_sessions.sql',
            'schema_convention_levels.sql',
        ]

        migration_files = [
            '../migrations/001_add_bidding_feedback_tables.sql',
        ]

        with get_connection() as conn:
            cursor = conn.cursor()

            for schema_file in schema_files:
                schema_path = schema_dir / schema_file
                if schema_path.exists():
                    with open(schema_path, 'r') as f:
                        sql = f.read()
                        try:
                            cursor.executescript(sql) if hasattr(cursor, 'executescript') else _execute_script(cursor, sql)
                        except Exception as e:
                            print(f"Warning applying {schema_file}: {e}")

            for migration_file in migration_files:
                migration_path = schema_dir / migration_file
                if migration_path.exists():
                    with open(migration_path, 'r') as f:
                        sql = f.read()
                        try:
                            cursor.executescript(sql) if hasattr(cursor, 'executescript') else _execute_script(cursor, sql)
                        except Exception as e:
                            print(f"Warning applying {migration_file}: {e}")


def _execute_script(cursor, script):
    """Execute a SQL script (multiple statements) on PostgreSQL."""
    # Remove single-line comments (-- to end of line)
    import re
    clean_script = re.sub(r'--[^\n]*\n', '\n', script)

    statements = [s.strip() for s in clean_script.split(';') if s.strip()]
    for statement in statements:
        # Skip empty statements
        if not statement:
            continue
        try:
            cursor.execute(statement)
        except Exception as e:
            # Log but continue for "already exists" type errors
            if 'already exists' not in str(e).lower():
                print(f"SQL Warning: {e}")


# Print startup message
if __name__ != '__main__':
    db_type = get_db_type()
    if db_type == 'postgresql':
        print(f"Database: PostgreSQL (production)")
    else:
        print(f"Database: SQLite ({SQLITE_PATH})")
