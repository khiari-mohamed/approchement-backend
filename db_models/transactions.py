from sqlalchemy import Column, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from db_models.base import BaseModel

class BankTransaction(BaseModel):
    __tablename__ = "bank_transactions"
    
    file_id = Column(String, ForeignKey("uploaded_files.id"), nullable=False)
    date = Column(Date, nullable=False)
    value_date = Column(Date)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="TND")
    description = Column(Text, nullable=False)
    normalized_description = Column(Text)
    reference = Column(String(100))
    status = Column(String(50), default="unmatched")  # matched, unmatched, suspense
    category = Column(String(100))
    ai_category = Column(String(100))
    ai_confidence = Column(Float)
    
    # Relationships
    file = relationship("UploadedFile", back_populates="bank_transactions")
    matches_as_bank = relationship("Match", foreign_keys="Match.bank_transaction_id", back_populates="bank_transaction")

class AccountingTransaction(BaseModel):
    __tablename__ = "accounting_transactions"
    
    file_id = Column(String, ForeignKey("uploaded_files.id"), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="TND")
    description = Column(Text, nullable=False)
    normalized_description = Column(Text)
    account_code = Column(String(20))  # PCN account code
    reference = Column(String(100))
    piece_number = Column(String(50))
    status = Column(String(50), default="unmatched")  # matched, unmatched, suspense
    
    # Relationships
    file = relationship("UploadedFile", back_populates="accounting_transactions")
    matches_as_accounting = relationship("Match", foreign_keys="Match.accounting_transaction_id", back_populates="accounting_transaction")