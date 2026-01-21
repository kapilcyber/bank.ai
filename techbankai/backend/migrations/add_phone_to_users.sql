-- Migration: Add phone column to users table
-- Date: 2024-12-26
-- Description: Adds phone number field to users table for storing user phone numbers

-- Add phone column to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS phone VARCHAR(20);

-- Add comment to the column
COMMENT ON COLUMN users.phone IS 'User phone number (10-20 characters)';

-- Note: This migration is safe to run multiple times (uses IF NOT EXISTS)
-- Existing users will have NULL phone values until they update their profile
