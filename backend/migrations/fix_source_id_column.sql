-- Migration: Fix source_id column type from VARCHAR(100) to VARCHAR(500)
-- This allows longer source IDs (like Outlook message IDs) to be stored
-- Outlook message IDs can be up to 172 characters, so VARCHAR(500) provides sufficient space

-- Check if column exists and alter its type
DO $$
BEGIN
    -- Check if the column is VARCHAR(100) and needs to be changed to VARCHAR(500)
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'resumes' 
        AND column_name = 'source_id'
        AND data_type = 'character varying'
        AND character_maximum_length = 100
    ) THEN
        ALTER TABLE resumes 
        ALTER COLUMN source_id TYPE VARCHAR(500);
        
        RAISE NOTICE 'Successfully changed source_id column from VARCHAR(100) to VARCHAR(500)';
    ELSE
        RAISE NOTICE 'Column source_id is already VARCHAR(500) or does not exist';
    END IF;
END $$;

