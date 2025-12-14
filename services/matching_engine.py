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
from services.tunisian_config import TunisianBankConfig
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
        
        # Add normalized transaction types
        bank_df['tx_type'] = bank_df['description'].apply(TunisianBankConfig.normalize_transaction_type)
        accounting_df['tx_type'] = accounting_df['description'].apply(TunisianBankConfig.normalize_transaction_type)
        
        # Calculate real balances (not sum of transactions)
        bank_total = self._calculate_bank_balance(bank_df)
        accounting_total = self._calculate_accounting_balance(accounting_df)
        initial_gap = bank_total - accounting_total
        
        matches = []
        used_bank_ids = set()
        used_accounting_ids = set()
        ai_assisted_count = 0
        
        # LEVEL 1: Exact matches (amount + date ±3 days + same sign)
        level1_matches = self._find_level1_matches(bank_df, accounting_df)
        self._update_used_ids(level1_matches, used_bank_ids, used_accounting_ids)
        matches.extend(level1_matches)
        print(f"DEBUG: Level 1 matched {len(level1_matches)} transactions")
        
        # LEVEL 2: Amount only + date tolerance = 5 days
        remaining_bank = bank_df[~bank_df['id'].isin(used_bank_ids)]
        remaining_accounting = accounting_df[~accounting_df['id'].isin(used_accounting_ids)]
        print(f"DEBUG: Level 2 - Remaining bank: {len(remaining_bank)}, accounting: {len(remaining_accounting)}")
        
        level2_matches = self._find_level2_matches(remaining_bank, remaining_accounting)
        self._update_used_ids(level2_matches, used_bank_ids, used_accounting_ids)
        matches.extend(level2_matches)
        print(f"DEBUG: Level 2 matched {len(level2_matches)} transactions")
        
        # LEVEL 3: Group matching (sum = sum)
        remaining_bank = bank_df[~bank_df['id'].isin(used_bank_ids)]
        remaining_accounting = accounting_df[~accounting_df['id'].isin(used_accounting_ids)]
        
        level3_matches = self._find_level3_group_matches(remaining_bank, remaining_accounting)
        self._update_used_ids(level3_matches, used_bank_ids, used_accounting_ids)
        matches.extend(level3_matches)
        
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
        """Normalize CSV data with Tunisian decimal format"""
        df = df.copy()
        
        if 'id' not in df.columns:
            df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        
        if 'date' in df.columns:
            # Keep as Timestamp for proper date arithmetic
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        
        if 'amount' in df.columns:
            # CRITIQUE : Format tunisien : 1.177.437,649 = 1177437.649
            df['amount'] = df['amount'].astype(str).apply(TunisianBankConfig.normalize_tunisian_amount)
        
        if 'description' in df.columns:
            df['description'] = df['description'].fillna('').astype(str).str.strip()
        
        # Garder toutes les lignes pour l'analyse
        return df
    
    def _find_exact_matches(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame) -> List[Match]:
        """Tier 1: Exact amount + date + high label similarity"""
        matches = []
        
        # N'essayer de matcher que les transactions non-soldes
        non_solde_bank = bank_df[~bank_df['description'].str.contains('SOLDE', case=False, na=False)]
        
        for _, bank_row in non_solde_bank.iterrows():
            # Recherche par montant exact (tolérance de 0.01 pour arrondis)
            candidates = accounting_df[
                (abs(accounting_df['amount'] - bank_row['amount']) <= 0.01)
            ]
            
            for _, acc_row in candidates.iterrows():
                # Tolérance de date plus grande (jusqu'à 7 jours)
                date_diff = abs((bank_row['date'] - acc_row['date']).days)
                if date_diff <= 7:  # Augmenté de 1 à 7 jours
                    # Similarité plus flexible
                    bank_desc = str(bank_row['description']).upper()
                    acc_desc = str(acc_row['description']).upper()
                    similarity = fuzz.token_sort_ratio(bank_desc, acc_desc)
                    
                    if similarity >= 60:  # Baissé de 80 à 60
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
        bank_date = pd.to_datetime(bank_row['date'])
        acc_date = pd.to_datetime(acc_row['date'])
        date_score = max(0, 1 - abs((bank_date - acc_date).days) / 7)
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
    
    def _find_level1_matches(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame) -> List[Match]:
        """LEVEL 1: Exact amount + date (±3 days) + same sign"""
        matches = []
        used_acc_ids = set()
        
        for _, bank_row in bank_df.iterrows():
            # Skip balance lines
            if 'SOLDE' in str(bank_row['description']).upper():
                continue
                
            candidates = accounting_df[
                (accounting_df['amount'] == bank_row['amount']) &  # Exact amount
                (accounting_df['amount'] != 0) &  # Not zero
                (~accounting_df['id'].isin(used_acc_ids))  # Not already matched
            ]
            
            for _, acc_row in candidates.iterrows():
                try:
                    # Handle both date and datetime objects
                    bank_date = bank_row['date']
                    acc_date = acc_row['date']
                    
                    # Convert to datetime if needed
                    if not isinstance(bank_date, (pd.Timestamp, datetime)):
                        bank_date = pd.to_datetime(bank_date)
                    if not isinstance(acc_date, (pd.Timestamp, datetime)):
                        acc_date = pd.to_datetime(acc_date)
                    
                    date_diff = abs((bank_date - acc_date).days)
                except:
                    date_diff = 999  # Set high to prevent matching on error
                    
                if date_diff <= 3:  # ±3 days
                    match = self._create_match(bank_row, acc_row, 1.0, MatchRule.EXACT)
                    matches.append(match)
                    used_acc_ids.add(acc_row['id'])
                    break  # Take first match
        
        return matches
    
    def _find_level2_matches(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame) -> List[Match]:
        """LEVEL 2: Amount only + date tolerance = 5 days"""
        matches = []
        used_acc_ids = set()
        
        for _, bank_row in bank_df.iterrows():
            # Skip balance lines
            if 'SOLDE' in str(bank_row['description']).upper():
                continue
            
            # Find candidates with exact amount match
            candidates = accounting_df[
                (accounting_df['amount'] == bank_row['amount']) &  # Exact amount
                (accounting_df['amount'] != 0) &
                (~accounting_df['id'].isin(used_acc_ids))
            ]
            
            if len(candidates) == 0:
                print(f"DEBUG L2: No candidates for {bank_row['description']} amount={bank_row['amount']}")
                continue
            
            for _, acc_row in candidates.iterrows():
                try:
                    bank_date = bank_row['date']
                    acc_date = acc_row['date']
                    
                    print(f"DEBUG L2: bank_date={bank_date} type={type(bank_date)}, acc_date={acc_date} type={type(acc_date)}")
                    
                    # Convert to Timestamp
                    if not isinstance(bank_date, pd.Timestamp):
                        bank_date = pd.Timestamp(bank_date)
                    if not isinstance(acc_date, pd.Timestamp):
                        acc_date = pd.Timestamp(acc_date)
                    
                    date_diff = abs((bank_date - acc_date).days)
                    print(f"DEBUG L2: {bank_row['description']} date_diff={date_diff}")
                except Exception as e:
                    print(f"DEBUG L2: ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                    date_diff = 999
                    
                if date_diff <= 5:  # ±5 days
                    match = self._create_match(bank_row, acc_row, 0.9, MatchRule.FUZZY_STRONG)
                    matches.append(match)
                    used_acc_ids.add(acc_row['id'])
                    print(f"DEBUG L2: ✅ MATCHED {bank_row['description']}")
                    break  # Take first match
        
        return matches
    
    def _find_level3_group_matches(self, bank_df: pd.DataFrame, accounting_df: pd.DataFrame) -> List[Match]:
        """LEVEL 3: Group matching (sum = sum)"""
        matches = []
        
        for _, bank_row in bank_df.iterrows():
            # Skip balance lines
            if 'SOLDE' in str(bank_row['description']).upper():
                continue
                
            bank_amount = bank_row['amount']
            bank_date = pd.to_datetime(bank_row['date'])
            
            # Look for groups of accounting entries that sum to bank amount
            # within ±5 days
            acc_dates = pd.to_datetime(accounting_df['date'])
            date_window = accounting_df[
                (abs((acc_dates - bank_date).dt.days) <= 5) &
                (accounting_df['amount'] != 0)
            ]
            
            if len(date_window) > 1:
                # Try different group sizes
                for group_size in range(2, min(10, len(date_window) + 1)):
                    for start_idx in range(len(date_window) - group_size + 1):
                        group = date_window.iloc[start_idx:start_idx + group_size]
                        group_sum = group['amount'].sum()
                        
                        if abs(group_sum - bank_amount) < 0.01:  # Exact sum match
                            # Create group match
                            bank_tx = self._row_to_transaction(bank_row)
                            acc_txs = [self._row_to_transaction(row) for _, row in group.iterrows()]
                            
                            match = Match(
                                id=str(uuid.uuid4()),
                                bank_tx=bank_tx,
                                accounting_txs=acc_txs,
                                score=0.8,
                                rule=MatchRule.GROUP,
                                status=MatchStatus.MATCHED
                            )
                            matches.append(match)
                            break
                    if matches and matches[-1].bank_tx.id == bank_row['id']:
                        break  # Found match for this bank row
        
        return matches
    
    def _calculate_bank_balance(self, bank_df: pd.DataFrame) -> float:
        """Calculate final bank balance from statement"""
        balance_rows = bank_df[bank_df['description'].str.contains('SOLDE', case=False, na=False)]
        
        if not balance_rows.empty:
            return float(balance_rows.iloc[-1]['amount'])
        else:
            non_balance = bank_df[~bank_df['description'].str.contains('SOLDE', case=False, na=False)]
            return float(non_balance['amount'].sum())
    
    def _calculate_accounting_balance(self, accounting_df: pd.DataFrame) -> float:
        """Calculate final accounting balance from ledger"""
        if 'solde_progressif' in accounting_df.columns:
            return float(accounting_df['solde_progressif'].iloc[-1])
        else:
            return float(accounting_df['amount'].sum())
    
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