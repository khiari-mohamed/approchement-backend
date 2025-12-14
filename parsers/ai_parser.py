"""
AI-Powered PDF Parser - Fallback layer when traditional parsing fails
Uses Claude API to intelligently extract transaction data
"""
import os
import re
import json
import pandas as pd
import uuid
from typing import Optional
try:
    import anthropic
except ImportError:
    anthropic = None

class AIPDFParser:
    """AI-powered parser using Claude for complex PDFs"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key) if anthropic and self.api_key else None
    
    def parse_with_ai(self, text: str, file_type: str) -> Optional[pd.DataFrame]:
        """Use AI to parse extracted text when traditional methods fail"""
        if not self.client:
            print("DEBUG: Claude API not available, skipping AI parsing")
            return None
        
        print(f"DEBUG: Attempting AI parsing for {file_type}")
        
        try:
            if file_type == 'bank':
                prompt = self._create_bank_prompt(text[:8000])  # Limit text size
            else:
                prompt = self._create_accounting_prompt(text[:8000])
            
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return self._parse_ai_response(content, file_type)
            
        except Exception as e:
            print(f"DEBUG: AI parsing failed: {str(e)}")
            return None
    
    def _create_bank_prompt(self, text: str) -> str:
        """Create prompt for bank statement parsing"""
        return f"""Extract ALL transactions from this BIAT bank statement text.

Format patterns to look for:
1. Balance: "SOLDE AU 31 07 2025 1.177.437,649"
2. Transaction: "01 08 REGLEMENT CHEQUE 0001294 31072025 7.908,050"
3. Commission: "01 08 ENG/SIGNATURE R0010350 01082025 3,800"

Rules:
- Convert dates to YYYY-MM-DD format
- Parse Tunisian amounts correctly: remove dots (thousands separators), replace comma with dot for decimals
- Examples: "1.234,56" → 1234.56, "630.298,000" → 630298.0
- Extract complete descriptions
- Identify transaction type (balance/transaction/commission)

Text:
{text}

Return ONLY valid JSON (no markdown):
{{"transactions": [{{"date": "YYYY-MM-DD", "description": "text", "amount": number, "type": "balance|transaction|commission"}}]}}"""
    
    def _create_accounting_prompt(self, text: str) -> str:
        """Create prompt for grand livre parsing"""
        return f"""Extract ALL transactions from this Tunisian grand livre (general ledger).

Format patterns:
1. "010825 5607 1000 MCC 3 462.900 -3 462.900"
   → date: 2025-08-01, description: "MCC", amount: -3462.9, solde: -3462.9
2. "290825 Autres frais 9.520 249.697,875"
   → date: 2025-08-29, description: "Autres frais", amount: -9.52, solde: 249697.875

Rules:
- Date format: DDMMYY → YYYY-MM-DD
- Last column is usually progressive balance (solde_progressif)
- Parse Tunisian amounts correctly: remove dots (thousands separators), replace comma with dot for decimals
- Examples: "249.697,875" → 249697.875, "3.462,900" → 3462.9
- Skip header rows

Text:
{text}

Return ONLY valid JSON (no markdown):
{{"transactions": [{{"date": "YYYY-MM-DD", "description": "text", "amount": number, "solde_progressif": number}}]}}"""
    
    def _parse_ai_response(self, content: str, file_type: str) -> Optional[pd.DataFrame]:
        """Parse AI response and convert to DataFrame"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                return None
            
            data = json.loads(json_match.group())
            transactions = data.get('transactions', [])
            
            if not transactions:
                return None
            
            # Add IDs
            for tx in transactions:
                tx['id'] = str(uuid.uuid4())
            
            df = pd.DataFrame(transactions)
            print(f"DEBUG: AI extracted {len(df)} transactions")
            return df
            
        except Exception as e:
            print(f"DEBUG: Failed to parse AI response: {str(e)}")
            return None
