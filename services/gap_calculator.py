"""
Real-time Gap Calculator - Cahier des Charges Implementation
Implements all required formulas for gap calculation
"""

from typing import Dict, List
import pandas as pd

class GapCalculator:
    """
    Production-ready gap calculator implementing Cahier des Charges formulas:
    - Écart initial = Solde bancaire - Solde comptable
    - Écart expliqué = Σ(Suspens bancaires) - Σ(Suspens comptables)
    - Écart résiduel = Écart initial - Écart expliqué
    - Taux de couverture = (Écart expliqué / Écart initial) × 100
    """
    
    def __init__(self):
        self.calculations = {}
    
    def calculate_all_gaps(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame,
                          matches: List[Dict], suspense: List[Dict]) -> Dict:
        """
        Calculate all gap metrics in real-time
        """
        # Calculate totals
        bank_total = float(bank_df['amount'].sum())
        accounting_total = float(accounting_df['amount'].sum())
        
        # Formula 1: Écart initial = Solde bancaire - Solde comptable
        initial_gap = bank_total - accounting_total
        
        # Calculate suspense totals (handle both dict and SuspenseItem objects)
        bank_suspense_total = sum([
            float(s.transaction.amount if hasattr(s, 'transaction') else s['transaction']['amount'])
            for s in suspense 
            if (s.type if hasattr(s, 'type') else s.get('type')) == 'bank'
        ])
        
        accounting_suspense_total = sum([
            float(s.transaction.amount if hasattr(s, 'transaction') else s['transaction']['amount'])
            for s in suspense 
            if (s.type if hasattr(s, 'type') else s.get('type')) == 'accounting'
        ])
        
        # Formula 2: Écart expliqué = Σ(Suspens bancaires) - Σ(Suspens comptables)
        explained_gap = bank_suspense_total - accounting_suspense_total
        
        # Formula 3: Écart résiduel = Écart initial - Écart expliqué
        residual_gap = initial_gap - explained_gap
        
        # Formula 4: Taux de couverture = (Écart expliqué / Écart initial) × 100
        if abs(initial_gap) > 0.01:
            coverage_percentage = (abs(explained_gap) / abs(initial_gap)) * 100
        else:
            coverage_percentage = 100.0 if abs(residual_gap) < 0.01 else 0.0
        
        # Calculate matched amount
        matched_amount = sum([
            float(m.get('bank_tx', {}).get('amount', 0))
            for m in matches
        ])
        
        # Calculate coverage ratio (matched / total)
        coverage_ratio = len(matches) / max(len(bank_df), len(accounting_df)) if max(len(bank_df), len(accounting_df)) > 0 else 0.0
        
        self.calculations = {
            # Basic totals
            "bank_total": round(bank_total, 3),
            "accounting_total": round(accounting_total, 3),
            
            # Gap calculations (Cahier des Charges formulas)
            "initial_gap": round(initial_gap, 3),
            "explained_gap": round(explained_gap, 3),
            "residual_gap": round(residual_gap, 3),
            "coverage_percentage": round(coverage_percentage, 2),
            
            # Suspense details
            "bank_suspense_total": round(bank_suspense_total, 3),
            "accounting_suspense_total": round(accounting_suspense_total, 3),
            
            # Match statistics
            "matched_count": len(matches),
            "suspense_count": len(suspense),
            "matched_amount": round(matched_amount, 3),
            "coverage_ratio": round(coverage_ratio, 4),
            
            # Validation flags
            "is_balanced": abs(residual_gap) < 0.01,
            "requires_investigation": abs(residual_gap) > (abs(bank_total) * 0.01),
            "high_suspense": len(suspense) > 10
        }
        
        return self.calculations
    
    def validate_gap_coherence(self) -> Dict:
        """
        Validate mathematical coherence of gap calculations
        """
        if not self.calculations:
            return {"valid": False, "error": "No calculations performed"}
        
        # Verify: Écart résiduel = Écart initial - Écart expliqué
        calculated_residual = self.calculations["initial_gap"] - self.calculations["explained_gap"]
        actual_residual = self.calculations["residual_gap"]
        
        coherent = abs(calculated_residual - actual_residual) < 0.01
        
        return {
            "valid": coherent,
            "calculated_residual": round(calculated_residual, 3),
            "actual_residual": round(actual_residual, 3),
            "difference": round(abs(calculated_residual - actual_residual), 3),
            "is_balanced": self.calculations["is_balanced"],
            "requires_investigation": self.calculations["requires_investigation"]
        }
    
    def get_gap_breakdown(self) -> Dict:
        """
        Get detailed breakdown of gap components
        """
        return {
            "initial_state": {
                "bank_total": self.calculations.get("bank_total", 0),
                "accounting_total": self.calculations.get("accounting_total", 0),
                "initial_gap": self.calculations.get("initial_gap", 0)
            },
            "suspense_analysis": {
                "bank_suspense": self.calculations.get("bank_suspense_total", 0),
                "accounting_suspense": self.calculations.get("accounting_suspense_total", 0),
                "explained_gap": self.calculations.get("explained_gap", 0)
            },
            "final_state": {
                "residual_gap": self.calculations.get("residual_gap", 0),
                "coverage_percentage": self.calculations.get("coverage_percentage", 0),
                "is_balanced": self.calculations.get("is_balanced", False)
            },
            "performance": {
                "matched_count": self.calculations.get("matched_count", 0),
                "suspense_count": self.calculations.get("suspense_count", 0),
                "coverage_ratio": self.calculations.get("coverage_ratio", 0)
            }
        }
    
    def generate_gap_report(self) -> str:
        """
        Generate human-readable gap analysis report
        """
        if not self.calculations:
            return "Aucun calcul disponible"
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║         ANALYSE DES ÉCARTS - RAPPROCHEMENT BANCAIRE          ║
╚══════════════════════════════════════════════════════════════╝

📊 ÉTAT INITIAL:
   Solde Bancaire:     {self.calculations['bank_total']:>12.3f} TND
   Solde Comptable:    {self.calculations['accounting_total']:>12.3f} TND
   ─────────────────────────────────────────────────
   Écart Initial:      {self.calculations['initial_gap']:>12.3f} TND

📋 ANALYSE DES SUSPENS:
   Suspens Bancaires:  {self.calculations['bank_suspense_total']:>12.3f} TND
   Suspens Comptables: {self.calculations['accounting_suspense_total']:>12.3f} TND
   ─────────────────────────────────────────────────
   Écart Expliqué:     {self.calculations['explained_gap']:>12.3f} TND

✅ RÉSULTAT FINAL:
   Écart Résiduel:     {self.calculations['residual_gap']:>12.3f} TND
   Taux de Couverture: {self.calculations['coverage_percentage']:>12.2f} %
   
   Statut: {'✓ ÉQUILIBRÉ' if self.calculations['is_balanced'] else '⚠ DÉSÉQUILIBRÉ'}
   {'⚠ Investigation requise (écart > 1%)' if self.calculations['requires_investigation'] else ''}

📈 STATISTIQUES:
   Transactions Rapprochées: {self.calculations['matched_count']}
   Transactions en Suspens:  {self.calculations['suspense_count']}
   Taux de Matching:         {self.calculations['coverage_ratio']*100:.1f}%

╚══════════════════════════════════════════════════════════════╝
"""
        return report
