"""
Test AI Parser with sample text
"""
import sys
sys.path.append('.')

from parsers.ai_parser import AIPDFParser

# Sample text from grand livre
sample_text = """
Date C.j. N° pièce Libellé Mouvement Solde
010825 5607 1000 MCC 3 462.900 -3 462.900
010825 5607 1001 MARE 9 791.105 -13 254.005
010825 5607 1002 MOUNIR CHAMMAM ATMC 17 325.000 -30 579.005
010825 5607 1003 OXFORD LANGUAGES CENTER 7 908.050 -38 487.055
290825 5607 1050 Autres frais et commissions 9.520 249 697.875
"""

print("=" * 80)
print("TEST AI PARSER")
print("=" * 80)

parser = AIPDFParser()

if not parser.client:
    print("⚠️ Claude API not configured. Set ANTHROPIC_API_KEY environment variable.")
    print("   Example: export ANTHROPIC_API_KEY=sk-ant-...")
else:
    print("✅ Claude API configured")
    print("\n📄 Testing with sample grand livre text...")
    
    result = parser.parse_with_ai(sample_text, 'accounting')
    
    if result is not None and not result.empty:
        print(f"\n✅ SUCCESS: Extracted {len(result)} transactions")
        print("\n📊 Sample data:")
        print(result[['date', 'description', 'amount']].head())
        
        if 'solde_progressif' in result.columns:
            print(f"\n💰 Final balance: {result['solde_progressif'].iloc[-1]}")
    else:
        print("\n❌ FAILED: No transactions extracted")

print("\n" + "=" * 80)
