-- Database Migration: Add missing columns to users table
-- Date: 2026-07-01
-- Reason: Schema mismatch after new model updates

-- Add missing columns for login tracking and password reset
ALTER TABLE users ADD COLUMN last_login DATETIME;
ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN password_reset_code VARCHAR(6);
ALTER TABLE users ADD COLUMN reset_code_expiry DATETIME;
ALTER TABLE users ADD COLUMN reset_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN reset_code_locked_until DATETIME;
