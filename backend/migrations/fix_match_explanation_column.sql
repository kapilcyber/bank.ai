-- Migration: Fix match_explanation column type from VARCHAR(100) to TEXT
-- This allows longer match explanations to be stored

-- Check if column exists and alter its type
DO $$
BEGIN
    -- Check if the column is VARCHAR(100) and needs to be changed to TEXT
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'match_results' 
        AND column_name = 'match_explanation'
        AND data_type = 'character varying'
        AND character_maximum_length = 100
    ) THEN
        ALTER TABLE match_results 
        ALTER COLUMN match_explanation TYPE TEXT;
        
        RAISE NOTICE 'Successfully changed match_explanation column from VARCHAR(100) to TEXT';
    ELSE
        RAISE NOTICE 'Column match_explanation is already TEXT or does not exist';
    END IF;
END $$;
