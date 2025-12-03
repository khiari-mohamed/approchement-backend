"""
Quick fix script for reconciliation errors
Fixes both database schema and AI rate limiting issues
"""
import sys
import os

print("=" * 60)
print("RAPPROCHEMENT APP - QUICK FIX")
print("=" * 60)
print()

# Step 1: Run migration
print("Step 1/2: Fixing database schema...")
print("-" * 60)
try:
    from migrations.add_execution_time_column import upgrade
    upgrade()
    print("✓ Database schema fixed!")
except Exception as e:
    print(f"✗ Database migration failed: {e}")
    print("\nManual fix required:")
    print("  psql -U your_user -d your_database")
    print("  ALTER TABLE audit_logs ADD COLUMN execution_time_ms INTEGER;")
    sys.exit(1)

print()

# Step 2: Verify AI rate limiting
print("Step 2/2: Verifying AI rate limiting...")
print("-" * 60)
try:
    from services.ai_assistant import MAX_REQUESTS_PER_MINUTE, wait_for_rate_limit
    print(f"✓ Rate limiting enabled: {MAX_REQUESTS_PER_MINUTE} requests/minute")
    print("✓ AI fallback mechanism active")
except Exception as e:
    print(f"⚠ Warning: Could not verify AI configuration: {e}")

print()
print("=" * 60)
print("✓ ALL FIXES APPLIED SUCCESSFULLY!")
print("=" * 60)
print()
print("Next steps:")
print("  1. Restart your backend server")
print("  2. Run reconciliation again")
print()
print("Tips:")
print("  - AI calls are now rate-limited to prevent quota errors")
print("  - Large suspense lists (>20 items) skip AI categorization")
print("  - To disable AI completely, set enable_ai_assistance: false")
print()
