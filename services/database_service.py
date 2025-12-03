from sqlalchemy.orm import Session
from db_models.reconciliation import Reconciliation, Match, SuspenseItem
from db_models.regularization import RegularizationEntry
from db_models.files import UploadedFile
from db_models.transactions import BankTransaction, AccountingTransaction
from db_models.audit import AuditLog
from db_models.performance import PerformanceMetrics
from typing import Optional, List
import json
from datetime import datetime

class DatabaseService:
    """Production-ready database service for reconciliation data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ RECONCILIATION OPERATIONS ============
    
    def create_reconciliation(self, bank_file_id: str, accounting_file_id: str, 
                            rules: dict, user_id: str) -> Reconciliation:
        """Create new reconciliation job"""
        recon = Reconciliation(
            bank_file_id=bank_file_id,
            accounting_file_id=accounting_file_id,
            rules_used=rules,
            created_by=user_id,
            status="processing"
        )
        self.db.add(recon)
        self.db.commit()
        self.db.refresh(recon)
        return recon
    
    def update_reconciliation_results(self, recon_id: str, summary: dict, 
                                     processing_time: float) -> Reconciliation:
        """Update reconciliation with results"""
        recon = self.db.query(Reconciliation).filter(Reconciliation.id == recon_id).first()
        if recon:
            recon.bank_total = summary.get("bank_total", 0.0)
            recon.accounting_total = summary.get("accounting_total", 0.0)
            recon.matched_count = summary.get("matched_count", 0)
            recon.suspense_count = summary.get("suspense_count", 0)
            recon.initial_gap = summary.get("initial_gap", 0.0)
            recon.residual_gap = summary.get("residual_gap", 0.0)
            recon.coverage_ratio = summary.get("coverage_ratio", 0.0)
            recon.ai_assisted_matches = summary.get("ai_assisted_matches", 0)
            recon.processing_time = processing_time
            recon.status = "completed"
            self.db.commit()
            self.db.refresh(recon)
        return recon
    
    def mark_reconciliation_failed(self, recon_id: str, error: str):
        """Mark reconciliation as failed"""
        recon = self.db.query(Reconciliation).filter(Reconciliation.id == recon_id).first()
        if recon:
            recon.status = "failed"
            recon.error_message = error
            self.db.commit()
    
    def get_reconciliation(self, recon_id: str) -> Optional[Reconciliation]:
        """Get reconciliation by ID"""
        return self.db.query(Reconciliation).filter(Reconciliation.id == recon_id).first()
    
    def list_reconciliations(self, user_id: str = None, limit: int = 50) -> List[Reconciliation]:
        """List reconciliations with optional user filter"""
        query = self.db.query(Reconciliation)
        if user_id:
            query = query.filter(Reconciliation.created_by == user_id)
        return query.order_by(Reconciliation.created_at.desc()).limit(limit).all()
    
    # ============ MATCH OPERATIONS ============
    
    def save_matches(self, recon_id: str, matches: List[dict]) -> List[Match]:
        """Save all matches for a reconciliation"""
        match_objects = []
        for match_data in matches:
            match = Match(
                reconciliation_id=recon_id,
                bank_transaction_id=match_data["bank_tx_id"],
                accounting_transaction_id=match_data.get("accounting_tx_id"),
                recon_number=match_data.get("recon_number"),
                match_rule=match_data["rule"],
                match_score=match_data["score"],
                ai_confidence=match_data.get("ai_confidence"),
                is_group_match=match_data.get("is_group_match", False),
                group_id=match_data.get("group_id"),
                status="matched"
            )
            self.db.add(match)
            match_objects.append(match)
        
        self.db.commit()
        return match_objects
    
    def get_matches(self, recon_id: str, page: int = 1, limit: int = 50) -> tuple:
        """Get paginated matches for reconciliation"""
        query = self.db.query(Match).filter(Match.reconciliation_id == recon_id)
        total = query.count()
        matches = query.offset((page - 1) * limit).limit(limit).all()
        return matches, total
    
    def validate_match(self, match_id: str, action: str, user_id: str, 
                      account_code: str = None, comment: str = None) -> Match:
        """Validate or reject a match"""
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if match:
            match.status = "validated" if action == "confirm" else "rejected"
            match.validated_by = user_id
            match.validated_at = datetime.utcnow().isoformat()
            match.validation_comment = comment
            
            # Log audit trail
            self.create_audit_log(
                user_id=user_id,
                action=f"match_{action}",
                entity_type="match",
                entity_id=match_id,
                event_metadata={"account_code": account_code, "comment": comment}
            )
            
            self.db.commit()
            self.db.refresh(match)
        return match
    
    # ============ SUSPENSE OPERATIONS ============
    
    def save_suspense_items(self, recon_id: str, suspense_items: List[dict]) -> List[SuspenseItem]:
        """Save suspense items"""
        suspense_objects = []
        for item_data in suspense_items:
            suspense = SuspenseItem(
                reconciliation_id=recon_id,
                transaction_id=item_data["transaction_id"],
                transaction_type=item_data["type"],
                reason=item_data["reason"],
                suggested_category=item_data.get("suggested_category"),
                suggested_account=item_data.get("suggested_account"),
                ai_confidence=item_data.get("ai_confidence"),
                status="pending"
            )
            self.db.add(suspense)
            suspense_objects.append(suspense)
        
        self.db.commit()
        return suspense_objects
    
    def get_suspense_items(self, recon_id: str) -> List[SuspenseItem]:
        """Get all suspense items for reconciliation"""
        return self.db.query(SuspenseItem).filter(
            SuspenseItem.reconciliation_id == recon_id
        ).all()
    
    def resolve_suspense(self, suspense_id: str, user_id: str, 
                        resolution: str, comment: str = None) -> SuspenseItem:
        """Resolve a suspense item"""
        suspense = self.db.query(SuspenseItem).filter(SuspenseItem.id == suspense_id).first()
        if suspense:
            suspense.status = "resolved"
            suspense.resolved_by = user_id
            suspense.resolved_at = datetime.utcnow().isoformat()
            suspense.resolution_comment = comment
            
            self.create_audit_log(
                user_id=user_id,
                action="suspense_resolved",
                entity_type="suspense",
                entity_id=suspense_id,
                event_metadata={"resolution": resolution, "comment": comment}
            )
            
            self.db.commit()
            self.db.refresh(suspense)
        return suspense
    
    # ============ FILE OPERATIONS ============
    
    def save_uploaded_file(self, filename: str, file_path: str, file_type: str, 
                          rows_count: int, user_id: str) -> UploadedFile:
        """Save uploaded file metadata"""
        file_obj = UploadedFile(
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            rows_count=rows_count,
            uploaded_by=user_id,
            status="processed"
        )
        self.db.add(file_obj)
        self.db.commit()
        self.db.refresh(file_obj)
        return file_obj
    
    def get_uploaded_file(self, file_id: str) -> Optional[UploadedFile]:
        """Get uploaded file by ID"""
        return self.db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    
    # ============ TRANSACTION OPERATIONS ============
    
    def save_bank_transactions(self, file_id: str, transactions: List[dict]) -> List[BankTransaction]:
        """Save bank transactions"""
        tx_objects = []
        for tx_data in transactions:
            tx = BankTransaction(
                file_id=file_id,
                transaction_date=tx_data["date"],
                amount=tx_data["amount"],
                description=tx_data["description"],
                currency=tx_data.get("currency", "TND"),
                reference=tx_data.get("reference")
            )
            self.db.add(tx)
            tx_objects.append(tx)
        
        self.db.commit()
        return tx_objects
    
    def save_accounting_transactions(self, file_id: str, transactions: List[dict]) -> List[AccountingTransaction]:
        """Save accounting transactions"""
        tx_objects = []
        for tx_data in transactions:
            tx = AccountingTransaction(
                file_id=file_id,
                transaction_date=tx_data["date"],
                amount=tx_data["amount"],
                description=tx_data["description"],
                account_code=tx_data.get("account_code"),
                journal_code=tx_data.get("journal_code"),
                piece_number=tx_data.get("piece_number")
            )
            self.db.add(tx)
            tx_objects.append(tx)
        
        self.db.commit()
        return tx_objects
    
    # ============ AUDIT OPERATIONS ============
    
    def create_audit_log(self, user_id: str, action: str, entity_type: str, 
                        entity_id: str, event_metadata: dict = None) -> AuditLog:
        """Create audit log entry"""
        audit = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            event_metadata=event_metadata or {},
            ip_address="0.0.0.0",
            user_agent="system",
            event_type="reconciliation",
            success="true"
        )
        self.db.add(audit)
        self.db.commit()
        return audit
    
    def get_audit_logs(self, entity_id: str = None, user_id: str = None, 
                      limit: int = 100) -> List[AuditLog]:
        """Get audit logs with filters"""
        query = self.db.query(AuditLog)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    # ============ REGULARIZATION OPERATIONS ============
    
    def save_regularization_entries(self, recon_id: str, entries: List[dict]) -> List[RegularizationEntry]:
        """Save regularization entries to database"""
        entry_objects = []
        for entry_data in entries:
            entry = RegularizationEntry(
                reconciliation_id=recon_id,
                entry_number=entry_data.get("entry_number", ""),
                entry_date=entry_data.get("date", ""),
                description=entry_data.get("description", ""),
                lines=entry_data.get("lines", []),
                total_debit=entry_data.get("total_debit", 0.0),
                total_credit=entry_data.get("total_credit", 0.0),
                is_balanced=entry_data.get("is_balanced", False),
                validation_errors=entry_data.get("validation_errors", []),
                status="generated"
            )
            self.db.add(entry)
            entry_objects.append(entry)
        
        self.db.commit()
        return entry_objects
    
    def get_regularization_entries(self, recon_id: str) -> List[RegularizationEntry]:
        """Get all regularization entries for a reconciliation"""
        return self.db.query(RegularizationEntry).filter(
            RegularizationEntry.reconciliation_id == recon_id
        ).order_by(RegularizationEntry.entry_number).all()
    
    def get_regularization_entry(self, entry_id: str) -> Optional[RegularizationEntry]:
        """Get a single regularization entry"""
        return self.db.query(RegularizationEntry).filter(RegularizationEntry.id == entry_id).first()
    
    # ============ PERFORMANCE METRICS OPERATIONS ============
    
    def save_performance_metrics(self, recon_id: str, metrics: dict) -> PerformanceMetrics:
        """Save performance metrics for a reconciliation"""
        # Check if metrics already exist
        existing = self.db.query(PerformanceMetrics).filter(
            PerformanceMetrics.reconciliation_id == recon_id
        ).first()
        
        if existing:
            # Update existing metrics
            for key, value in metrics.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new metrics
            perf_metrics = PerformanceMetrics(
                reconciliation_id=recon_id,
                **metrics
            )
            self.db.add(perf_metrics)
            self.db.commit()
            self.db.refresh(perf_metrics)
            return perf_metrics
    
    def get_performance_metrics(self, recon_id: str) -> Optional[PerformanceMetrics]:
        """Get performance metrics for a reconciliation"""
        return self.db.query(PerformanceMetrics).filter(
            PerformanceMetrics.reconciliation_id == recon_id
        ).first()

