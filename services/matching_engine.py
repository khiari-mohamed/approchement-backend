import pandas as pd
from rapidfuzz import fuzz
from typing import List, Dict, Tuple
import uuid
import time
from datetime import datetime, timedelta
from models import *
from services.ai_assistant import compare_labels, categorize_transaction
from services.validation_service import ValidationService
from services.gap_calculator import GapCalculator
from utils.logger import log_matching_step

class ReconciliationEngine:
    def __init__(self, rules: ReconciliationRules = None):
        self.rules = rules or ReconciliationRules()
        self.match_counter = 0
        self.validator = ValidationService()
        self.gap_calculator = GapCalculator()
        self.start_time = None
        self.processing_metrics = {}
    
    def reconcile(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame) -> ReconciliationResult:
        """Main reconciliation process with 5 tiers + validation + gap calculation"""
        self.start_time = time.time()
        log_matching_step("reconciliation_start", {"bank_rows": len(bank_df), "acc_rows": len(accounting_df)})
        
        # Normalize data
        bank_df = self._normalize_dataframe(bank_df)
        accounting_df = self._normalize_dataframe(accounting_df)
        
        # Calculate totals
        bank_total = bank_df['amount'].sum()
        accounting_total = accounting_df['amount'].sum()
        initial_gap = abs(bank_total - accounting_total)
        
        matches = []
        used_bank_ids = set()
        used_accounting_ids = set()
        ai_assisted_count = 0
        
        # Tier 1: Exact matches
        exact_matches = self._find_exact_matches(bank_df, accounting_df)
        self._update_used_ids(exact_matches, used_bank_ids, used_accounting_ids)
        matches.extend(exact_matches)
        
        # Tier 2: Fuzzy matches (strong)
        remaining_bank = bank_df[~bank_df['id'].isin(used_bank_ids)]
        remaining_accounting = accounting_df[~accounting_df['id'].isin(used_accounting_ids)]
        
        fuzzy_strong = self._find_fuzzy_matches(remaining_bank, remaining_accounting, strong=True)
        self._update_used_ids(fuzzy_strong, used_bank_ids, used_accounting_ids)
        matches.extend(fuzzy_strong)
        
        # Tier 3: AI-assisted matches
        if self.rules.enable_ai_assistance:
            remaining_bank = bank_df[~bank_df['id'].isin(used_bank_ids)]
            remaining_accounting = accounting_df[~accounting_df['id'].isin(used_accounting_ids)]
            
            ai_matches = self._find_ai_matches(remaining_bank, remaining_accounting)
            self._update_used_ids(ai_matches, used_bank_ids, used_accounting_ids)
            matches.extend(ai_matches)
            ai_assisted_count = len(ai_matches)
        
        # Tier 4: Weak fuzzy matches
        remaining_bank = bank_df[~bank_df['id'].isin(used_bank_ids)]
        remaining_accounting = accounting_df[~accounting_df['id'].isin(used_accounting_ids)]
        
        fuzzy_weak = self._find_fuzzy_matches(remaining_bank, remaining_accounting, strong=False)
        self._update_used_ids(fuzzy_weak, used_bank_ids, used_accounting_ids)
        matches.extend(fuzzy_weak)
        
        # Tier 5: Group matches
        if self.rules.enable_group_matching:
            remaining_bank = bank_df[~bank_df['id'].isin(used_bank_ids)]
            remaining_accounting = accounting_df[~accounting_df['id'].isin(used_accounting_ids)]
            
            group_matches = self._find_group_matches(remaining_bank, remaining_accounting)
            self._update_used_ids(group_matches, used_bank_ids, used_accounting_ids)
            matches.extend(group_matches)
        
        # Create suspense items
        suspense = self._create_suspense_items(bank_df, accounting_df, used_bank_ids, used_accounting_ids)
        
        # Calculate processing time
        processing_time = time.time() - self.start_time
        
        # Prepare data for validation and gap calculation
        matches_data = [{
            "id": m.id,
            "bank_tx_id": m.bank_tx.id,
            "accounting_tx_id": m.accounting_tx.id if m.accounting_tx else None,
            "amount": m.bank_tx.amount,
            "bank_amount": m.bank_tx.amount,
            "accounting_amount": m.accounting_tx.amount if m.accounting_tx else 0
        } for m in matches]
        
        suspense_data = [{
            "type": s.type,
            "transaction": {
                "id": s.transaction.id,
                "amount": s.transaction.amount
            },
            "amount": s.transaction.amount
        } for s in suspense]
        
        # Run validation (Cahier des Charges)
        validation_result = self.validator.validate_reconciliation(
            bank_df, accounting_df, matches_data, suspense_data
        )
        
        # Calculate gaps (Cahier des Charges formulas)
        gap_calculations = self.gap_calculator.calculate_all_gaps(
            bank_df, accounting_df, matches, suspense
        )
        
        # Validate gap coherence
        gap_coherence = self.gap_calculator.validate_gap_coherence()
        
        # Store processing metrics
        self.processing_metrics = {
            "processing_time": processing_time,
            "validation_result": validation_result,
            "gap_calculations": gap_calculations,
            "gap_coherence": gap_coherence,
            "manual_interventions": len([m for m in matches if m.status == MatchStatus.MATCHED]),
            "match_accuracy": len([m for m in matches if m.score >= 0.9]) / len(matches) if matches else 0
        }
        
        # Create enhanced summary with gap calculations
        summary = ReconciliationSummary(
            bank_total=gap_calculations["bank_total"],
            accounting_total=gap_calculations["accounting_total"],
            matched_count=gap_calculations["matched_count"],
            suspense_count=gap_calculations["suspense_count"],
            initial_gap=gap_calculations["initial_gap"],
            residual_gap=gap_calculations["residual_gap"],
            coverage_ratio=gap_calculations["coverage_ratio"],
            opening_balance=gap_calculations["bank_total"],
            ai_assisted_matches=ai_assisted_count
        )
        
        log_matching_step("reconciliation_complete", {
            "matches": len(matches),
            "suspense": len(suspense),
            "coverage": f"{gap_calculations['coverage_ratio']:.2%}",
            "processing_time": f"{processing_time:.2f}s",
            "validation_passed": validation_result["valid"],
            "gap_balanced": gap_calculations["is_balanced"]
        })
        
        result = ReconciliationResult(
            summary=summary,
            matches=matches,
            suspense=suspense
        )
        
        # Attach metadata for persistence
        result.metadata = {
            "validation": validation_result,
            "gap_calculations": gap_calculations,
            "gap_coherence": gap_coherence,
            "processing_metrics": self.processing_metrics,
            "gap_report": self.gap_calculator.generate_gap_report()
        }
        
        return result
    
    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize CSV data"""
        df = df.copy()
        
        if 'id' not in df.columns:
            df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce').dt.date
        
        if 'amount' in df.columns:
            df['amount'] = df['amount'].astype(str).str.replace(',', '').str.replace(' ', '')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        if 'description' in df.columns:
            df['description'] = df['description'].fillna('').astype(str).str.strip()
        
        return df.dropna(subset=['date', 'amount'])
    
    def _find_exact_matches(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame) -> List[Match]:
        """Tier 1: Exact amount + date + high label similarity"""
        matches = []
        
        for _, bank_row in bank_df.iterrows():
            candidates = accounting_df[
                (abs(accounting_df['amount'] - bank_row['amount']) <= self.rules.amount_tolerance)
            ]
            
            for _, acc_row in candidates.iterrows():
                date_diff = abs((bank_row['date'] - acc_row['date']).days)
                if date_diff <= self.rules.date_tolerance_days:
                    similarity = fuzz.token_sort_ratio(bank_row['description'], acc_row['description'])
                    if similarity >= self.rules.label_similarity_threshold:
                        match = self._create_match(bank_row, acc_row, similarity/100, MatchRule.EXACT)
                        matches.append(match)
                        break
        
        return matches
    
    def _find_fuzzy_matches(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame, strong: bool = True) -> List[Match]:
        """Tier 2/4: Fuzzy matching with configurable thresholds"""
        matches = []
        used_acc_ids = set()
        
        date_tolerance = self.rules.fuzzy_date_tolerance_days if strong else self.rules.weak_date_tolerance_days
        label_threshold = self.rules.fuzzy_label_threshold if strong else self.rules.weak_label_threshold
        rule = MatchRule.FUZZY_STRONG if strong else MatchRule.FUZZY_WEAK
        
        for _, bank_row in bank_df.iterrows():
            best_match = None
            best_score = 0
            
            candidates = accounting_df[
                (abs(accounting_df['amount'] - bank_row['amount']) <= self.rules.amount_tolerance) &
                (~accounting_df['id'].isin(used_acc_ids))
            ]
            
            for _, acc_row in candidates.iterrows():
                date_diff = abs((bank_row['date'] - acc_row['date']).days)
                if date_diff <= date_tolerance:
                    similarity = fuzz.token_sort_ratio(bank_row['description'], acc_row['description'])
                    if similarity >= label_threshold:
                        score = self._calculate_composite_score(bank_row, acc_row, similarity)
                        if score > best_score:
                            best_score = score
                            best_match = acc_row
            
            if best_match is not None and best_score >= 0.6:
                match = self._create_match(bank_row, best_match, best_score, rule)
                matches.append(match)
                used_acc_ids.add(best_match['id'])
        
        return matches
    
    def _find_ai_matches(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame) -> List[Match]:
        """Tier 3: AI-assisted matching with fallback to fuzzy"""
        matches = []
        used_acc_ids = set()
        
        for _, bank_row in bank_df.iterrows():
            best_match = None
            best_score = 0
            
            candidates = accounting_df[
                (abs(accounting_df['amount'] - bank_row['amount']) <= self.rules.amount_tolerance * 2) &
                (~accounting_df['id'].isin(used_acc_ids))
            ]
            
            for _, acc_row in candidates.iterrows():
                date_diff = abs((bank_row['date'] - acc_row['date']).days)
                if date_diff <= self.rules.weak_date_tolerance_days:
                    # Try AI first, fallback to fuzzy if AI fails
                    ai_result = compare_labels(bank_row['description'], acc_row['description'])
                    
                    if isinstance(ai_result, dict):
                        ai_similarity = ai_result.get('score', 0.0)
                        # If AI failed (fallback=True), use fuzzy matching instead
                        if ai_result.get('fallback', False):
                            ai_similarity = fuzz.token_sort_ratio(bank_row['description'], acc_row['description']) / 100
                    else:
                        ai_similarity = float(ai_result) if ai_result else 0.0
                    
                    if ai_similarity >= 0.7:  # AI threshold
                        score = self._calculate_ai_score(bank_row, acc_row, ai_similarity, date_diff)
                        if score > best_score:
                            best_score = score
                            best_match = acc_row
            
            if best_match is not None and best_score >= 0.65:
                match = self._create_match(bank_row, best_match, best_score, MatchRule.AI_ASSISTED)
                match.ai_confidence = best_score
                matches.append(match)
                used_acc_ids.add(best_match['id'])
        
        return matches
    
    def _find_group_matches(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame) -> List[Match]:
        """Tier 5: Group matching (1-to-N)"""
        matches = []
        used_acc_ids = set()
        
        for _, bank_row in bank_df.iterrows():
            candidates = accounting_df[
                (~accounting_df['id'].isin(used_acc_ids))
            ].head(self.rules.max_group_size * 2)  # Limit search space
            
            best_group = self._find_best_group_combination(
                bank_row['amount'], 
                candidates,
                self.rules.max_group_size,
                self.rules.amount_tolerance
            )
            
            if not best_group.empty and len(best_group) > 1:
                match = Match(
                    id=str(uuid.uuid4()),
                    bank_tx=self._row_to_transaction(bank_row),
                    accounting_txs=[self._row_to_transaction(row) for _, row in best_group.iterrows()],
                    score=0.8,
                    rule=MatchRule.GROUP,
                    status=MatchStatus.MATCHED,
                    recon_id=f"RG{self.match_counter:06d}"
                )
                matches.append(match)
                used_acc_ids.update(best_group['id'].tolist())
                self.match_counter += 1
        
        return matches
    
    def _create_suspense_items(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame, 
                             used_bank_ids: set, used_acc_ids: set) -> List[SuspenseItem]:
        """Create suspense items for unmatched transactions"""
        suspense = []
        
        # Unmatched bank transactions
        unmatched_bank = bank_df[~bank_df['id'].isin(used_bank_ids)]
        
        # Only categorize if AI is enabled and we have a reasonable number of items
        # Limit to first 100 items to avoid quota issues (with rate limiting, this is safe)
        categorize_with_ai = self.rules.enable_ai_assistance and len(unmatched_bank) <= 100
        
        for _, row in unmatched_bank.iterrows():
            if categorize_with_ai:
                category_result = categorize_transaction(row['description'])
                suggested_category = category_result.get("category")
                ai_confidence = category_result.get("confidence")
            else:
                suggested_category = None
                ai_confidence = None
            
            suspense.append(SuspenseItem(
                transaction=self._row_to_transaction(row),
                type="bank",
                reason="No matching accounting entry found",
                suggested_category=suggested_category,
                ai_confidence=ai_confidence
            ))
        
        # Unmatched accounting transactions
        unmatched_acc = accounting_df[~accounting_df['id'].isin(used_acc_ids)]
        for _, row in unmatched_acc.iterrows():
            suspense.append(SuspenseItem(
                transaction=self._row_to_transaction(row),
                type="accounting",
                reason="No matching bank entry found"
            ))
        
        return suspense
    
    def _create_match(self, bank_row, acc_row, score: float, rule: MatchRule) -> Match:
        """Create a match object"""
        self.match_counter += 1
        return Match(
            id=str(uuid.uuid4()),
            bank_tx=self._row_to_transaction(bank_row),
            accounting_tx=self._row_to_transaction(acc_row),
            score=score,
            rule=rule,
            status=MatchStatus.MATCHED,
            recon_id=f"R{self.match_counter:06d}"
        )
    
    def _calculate_composite_score(self, bank_row, acc_row, similarity: float) -> float:
        """Calculate weighted composite score"""
        amount_score = 1 - (abs(bank_row['amount'] - acc_row['amount']) / max(abs(bank_row['amount']), 1))
        date_score = max(0, 1 - abs((bank_row['date'] - acc_row['date']).days) / 7)
        label_score = similarity / 100
        
        return 0.5 * amount_score + 0.2 * date_score + 0.3 * label_score
    
    def _calculate_ai_score(self, bank_row, acc_row, ai_similarity: float, date_diff: int) -> float:
        """Calculate AI-assisted score"""
        amount_score = 1 - (abs(bank_row['amount'] - acc_row['amount']) / max(abs(bank_row['amount']), 1))
        date_score = max(0, 1 - date_diff / 7)
        
        return 0.4 * amount_score + 0.1 * date_score + 0.5 * ai_similarity
    
    def _find_best_group_combination(self, target_amount: float, candidates: pd.DataFrame, 
                                   max_size: int, tolerance: float) -> pd.DataFrame:
        """Find best combination of entries that sum to target amount"""
        candidates = candidates.sort_values('amount')
        
        for size in range(2, min(max_size + 1, len(candidates) + 1)):
            for i in range(len(candidates) - size + 1):
                group = candidates.iloc[i:i+size]
                group_sum = group['amount'].sum()
                if abs(group_sum - target_amount) <= tolerance:
                    return group
        
        return pd.DataFrame()
    
    def _update_used_ids(self, matches: List[Match], used_bank_ids: set, used_acc_ids: set):
        """Update sets of used transaction IDs"""
        for match in matches:
            used_bank_ids.add(match.bank_tx.id)
            if match.accounting_tx:
                used_acc_ids.add(match.accounting_tx.id)
            if match.accounting_txs:
                used_acc_ids.update([tx.id for tx in match.accounting_txs])
    
    def _row_to_transaction(self, row) -> Transaction:
        """Convert DataFrame row to Transaction model"""
        return Transaction(
            id=str(row['id']),
            date=str(row['date']),
            amount=float(row['amount']),
            description=str(row.get('description', '')),
            currency=str(row.get('currency', 'TND')),
            account_code=str(row.get('account_code', '')) if 'account_code' in row else None
        )