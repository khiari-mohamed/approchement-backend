from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MatchStatus(str, Enum):
    MATCHED = "matched"
    SUSPENSE = "suspense" 
    UNMATCHED = "unmatched"
    VALIDATED = "validated"

class MatchRule(str, Enum):
    EXACT = "exact"
    FUZZY_STRONG = "fuzzy_strong"
    FUZZY_WEAK = "fuzzy_weak"
    GROUP = "group"
    AI_ASSISTED = "ai_assisted"
    MANUAL = "manual"

class Transaction(BaseModel):
    id: str
    date: str
    amount: float
    description: str
    currency: str = "TND"
    account_code: Optional[str] = None
    value_date: Optional[str] = None
    category: Optional[str] = None

class Match(BaseModel):
    id: str
    bank_tx: Transaction
    accounting_tx: Optional[Transaction] = None
    accounting_txs: Optional[List[Transaction]] = None
    score: float
    rule: MatchRule
    status: MatchStatus
    recon_id: Optional[str] = None
    account_code: Optional[str] = None
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    ai_confidence: Optional[float] = None

class SuspenseItem(BaseModel):
    transaction: Transaction
    type: str
    reason: str
    suggested_category: Optional[str] = None
    ai_confidence: Optional[float] = None

class ReconciliationSummary(BaseModel):
    bank_total: float
    accounting_total: float
    matched_count: int
    suspense_count: int
    initial_gap: float
    residual_gap: float
    coverage_ratio: float
    opening_balance: float
    ai_assisted_matches: int = 0

class ReconciliationResult(BaseModel):
    summary: ReconciliationSummary
    matches: List[Match]
    suspense: List[SuspenseItem]
    metadata: Optional[Dict[str, Any]] = None

class UploadData(BaseModel):
    id: str
    filename: str
    file_type: str
    rows_count: int
    data: List[Dict[str, Any]]
    uploaded_at: datetime

class ReconciliationRules(BaseModel):
    amount_tolerance: float = 0.01
    date_tolerance_days: int = 1
    fuzzy_date_tolerance_days: int = 3
    weak_date_tolerance_days: int = 7
    label_similarity_threshold: float = 0.95
    fuzzy_label_threshold: float = 0.80
    weak_label_threshold: float = 0.60
    enable_group_matching: bool = True
    max_group_size: int = 5
    enable_ai_assistance: bool = True

class ReconcileRequest(BaseModel):
    bank_file: str
    accounting_file: str
    rules: Optional[ReconciliationRules] = None

class MatchValidation(BaseModel):
    action: str
    accountCode: Optional[str] = None

class AIRequest(BaseModel):
    label1: str
    label2: str

class CategoryRequest(BaseModel):
    description: str

class PCNRequest(BaseModel):
    account_code: str