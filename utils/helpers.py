import uuid
import os
from datetime import datetime
from typing import Dict, Any

def generate_unique_id() -> str:
    """Generate unique identifier"""
    return str(uuid.uuid4())

def generate_recon_id(counter: int, prefix: str = "R") -> str:
    """Generate reconciliation ID (N° R)"""
    return f"{prefix}{counter:06d}"

def safe_float_conversion(value: Any) -> float:
    """Safely convert value to float"""
    try:
        if isinstance(value, str):
            value = value.replace(',', '.').replace(' ', '')
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def normalize_description(text: str) -> str:
    """Normalize transaction description"""
    if not text:
        return ""
    return str(text).strip().upper()

def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage safely"""
    if total == 0:
        return 0.0
    return (part / total) * 100

def ensure_directory_exists(path: str):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)

def format_currency(amount: float, currency: str = "TND") -> str:
    """Format currency amount"""
    return f"{amount:,.2f} {currency}"

def validate_csv_headers(headers: list, required: list) -> Dict[str, bool]:
    """Validate CSV headers"""
    result = {"valid": True, "missing": []}
    
    headers_lower = [h.lower().strip() for h in headers]
    
    for req in required:
        if req.lower() not in headers_lower:
            result["missing"].append(req)
            result["valid"] = False
    
    return result