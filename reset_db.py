"""
Reset database - Delete all data but keep tables
"""
import sys
sys.path.append('.')

from database import SessionLocal, engine
from db_models.transactions import BankTransaction, AccountingTransaction
from db_models.reconciliation import Reconciliation, Match, SuspenseItem
from db_models.files import UploadedFile
from db_models.audit import AuditLog
from db_models.performance import PerformanceMetrics
from sqlalchemy import text

db = SessionLocal()

try:
    print("🗑️  Deleting all data...")
    
    # Delete in correct order (respecting foreign keys)
    db.query(PerformanceMetrics).delete()
    db.query(AuditLog).delete()
    
    # Delete regularization entries first
    db.execute(text("DELETE FROM regularization_entries"))
    
    db.query(SuspenseItem).delete()
    db.query(Match).delete()
    db.query(BankTransaction).delete()
    db.query(AccountingTransaction).delete()
    db.query(Reconciliation).delete()
    db.query(UploadedFile).delete()
    
    db.commit()
    print("✅ All data deleted successfully!")
    print("📊 Tables kept intact")
    
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()
