import sys
sys.path.append('.')
import pandas as pd
from services.database_service import DatabaseService
from database import SessionLocal

db = SessionLocal()
db_service = DatabaseService(db)

# Get latest reconciliation
recons = db_service.list_reconciliations(limit=1)
if not recons:
    print("No reconciliations found")
    sys.exit(1)

latest_recon = recons[0]
print(f"=== VÉRIFICATION DES DONNÉES ===")
print(f"Reconciliation ID: {latest_recon.id}")

# Get files
bank_file = db_service.get_uploaded_file(str(latest_recon.bank_file_id))
acc_file = db_service.get_uploaded_file(str(latest_recon.accounting_file_id))

if bank_file and acc_file:
    bank_df = pd.read_csv(bank_file.file_path)
    acc_df = pd.read_csv(acc_file.file_path)
    
    print(f"\nBANQUE: {len(bank_df)} transactions")
    print("10 premières transactions:")
    print(bank_df[['date', 'description', 'amount']].head(10))
    
    print(f"\nMontants bancaires - Statistiques:")
    print(bank_df['amount'].describe())
    
    print(f"\nCOMPTABILITÉ: {len(acc_df)} transactions")
    print("10 premières transactions:")
    print(acc_df[['date', 'description', 'amount']].head(10))
    
    print(f"\nMontants comptables - Statistiques:")
    print(acc_df['amount'].describe())
else:
    print("Files not found")

db.close()
