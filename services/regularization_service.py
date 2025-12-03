"""
Service for generating accounting regularization entries (écritures de régularisation)
Follows Tunisian accounting standards and PCN
"""

from typing import List, Dict
from datetime import datetime
from services.pcn_service import PCNService
import uuid

class RegularizationEntry:
    """Represents a single accounting entry line"""
    def __init__(self, account_code: str, account_name: str, debit: float = 0.0, 
                 credit: float = 0.0, description: str = ""):
        self.account_code = account_code
        self.account_name = account_name
        self.debit = debit
        self.credit = credit
        self.description = description
    
    def to_dict(self) -> dict:
        return {
            "account_code": self.account_code,
            "account_name": self.account_name,
            "debit": round(self.debit, 3),
            "credit": round(self.credit, 3),
            "description": self.description
        }

class RegularizationJournal:
    """Represents a complete journal entry"""
    def __init__(self, entry_number: str, date: str, description: str):
        self.entry_number = entry_number
        self.date = date
        self.description = description
        self.lines: List[RegularizationEntry] = []
    
    def add_line(self, line: RegularizationEntry):
        self.lines.append(line)
    
    def is_balanced(self) -> bool:
        """Check if debit equals credit"""
        total_debit = sum(line.debit for line in self.lines)
        total_credit = sum(line.credit for line in self.lines)
        return abs(total_debit - total_credit) < 0.01
    
    def to_dict(self) -> dict:
        return {
            "entry_number": self.entry_number,
            "date": self.date,
            "description": self.description,
            "lines": [line.to_dict() for line in self.lines],
            "total_debit": round(sum(line.debit for line in self.lines), 3),
            "total_credit": round(sum(line.credit for line in self.lines), 3),
            "is_balanced": self.is_balanced()
        }

class RegularizationService:
    """Production-ready service for generating regularization entries"""
    
    def __init__(self):
        self.pcn = PCNService()
        self.entry_counter = 1
    
    def generate_entries_for_suspense(self, suspense_items: List[dict], 
                                     reconciliation_date: str = None) -> List[RegularizationJournal]:
        """Generate all regularization entries for suspense items"""
        if not reconciliation_date:
            reconciliation_date = datetime.now().strftime("%Y-%m-%d")
        
        entries = []
        
        for item in suspense_items:
            if item["type"] == "bank":
                # Bank suspense: transaction in bank but not in accounting
                entry = self._generate_bank_suspense_entry(item, reconciliation_date)
                if entry:
                    entries.append(entry)
            else:
                # Accounting suspense: transaction in accounting but not in bank
                entry = self._generate_accounting_suspense_entry(item, reconciliation_date)
                if entry:
                    entries.append(entry)
        
        return entries
    
    def _generate_bank_suspense_entry(self, item: dict, date: str) -> RegularizationJournal:
        """Generate entry for bank transaction not in accounting"""
        transaction = item["transaction"]
        amount = abs(transaction["amount"])
        description = transaction["description"]
        # Handle both dict and object access
        if isinstance(item, dict):
            category = item.get("suggested_category", "AUTRE")
        else:
            category = getattr(item, "suggested_category", "AUTRE")
        
        # Get appropriate PCN account based on category
        account_info = self.pcn.get_account_for_category(category)
        expense_account = account_info["account_code"]
        expense_name = account_info["name"]
        
        # Bank account (always 512000)
        bank_account = "512000"
        bank_name = "Banques"
        
        # Create journal entry
        entry_number = f"REG{self.entry_counter:06d}"
        self.entry_counter += 1
        
        journal = RegularizationJournal(
            entry_number=entry_number,
            date=date,
            description=f"Régularisation: {description[:50]}"
        )
        
        # Determine debit/credit based on amount sign
        if transaction["amount"] < 0:
            # Negative amount = expense/payment
            # Debit: Expense account
            # Credit: Bank account
            journal.add_line(RegularizationEntry(
                account_code=expense_account,
                account_name=expense_name,
                debit=amount,
                credit=0.0,
                description=description
            ))
            journal.add_line(RegularizationEntry(
                account_code=bank_account,
                account_name=bank_name,
                debit=0.0,
                credit=amount,
                description=description
            ))
        else:
            # Positive amount = income/receipt
            # Debit: Bank account
            # Credit: Income/Suspense account
            journal.add_line(RegularizationEntry(
                account_code=bank_account,
                account_name=bank_name,
                debit=amount,
                credit=0.0,
                description=description
            ))
            journal.add_line(RegularizationEntry(
                account_code=expense_account,
                account_name=expense_name,
                debit=0.0,
                credit=amount,
                description=description
            ))
        
        return journal
    
    def _generate_accounting_suspense_entry(self, item: dict, date: str) -> RegularizationJournal:
        """Generate entry for accounting transaction not in bank"""
        transaction = item["transaction"]
        amount = abs(transaction["amount"])
        description = transaction["description"]
        
        # These are typically checks issued but not cashed, or transfers not yet processed
        # Use check suspense account or supplier account
        
        entry_number = f"REG{self.entry_counter:06d}"
        self.entry_counter += 1
        
        journal = RegularizationJournal(
            entry_number=entry_number,
            date=date,
            description=f"Régularisation: {description[:50]}"
        )
        
        # For accounting suspense, typically:
        # - Checks issued not cashed: 511200 (Chèques à encaisser)
        # - Transfers pending: 471000 (Suspense)
        
        if "cheque" in description.lower() or "chèque" in description.lower():
            suspense_account = "511200"
            suspense_name = "Caisse - Chèques à encaisser"
        else:
            suspense_account = "471000"
            suspense_name = "Comptes transitoires ou d'attente"
        
        bank_account = "512000"
        bank_name = "Banques"
        
        if transaction["amount"] < 0:
            # Payment not yet processed
            journal.add_line(RegularizationEntry(
                account_code=suspense_account,
                account_name=suspense_name,
                debit=amount,
                credit=0.0,
                description=description
            ))
            journal.add_line(RegularizationEntry(
                account_code=bank_account,
                account_name=bank_name,
                debit=0.0,
                credit=amount,
                description=description
            ))
        else:
            # Receipt not yet processed
            journal.add_line(RegularizationEntry(
                account_code=bank_account,
                account_name=bank_name,
                debit=amount,
                credit=0.0,
                description=description
            ))
            journal.add_line(RegularizationEntry(
                account_code=suspense_account,
                account_name=suspense_name,
                debit=0.0,
                credit=amount,
                description=description
            ))
        
        return journal
    
    def generate_bank_fee_entry(self, amount: float, description: str, date: str) -> RegularizationJournal:
        """Generate specific entry for bank fees"""
        entry_number = f"REG{self.entry_counter:06d}"
        self.entry_counter += 1
        
        journal = RegularizationJournal(
            entry_number=entry_number,
            date=date,
            description=f"Frais bancaires: {description}"
        )
        
        # Debit: 627100 (Bank fees)
        # Credit: 512000 (Bank)
        journal.add_line(RegularizationEntry(
            account_code="627100",
            account_name="Commissions bancaires",
            debit=abs(amount),
            credit=0.0,
            description=description
        ))
        journal.add_line(RegularizationEntry(
            account_code="512000",
            account_name="Banques",
            debit=0.0,
            credit=abs(amount),
            description=description
        ))
        
        return journal
    
    def generate_interest_entry(self, amount: float, description: str, date: str, 
                               is_credit: bool = True) -> RegularizationJournal:
        """Generate entry for bank interest"""
        entry_number = f"REG{self.entry_counter:06d}"
        self.entry_counter += 1
        
        journal = RegularizationJournal(
            entry_number=entry_number,
            date=date,
            description=f"Intérêts bancaires: {description}"
        )
        
        if is_credit:
            # Credit interest (income)
            # Debit: 512000 (Bank)
            # Credit: 768000 (Interest income)
            journal.add_line(RegularizationEntry(
                account_code="512000",
                account_name="Banques",
                debit=abs(amount),
                credit=0.0,
                description=description
            ))
            journal.add_line(RegularizationEntry(
                account_code="768000",
                account_name="Intérêts et produits assimilés",
                debit=0.0,
                credit=abs(amount),
                description=description
            ))
        else:
            # Debit interest (expense)
            # Debit: 627200 (Interest expense)
            # Credit: 512000 (Bank)
            journal.add_line(RegularizationEntry(
                account_code="627200",
                account_name="Intérêts bancaires",
                debit=abs(amount),
                credit=0.0,
                description=description
            ))
            journal.add_line(RegularizationEntry(
                account_code="512000",
                account_name="Banques",
                debit=0.0,
                credit=abs(amount),
                description=description
            ))
        
        return journal
    
    def validate_entries(self, entries: List[RegularizationJournal]) -> dict:
        """Validate all entries are balanced and use valid PCN accounts"""
        validation_result = {
            "valid": True,
            "total_entries": len(entries),
            "balanced_entries": 0,
            "unbalanced_entries": 0,
            "invalid_accounts": [],
            "errors": []
        }
        
        for entry in entries:
            # Check balance
            if entry.is_balanced():
                validation_result["balanced_entries"] += 1
            else:
                validation_result["unbalanced_entries"] += 1
                validation_result["errors"].append(
                    f"Entry {entry.entry_number} is not balanced"
                )
                validation_result["valid"] = False
            
            # Check PCN accounts
            for line in entry.lines:
                account_validation = self.pcn.validate_account(line.account_code)
                if not account_validation["valid"]:
                    validation_result["invalid_accounts"].append({
                        "entry": entry.entry_number,
                        "account": line.account_code,
                        "error": account_validation.get("message")
                    })
                    validation_result["valid"] = False
        
        return validation_result
    
    def export_to_accounting_format(self, entries: List[RegularizationJournal]) -> List[dict]:
        """Export entries in standard accounting import format"""
        export_data = []
        
        for entry in entries:
            for line in entry.lines:
                export_data.append({
                    "journal_code": "OD",  # Operations Diverses
                    "entry_number": entry.entry_number,
                    "entry_date": entry.date,
                    "account_code": line.account_code,
                    "account_name": line.account_name,
                    "description": line.description,
                    "debit": line.debit,
                    "credit": line.credit,
                    "currency": "TND",
                    "piece_number": entry.entry_number
                })
        
        return export_data
