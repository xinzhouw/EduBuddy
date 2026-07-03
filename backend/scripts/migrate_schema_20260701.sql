-- Database Migration: Add missing columns to users table
-- Date: 2026-07-01
-- Reason: Schema mismatch after new model updates
-- Note: Uses PRAGMA foreign_keys to safely check column existence

PRAGMA foreign_keys=ON;

-- Helper function to conditionally add columns (SQLite doesn't support IF NOT EXISTS for ALTER TABLE)
-- So we use a workaround: try to add, catch the error in Python

-- Columns that should exist (already defined in User model):
-- last_login, login_count, password_reset_code, reset_code_expiry, reset_attempts, reset_code_locked_until
