import sys
sys.path.append('.')
from services.file_processor import FileProcessor

processor = FileProcessor()

# Lire vos fichiers
with open('BIAT 08-2025.pdf', 'rb') as f:
    bank_content = f.read()

with open('Grand-livre_BIAT.pdf', 'rb') as f:
    acc_content = f.read()

print("=== TEST DU PARSER SANS FIX ===")
# Appeler directement le parser IA
from parsers.intelligent_parser import IntelligentPDFParser
parser = IntelligentPDFParser()

bank_df = parser.parse_with_fallback(bank_content, 'bank')
print(f"Bank parsed: {len(bank_df)} rows")
print(f"Bank total: {bank_df['amount'].sum():,.2f}")
print("\nFirst 5 transactions:")
print(bank_df[['date', 'description', 'amount']].head())

print("\n=== APRÈS FIX ===")
from services.data_fixer import UltimateDataFixer
fixer = UltimateDataFixer()
bank_fixed = fixer.fix_bank_data(bank_df)
print(f"Bank fixed total: {bank_fixed['amount'].sum():,.2f}")
print("\nFirst 5 after fix:")
print(bank_fixed[['date', 'description', 'amount']].head())
