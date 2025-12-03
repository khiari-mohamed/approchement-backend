-- Add missing columns to reconciliations table
ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS explained_gap FLOAT DEFAULT 0.0;
ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS bank_suspense_total FLOAT DEFAULT 0.0;
ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS accounting_suspense_total FLOAT DEFAULT 0.0;
ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS coverage_percentage FLOAT DEFAULT 0.0;
ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS processing_time FLOAT;
ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS manual_interventions INTEGER DEFAULT 0;
ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS match_accuracy FLOAT DEFAULT 0.0;
ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS duplicate_count INTEGER DEFAULT 0;
ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS validation_errors JSON;
