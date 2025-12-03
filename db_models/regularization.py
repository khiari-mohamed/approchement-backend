from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from db_models.base import BaseModel

class RegularizationEntry(BaseModel):
    __tablename__ = "regularization_entries"
    
    reconciliation_id = Column(String, ForeignKey("reconciliations.id"), nullable=False)
    
    # Entry details
    entry_number = Column(String(50), nullable=False)
    entry_date = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    
    # Entry lines stored as JSON for flexibility
    lines = Column(JSON, nullable=False)  # List of {account_code, account_name, debit, credit, description}
    
    # Totals
    total_debit = Column(Float, default=0.0)
    total_credit = Column(Float, default=0.0)
    
    # Validation
    is_balanced = Column(Boolean, default=True)
    validation_errors = Column(JSON)  # List of validation error messages
    
    # Status
    status = Column(String(50), default="generated")  # generated, validated, exported, applied
    
    # Relationships
    reconciliation = relationship("Reconciliation", foreign_keys=[reconciliation_id])
