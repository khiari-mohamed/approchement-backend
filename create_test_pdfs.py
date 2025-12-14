"""
Create small test PDFs for reconciliation testing
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os

def create_test_bank_pdf():
    """Create a small BIAT bank statement PDF with 20 transactions"""
    filename = "storage/uploads/TEST_BANK_20.pdf"
    os.makedirs("storage/uploads", exist_ok=True)
    
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 2*cm, "BIAT - Relevé Bancaire TEST")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 2.5*cm, "Période: 01/08/2025 au 31/08/2025")
    
    # Transactions (20 matching transactions)
    y = height - 4*cm
    c.setFont("Courier", 9)
    
    transactions = [
        "01 08 REGLEMENT CHEQUE 001234      01082025      1.500,000",
        "02 08 VIREMENT SALAIRE              02082025      3.200,000",
        "05 08 PRELEVEMENT LOYER             05082025      -800,000",
        "07 08 CARTE BANCAIRE CARREFOUR      07082025      -150,500",
        "08 08 VIREMENT CLIENT ABC           08082025      2.500,000",
        "10 08 CHEQUE 001235                 10082025      -450,000",
        "12 08 VIREMENT FOURNISSEUR          12082025      -1.200,000",
        "15 08 DEPOT ESPECES                 15082025      500,000",
        "18 08 CARTE BANCAIRE MONOPRIX       18082025      -75,250",
        "20 08 VIREMENT CLIENT XYZ           20082025      1.800,000",
        "22 08 PRELEVEMENT ELECTRICITE       22082025      -120,000",
        "23 08 CHEQUE 001236                 23082025      -300,000",
        "25 08 VIREMENT SALAIRE              25082025      3.200,000",
        "26 08 CARTE BANCAIRE GEANT          26082025      -200,000",
        "28 08 VIREMENT CLIENT DEF           28082025      950,000",
        "29 08 PRELEVEMENT TELEPHONE         29082025      -45,000",
        "30 08 CHEQUE 001237                 30082025      -600,000",
        "31 08 VIREMENT FOURNISSEUR          31082025      -850,000",
        "31 08 FRAIS BANCAIRES               31082025      -25,000",
        "31 08 COMMISSION TENUE COMPTE       31082025      -15,000",
    ]
    
    for tx in transactions:
        c.drawString(2*cm, y, tx)
        y -= 0.5*cm
    
    c.save()
    print(f"✅ Created test bank PDF: {filename} (20 transactions)")

def create_test_accounting_pdf():
    """Create a small Grand Livre PDF with 20 transactions"""
    filename = "storage/uploads/TEST_ACCOUNTING_20.pdf"
    os.makedirs("storage/uploads", exist_ok=True)
    
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 2*cm, "Grand Livre - Compte 512000 - TEST")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 2.5*cm, "Période: 01/08/2025 au 31/08/2025")
    
    # Transactions (20 matching transactions)
    y = height - 4*cm
    c.setFont("Courier", 8)
    
    transactions = [
        "010825 5607 1001 REGLEMENT CHEQUE 001234        1 500.000      1 500.000",
        "020825 5607 1002 VIREMENT SALAIRE               3 200.000      4 700.000",
        "050825 5607 1003 PRELEVEMENT LOYER              -800.000       3 900.000",
        "070825 5607 1004 CARTE BANCAIRE CARREFOUR       -150.500       3 749.500",
        "080825 5607 1005 VIREMENT CLIENT ABC            2 500.000      6 249.500",
        "100825 5607 1006 CHEQUE 001235                  -450.000       5 799.500",
        "120825 5607 1007 VIREMENT FOURNISSEUR           -1 200.000     4 599.500",
        "150825 5607 1008 DEPOT ESPECES                  500.000        5 099.500",
        "180825 5607 1009 CARTE BANCAIRE MONOPRIX        -75.250        5 024.250",
        "200825 5607 1010 VIREMENT CLIENT XYZ            1 800.000      6 824.250",
        "220825 5607 1011 PRELEVEMENT ELECTRICITE        -120.000       6 704.250",
        "230825 5607 1012 CHEQUE 001236                  -300.000       6 404.250",
        "250825 5607 1013 VIREMENT SALAIRE               3 200.000      9 604.250",
        "260825 5607 1014 CARTE BANCAIRE GEANT           -200.000       9 404.250",
        "280825 5607 1015 VIREMENT CLIENT DEF            950.000        10 354.250",
        "290825 5607 1016 PRELEVEMENT TELEPHONE          -45.000        10 309.250",
        "300825 5607 1017 CHEQUE 001237                  -600.000       9 709.250",
        "310825 5607 1018 VIREMENT FOURNISSEUR           -850.000       8 859.250",
        "310825 5607 1019 FRAIS BANCAIRES                -25.000        8 834.250",
        "310825 5607 1020 COMMISSION TENUE COMPTE        -15.000        8 819.250",
    ]
    
    for tx in transactions:
        c.drawString(1.5*cm, y, tx)
        y -= 0.5*cm
    
    c.save()
    print(f"✅ Created test accounting PDF: {filename} (20 transactions)")

if __name__ == "__main__":
    print("🔧 Creating test PDFs...")
    create_test_bank_pdf()
    create_test_accounting_pdf()
    print("\n✨ Test PDFs created successfully!")
    print("📁 Location: storage/uploads/")
    print("   - TEST_BANK_20.pdf (20 bank transactions)")
    print("   - TEST_ACCOUNTING_20.pdf (20 accounting transactions)")
    print("\n💡 These files have matching transactions for testing reconciliation.")
