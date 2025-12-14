from enum import Enum
import pandas as pd
from typing import Optional, Dict, Any
import base64
import json
import re
import uuid
import io
import os
from services.tunisian_config import TunisianBankConfig

class ParserStrategy(Enum):
    TRADITIONAL = 1
    OCR_TESSERACT = 2
    AI_VISION = 3
    AI_STRUCTURED = 4
    HYBRID = 5

class IntelligentPDFParser:
    def __init__(self, claude_api_key: str = None):
        self.claude_key = claude_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.parsing_history = []
    
    def parse_with_fallback(self, pdf_content: bytes, file_type: str) -> pd.DataFrame:
        strategies = [
            self._parse_traditional,
            self._parse_with_structured_ai,
            self._parse_hybrid_emergency
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                print(f"Essai stratégie {i+1}/{len(strategies)}...")
                result = strategy(pdf_content, file_type)
                
                min_rows = 5 if file_type == 'accounting' else 10
                if result is not None and not result.empty and len(result) >= min_rows:
                    print(f"✅ Stratégie {i+1} réussie: {len(result)} transactions extraites")
                    return result
                    
            except Exception as e:
                print(f"❌ Stratégie {i+1} échouée: {str(e)}")
                continue
        
        result = self._parse_hybrid_emergency(pdf_content, file_type)
        if result.empty:
            raise ValueError(f"Aucune transaction extraite pour {file_type}")
        return result
    
    def _parse_traditional(self, pdf_content: bytes, file_type: str) -> Optional[pd.DataFrame]:
        import pdfplumber
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        df = self._process_table(table, file_type)
                        if df is not None and not df.empty:
                            return df
        
        return pd.DataFrame()
    
    def _parse_with_structured_ai(self, pdf_content: bytes, file_type: str) -> Optional[pd.DataFrame]:
        if not self.claude_key:
            return None
        
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages[:5]])
        
        return self._call_claude_structured(text, file_type)
    
    def _call_claude_structured(self, text: str, file_type: str) -> Optional[pd.DataFrame]:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.claude_key)
            
            if file_type == 'bank':
                prompt = self._create_bank_prompt(text[:5000])
            else:
                prompt = self._create_accounting_prompt(text[:5000])
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_ai_response(response.content[0].text, file_type)
        except Exception as e:
            print(f"Erreur Claude API: {e}")
            return None
    
    def _create_bank_prompt(self, text: str) -> str:
        return f"""Tu es un expert des relevés bancaires BIAT Tunisie.

Extrais TOUTES les transactions:
1. Soldes: "SOLDE AU 31 07 2025 1.177.437,649" → date: 2025-07-31, description: "SOLDE AU 31/07/2025", amount: 1177437.649
2. Transactions: "01 08 REGLEMENT CHEQUE 0001294 31072025 7.908,050" → date: 2025-08-01, description: "REGLEMENT CHEQUE 0001294", amount: 7908.05
3. Commissions: "01 08 ENG/SIGNATURE R0010350 01082025 3,800" → date: 2025-08-01, description: "ENG/SIGNATURE R0010350", amount: 3.8

Règles de parsing des montants tunisiens:
- Enlève les points (séparateurs de milliers)
- Remplace la virgule par un point (séparateur décimal)
- Exemples: "630.298,000" → 630298.0, "1.177.437,649" → 1177437.649

Texte:
{text}

Retourne UNIQUEMENT un JSON:
{{"transactions": [{{"date": "YYYY-MM-DD", "description": "texte", "amount": nombre, "type": "balance|transaction|commission"}}]}}"""
    
    def _create_accounting_prompt(self, text: str) -> str:
        return f"""Tu es un expert en comptabilité tunisienne. Extrais les données de ce grand livre.

Format: "010825 5607 1000 MCC 3 462.900 -3 462.900" → date: 2025-08-01, description: "MCC", amount: -3462.9, solde_progressif: -3462.9

Règles de parsing des montants tunisiens:
- Enlève les points (séparateurs de milliers)
- Remplace la virgule par un point (séparateur décimal)
- Exemples: "249.697,875" → 249697.875, "3.462,900" → 3462.9

Texte:
{text}

Retourne UNIQUEMENT un JSON:
{{"transactions": [{{"date": "YYYY-MM-DD", "description": "libellé", "amount": nombre, "solde_progressif": nombre}}]}}"""
    
    def _parse_ai_response(self, content: str, file_type: str) -> Optional[pd.DataFrame]:
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                return None
            
            data = json.loads(json_match.group())
            transactions = data.get('transactions', [])
            
            if not transactions:
                return None
            
            for tx in transactions:
                tx['id'] = str(uuid.uuid4())
            
            return pd.DataFrame(transactions)
        except:
            return None
    
    def _parse_hybrid_emergency(self, pdf_content: bytes, file_type: str) -> pd.DataFrame:
        import pdfplumber
        
        full_text = ""
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        return self._ml_based_parsing(full_text, file_type)
    
    def _ml_based_parsing(self, text: str, file_type: str) -> pd.DataFrame:
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Skip header lines
            if any(kw in line.upper() for kw in ['DATE', 'LIBELLE', 'MONTANT', 'SOLDE', 'DEBIT', 'CREDIT']):
                continue
            
            if file_type == 'bank':
                # BIAT format: "01 08 REGLEMENT CHEQUE 0001294 31072025 7.908,050"
                # Also handle: "01 08 REGLEMENT CHEQUE 001234      01082025      1.500,000"
                # Pattern: DD MM Description Date(8digits) Amount
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        # First two parts should be day and month
                        day = parts[0]
                        month = parts[1]
                        
                        if not (day.isdigit() and month.isdigit() and len(day) == 2 and len(month) == 2):
                            continue
                        
                        # Find the 8-digit date (DDMMYYYY) and amount with decimal
                        date_8digit = None
                        amount_str = None
                        desc_parts = []
                        
                        for i, part in enumerate(parts[2:], start=2):
                            if len(part) == 8 and part.isdigit():
                                date_8digit = part
                            elif re.match(r'-?[\d\.,]+', part) and ('.' in part or ',' in part):
                                amount_str = part
                            elif not date_8digit:
                                desc_parts.append(part)
                        
                        if not (date_8digit and amount_str):
                            continue
                        
                        # Parse date as datetime object - DDMMYYYY format
                        d_day = int(date_8digit[:2])
                        d_month = int(date_8digit[2:4])
                        d_year = int(date_8digit[4:])
                        date = pd.Timestamp(year=d_year, month=d_month, day=d_day)
                        print(f"DEBUG: Parsed {date_8digit} -> {date.date()}")
                        
                        desc = ' '.join(desc_parts).strip()
                        
                        # Skip balance lines
                        if 'SOLDE' in desc.upper():
                            continue
                        
                        amount = self._parse_tunisian_amount(amount_str)
                        
                        if desc and abs(amount) > 0.001:
                            transactions.append({
                                'id': str(uuid.uuid4()),
                                'date': date,
                                'description': desc,
                                'amount': amount,
                                'type': 'transaction'
                            })
                    except Exception as e:
                        continue
            else:
                # Accounting format: "010825 5607 1000 MCC 3 462.900 -3 462.900"
                # Try to find date at start (DDMMYY format)
                date_match = re.match(r'^(\d{6})', line)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        day = date_str[:2]
                        month = date_str[2:4]
                        year = "20" + date_str[4:6]
                        
                        # Validate date
                        if int(month) > 12 or int(month) < 1 or int(day) > 31 or int(day) < 1:
                            continue
                        
                        date = pd.Timestamp(year=int(year), month=int(month), day=int(day))
                        print(f"DEBUG ACC: Parsed {date_str} -> {date.date()}")
                        
                        # Extract amounts more carefully
                        # Format: "010825 5607 1000 MCC 3 462.900 -3 462.900"
                        # Skip first 2 numbers (journal code + piece number), then find amounts
                        rest_of_line = line[6:].strip()
                        
                        # Skip journal code (4 digits) and piece number (4 digits)
                        # Pattern: DDMMYY JJJJ PPPP Description Amount Balance
                        parts = rest_of_line.split()
                        if len(parts) < 3:
                            continue
                        
                        # Skip first 2 parts (journal + piece), rest is description + amounts
                        desc_and_amounts = ' '.join(parts[2:])
                        
                        # Find amounts with decimal separators (dot or comma with 3 digits after)
                        # This distinguishes real amounts from journal/piece numbers
                        amount_pattern = r'-?\d+[\s\.]*\d+[\.,]\d{3}'
                        amounts_found = re.findall(amount_pattern, desc_and_amounts)
                        
                        if len(amounts_found) >= 1:
                            # Take the FIRST amount as the movement
                            movement_str = amounts_found[0].strip()
                            amount = self._parse_tunisian_amount(movement_str)
                            
                            # Description is before the first amount
                            desc_end = desc_and_amounts.find(amounts_found[0])
                            desc = desc_and_amounts[:desc_end].strip() if desc_end > 0 else parts[2]
                            desc = ' '.join(desc.split())  # Clean whitespace
                            
                            if desc and abs(amount) > 0.001:  # Only add if we have a description and non-zero amount
                                transactions.append({
                                    'id': str(uuid.uuid4()),
                                    'date': date,
                                    'description': desc[:100],
                                    'amount': amount,
                                    'type': 'transaction'
                                })
                    except:
                        continue
        
        return pd.DataFrame(transactions)
    
    def _parse_tunisian_amount(self, amount_str: str) -> float:
        """Parse Tunisian amount format: '3 462.900' or '-3 462.900' → -3462.9"""
        original = amount_str
        
        # Handle negative sign
        is_negative = '-' in amount_str
        amount_str = amount_str.replace('-', '').strip()
        
        # Remove all spaces
        amount_str = amount_str.replace(' ', '')
        
        # Tunisian format: spaces/dots are thousands, dot/comma with 3 decimals
        # Examples: "3 462.900" or "3.462,900" → 3462.9
        
        if ',' in amount_str:
            # Comma is decimal separator: "3.462,900" → 3462.9
            amount_str = amount_str.replace('.', '').replace(',', '.')
        elif '.' in amount_str:
            # Dot with 3 decimals: "3 462.900" → 3462.9
            # Remove spaces/dots except last dot
            parts = amount_str.split('.')
            if len(parts) >= 2 and len(parts[-1]) == 3:
                # Last part is 3 decimals, keep it
                amount_str = ''.join(parts[:-1]) + '.' + parts[-1]
            else:
                # No clear decimal, remove all dots
                amount_str = amount_str.replace('.', '')
        
        try:
            value = float(amount_str)
            result = -value if is_negative else value
            return result
        except Exception as e:
            print(f"⚠️ Failed to parse amount '{original}': {e}")
            return 0.0
    
    def _process_table(self, table, file_type):
        return None
