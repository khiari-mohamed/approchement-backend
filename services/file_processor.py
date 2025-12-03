import pandas as pd
import io
from typing import Dict, Any
import uuid
import os
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
            return self.parse_pdf(content, file_type)
        elif file_ext in ['.xlsx', '.xls']:
            return self.parse_excel(content, file_type)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            return self.parse_image(content, file_type)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def parse_pdf(self, content: bytes, file_type: str) -> pd.DataFrame:
        """Extract data from PDF using pdfplumber"""
        try:
            import pdfplumber
            import re
            pdf_file = io.BytesIO(content)
            
            transactions = []
            
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    # Extract text
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    lines = text.split('\n')
                    
                    for i, line in enumerate(lines):
                        # Look for date pattern (DD MM or DDMMYYYY)
                        date_match = re.search(r'(\d{2})\s+(\d{2})', line)
                        if not date_match:
                            continue
                        
                        # Extract components from the line
                        parts = line.split()
                        
                        # Try to find amounts (numbers with decimals or commas)
                        amounts = []
                        description_parts = []
                        
                        for part in parts:
                            # Check if it's a number (amount)
                            clean_part = part.replace(',', '.').replace(' ', '')
                            try:
                                amount = float(clean_part)
                                amounts.append(amount)
                            except:
                                # It's part of description
                                if not re.match(r'^\d{2}$', part):  # Not just day/month
                                    description_parts.append(part)
                        
                        # If we have a date and at least one amount
                        if date_match and amounts:
                            date_str = f"{date_match.group(1)}/{date_match.group(2)}/2025"
                            description = ' '.join(description_parts) if description_parts else 'Transaction'
                            
                            # Determine debit/credit (last amount is usually the one we need)
                            amount = amounts[-1] if amounts else 0
                            
                            transactions.append({
                                'date': date_str,
                                'description': description,
                                'amount': amount
                            })
            
            if not transactions:
                raise ValueError("No transactions found in PDF")
            
            df = pd.DataFrame(transactions)
            
            # Process based on file type
            if file_type == 'bank':
                return self._normalize_bank_data(df)
            else:
                return self._normalize_accounting_data(df)
                
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    def parse_excel(self, content: bytes, file_type: str) -> pd.DataFrame:
        """Parse Excel file"""
        try:
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
            
            # Parse extracted text as CSV-like data
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
    
    def _normalize_accounting_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize accounting data from any format"""
        df.columns = df.columns.str.lower().str.strip()
        
        column_mapping = {
            'date': ['date', 'date_ecriture', 'date_piece', 'dateop'],
            'amount': ['montant', 'amount', 'debit', 'credit', 'solde'],
            'description': ['libelle', 'description', 'motif', 'reference', 'piece'],
            'account_code': ['compte', 'code_compte', 'numero_compte', 'pcn', 'account']
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
            df['amount'] = df.apply(lambda row: row['debit'] if row['debit'] != 0 else -row['credit'], axis=1)
        
        df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        return self._clean_dataframe(df)
    
    def parse_bank_csv(self, content: bytes) -> pd.DataFrame:
        """Parse bank CSV file with common Tunisian bank formats"""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode file with any supported encoding")
            
            # Try different separators
            for sep in [',', ';', '\t']:
                try:
                    df = pd.read_csv(io.StringIO(text_content), sep=sep)
                    if len(df.columns) > 1:  # Valid CSV should have multiple columns
                        break
                except:
                    continue
            else:
                raise ValueError("Could not parse CSV with any supported separator")
            
            # Normalize column names (common Tunisian bank formats)
            df.columns = df.columns.str.lower().str.strip()
            
            # Map common column variations
            column_mapping = {
                'date': ['date', 'date_operation', 'date_valeur', 'dateop', 'datevaleur'],
                'amount': ['montant', 'amount', 'debit', 'credit', 'solde'],
                'description': ['libelle', 'description', 'motif', 'reference', 'desc'],
                'account_code': ['compte', 'account', 'numero_compte', 'account_number']
            }
            
            # Apply column mapping
            for target_col, possible_names in column_mapping.items():
                for col in df.columns:
                    if any(name in col for name in possible_names):
                        if target_col not in df.columns:
                            df[target_col] = df[col]
                        break
            
            # Handle debit/credit columns (merge into amount)
            if 'debit' in df.columns and 'credit' in df.columns:
                df['debit'] = pd.to_numeric(df['debit'], errors='coerce').fillna(0)
                df['credit'] = pd.to_numeric(df['credit'], errors='coerce').fillna(0)
                df['amount'] = df['credit'] - df['debit']  # Credit positive, debit negative
            
            # Ensure required columns exist
            required_columns = ['date', 'amount', 'description']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Required column '{col}' not found in bank CSV")
            
            # Add unique IDs
            df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            
            # Clean and validate data
            df = self._clean_dataframe(df)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error parsing bank CSV: {str(e)}")
    
    def parse_accounting_csv(self, content: bytes) -> pd.DataFrame:
        """Parse accounting/ERP CSV file"""
        try:
            # Similar parsing logic as bank CSV
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
            
            # Normalize column names
            df.columns = df.columns.str.lower().str.strip()
            
            # Map accounting-specific columns
            column_mapping = {
                'date': ['date', 'date_ecriture', 'date_piece', 'dateop'],
                'amount': ['montant', 'amount', 'debit', 'credit', 'solde'],
                'description': ['libelle', 'description', 'motif', 'reference', 'piece'],
                'account_code': ['compte', 'code_compte', 'numero_compte', 'pcn', 'account']
            }
            
            for target_col, possible_names in column_mapping.items():
                for col in df.columns:
                    if any(name in col for name in possible_names):
                        if target_col not in df.columns:
                            df[target_col] = df[col]
                        break
            
            # Handle debit/credit for accounting entries
            if 'debit' in df.columns and 'credit' in df.columns:
                df['debit'] = pd.to_numeric(df['debit'], errors='coerce').fillna(0)
                df['credit'] = pd.to_numeric(df['credit'], errors='coerce').fillna(0)
                # For accounting: use the non-zero value (debit or credit)
                df['amount'] = df.apply(lambda row: row['debit'] if row['debit'] != 0 else -row['credit'], axis=1)
            
            # Ensure required columns
            required_columns = ['date', 'amount', 'description']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Required column '{col}' not found in accounting CSV")
            
            # Add unique IDs
            df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            
            # Clean and validate
            df = self._clean_dataframe(df)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error parsing accounting CSV: {str(e)}")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate dataframe"""
        df = df.copy()
        
        # Remove empty rows
        df = df.dropna(subset=['date', 'amount'])
        
        # Clean amount column
        if 'amount' in df.columns:
            # Remove currency symbols and spaces
            df['amount'] = df['amount'].astype(str)
            df['amount'] = df['amount'].str.replace('TND', '').str.replace('DT', '')
            df['amount'] = df['amount'].str.replace(' ', '').str.replace(',', '.')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            df = df.dropna(subset=['amount'])
        
        # Clean date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['date'])
        
        # Clean description
        if 'description' in df.columns:
            df['description'] = df['description'].fillna('').astype(str).str.strip()
        
        # Add currency if missing
        if 'currency' not in df.columns:
            df['currency'] = 'TND'
        
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
        
        # Check required columns
        required_columns = ['date', 'amount', 'description']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation['valid'] = False
            validation['errors'].append(f"Missing required columns: {missing_columns}")
        
        # Check data quality
        if 'amount' in df.columns:
            zero_amounts = df['amount'].eq(0).sum()
            if zero_amounts > 0:
                validation['warnings'].append(f"{zero_amounts} transactions with zero amount")
        
        if 'date' in df.columns:
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                validation['warnings'].append(f"{invalid_dates} transactions with invalid dates")
        
        # File type specific validations
        if file_type == 'accounting' and 'account_code' not in df.columns:
            validation['warnings'].append("No account codes found - manual assignment may be required")
        
        return validation