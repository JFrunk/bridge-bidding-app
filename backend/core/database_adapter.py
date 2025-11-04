"""
Database Abstraction Layer
===========================

Provides unified interface for both SQLite (development) and PostgreSQL (production).
Automatically selects database based on environment variables.

Environment Variables:
- DATABASE_URL: PostgreSQL connection string (Render auto-sets this)
- If DATABASE_URL exists → PostgreSQL
- If DATABASE_URL missing → SQLite (bridge.db)

Usage:
    from core.database_adapter import get_db_connection, execute_query

    # Get connection (auto-detects DB type)
    conn = get_db_connection()

    # Execute query (works with both SQLite and PostgreSQL)
    result = execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
"""

import os
import sqlite3
import json
from typing import Optional, Dict, List, Tuple, Any
from contextlib import contextmanager

# Check if PostgreSQL is available
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Determine database type from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None and POSTGRES_AVAILABLE

# SQLite path for development
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bridge.db')


class DatabaseAdapter:
    """
    Unified database interface supporting both SQLite and PostgreSQL.

    Handles:
    - Connection management
    - Query execution with parameter substitution
    - JSON serialization/deserialization
    - Transaction management
    - Error handling
    """

    def __init__(self):
        self.db_type = 'postgresql' if USE_POSTGRES else 'sqlite'
        print(f"[DatabaseAdapter] Using {self.db_type}")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Ensures proper cleanup even if errors occur.

        Usage:
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        if USE_POSTGRES:
            conn = psycopg2.connect(DATABASE_URL)
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                yield conn
            finally:
                conn.close()

    def execute_query(self, query: str, params: Tuple = (), fetch: str = 'all') -> Optional[List[Dict]]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query (use ? for parameters in SQLite, %s in PostgreSQL)
            params: Query parameters
            fetch: 'all', 'one', or 'none'

        Returns:
            List of dicts (fetch='all'), single dict (fetch='one'), or None (fetch='none')

        Note: This method automatically converts ? to %s for PostgreSQL
        """
        # Convert SQLite placeholders (?) to PostgreSQL placeholders (%s)
        if USE_POSTGRES:
            query = query.replace('?', '%s')

        with self.get_connection() as conn:
            if USE_POSTGRES:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            else:
                cursor = conn.cursor()

            cursor.execute(query, params)

            if fetch == 'all':
                rows = cursor.fetchall()
                return [dict(row) for row in rows] if rows else []
            elif fetch == 'one':
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                return None

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Number of rows affected
        """
        # Convert SQLite placeholders to PostgreSQL
        if USE_POSTGRES:
            query = query.replace('?', '%s')

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def execute_insert(self, query: str, params: Tuple = ()) -> Optional[int]:
        """
        Execute an INSERT query and return the new row ID.

        Args:
            query: SQL INSERT query
            params: Query parameters

        Returns:
            ID of newly inserted row
        """
        # Convert SQLite placeholders to PostgreSQL
        if USE_POSTGRES:
            query = query.replace('?', '%s')
            # Add RETURNING id for PostgreSQL
            if 'RETURNING' not in query.upper():
                query += ' RETURNING id'

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

            if USE_POSTGRES:
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                return cursor.lastrowid

    def serialize_json(self, data: Any) -> str:
        """
        Serialize Python object to JSON string.

        For SQLite: Returns JSON string
        For PostgreSQL: Returns JSON string (JSONB column handles it)
        """
        if data is None:
            return None
        return json.dumps(data)

    def deserialize_json(self, json_str: str) -> Any:
        """
        Deserialize JSON string to Python object.

        Args:
            json_str: JSON string from database

        Returns:
            Python dict/list/primitive
        """
        if json_str is None:
            return None

        # PostgreSQL returns dict directly from JSONB columns
        if isinstance(json_str, dict) or isinstance(json_str, list):
            return json_str

        # SQLite returns string - need to parse
        return json.loads(json_str)

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of table to check

        Returns:
            True if table exists, False otherwise
        """
        if USE_POSTGRES:
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """
            result = self.execute_query(query, (table_name,), fetch='one')
            return result['exists'] if result else False
        else:
            query = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """
            result = self.execute_query(query, (table_name,), fetch='one')
            return result is not None

    def create_tables_if_needed(self):
        """
        Create database tables if they don't exist.

        For SQLite: Runs backend/database/init_all_tables.py
        For PostgreSQL: Runs backend/database/postgresql_schema.sql
        """
        # Check if critical tables exist
        if self.table_exists('users') and self.table_exists('active_play_states'):
            print("[DatabaseAdapter] Tables already exist")
            return

        print("[DatabaseAdapter] Creating tables...")

        if USE_POSTGRES:
            # Read and execute PostgreSQL schema
            schema_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'database',
                'postgresql_schema.sql'
            )

            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"PostgreSQL schema not found: {schema_path}")

            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(schema_sql)
                conn.commit()

            print("[DatabaseAdapter] PostgreSQL tables created")
        else:
            # Use existing SQLite initialization
            import subprocess
            init_script = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'database',
                'init_all_tables.py'
            )

            subprocess.run(['python3', init_script], check=True)
            print("[DatabaseAdapter] SQLite tables created")


# Global adapter instance
_adapter = None

def get_adapter() -> DatabaseAdapter:
    """Get or create the global DatabaseAdapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = DatabaseAdapter()
    return _adapter

def get_db_connection():
    """
    Get a database connection (context manager).

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
    """
    return get_adapter().get_connection()

def execute_query(query: str, params: Tuple = (), fetch: str = 'all') -> Optional[List[Dict]]:
    """Execute a SELECT query. See DatabaseAdapter.execute_query for details."""
    return get_adapter().execute_query(query, params, fetch)

def execute_update(query: str, params: Tuple = ()) -> int:
    """Execute an UPDATE/DELETE query. See DatabaseAdapter.execute_update for details."""
    return get_adapter().execute_update(query, params)

def execute_insert(query: str, params: Tuple = ()) -> Optional[int]:
    """Execute an INSERT query. See DatabaseAdapter.execute_insert for details."""
    return get_adapter().execute_insert(query, params)
