import re
from rapidfuzz import fuzz
from typing import List, Tuple

class IntelligentMatcher:
    PATTERN_MAPPINGS = {
        r'REGLEMENT CHEQUE \d+': 'CHÈQUE',
        r'ENG/SIGNATURE \w+': 'COMMISSION BANCAIRE',
        r'PAIEMENT EFFET \d+': 'EFFET',
        r'VIREMENT.*': 'VIREMENT',
        r'EFFET IMPAYE \d+': 'EFFET IMPAYÉ',
        r'COMMISSION.*': 'FRAIS',
        r'DEBLOCAGE CREDIT.*': 'CRÉDIT',
        r'AGIOS.*': 'INTÉRÊTS',
    }
    
    KEYWORD_MAPPINGS = {
        'oxford': 'OXFORD',
        'mare': 'MARE',
        'mcc': 'MCC',
        'chammam': 'CHAMMAM',
        'virement': 'TRANSFERT',
        'cheque': 'CHÈQUE',
        'effet': 'EFFET',
        'impaye': 'IMPAYÉ',
        'commission': 'FRAIS',
        'agios': 'INTÉRÊTS',
    }
    
    @staticmethod
    def normalize_description(desc: str) -> str:
        if not desc:
            return ""
        
        desc = desc.upper()
        desc = re.sub(r'\d{8,}', '', desc)
        desc = re.sub(r'\b\d{6,}\b', '', desc)
        desc = re.sub(r'R\d{7}', '', desc)
        desc = re.sub(r'\d{8}', '', desc)
        
        stop_words = ['01 08', '02 08', 'REGLEMENT', 'PAIEMENT', 'VIREMENT', 'TN', 'BQ']
        for word in stop_words:
            desc = desc.replace(word, '')
        
        desc = ' '.join(desc.split())
        return desc.strip()
    
    @staticmethod
    def extract_keywords(desc: str) -> List[str]:
        desc = IntelligentMatcher.normalize_description(desc)
        stop_words = {'AU', 'ET', 'DE', 'LA', 'LE', 'DU', 'DES', 'LES', 'POUR', 'SUR'}
        words = desc.split()
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        return keywords
    
    @staticmethod
    def find_best_match(bank_desc: str, accounting_descs: List[str], 
                       amounts: List[float], bank_amount: float) -> Tuple[int, float]:
        if not accounting_descs:
            return -1, 0.0
        
        norm_bank = IntelligentMatcher.normalize_description(bank_desc)
        norm_accounting = [IntelligentMatcher.normalize_description(d) for d in accounting_descs]
        
        bank_keywords = IntelligentMatcher.extract_keywords(bank_desc)
        
        best_match_idx = -1
        best_score = 0.0
        
        for i, (acc_desc, acc_amount) in enumerate(zip(norm_accounting, amounts)):
            text_score = fuzz.token_sort_ratio(norm_bank, acc_desc) / 100
            amount_score = 1.0 if abs(acc_amount - bank_amount) < 0.01 else 0.0
            
            acc_keywords = IntelligentMatcher.extract_keywords(accounting_descs[i])
            keyword_score = len(set(bank_keywords) & set(acc_keywords)) / max(len(set(bank_keywords) | set(acc_keywords)), 1)
            
            composite_score = (text_score * 0.3) + (amount_score * 0.5) + (keyword_score * 0.2)
            
            if composite_score > best_score:
                best_score = composite_score
                best_match_idx = i
        
        return best_match_idx, best_score
