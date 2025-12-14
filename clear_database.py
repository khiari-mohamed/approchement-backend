"""
Clear all data from the database
"""
from database import SessionLocal, engine
from db_models.all_models import *
from sqlalchemy import text

def clear_all_data():
    db = SessionLocal()
    try:
        print("🗑️  Clearing all data from database...")
        
        # Delete in correct order (respecting foreign keys)
        tables_to_clear = [
            'suspense_items',
            'matches',
            'regularization_entries',
            'performance_metrics',
            'ai_call_logs',
            'audit_logs',
            'bank_transactions',
            'accounting_transactions',
            'reconciliations',
            'uploaded_files',
        ]
        
        for table in tables_to_clear:
            try:
                result = db.execute(text(f"DELETE FROM {table}"))
                db.commit()
                print(f"✅ Cleared {table}: {result.rowcount} rows deleted")
            except Exception as e:
                print(f"⚠️  {table}: {e}")
                db.rollback()
        
        print("\n✨ Database cleared successfully!")
        print("You can now upload fresh files for reconciliation.")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_data()
