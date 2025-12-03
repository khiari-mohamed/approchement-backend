from sqlalchemy import Column, String, Text, JSON, Integer, Float
from db_models.base import BaseModel

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    # Event details
    event_type = Column(String(100), nullable=False)  # upload, reconciliation, validation, ai_call
    entity_type = Column(String(50))  # file, reconciliation, match, transaction
    entity_id = Column(String, nullable=False)
    
    # User and context
    user_id = Column(String(100), default="system")
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Event data
    action = Column(String(100), nullable=False)  # created, updated, deleted, validated
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    event_metadata = Column(JSON)    # Additional context
    
    # Result
    success = Column(String(10), default="true")  # true, false
    error_message = Column(Text)
    
    # Performance tracking
    execution_time_ms = Column(Integer)  # milliseconds
    
    # Error handling (Cahier des Charges)
    fallback_used = Column(String(10), default="false")  # AI timeout fallback
    retry_count = Column(Integer, default=0)

class AICallLog(BaseModel):
    __tablename__ = "ai_call_logs"
    
    # AI service details
    function_name = Column(String(100), nullable=False)  # compare_labels, categorize_transaction, etc.
    model_name = Column(String(50), default="gemini-2.0-flash-exp")
    
    # Input/Output
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON)
    
    # Performance (Cahier des Charges monitoring)
    response_time_ms = Column(Integer)  # milliseconds
    tokens_used = Column(Integer)
    
    # Context
    reconciliation_id = Column(String)
    transaction_id = Column(String)
    
    # Result
    success = Column(String(10), default="true")
    error_message = Column(Text)
    confidence_score = Column(Float)
    
    # Hallucination detection
    is_hallucination = Column(String(10), default="false")
    validation_status = Column(String(20))  # validated, rejected, pending
    validated_by_user = Column(String(10), default="false")