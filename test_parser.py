"""
Test script for BIAT PDF parser
Run this to verify the parser extracts transactions correctly
"""
import sys
import os
sys.path.append('.')

from parsers.biat_parser import BIATPDFParser

def test_parser():
    print("=" * 80)
    print("BIAT PDF PARSER TEST")
    print("=" * 80)
    
    # Test bank statement
    bank_file = "BIAT 08-2025.pdf"
    if os.path.exists(bank_file):
        print(f"\n📄 Testing Bank Statement: {bank_file}")
        try:
            with open(bank_file, 'rb') as f:
                bank_content = f.read()
            
            bank_df = BIATPDFParser.parse_bank_statement(bank_content)
            print(f"✅ Transactions bancaires extraites: {len(bank_df)}")
            
            if len(bank_df) > 0:
                print("\n📊 5 premières transactions:")
                print(bank_df[['date', 'description', 'amount']].head())
                
                # Check for balance
                balance_rows = bank_df[bank_df['description'].str.contains('SOLDE', case=False, na=False)]
                if len(balance_rows) > 0:
                    bank_balance = balance_rows['amount'].iloc[-1]
                    print(f"\n💰 Solde bancaire trouvé: {bank_balance:,.3f} TND")
                
                print(f"\n📈 Total des transactions: {bank_df['amount'].sum():,.3f} TND")
            else:
                print("⚠️ AUCUNE transaction extraite!")
                
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️ Fichier non trouvé: {bank_file}")
    
    # Test grand livre
    gl_file = "Grand-livre_BIAT.pdf"
    if os.path.exists(gl_file):
        print(f"\n📄 Testing Grand Livre: {gl_file}")
        try:
            with open(gl_file, 'rb') as f:
                gl_content = f.read()
            
            gl_df = BIATPDFParser.parse_grand_livre(gl_content)
            print(f"✅ Transactions comptables extraites: {len(gl_df)}")
            
            if len(gl_df) > 0:
                print("\n📊 5 premières transactions:")
                print(gl_df[['date', 'description', 'amount']].head())
                
                # Check for balance
                if 'solde_progressif' in gl_df.columns:
                    gl_balance = gl_df['solde_progressif'].iloc[-1]
                    print(f"\n💰 Solde comptable trouvé: {gl_balance:,.3f} TND")
                
                print(f"\n📈 Total des transactions: {gl_df['amount'].sum():,.3f} TND")
            else:
                print("⚠️ AUCUNE transaction extraite!")
                
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️ Fichier non trouvé: {gl_file}")
    
    print("\n" + "=" * 80)
    print("TEST TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    test_parser()
