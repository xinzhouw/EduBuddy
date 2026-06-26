"""
Migration: Add password reset fields to users table

Adds the following columns:
- password_reset_code: VARCHAR(6) NULL
- reset_code_expiry: DATETIME NULL
- reset_attempts: INTEGER DEFAULT 0
- reset_code_locked_until: DATETIME NULL

Run from the backend directory:
    python scripts/migrate_password_reset_fields.py
"""

import sqlite3
import sys
import os

# Resolve database path relative to backend dir
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BACKEND_DIR, "data", "edubuddy.db")


def get_existing_columns(cursor, table: str) -> set:
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    existing = get_existing_columns(cursor, "users")

    migrations = [
        ("password_reset_code", "ALTER TABLE users ADD COLUMN password_reset_code VARCHAR(6)"),
        ("reset_code_expiry",   "ALTER TABLE users ADD COLUMN reset_code_expiry DATETIME"),
        ("reset_attempts",      "ALTER TABLE users ADD COLUMN reset_attempts INTEGER DEFAULT 0"),
        ("reset_code_locked_until", "ALTER TABLE users ADD COLUMN reset_code_locked_until DATETIME"),
    ]

    applied = []
    skipped = []

    for col_name, sql in migrations:
        if col_name in existing:
            skipped.append(col_name)
        else:
            cursor.execute(sql)
            applied.append(col_name)

    conn.commit()
    conn.close()

    if applied:
        print(f"Applied: {applied}")
    if skipped:
        print(f"Already present (skipped): {skipped}")
    print("Migration complete.")


if __name__ == "__main__":
    run_migration()
