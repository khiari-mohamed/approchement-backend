import pandas as pd
import io
from typing import Dict, Any
import uuid
import os
from datetime import datetime
from parsers.biat_parser import BIATPDFParser
from parsers.intelligent_parser import IntelligentPDFParser
from services.data_fixer import UltimateDataFixer
from services.tunisian_config import TunisianBankConfig
from utils.date_parser import parse_date_universal
try:
    import PyPDF2
    import pdfplumber
except ImportError:
    PyPDF2 = None
    pdfplumber = None
try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

class FileProcessor:
    def __init__(self):
        self.supported_formats = ['.csv', '.pdf', '.xlsx', '.xls', '.png', '.jpg', '.jpeg']
        self.intelligent_parser = IntelligentPDFParser()
    
    def process_file(self, file_path: str, file_type: str) -> pd.DataFrame:
        """Process any supported file format"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        if file_ext == '.csv':
            if file_type == 'bank':
                return self.parse_bank_csv(content)
            else:
                return self.parse_accounting_csv(content)
        elif file_ext == '.pdf':
            if file_type == 'bank':
                return self.parse_pdf(content, file_type)
            else:
                return self.parse_grand_livre_pdf(content)
        elif file_ext in ['.xlsx', '.xls']:
            return self.parse_excel(content, file_type)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            return self.parse_image(content, file_type)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def parse_pdf(self, content: bytes, file_type: str) -> pd.DataFrame:
        """Parse PDF using intelligent parser with fallback"""
        try:
            print(f"🔍 Parsing intelligent du PDF ({file_type})...")
            df = self.intelligent_parser.parse_with_fallback(content, file_type)
            
            if df is None or df.empty:
                raise ValueError("Aucune transaction extraite")
            
            print(f"✅ {len(df)} transactions extraites")
            
            # Apply ultimate fix
            fixer = UltimateDataFixer()
            if file_type == 'bank':
                df = fixer.fix_bank_data(df)
            else:
                df = fixer.fix_accounting_data(df)
            
            required_cols = ['id', 'date', 'description', 'amount']
            for col in required_cols:
                if col not in df.columns:
                    if col == 'id':
                        df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
                    elif col == 'date':
                        df['date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
                    elif col == 'description':
                        df['description'] = 'Transaction'
                    elif col == 'amount':
                        df['amount'] = 0.0
            
            if file_type == 'bank':
                return self._normalize_bank_data(df)
            else:
                return self._normalize_accounting_data(df)
            
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    def parse_excel(self, content: bytes, file_type: str) -> pd.DataFrame:
        """Parse Excel file"""
        try:
            # Try reading with different parameters
            df = pd.read_excel(io.BytesIO(content), header=None)
            
            # Check if it's a Grand Livre format (Sage export)
            if file_type == 'accounting' and self._is_grand_livre_format(df):
                df = self._parse_grand_livre_excel(df)
            else:
                # Standard Excel parsing
                df = pd.read_excel(io.BytesIO(content))
            
            if file_type == 'bank':
                return self._normalize_bank_data(df)
            else:
                return self._normalize_accounting_data(df)
                
        except Exception as e:
            raise ValueError(f"Error parsing Excel: {str(e)}")
    
    def parse_image(self, content: bytes, file_type: str) -> pd.DataFrame:
        """Extract data from image using OCR"""
        if Image is None or pytesseract is None:
            raise ValueError("Image OCR support not installed. Install: pip install Pillow pytesseract")
        
        try:
            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image)
            
            lines = text.strip().split('\n')
            data = [line.split() for line in lines if line.strip()]
            
            if not data:
                raise ValueError("No data extracted from image")
            
            df = pd.DataFrame(data[1:], columns=data[0])
            
            if file_type == 'bank':
                return self._normalize_bank_data(df)
            else:
                return self._normalize_accounting_data(df)
                
        except Exception as e:
            raise ValueError(f"Error parsing image: {str(e)}")
    
    def _normalize_bank_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize bank data from any format"""
        df.columns = df.columns.astype(str).str.lower().str.strip()
        
        column_mapping = {
            'date': ['date', 'date_operation', 'date_valeur', 'dateop', 'datevaleur'],
            'amount': ['montant', 'amount', 'debit', 'credit', 'solde'],
            'description': ['libelle', 'description', 'motif', 'reference', 'desc'],
        }
        
        for target_col, possible_names in column_mapping.items():
            for col in df.columns:
                col_str = str(col)
                if any(name in col_str for name in possible_names):
                    if target_col not in df.columns:
                        df[target_col] = df[col]
                    break
        
        if 'debit' in df.columns and 'credit' in df.columns:
            df['debit'] = pd.to_numeric(df['debit'], errors='coerce').fillna(0)
            df['credit'] = pd.to_numeric(df['credit'], errors='coerce').fillna(0)
            df['amount'] = df['credit'] - df['debit']
        
        df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        return self._clean_dataframe(df)
    
    def _normalize_accounting_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize accounting data from any format"""
        df.columns = df.columns.astype(str).str.lower().str.strip()
        
        column_mapping = {
            'date': ['date', 'date_ecriture', 'date_piece', 'dateop'],
            'amount': ['montant', 'amount', 'debit', 'credit', 'solde'],
            'description': ['libelle', 'description', 'motif', 'reference', 'piece'],
            'account_code': ['compte', 'code_compte', 'numero_compte', 'pcn', 'account']
        }
        
        for target_col, possible_names in column_mapping.items():
            for col in df.columns:
                col_str = str(col)
                if any(name in col_str for name in possible_names):
                    if target_col not in df.columns:
                        df[target_col] = df[col]
                    break
        
        if 'debit' in df.columns and 'credit' in df.columns:
            df['debit'] = pd.to_numeric(df['debit'], errors='coerce').fillna(0)
            df['credit'] = pd.to_numeric(df['credit'], errors='coerce').fillna(0)
            df['amount'] = df.apply(lambda row: row['debit'] if row['debit'] != 0 else -row['credit'], axis=1)
        
        df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        return self._clean_dataframe(df)
    
    def parse_bank_csv(self, content: bytes) -> pd.DataFrame:
        """Parse bank CSV file with common Tunisian bank formats"""
        try:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode file with any supported encoding")
            
            for sep in [',', ';', '\t']:
                try:
                    df = pd.read_csv(io.StringIO(text_content), sep=sep)
                    if len(df.columns) > 1:
                        break
                except:
                    continue
            else:
                raise ValueError("Could not parse CSV with any supported separator")
            
            df.columns = df.columns.str.lower().str.strip()
            
            column_mapping = {
                'date': ['date', 'date_operation', 'date_valeur', 'dateop', 'datevaleur'],
                'amount': ['montant', 'amount', 'debit', 'credit', 'solde'],
                'description': ['libelle', 'description', 'motif', 'reference', 'desc'],
                'account_code': ['compte', 'account', 'numero_compte', 'account_number']
            }
            
            for target_col, possible_names in column_mapping.items():
                for col in df.columns:
                    if any(name in col for name in possible_names):
                        if target_col not in df.columns:
                            df[target_col] = df[col]
                        break
            
            if 'debit' in df.columns and 'credit' in df.columns:
                df['debit'] = pd.to_numeric(df['debit'], errors='coerce').fillna(0)
                df['credit'] = pd.to_numeric(df['credit'], errors='coerce').fillna(0)
                df['amount'] = df['credit'] - df['debit']
            
            df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            
            return self._clean_dataframe(df)
            
        except Exception as e:
            raise ValueError(f"Error parsing bank CSV: {str(e)}")
    
    def parse_accounting_csv(self, content: bytes) -> pd.DataFrame:
        """Parse accounting CSV file"""
        try:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode file with any supported encoding")
            
            for sep in [',', ';', '\t']:
                try:
                    df = pd.read_csv(io.StringIO(text_content), sep=sep)
                    if len(df.columns) > 1:
                        break
                except:
                    continue
            else:
                raise ValueError("Could not parse CSV with any supported separator")
            
            return self._normalize_accounting_data(df)
            
        except Exception as e:
            raise ValueError(f"Error parsing accounting CSV: {str(e)}")
    
    def parse_grand_livre_pdf(self, content: bytes) -> pd.DataFrame:
        """Parse Grand Livre PDF using intelligent parser"""
        return self.intelligent_parser.parse_with_fallback(content, 'accounting')
    
    def _is_grand_livre_format(self, df: pd.DataFrame) -> bool:
        """Check if Excel is Grand Livre format"""
        # Check for typical Grand Livre headers
        first_rows = df.head(10).astype(str)
        indicators = ['grand-livre', 'solde progressif', 'mouvement', 'sage']
        return any(any(ind in str(cell).lower() for cell in row) for row in first_rows.values for ind in indicators)
    
    def _parse_grand_livre_excel(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse Sage Grand Livre Excel format"""
        transactions = []
        
        # Find data rows (skip headers/footers)
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)]).strip()
            
            # Skip empty rows, headers, footers, page breaks
            if not row_str or len(row_str) < 10:
                continue
            if any(skip in row_str.lower() for skip in ['grand-livre', 'page', 'total', 'report', 'impression', 'sage', 'période']):
                continue
            
            # Try to extract transaction data
            # Format: Date | C.j | N° pièce | Libellé | Débit | Crédit | Solde
            try:
                cells = [cell for cell in row if pd.notna(cell)]
                if len(cells) < 4:
                    continue
                
                # First cell should be date (DDMMYY format)
                date_str = str(cells[0]).strip()
                if len(date_str) == 6 and date_str.isdigit():
                    # Parse date DDMMYY
                    day = date_str[:2]
                    month = date_str[2:4]
                    year = '20' + date_str[4:6]
                    date = f"{year}-{month}-{day}"
                    
                    # Find description (usually longest text field)
                    description = ''
                    amounts = []
                    for cell in cells[1:]:
                        cell_str = str(cell).strip()
                        # Try to parse as amount
                        try:
                            # Handle Tunisian format: spaces as thousands separator
                            amount_str = cell_str.replace(' ', '').replace(',', '.')
                            if amount_str.replace('.', '').replace('-', '').isdigit():
                                amounts.append(float(amount_str))
                            else:
                                description += ' ' + cell_str
                        except:
                            description += ' ' + cell_str
                    
                    description = description.strip()
                    
                    # Last amount is usually the balance, second-to-last is the movement
                    if len(amounts) >= 2:
                        amount = amounts[-2]  # Movement amount
                        
                        transactions.append({
                            'date': date,
                            'description': description,
                            'amount': amount
                        })
            except Exception as e:
                continue
        
        if not transactions:
            # Fallback: return empty dataframe with required columns
            return pd.DataFrame(columns=['date', 'description', 'amount'])
        
        return pd.DataFrame(transactions)
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate dataframe"""
        print(f"DEBUG: Cleaning {len(df)} rows BEFORE cleaning")
        
        required_cols = ['id', 'date', 'amount', 'description']
        for col in required_cols:
            if col not in df.columns:
                if col == 'id':
                    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
                elif col == 'date':
                    df['date'] = pd.Timestamp.now()
                elif col == 'description':
                    df['description'] = ''
                elif col == 'amount':
                    df['amount'] = 0.0
        
        # Keep as Timestamp, don't convert to date
        df['date'] = pd.to_datetime(df['date'].apply(parse_date_universal), errors='coerce')
        
        if df['amount'].dtype == 'object':
            df['amount'] = df['amount'].astype(str).apply(TunisianBankConfig.normalize_tunisian_amount)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
        
        zero_count = (df['amount'] == 0).sum()
        if zero_count > 0:
            print(f"DEBUG: {zero_count} transactions with ZERO amount found")
        
        df['description'] = df['description'].astype(str).fillna('')
        
        print(f"DEBUG: Cleaning complete: {len(df)} rows AFTER cleaning")
        
        return df
    
    def validate_csv_structure(self, df: pd.DataFrame, file_type: str) -> Dict[str, Any]:
        """Validate CSV structure and return validation results"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'row_count': len(df),
            'columns': list(df.columns)
        }
        
        required_columns = ['date', 'amount', 'description']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation['valid'] = False
            validation['errors'].append(f"Missing required columns: {missing_columns}")
        
        if 'amount' in df.columns:
            zero_amounts = df['amount'].eq(0).sum()
            if zero_amounts > 0:
                validation['warnings'].append(f"{zero_amounts} transactions with zero amount")
        
        if 'date' in df.columns:
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                validation['warnings'].append(f"{invalid_dates} transactions with invalid dates")
        
        if file_type == 'accounting' and 'account_code' not in df.columns:
            validation['warnings'].append("No account codes found - manual assignment may be required")
        
        return validation
