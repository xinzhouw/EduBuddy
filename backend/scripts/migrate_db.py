#!/usr/bin/env python3
"""
Database Migration Script: Add missing columns to users table
Date: 2026-07-01
"""
import sqlite3
import sys

DB_PATH = "/app/data/edubuddy.db"

MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN last_login DATETIME;",
    "ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0;",
    "ALTER TABLE users ADD COLUMN password_reset_code VARCHAR(6);",
    "ALTER TABLE users ADD COLUMN reset_code_expiry DATETIME;",
    "ALTER TABLE users ADD COLUMN reset_attempts INTEGER DEFAULT 0;",
    "ALTER TABLE users ADD COLUMN reset_code_locked_until DATETIME;",
]

def migrate():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for i, sql in enumerate(MIGRATIONS, 1):
            try:
                cursor.execute(sql)
                print(f"✓ Migration {i}: {sql[:50]}...")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    print(f"⊘ Migration {i}: Column already exists (skipped)")
                else:
                    print(f"✗ Migration {i} FAILED: {e}")
                    conn.rollback()
                    return False

        conn.commit()
        print("\n✓ All migrations completed successfully!")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
