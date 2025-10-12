"""
Initialize convention data in database from ConventionRegistry.

This script:
1. Creates convention tables if they don't exist
2. Populates conventions table with metadata
3. Populates convention_prerequisites table
4. Creates initial user progress records (optional)
"""

import sqlite3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ai.conventions.convention_registry import get_convention_registry


def init_convention_tables(db_path='bridge.db'):
    """Initialize convention tables and data"""

    # Read schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema_convention_levels.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Execute schema
        print("Creating convention tables...")
        cursor.executescript(schema_sql)
        conn.commit()
        print("✓ Tables created successfully")

        # Get convention data from registry
        print("\nPopulating convention data...")
        registry = get_convention_registry()

        # Clear existing data
        cursor.execute("DELETE FROM convention_prerequisites")
        cursor.execute("DELETE FROM conventions")
        conn.commit()

        # Insert conventions
        conventions_inserted = 0
        prerequisites_inserted = 0

        for convention in registry.get_all_conventions():
            # Insert convention
            cursor.execute("""
                INSERT INTO conventions (
                    convention_id, name, level, category, frequency, complexity,
                    description, short_description, learning_time_minutes,
                    practice_hands_required, passing_accuracy
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                # Determine if prerequisite is a skill or convention
                prereq_type = 'convention' if prereq in registry.conventions else 'skill'

                cursor.execute("""
                    INSERT INTO convention_prerequisites (
                        convention_id, prerequisite_id, prerequisite_type
                    ) VALUES (?, ?, ?)
                """, (convention.id, prereq, prereq_type))
                prerequisites_inserted += 1

        conn.commit()

        print(f"✓ Inserted {conventions_inserted} conventions")
        print(f"✓ Inserted {prerequisites_inserted} prerequisites")

        # Display summary
        print("\n" + "="*60)
        print("CONVENTION SUMMARY")
        print("="*60)

        for level_name in ['essential', 'intermediate', 'advanced']:
            cursor.execute("""
                SELECT COUNT(*), GROUP_CONCAT(name, ', ')
                FROM conventions
                WHERE level = ?
            """, (level_name,))
            count, names = cursor.fetchone()
            print(f"\n{level_name.upper()} ({count}):")
            print(f"  {names}")

        print("\n" + "="*60)
        print("✓ Convention data initialization complete!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Error initializing convention data: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


def init_user_convention_progress(user_id, db_path='bridge.db'):
    """
    Initialize convention progress for a specific user.
    Creates 'locked' status for all conventions initially.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print(f"\nInitializing convention progress for user {user_id}...")

        # Get all conventions
        cursor.execute("SELECT convention_id FROM conventions")
        conventions = cursor.fetchall()

        # Insert initial progress records
        for (convention_id,) in conventions:
            cursor.execute("""
                INSERT OR IGNORE INTO user_convention_progress (
                    user_id, convention_id, status, attempts, correct, accuracy
                ) VALUES (?, ?, 'locked', 0, 0, 0.0)
            """, (user_id, convention_id))

        conn.commit()
        print(f"✓ Initialized progress for {len(conventions)} conventions")

    except Exception as e:
        print(f"✗ Error initializing user progress: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


def verify_convention_data(db_path='bridge.db'):
    """Verify convention data was populated correctly"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    # Check conventions
    cursor.execute("SELECT COUNT(*) FROM conventions")
    conv_count = cursor.fetchone()[0]
    print(f"Total conventions: {conv_count}")

    # Check prerequisites
    cursor.execute("SELECT COUNT(*) FROM convention_prerequisites")
    prereq_count = cursor.fetchone()[0]
    print(f"Total prerequisites: {prereq_count}")

    # Check each level
    for level in ['essential', 'intermediate', 'advanced']:
        cursor.execute("""
            SELECT COUNT(*)
            FROM conventions
            WHERE level = ?
        """, (level,))
        count = cursor.fetchone()[0]
        print(f"{level.capitalize()} conventions: {count}")

    # Check prerequisite breakdown
    cursor.execute("""
        SELECT prerequisite_type, COUNT(*)
        FROM convention_prerequisites
        GROUP BY prerequisite_type
    """)
    print("\nPrerequisite types:")
    for prereq_type, count in cursor.fetchall():
        print(f"  {prereq_type}: {count}")

    conn.close()
    print("="*60)


if __name__ == '__main__':
    print("="*60)
    print("CONVENTION DATA INITIALIZATION")
    print("="*60)

    # Default database path
    db_path = 'bridge.db'

    # Check if database path provided
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    print(f"\nDatabase: {db_path}")

    # Initialize tables and data
    init_convention_tables(db_path)

    # Verify
    verify_convention_data(db_path)

    # Optionally initialize a test user
    if '--init-test-user' in sys.argv:
        init_user_convention_progress(user_id=1, db_path=db_path)

    print("\n✓ All done!")
