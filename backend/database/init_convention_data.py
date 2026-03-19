"""
Initialize convention data in database from ConventionRegistry.

This script:
1. Creates convention tables if they don't exist
2. Populates conventions table with metadata
3. Populates convention_prerequisites table
4. Creates initial user progress records (optional)
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_connection, _execute_script
from engine.ai.conventions.convention_registry import get_convention_registry


def init_convention_tables():
    """Initialize convention tables and data"""

    # Read schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema_convention_levels.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    # Execute schema
    print("Creating convention tables...")
    with get_connection() as conn:
        cursor = conn.cursor()
        _execute_script(cursor, schema_sql)
    print("Tables created successfully")

    # Populate convention data
    print("\nPopulating convention data...")
    registry = get_convention_registry()

    with get_connection() as conn:
        cursor = conn.cursor()

        # Clear existing data
        cursor.execute("DELETE FROM convention_prerequisites")
        cursor.execute("DELETE FROM conventions")

        # Insert conventions
        conventions_inserted = 0
        prerequisites_inserted = 0

        for convention in registry.get_all_conventions():
            cursor.execute("""
                INSERT INTO conventions (
                    convention_id, name, level, category, frequency, complexity,
                    description, short_description, learning_time_minutes,
                    practice_hands_required, passing_accuracy
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                convention.id,
                convention.name,
                convention.level.name.lower(),
                convention.category.value,
                convention.frequency,
                convention.complexity,
                convention.description,
                convention.short_description,
                convention.learning_time_minutes,
                convention.practice_hands_required,
                convention.passing_accuracy
            ))
            conventions_inserted += 1

            # Insert prerequisites
            for prereq in convention.prerequisites:
                prereq_type = 'convention' if prereq in registry.conventions else 'skill'

                cursor.execute("""
                    INSERT INTO convention_prerequisites (
                        convention_id, prerequisite_id, prerequisite_type
                    ) VALUES (%s, %s, %s)
                """, (convention.id, prereq, prereq_type))
                prerequisites_inserted += 1

    print(f"Inserted {conventions_inserted} conventions")
    print(f"Inserted {prerequisites_inserted} prerequisites")

    # Display summary
    print("\n" + "=" * 60)
    print("CONVENTION SUMMARY")
    print("=" * 60)

    with get_connection() as conn:
        cursor = conn.cursor()
        for level_name in ['essential', 'intermediate', 'advanced']:
            cursor.execute("""
                SELECT COUNT(*), string_agg(name, ', ')
                FROM conventions
                WHERE level = %s
            """, (level_name,))
            row = cursor.fetchone()
            count = row['count']
            names = row['string_agg']
            print(f"\n{level_name.upper()} ({count}):")
            print(f"  {names}")

    print("\n" + "=" * 60)
    print("Convention data initialization complete!")
    print("=" * 60)


def init_user_convention_progress(user_id):
    """
    Initialize convention progress for a specific user.
    Creates 'locked' status for all conventions initially.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        print(f"\nInitializing convention progress for user {user_id}...")

        # Get all conventions
        cursor.execute("SELECT convention_id FROM conventions")
        conventions = cursor.fetchall()

        # Insert initial progress records
        for row in conventions:
            cursor.execute("""
                INSERT INTO user_convention_progress (
                    user_id, convention_id, status, attempts, correct, accuracy
                ) VALUES (%s, %s, 'locked', 0, 0, 0.0)
                ON CONFLICT DO NOTHING
            """, (user_id, row['convention_id']))

        print(f"Initialized progress for {len(conventions)} conventions")


def verify_convention_data():
    """Verify convention data was populated correctly"""

    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check conventions
        cursor.execute("SELECT COUNT(*) FROM conventions")
        conv_count = cursor.fetchone()['count']
        print(f"Total conventions: {conv_count}")

        # Check prerequisites
        cursor.execute("SELECT COUNT(*) FROM convention_prerequisites")
        prereq_count = cursor.fetchone()['count']
        print(f"Total prerequisites: {prereq_count}")

        # Check each level
        for level in ['essential', 'intermediate', 'advanced']:
            cursor.execute("""
                SELECT COUNT(*)
                FROM conventions
                WHERE level = %s
            """, (level,))
            count = cursor.fetchone()['count']
            print(f"{level.capitalize()} conventions: {count}")

        # Check prerequisite breakdown
        cursor.execute("""
            SELECT prerequisite_type, COUNT(*)
            FROM convention_prerequisites
            GROUP BY prerequisite_type
        """)
        print("\nPrerequisite types:")
        for row in cursor.fetchall():
            print(f"  {row['prerequisite_type']}: {row['count']}")

    print("=" * 60)


if __name__ == '__main__':
    print("=" * 60)
    print("CONVENTION DATA INITIALIZATION")
    print("=" * 60)

    print("\nDatabase: PostgreSQL")

    # Initialize tables and data
    init_convention_tables()

    # Verify
    verify_convention_data()

    # Optionally initialize a test user
    if '--init-test-user' in sys.argv:
        init_user_convention_progress(user_id=1)

    print("\nAll done!")
