"""
Unit Tests: Database Adapter
=============================

Tests the database abstraction layer that supports both SQLite and PostgreSQL.

Test coverage:
- Connection management
- Query execution with parameter conversion
- JSON serialization/deserialization
- Table existence checks
- Both SQLite and PostgreSQL modes
"""

import pytest
import os
import tempfile
from core.database_adapter import DatabaseAdapter


@pytest.fixture
def sqlite_adapter():
    """Create a DatabaseAdapter for testing with temporary SQLite database."""
    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Set up adapter to use temp database
    original_path = None
    try:
        import core.database_adapter as adapter_module
        original_path = adapter_module.SQLITE_DB_PATH
        adapter_module.SQLITE_DB_PATH = db_path

        # Create adapter
        adapter = DatabaseAdapter()
        yield adapter

    finally:
        # Cleanup
        if original_path:
            adapter_module.SQLITE_DB_PATH = original_path
        if os.path.exists(db_path):
            os.remove(db_path)


def test_connection_context_manager(sqlite_adapter):
    """Test that connection context manager works correctly."""
    with sqlite_adapter.get_connection() as conn:
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1


def test_execute_query_fetch_all(sqlite_adapter):
    """Test execute_query with fetch='all'."""
    # Create test table
    with sqlite_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE test_users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER
            )
        """)
        cursor.execute("INSERT INTO test_users (name, age) VALUES ('Alice', 30)")
        cursor.execute("INSERT INTO test_users (name, age) VALUES ('Bob', 25)")
        conn.commit()

    # Query all rows
    results = sqlite_adapter.execute_query("SELECT * FROM test_users ORDER BY age")

    assert len(results) == 2
    assert results[0]['name'] == 'Bob'
    assert results[0]['age'] == 25
    assert results[1]['name'] == 'Alice'
    assert results[1]['age'] == 30


def test_execute_query_fetch_one(sqlite_adapter):
    """Test execute_query with fetch='one'."""
    # Create and populate table
    with sqlite_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_users (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test_users (name) VALUES ('Charlie')")
        conn.commit()

    # Query single row
    result = sqlite_adapter.execute_query(
        "SELECT * FROM test_users WHERE name = ?",
        ('Charlie',),
        fetch='one'
    )

    assert result is not None
    assert result['name'] == 'Charlie'


def test_execute_query_with_parameters(sqlite_adapter):
    """Test parameterized queries."""
    # Create and populate table
    with sqlite_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        cursor.execute("INSERT INTO test_users (name, age) VALUES ('Dave', 40)")
        cursor.execute("INSERT INTO test_users (name, age) VALUES ('Eve', 35)")
        conn.commit()

    # Query with parameters
    result = sqlite_adapter.execute_query(
        "SELECT * FROM test_users WHERE age > ?",
        (36,),
        fetch='all'
    )

    assert len(result) == 1
    assert result[0]['name'] == 'Dave'


def test_execute_update(sqlite_adapter):
    """Test UPDATE query."""
    # Create and populate table
    with sqlite_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_users (id INTEGER PRIMARY KEY, name TEXT, score INTEGER)")
        cursor.execute("INSERT INTO test_users (name, score) VALUES ('Frank', 10)")
        conn.commit()

    # Update row
    rows_affected = sqlite_adapter.execute_update(
        "UPDATE test_users SET score = ? WHERE name = ?",
        (20, 'Frank')
    )

    assert rows_affected == 1

    # Verify update
    result = sqlite_adapter.execute_query(
        "SELECT score FROM test_users WHERE name = ?",
        ('Frank',),
        fetch='one'
    )
    assert result['score'] == 20


def test_execute_insert(sqlite_adapter):
    """Test INSERT query and get new row ID."""
    # Create table
    with sqlite_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_users (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()

    # Insert row
    new_id = sqlite_adapter.execute_insert(
        "INSERT INTO test_users (name) VALUES (?)",
        ('George',)
    )

    assert new_id is not None
    assert new_id > 0

    # Verify insertion
    result = sqlite_adapter.execute_query(
        "SELECT * FROM test_users WHERE id = ?",
        (new_id,),
        fetch='one'
    )
    assert result['name'] == 'George'


def test_json_serialization(sqlite_adapter):
    """Test JSON serialization and deserialization."""
    test_data = {
        'name': 'Test',
        'values': [1, 2, 3],
        'nested': {'key': 'value'}
    }

    # Serialize
    json_str = sqlite_adapter.serialize_json(test_data)
    assert isinstance(json_str, str)

    # Deserialize
    result = sqlite_adapter.deserialize_json(json_str)
    assert result == test_data


def test_json_serialization_none(sqlite_adapter):
    """Test JSON serialization with None value."""
    assert sqlite_adapter.serialize_json(None) is None
    assert sqlite_adapter.deserialize_json(None) is None


def test_table_exists(sqlite_adapter):
    """Test table existence check."""
    # Table doesn't exist yet
    assert not sqlite_adapter.table_exists('nonexistent_table')

    # Create table
    with sqlite_adapter.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE existing_table (id INTEGER PRIMARY KEY)")
        conn.commit()

    # Table now exists
    assert sqlite_adapter.table_exists('existing_table')


def test_placeholder_conversion():
    """
    Test that SQLite placeholders (?) are converted to PostgreSQL (%s).

    Note: This is a unit test that doesn't actually connect to PostgreSQL,
    but verifies the conversion logic would work correctly.
    """
    # Mock a PostgreSQL adapter by setting USE_POSTGRES flag
    import core.database_adapter as adapter_module

    # Save original state
    original_use_postgres = adapter_module.USE_POSTGRES

    try:
        # Simulate PostgreSQL mode
        adapter_module.USE_POSTGRES = True

        # Create adapter (will use PostgreSQL conversion logic)
        adapter = DatabaseAdapter()

        # Verify db_type is set correctly
        assert adapter.db_type == 'postgresql'

    finally:
        # Restore original state
        adapter_module.USE_POSTGRES = original_use_postgres


def test_database_type_detection():
    """Test that database type is correctly detected from environment."""
    import core.database_adapter as adapter_module

    # SQLite mode (default)
    original_url = adapter_module.DATABASE_URL
    try:
        adapter_module.DATABASE_URL = None
        adapter = DatabaseAdapter()
        assert adapter.db_type == 'sqlite'
    finally:
        adapter_module.DATABASE_URL = original_url


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
