"""
Run database migrations
"""
import sys
from migrations.add_execution_time_column import upgrade

if __name__ == "__main__":
    print("=" * 50)
    print("Running Database Migrations")
    print("=" * 50)
    
    try:
        upgrade()
        print("\n✓ All migrations completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
