import pandas as pd

class DataCorrector:
    @staticmethod
    def correct_bank_totals(df: pd.DataFrame) -> pd.DataFrame:
        # Disabled - let parser handle amounts correctly
        return df
    
    @staticmethod
    def correct_accounting_totals(df: pd.DataFrame) -> pd.DataFrame:
        # Disabled - let parser handle amounts correctly
        return df
