from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from db_models.base import BaseModel

class UploadedFile(BaseModel):
    __tablename__ = "uploaded_files"
    
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'bank' or 'accounting'
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    rows_count = Column(Integer, default=0)
    uploaded_by = Column(String(100), default="system")
    status = Column(String(50), default="uploaded")  # uploaded, processed, error
    error_message = Column(Text)
    
    # Relationships
    bank_transactions = relationship("BankTransaction", back_populates="file", cascade="all, delete-orphan")
    accounting_transactions = relationship("AccountingTransaction", back_populates="file", cascade="all, delete-orphan")
    reconciliations_as_bank = relationship("Reconciliation", foreign_keys="Reconciliation.bank_file_id", back_populates="bank_file")
    reconciliations_as_accounting = relationship("Reconciliation", foreign_keys="Reconciliation.accounting_file_id", back_populates="accounting_file")