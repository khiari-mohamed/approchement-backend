from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from db_models.base import BaseModel

class Reconciliation(BaseModel):
    __tablename__ = "reconciliations"
    
    bank_file_id = Column(String, ForeignKey("uploaded_files.id"), nullable=False)
    accounting_file_id = Column(String, ForeignKey("uploaded_files.id"), nullable=False)
    
    # Summary statistics
    bank_total = Column(Float, default=0.0)
    accounting_total = Column(Float, default=0.0)
    matched_count = Column(Integer, default=0)
    suspense_count = Column(Integer, default=0)
    initial_gap = Column(Float, default=0.0)
    residual_gap = Column(Float, default=0.0)
    coverage_ratio = Column(Float, default=0.0)
    ai_assisted_matches = Column(Integer, default=0)
    
    # Enhanced gap calculations (Cahier des Charges)
    explained_gap = Column(Float, default=0.0)  # Écart expliqué
    bank_suspense_total = Column(Float, default=0.0)  # Σ(Suspens bancaires)
    accounting_suspense_total = Column(Float, default=0.0)  # Σ(Suspens comptables)
    coverage_percentage = Column(Float, default=0.0)  # (Écart expliqué / Écart initial) × 100
    
    # Performance metrics
    processing_time = Column(Float)  # seconds
    manual_interventions = Column(Integer, default=0)
    match_accuracy = Column(Float, default=0.0)  # percentage
    duplicate_count = Column(Integer, default=0)
    validation_errors = Column(JSON)  # List of validation errors
    
    # Processing info
    status = Column(String(50), default="processing")  # processing, completed, failed
    error_message = Column(Text)
    rules_used = Column(JSON)  # Store reconciliation rules as JSON
    
    # Report generation
    report_path = Column(String(500))
    report_generated = Column(Boolean, default=False)
    
    # User info
    created_by = Column(String(100), default="system")
    
    # Relationships
    bank_file = relationship("UploadedFile", foreign_keys=[bank_file_id], back_populates="reconciliations_as_bank")
    accounting_file = relationship("UploadedFile", foreign_keys=[accounting_file_id], back_populates="reconciliations_as_accounting")
    matches = relationship("Match", back_populates="reconciliation", cascade="all, delete-orphan")
    suspense_items = relationship("SuspenseItem", back_populates="reconciliation", cascade="all, delete-orphan")

class Match(BaseModel):
    __tablename__ = "matches"
    
    reconciliation_id = Column(String, ForeignKey("reconciliations.id"), nullable=False)
    bank_transaction_id = Column(String, ForeignKey("bank_transactions.id"), nullable=False)
    accounting_transaction_id = Column(String, ForeignKey("accounting_transactions.id"))
    
    # Match details
    recon_number = Column(String(20))  # N° R (Numéro de Rapprochement)
    match_rule = Column(String(50), nullable=False)  # exact, fuzzy_strong, fuzzy_weak, group, ai_assisted
    match_score = Column(Float, default=0.0)
    ai_confidence = Column(Float)
    
    # Status and validation
    status = Column(String(50), default="matched")  # matched, validated, rejected, manual
    validated_by = Column(String(100))
    validated_at = Column(String)
    validation_comment = Column(Text)
    
    # Group matching support
    is_group_match = Column(Boolean, default=False)
    group_id = Column(String(50))  # For 1-to-N matches
    
    # Relationships
    reconciliation = relationship("Reconciliation", back_populates="matches")
    bank_transaction = relationship("BankTransaction", foreign_keys=[bank_transaction_id], back_populates="matches_as_bank")
    accounting_transaction = relationship("AccountingTransaction", foreign_keys=[accounting_transaction_id], back_populates="matches_as_accounting")

class SuspenseItem(BaseModel):
    __tablename__ = "suspense_items"
    
    reconciliation_id = Column(String, ForeignKey("reconciliations.id"), nullable=False)
    transaction_id = Column(String, nullable=False)  # ID of unmatched transaction
    transaction_type = Column(String(20), nullable=False)  # 'bank' or 'accounting'
    
    # Suspense details
    reason = Column(Text, nullable=False)
    suggested_category = Column(String(100))
    suggested_account = Column(String(20))  # PCN account suggestion
    ai_confidence = Column(Float)
    
    # Resolution
    status = Column(String(50), default="pending")  # pending, resolved, ignored
    resolved_by = Column(String(100))
    resolved_at = Column(String)
    resolution_comment = Column(Text)
    
    # Relationships
    reconciliation = relationship("Reconciliation", back_populates="suspense_items")