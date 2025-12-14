import re
import pdfplumber
import pandas as pd
from typing import List, Dict
import uuid
import io
from parsers.ai_parser import AIPDFParser
from services.tunisian_config import TunisianBankConfig

class BIATPDFParser:
    """Parser spécifique pour les relevés BIAT Tunisie"""
    
    @staticmethod
    def parse_bank_statement(pdf_content: bytes) -> pd.DataFrame:
        """
        Parse le relevé bancaire BIAT avec le format exact
        Format attendu : 
        01 08 REGLEMENT CHEQUE 0001294 31072025 7.908,050
        """
        print(f"DEBUG: Starting BIAT bank statement parsing, content size: {len(pdf_content)} bytes")
        transactions = []
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                print(f"DEBUG: PDF opened successfully, {len(pdf.pages)} pages found")
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                # Séparer par lignes
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 1. EXTRAIRE LE SOLDE (format: "SOLDE AU 31 07 2025 1.177.437,649")
                    solde_match = re.search(
                        r'SOLDE\s+AU\s+(\d{2})\s+(\d{2})\s+(\d{4})\s+([\d\.,]+)',
                        line, 
                        re.IGNORECASE
                    )
                    if solde_match:
                        day, month, year, amount_str = solde_match.groups()
                        amount = TunisianBankConfig.normalize_tunisian_amount(amount_str)
                        transactions.append({
                            'id': str(uuid.uuid4()),
                            'date': f"{year}-{month}-{day}",
                            'description': f"SOLDE AU {day}/{month}/{year}",
                            'amount': amount,
                            'page': page_num + 1,
                            'type': 'balance'
                        })
                        continue
                    
                    # 2. EXTRAIRE LES TRANSACTIONS RÉGULIÈRES
                    # Format: "01 08 REGLEMENT CHEQUE 0001294 31072025 7.908,050"
                    # Structure: jour mois description date_comptable montant
                    tx_pattern = r'^(\d{2})\s+(\d{2})\s+(.+?)\s+(\d{8})\s+([\d\.,]+)$'
                    tx_match = re.match(tx_pattern, line)
                    
                    if tx_match:
                        day, month, desc, tx_date, amount_str = tx_match.groups()
                        amount = TunisianBankConfig.normalize_tunisian_amount(amount_str)
                        
                        # Convertir la date comptable (DDMMYYYY) en format ISO
                        if len(tx_date) == 8:
                            d_day = tx_date[:2]
                            d_month = tx_date[2:4]
                            d_year = tx_date[4:]
                            iso_date = f"{d_year}-{d_month}-{d_day}"
                        else:
                            iso_date = f"2025-{month}-{day}"
                        
                        transactions.append({
                            'id': str(uuid.uuid4()),
                            'date': iso_date,
                            'description': desc.strip(),
                            'amount': amount,
                            'page': page_num + 1,
                            'type': 'transaction'
                        })
                        continue
                    
                    # 3. EXTRAIRE LES COMMISSIONS (ENG/SIGNATURE)
                    # Format: "01 08 ENG/SIGNATURE R0010350 01082025 3,800"
                    eng_pattern = r'^(\d{2})\s+(\d{2})\s+(ENG/SIGNATURE\s+\w+)\s+(\d{8})\s+([\d\.,]+)$'
                    eng_match = re.match(eng_pattern, line)
                    
                    if eng_match:
                        day, month, desc, tx_date, amount_str = eng_match.groups()
                        amount = TunisianBankConfig.normalize_tunisian_amount(amount_str)
                        
                        # Convertir la date
                        if len(tx_date) == 8:
                            d_day = tx_date[:2]
                            d_month = tx_date[2:4]
                            d_year = tx_date[4:]
                            iso_date = f"{d_year}-{d_month}-{d_day}"
                        else:
                            iso_date = f"2025-{month}-{day}"
                        
                        transactions.append({
                            'id': str(uuid.uuid4()),
                            'date': iso_date,
                            'description': desc.strip(),
                            'amount': amount,
                            'page': page_num + 1,
                            'type': 'commission'
                        })
            
            print(f"DEBUG: Extracted {len(transactions)} transactions from bank statement")
            
            if not transactions:
                print("DEBUG: No transactions found with regex patterns, trying AI parsing")
                # Try AI parsing as fallback
                ai_parser = AIPDFParser()
                with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                    full_text = "\n".join([page.extract_text() or "" for page in pdf.pages[:5]])
                    ai_result = ai_parser.parse_with_ai(full_text, 'bank')
                    if ai_result is not None and not ai_result.empty:
                        print(f"DEBUG: AI parsing successful: {len(ai_result)} transactions")
                        return ai_result
                
                print("DEBUG: AI parsing failed, trying simple extraction")
                # Fallback: extract any line with amounts
                with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text:
                            lines = text.split('\n')
                            for line in lines:
                                # Look for any line with a Tunisian amount pattern
                                amount_matches = re.findall(r'([\d\.]+,[\d]+)', line)
                                if amount_matches:
                                    amount_str = amount_matches[-1]  # Take last amount on line
                                    try:
                                        amount = TunisianBankConfig.normalize_tunisian_amount(amount_str)
                                        if amount > 0:
                                            transactions.append({
                                                'id': str(uuid.uuid4()),
                                                'date': '2025-08-01',  # Default date
                                                'description': line.strip()[:100],
                                                'amount': amount,
                                                'page': page_num + 1,
                                                'type': 'transaction'
                                            })
                                    except:
                                        continue
                print(f"DEBUG: Fallback extraction found {len(transactions)} transactions")
            
            if not transactions:
                raise ValueError("Aucune transaction extraite du PDF BIAT - le format ne correspond pas")
            
            return pd.DataFrame(transactions)
        except Exception as e:
            print(f"DEBUG: Error parsing bank statement: {str(e)}")
            raise
    
    @staticmethod
    def parse_grand_livre(pdf_content: bytes) -> pd.DataFrame:
        """
        Parse le grand livre PDF spécifique
        Format: Tableau avec colonnes Date, Description, Débit, Crédit, Solde
        """
        print(f"DEBUG: Starting Grand Livre parsing, content size: {len(pdf_content)} bytes")
        transactions = []
        
        # Header keywords to skip
        header_keywords = ['date', 'libellé', 'libelle', 'débit', 'debit', 'crédit', 'credit', 
                          'solde', 'n°pièce', 'n°piece', 'piece', 'compte', 'total']
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            print(f"DEBUG: Grand Livre PDF opened, {len(pdf.pages)} pages found")
            for page_num, page in enumerate(pdf.pages):
                # Essayer d'extraire les tables
                tables = page.extract_tables()
                
                for table in tables:
                    for row_idx, row in enumerate(table):
                        if len(row) >= 5:  # Au moins Date, Description, Débit, Crédit, Solde
                            date, description, debit, credit, solde = row[:5]
                            
                            # Skip header rows
                            if date and any(keyword in str(date).lower() for keyword in header_keywords):
                                continue
                            if description and any(keyword in str(description).lower() for keyword in header_keywords):
                                continue
                            
                            # Skip rows without valid data
                            if not date or (not debit and not credit and not solde):
                                continue
                            
                            try:
                                # Nettoyer les valeurs
                                date = str(date).strip() if date else ""
                                description = str(description).strip() if description else ""
                                
                                # Parse amounts safely
                                debit = TunisianBankConfig.normalize_tunisian_amount(str(debit)) if debit and str(debit).strip() else 0
                                credit = TunisianBankConfig.normalize_tunisian_amount(str(credit)) if credit and str(credit).strip() else 0
                                solde_val = TunisianBankConfig.normalize_tunisian_amount(str(solde)) if solde and str(solde).strip() else 0
                                
                                # Déterminer le montant (débit positif, crédit négatif)
                                amount = debit if debit > 0 else -credit if credit > 0 else solde_val
                                
                                transactions.append({
                                    'id': str(uuid.uuid4()),
                                    'date': date,
                                    'description': description,
                                    'debit': debit,
                                    'credit': credit,
                                    'amount': amount,
                                    'solde_progressif': solde_val,
                                    'page': page_num + 1
                                })
                            except ValueError as e:
                                # Skip rows that can't be parsed
                                print(f"DEBUG: Skipping row {row_idx} on page {page_num + 1}: {str(e)}")
                                continue
                
                # Fallback 1: extraction par texte si pas de tables
                if not transactions:
                    text = page.extract_text()
                    if text:
                        # Chercher les lignes de transaction
                        lines = text.split('\n')
                        for line in lines:
                            # Chercher des montants dans la ligne
                            amounts = re.findall(r'[\d\.,]+', line)
                            if len(amounts) >= 3:
                                solde_val = BIATPDFParser._parse_tunisian_amount(amounts[-1])
                                
                                # Chercher une date
                                date_match = re.search(r'\d{2}/\d{2}/\d{4}', line)
                                date = date_match.group(0) if date_match else ""
                                
                                # Extraire la description
                                desc_start = line.find(date) + len(date) if date else 0
                                desc_end = line.find(amounts[0]) if amounts else len(line)
                                description = line[desc_start:desc_end].strip()
                                
                                transactions.append({
                                    'id': str(uuid.uuid4()),
                                    'date': date,
                                    'description': description,
                                    'amount': solde_val,
                                    'solde_progressif': solde_val,
                                    'page': page_num + 1
                                })
        
        print(f"DEBUG: Extracted {len(transactions)} transactions from grand livre")
        
        if not transactions or len(transactions) < 10:
            print("DEBUG: Too few transactions, trying AI parsing")
            # Try AI parsing as fallback
            ai_parser = AIPDFParser()
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                ai_result = ai_parser.parse_with_ai(full_text, 'accounting')
                if ai_result is not None and len(ai_result) > len(transactions):
                    print(f"DEBUG: AI parsing better: {len(ai_result)} vs {len(transactions)} transactions")
                    return ai_result
        
        if not transactions:
            raise ValueError("Aucune transaction extraite du grand livre")
        
        return pd.DataFrame(transactions)
    
    @staticmethod
    def _parse_tunisian_amount(amount_str: str) -> float:
        """Convertit un montant tunisien (1.234,56) en float"""
        return TunisianBankConfig.normalize_tunisian_amount(amount_str)
