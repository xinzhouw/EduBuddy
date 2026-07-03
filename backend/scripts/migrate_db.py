#!/usr/bin/env python3
"""
Database Migration Script: Add missing columns to users table
Date: 2026-07-01

This script safely adds columns to the users table, gracefully handling cases where:
1. The column already exists (common on subsequent container restarts)
2. The database doesn't exist yet (will be created by SQLAlchemy init_db())
"""
import sqlite3
import sys
import os

DB_PATH = os.environ.get("DATABASE_URL", "sqlite:////app/data/edubuddy.db").replace("sqlite:///", "")

# Columns that should exist in users table
MIGRATIONS = [
    ("last_login", "ALTER TABLE users ADD COLUMN last_login DATETIME;"),
    ("login_count", "ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0;"),
    ("password_reset_code", "ALTER TABLE users ADD COLUMN password_reset_code VARCHAR(6);"),
    ("reset_code_expiry", "ALTER TABLE users ADD COLUMN reset_code_expiry DATETIME;"),
    ("reset_attempts", "ALTER TABLE users ADD COLUMN reset_attempts INTEGER DEFAULT 0;"),
    ("reset_code_locked_until", "ALTER TABLE users ADD COLUMN reset_code_locked_until DATETIME;"),
]

def column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table using PRAGMA table_info"""
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)

def migrate():
    """Run all pending migrations, skipping columns that already exist"""
    # If database doesn't exist, that's OK - init_db() will create it
    if not os.path.exists(DB_PATH):
        print(f"⊘ Database not found at {DB_PATH} (will be created by init_db())")
        return True

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("⊘ users table doesn't exist yet (will be created by init_db())")
            conn.close()
            return True

        print("🔍 Checking for missing columns in users table...")
        applied_count = 0

        for column_name, sql in MIGRATIONS:
            if column_exists(cursor, "users", column_name):
                print(f"⊘ Column '{column_name}' already exists (skipped)")
            else:
                try:
                    cursor.execute(sql)
                    applied_count += 1
                    print(f"✓ Added column '{column_name}'")
                except sqlite3.OperationalError as e:
                    print(f"✗ Migration failed for column '{column_name}': {e}")
                    conn.rollback()
                    return False

        conn.commit()
        if applied_count > 0:
            print(f"\n✓ {applied_count} migration(s) applied successfully!")
        else:
            print(f"\n⊘ No new migrations needed (schema is up-to-date)")
        return True
    except Exception as e:
        print(f"✗ Migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
