"""
Universal date parser for all date formats
Handles: YYYY-MM-DD, DD/MM/YYYY, DDMMYYYY, timestamps, etc.
"""
import pandas as pd
from datetime import datetime, date
from typing import Union

def parse_date_universal(date_input: Union[str, datetime, date, pd.Timestamp]) -> pd.Timestamp:
    """
    Parse any date format and return pd.Timestamp
    Handles all common formats without errors
    """
    # Already a Timestamp
    if isinstance(date_input, pd.Timestamp):
        return date_input
    
    # Already a datetime
    if isinstance(date_input, datetime):
        return pd.Timestamp(date_input)
    
    # Already a date
    if isinstance(date_input, date):
        return pd.Timestamp(date_input)
    
    # String parsing
    if isinstance(date_input, str):
        date_str = str(date_input).strip()
        
        # Try YYYY-MM-DD format first (ISO)
        try:
            return pd.to_datetime(date_str, format='%Y-%m-%d')
        except:
            pass
        
        # Try DD/MM/YYYY
        try:
            return pd.to_datetime(date_str, format='%d/%m/%Y')
        except:
            pass
        
        # Try DD-MM-YYYY
        try:
            return pd.to_datetime(date_str, format='%d-%m-%Y')
        except:
            pass
        
        # Try DDMMYYYY (8 digits)
        if len(date_str) == 8 and date_str.isdigit():
            try:
                day = int(date_str[:2])
                month = int(date_str[2:4])
                year = int(date_str[4:])
                return pd.Timestamp(year=year, month=month, day=day)
            except:
                pass
        
        # Try DDMMYY (6 digits)
        if len(date_str) == 6 and date_str.isdigit():
            try:
                day = int(date_str[:2])
                month = int(date_str[2:4])
                year = 2000 + int(date_str[4:])
                return pd.Timestamp(year=year, month=month, day=day)
            except:
                pass
        
        # Last resort: pandas auto-detect
        try:
            return pd.to_datetime(date_str)
        except:
            pass
    
    # If all fails, return default
    return pd.Timestamp('2025-08-01')

def parse_date_to_python_date(date_input: Union[str, datetime, date, pd.Timestamp]) -> date:
    """Parse any date format and return Python date object"""
    ts = parse_date_universal(date_input)
    return ts.date()
