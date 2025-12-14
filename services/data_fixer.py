import pandas as pd
import re
from typing import Tuple

class UltimateDataFixer:
    @staticmethod
    def fix_bank_data(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        print(f"🔧 Fixing bank data: {len(df)} rows")
        
        if 'description' in df.columns:
            solde_mask = df['description'].str.contains('SOLDE', case=False, na=False)
            if solde_mask.any():
                solde_count = solde_mask.sum()
                print(f"  Found {solde_count} balance entries")
                df['is_balance'] = solde_mask
        
        return df
    
    @staticmethod
    def fix_accounting_data(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        print(f"🔧 Fixing accounting data: {len(df)} rows")
        return df
    
    @staticmethod
    def enforce_correct_totals(bank_df: pd.DataFrame, acc_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        # Disabled - let the parser handle amounts correctly
        return bank_df, acc_df
