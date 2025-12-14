"""
Tunisian Banking Configuration
Dynamic configuration for Tunisian bank formats
"""

class TunisianBankConfig:
    """Configuration for Tunisian banking formats"""
    
    DATE_FORMATS = [
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%d%m%Y',
        '%d %m %Y',
    ]
    
    BALANCE_KEYWORDS = [
        'SOLDE',
        'SOLDE AU',
        'SOLDE DU',
        'BALANCE',
        'FINAL BALANCE'
    ]
    
    TRANSACTION_TYPES = {
        'CHEQUE': ['REGLEMENT CHEQUE', 'CHEQUE', 'CHQ', 'CH'],
        'VIREMENT': ['VIREMENT', 'TRANSFERT', 'VIR', 'VIRM', 'VERSEMENT'],
        'PRELEVEMENT': ['PRELEVEMENT', 'PRLV', 'RETRAIT'],
        'CARTE': ['CARTE BANCAIRE', 'CB', 'CLC', 'TPAY', 'PAY', 'POS'],
        'TPE': ['TPE', 'REGLEMENT TPE', 'RÉG TPE'],
        'COMMISSION': ['ENG/SIGNATURE', 'COMMISSION', 'FRAIS', 'FRAIS DIVERS'],
        'EFFET': ['EFFET', 'BILLET', 'LETTRE'],
        'CREDIT': ['CREDIT', 'PRÊT', 'LOAN'],
        'DEBIT': ['DEBIT', 'RETRAIT']
    }
    
    @classmethod
    def normalize_transaction_type(cls, description: str) -> str:
        """Normalize transaction description to standard Tunisian types"""
        desc_upper = str(description).upper()
        
        for tx_type, keywords in cls.TRANSACTION_TYPES.items():
            for keyword in keywords:
                if keyword.upper() in desc_upper:
                    return tx_type
        
        return 'OTHER'
    
    @classmethod
    def normalize_tunisian_amount(cls, amount_str) -> float:
        """Convert Tunisian amount format (1.234,56 or 630.298,000) to float (1234.56 or 630298.0)"""
        if not isinstance(amount_str, str):
            amount_str = str(amount_str)
        
        amount_str = amount_str.replace(' ', '').replace('TND', '').replace('DT', '').replace('None', '')
        
        if not amount_str or amount_str == '':
            return 0.0
        
        # Tunisian format: dots are thousands separators, comma is decimal separator
        # Remove all dots (thousands separators), then replace comma with dot
        amount_str = amount_str.replace('.', '').replace(',', '.')
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
