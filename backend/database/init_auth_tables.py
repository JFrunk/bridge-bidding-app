#!/usr/bin/env python3
"""
Initialize authentication tables for the Auth V2 system.

Applies the auth migration (backend/migrations/20260319_auth_v2.sql) and
verifies all auth-related tables and columns are present.

Safe to run multiple times — all operations are idempotent.
"""

import re
import sys
from pathlib import Path

# Add backend dir to path so we can import db module
script_dir = Path(__file__).parent.resolve()
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from db import get_connection
from utils.error_logger import log_error

# Tables created by the auth v2 migration
AUTH_TABLES = ['auth_providers', 'auth_tokens', 'refresh_tokens']

# Columns added to the users table by the auth v2 migration
AUTH_USER_COLUMNS = [
    'password_hash', 'email_verified', 'profile_picture_url',
    'failed_login_attempts', 'locked_until'
]


def init_auth_tables():
    """Apply auth v2 migration and verify all auth tables and columns."""

    print("Initializing Auth V2 tables (PostgreSQL)")

    with get_connection() as conn:
        cursor = conn.cursor()

        try:
            # Verify users table exists (prerequisite)
            cursor.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename = 'users'
            """)
            if not cursor.fetchone():
                print("Users table doesn't exist. Run init_all_tables.py first.")
                return False

            # Apply the migration SQL
            migration_path = backend_dir / 'migrations' / '20260319_auth_v2.sql'
            if migration_path.exists():
                print(f"Applying migration: {migration_path.name}")
                with open(migration_path, 'r') as f:
                    sql = f.read()

                # Strip line comments before splitting to avoid losing
                # statements that share a chunk with preceding comments
                clean_sql = re.sub(r'--[^\n]*\n', '\n', sql)
                statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
                for stmt in statements:
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        # Skip "already exists" errors for idempotency
                        err_msg = str(e).lower()
                        if 'already exists' in err_msg or 'duplicate' in err_msg:
                            pass
                        else:
                            raise
            else:
                print(f"WARNING: Migration file not found at {migration_path}")
                return False

            # Verify auth tables exist
            print("\nVerifying auth tables...")
            all_good = True
            for table in AUTH_TABLES:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = %s
                    )
                """, (table,))
                result = cursor.fetchone()
                exists = result['exists'] if isinstance(result, dict) else result[0]
                status = "OK" if exists else "MISSING"
                print(f"  {table}: {status}")
                if not exists:
                    all_good = False

            # Verify users table columns
            print("\nVerifying users table auth columns...")
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'users'
            """)
            existing_columns = {row['column_name'] for row in cursor.fetchall()}

            for col in AUTH_USER_COLUMNS:
                status = "OK" if col in existing_columns else "MISSING"
                print(f"  users.{col}: {status}")
                if col not in existing_columns:
                    all_good = False

            # Verify indexes
            print("\nVerifying indexes...")
            cursor.execute("""
                SELECT indexname FROM pg_indexes
                WHERE schemaname = 'public'
                AND (indexname LIKE 'idx_auth%' OR indexname LIKE 'idx_refresh%')
            """)
            indexes = {row['indexname'] for row in cursor.fetchall()}
            expected_indexes = [
                'idx_auth_providers_user',
                'idx_auth_tokens_user_type',
                'idx_refresh_tokens_user',
            ]
            for idx in expected_indexes:
                status = "OK" if idx in indexes else "MISSING"
                print(f"  {idx}: {status}")
                if idx not in indexes:
                    all_good = False

            if all_good:
                print("\nAuth V2 database infrastructure ready!")
            else:
                print("\nWARNING: Some auth components are missing.")

            return all_good

        except Exception as e:
            print(f"Error: {e}")
            log_error(e)
            return False


if __name__ == '__main__':
    success = init_auth_tables()
    sys.exit(0 if success else 1)
