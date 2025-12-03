"""
Validation Service - Automatic checks as per Cahier des Charges
Implements all required validations for data integrity
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import pandas as pd

class ValidationService:
    """Production-ready validation service for reconciliation data"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.alerts = []
    
    def validate_reconciliation(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame, 
                               matches: List[Dict], suspense: List[Dict]) -> Dict:
        """
        Comprehensive validation as per Cahier des Charges:
        - Cohérence mathématique des soldes
        - Équilibre débit/crédit
        - Vérification des comptes PCN
        - Alertes sur écarts anormaux
        """
        self.errors = []
        self.warnings = []
        self.alerts = []
        
        # 1. Validate mathematical coherence
        self._validate_balance_coherence(bank_df, accounting_df, matches, suspense)
        
        # 2. Check for duplicates
        duplicates = self._detect_duplicate_matches(matches)
        
        # 3. Validate date ranges
        date_violations = self._validate_date_ranges(bank_df, accounting_df)
        
        # 4. Check debit/credit balance
        debit_credit_check = self._validate_debit_credit_balance(matches)
        
        # 5. Validate transaction counts
        self._validate_transaction_counts(bank_df, accounting_df, matches, suspense)
        
        # 6. Generate alerts for anomalies
        self._generate_alerts(bank_df, accounting_df, matches, suspense)
        
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "alerts": self.alerts,
            "duplicates_found": duplicates,
            "date_violations": date_violations,
            "debit_credit_balanced": debit_credit_check["balanced"],
            "debit_credit_imbalances": debit_credit_check["imbalances"]
        }
    
    def _validate_balance_coherence(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame,
                                   matches: List[Dict], suspense: List[Dict]):
        """
        Validate: Solde bancaire final = Solde comptable + Écart expliqué
        """
        bank_total = bank_df['amount'].sum()
        accounting_total = accounting_df['amount'].sum()
        
        matched_total = sum([m.get('amount', 0) for m in matches])
        suspense_total = sum([s.get('amount', 0) for s in suspense])
        
        # Check if totals match
        calculated_total = matched_total + suspense_total
        
        if abs(bank_total - calculated_total) > 0.01:
            self.errors.append({
                "type": "balance_incoherence",
                "message": f"Incohérence mathématique: Total bancaire ({bank_total:.3f}) != Total calculé ({calculated_total:.3f})",
                "severity": "critical"
            })
    
    def _detect_duplicate_matches(self, matches: List[Dict]) -> int:
        """
        Detect duplicate matches - Aucun doublon dans les matches
        """
        bank_tx_ids = []
        accounting_tx_ids = []
        duplicates = 0
        
        for match in matches:
            bank_id = match.get('bank_tx_id')
            acc_id = match.get('accounting_tx_id')
            
            if bank_id in bank_tx_ids:
                duplicates += 1
                self.errors.append({
                    "type": "duplicate_match",
                    "message": f"Transaction bancaire {bank_id} rapprochée plusieurs fois",
                    "severity": "high"
                })
            
            if acc_id and acc_id in accounting_tx_ids:
                duplicates += 1
                self.errors.append({
                    "type": "duplicate_match",
                    "message": f"Transaction comptable {acc_id} rapprochée plusieurs fois",
                    "severity": "high"
                })
            
            bank_tx_ids.append(bank_id)
            if acc_id:
                accounting_tx_ids.append(acc_id)
        
        return duplicates
    
    def _validate_date_ranges(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame) -> int:
        """
        Validate: Dates dans la période analysée
        """
        violations = 0
        
        # Convert dates
        bank_df['date'] = pd.to_datetime(bank_df['date'], errors='coerce')
        accounting_df['date'] = pd.to_datetime(accounting_df['date'], errors='coerce')
        
        # Check for invalid dates
        invalid_bank = bank_df['date'].isna().sum()
        invalid_accounting = accounting_df['date'].isna().sum()
        
        if invalid_bank > 0:
            violations += invalid_bank
            self.warnings.append({
                "type": "invalid_dates",
                "message": f"{invalid_bank} transactions bancaires avec dates invalides",
                "severity": "medium"
            })
        
        if invalid_accounting > 0:
            violations += invalid_accounting
            self.warnings.append({
                "type": "invalid_dates",
                "message": f"{invalid_accounting} transactions comptables avec dates invalides",
                "severity": "medium"
            })
        
        # Check for dates outside reasonable range (e.g., future dates or very old)
        today = datetime.now()
        future_bank = (bank_df['date'] > today).sum()
        future_accounting = (accounting_df['date'] > today).sum()
        
        if future_bank > 0 or future_accounting > 0:
            violations += future_bank + future_accounting
            self.warnings.append({
                "type": "future_dates",
                "message": f"Dates futures détectées: {future_bank} bancaires, {future_accounting} comptables",
                "severity": "medium"
            })
        
        return violations
    
    def _validate_debit_credit_balance(self, matches: List[Dict]) -> Dict:
        """
        Validate: Équilibre débit/crédit for all matches
        """
        imbalances = []
        
        for match in matches:
            bank_amount = match.get('bank_amount', 0)
            acc_amount = match.get('accounting_amount', 0)
            
            if abs(bank_amount - acc_amount) > 0.01:
                imbalances.append({
                    "match_id": match.get('id'),
                    "bank_amount": bank_amount,
                    "accounting_amount": acc_amount,
                    "difference": abs(bank_amount - acc_amount)
                })
        
        if imbalances:
            self.warnings.append({
                "type": "debit_credit_imbalance",
                "message": f"{len(imbalances)} rapprochements avec déséquilibre débit/crédit",
                "severity": "medium",
                "details": imbalances
            })
        
        return {
            "balanced": len(imbalances) == 0,
            "imbalances": len(imbalances),
            "details": imbalances
        }
    
    def _validate_transaction_counts(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame,
                                    matches: List[Dict], suspense: List[Dict]):
        """
        Validate: Nombre total transactions = Rapprochées + Suspens
        """
        total_bank = len(bank_df)
        total_accounting = len(accounting_df)
        
        matched_bank = len([m for m in matches if m.get('bank_tx_id')])
        matched_accounting = len([m for m in matches if m.get('accounting_tx_id')])
        
        suspense_bank = len([s for s in suspense if s.get('type') == 'bank'])
        suspense_accounting = len([s for s in suspense if s.get('type') == 'accounting'])
        
        # Validate bank transactions
        if total_bank != (matched_bank + suspense_bank):
            self.errors.append({
                "type": "transaction_count_mismatch",
                "message": f"Incohérence bancaire: {total_bank} total != {matched_bank} rapprochées + {suspense_bank} suspens",
                "severity": "critical"
            })
        
        # Validate accounting transactions
        if total_accounting != (matched_accounting + suspense_accounting):
            self.errors.append({
                "type": "transaction_count_mismatch",
                "message": f"Incohérence comptable: {total_accounting} total != {matched_accounting} rapprochées + {suspense_accounting} suspens",
                "severity": "critical"
            })
    
    def _generate_alerts(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame,
                        matches: List[Dict], suspense: List[Dict]):
        """
        Generate alerts as per Cahier des Charges:
        - Écart résiduel > 1% du solde → Investigation requise
        - Suspens > 10 transactions → Vérification manuelle
        - Temps de processing anormal → Notification
        """
        bank_total = bank_df['amount'].sum()
        
        # Calculate residual gap
        matched_total = sum([m.get('amount', 0) for m in matches])
        initial_gap = abs(bank_total - accounting_df['amount'].sum())
        residual_gap = initial_gap - abs(matched_total)
        
        # Alert 1: Residual gap > 1%
        if abs(residual_gap) > (abs(bank_total) * 0.01):
            self.alerts.append({
                "type": "high_residual_gap",
                "message": f"Écart résiduel élevé: {residual_gap:.3f} TND (> 1% du solde)",
                "severity": "high",
                "action_required": "Investigation requise"
            })
        
        # Alert 2: High suspense count
        if len(suspense) > 10:
            self.alerts.append({
                "type": "high_suspense_count",
                "message": f"{len(suspense)} transactions en suspens (> 10)",
                "severity": "medium",
                "action_required": "Vérification manuelle recommandée"
            })
        
        # Alert 3: Low match rate
        match_rate = len(matches) / max(len(bank_df), len(accounting_df)) if max(len(bank_df), len(accounting_df)) > 0 else 0
        if match_rate < 0.7:
            self.alerts.append({
                "type": "low_match_rate",
                "message": f"Taux de rapprochement faible: {match_rate*100:.1f}% (< 70%)",
                "severity": "medium",
                "action_required": "Vérifier la qualité des données"
            })
