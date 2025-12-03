#!/usr/bin/env python3
"""Add missing columns to reconciliations table"""

from database import engine
from sqlalchemy import text

sql_commands = [
    "ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS explained_gap FLOAT DEFAULT 0.0",
    "ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS bank_suspense_total FLOAT DEFAULT 0.0",
    "ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS accounting_suspense_total FLOAT DEFAULT 0.0",
    "ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS coverage_percentage FLOAT DEFAULT 0.0",
    "ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS processing_time FLOAT",
    "ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS manual_interventions INTEGER DEFAULT 0",
    "ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS match_accuracy FLOAT DEFAULT 0.0",
    "ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS duplicate_count INTEGER DEFAULT 0",
    "ALTER TABLE reconciliations ADD COLUMN IF NOT EXISTS validation_errors JSON"
]

print("🔧 Adding missing columns to reconciliations table...")

with engine.connect() as conn:
    for sql in sql_commands:
        try:
            conn.execute(text(sql))
            conn.commit()
            col_name = sql.split('ADD COLUMN IF NOT EXISTS')[1].split()[0]
            print(f"✅ {col_name}")
        except Exception as e:
            print(f"⚠️  {e}")

print("✅ Database fixed!")
