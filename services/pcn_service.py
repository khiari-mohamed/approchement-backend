"""
Tunisian PCN (Plan Comptable National) Service
Complete reference data for Tunisian accounting chart of accounts
"""

class PCNService:
    """Production-ready PCN validation and mapping service"""
    
    # Complete Tunisian PCN Chart of Accounts
    PCN_ACCOUNTS = {
        # Class 1: Capital Accounts
        "101000": {"name": "Capital social", "type": "capital"},
        "106000": {"name": "Réserves", "type": "capital"},
        "110000": {"name": "Report à nouveau", "type": "capital"},
        "120000": {"name": "Résultat de l'exercice", "type": "capital"},
        "130000": {"name": "Subventions d'investissement", "type": "capital"},
        "140000": {"name": "Provisions réglementées", "type": "capital"},
        "150000": {"name": "Emprunts et dettes assimilées", "type": "capital"},
        "160000": {"name": "Comptes de liaison", "type": "capital"},
        
        # Class 2: Fixed Assets
        "201000": {"name": "Frais d'établissement", "type": "immobilisation"},
        "210000": {"name": "Immobilisations incorporelles", "type": "immobilisation"},
        "220000": {"name": "Terrains", "type": "immobilisation"},
        "230000": {"name": "Constructions", "type": "immobilisation"},
        "240000": {"name": "Matériel et outillage", "type": "immobilisation"},
        "250000": {"name": "Mobilier et matériel de bureau", "type": "immobilisation"},
        "260000": {"name": "Matériel de transport", "type": "immobilisation"},
        "270000": {"name": "Immobilisations financières", "type": "immobilisation"},
        "280000": {"name": "Amortissements", "type": "immobilisation"},
        "290000": {"name": "Provisions pour dépréciation", "type": "immobilisation"},
        
        # Class 3: Inventory
        "310000": {"name": "Matières premières", "type": "stock"},
        "320000": {"name": "Autres approvisionnements", "type": "stock"},
        "330000": {"name": "En-cours de production", "type": "stock"},
        "340000": {"name": "Produits intermédiaires", "type": "stock"},
        "350000": {"name": "Produits finis", "type": "stock"},
        "360000": {"name": "Produits résiduels", "type": "stock"},
        "370000": {"name": "Stocks de marchandises", "type": "stock"},
        "390000": {"name": "Provisions pour dépréciation des stocks", "type": "stock"},
        
        # Class 4: Third Parties (Most used in reconciliation)
        "401000": {"name": "Fournisseurs", "type": "tiers"},
        "402000": {"name": "Fournisseurs - Effets à payer", "type": "tiers"},
        "403000": {"name": "Fournisseurs - Retenues de garantie", "type": "tiers"},
        "408000": {"name": "Fournisseurs - Factures non parvenues", "type": "tiers"},
        "409000": {"name": "Fournisseurs débiteurs", "type": "tiers"},
        "411000": {"name": "Clients", "type": "tiers"},
        "412000": {"name": "Clients - Effets à recevoir", "type": "tiers"},
        "413000": {"name": "Clients - Retenues de garantie", "type": "tiers"},
        "416000": {"name": "Clients douteux", "type": "tiers"},
        "418000": {"name": "Clients - Produits à recevoir", "type": "tiers"},
        "419000": {"name": "Clients créditeurs", "type": "tiers"},
        "421000": {"name": "Personnel - Rémunérations dues", "type": "tiers"},
        "422000": {"name": "Personnel - Œuvres sociales", "type": "tiers"},
        "425000": {"name": "Personnel - Avances et acomptes", "type": "tiers"},
        "431000": {"name": "Sécurité sociale", "type": "tiers"},
        "432000": {"name": "Autres organismes sociaux", "type": "tiers"},
        "441000": {"name": "État - Impôts sur les bénéfices", "type": "tiers"},
        "442000": {"name": "État - Autres impôts et taxes", "type": "tiers"},
        "443000": {"name": "État - TVA facturée", "type": "tiers"},
        "445000": {"name": "État - TVA récupérable", "type": "tiers"},
        "447000": {"name": "État - Autres comptes débiteurs", "type": "tiers"},
        "448000": {"name": "État - Autres comptes créditeurs", "type": "tiers"},
        "451000": {"name": "Groupe et associés", "type": "tiers"},
        "455000": {"name": "Associés - Comptes courants", "type": "tiers"},
        "456000": {"name": "Associés - Capital à libérer", "type": "tiers"},
        "457000": {"name": "Associés - Dividendes à payer", "type": "tiers"},
        "461000": {"name": "Créditeurs divers", "type": "tiers"},
        "462000": {"name": "Débiteurs divers", "type": "tiers"},
        "471000": {"name": "Comptes transitoires ou d'attente", "type": "tiers"},
        "475000": {"name": "Comptes de régularisation - Actif", "type": "tiers"},
        "476000": {"name": "Comptes de régularisation - Passif", "type": "tiers"},
        "490000": {"name": "Provisions pour dépréciation des comptes de tiers", "type": "tiers"},
        
        # Class 5: Financial Accounts (Critical for bank reconciliation)
        "511100": {"name": "Caisse - Espèces", "type": "tresorerie"},
        "511200": {"name": "Caisse - Chèques à encaisser", "type": "tresorerie"},
        "511300": {"name": "Caisse - Effets à encaisser", "type": "tresorerie"},
        "512000": {"name": "Banques", "type": "tresorerie"},
        "513000": {"name": "Comptes chèques postaux", "type": "tresorerie"},
        "514000": {"name": "Trésor", "type": "tresorerie"},
        "515000": {"name": "Régies d'avances et accréditifs", "type": "tresorerie"},
        "516000": {"name": "Virements internes", "type": "tresorerie"},
        "517000": {"name": "Autres organismes financiers", "type": "tresorerie"},
        "520000": {"name": "Instruments de trésorerie", "type": "tresorerie"},
        "530000": {"name": "Cautions et dépôts versés", "type": "tresorerie"},
        "540000": {"name": "Valeurs mobilières de placement", "type": "tresorerie"},
        "580000": {"name": "Virements internes", "type": "tresorerie"},
        "590000": {"name": "Provisions pour dépréciation des comptes financiers", "type": "tresorerie"},
        
        # Class 6: Expenses (Used in regularization entries)
        "601000": {"name": "Achats de matières premières", "type": "charge"},
        "602000": {"name": "Achats d'autres approvisionnements", "type": "charge"},
        "604000": {"name": "Achats de marchandises", "type": "charge"},
        "605000": {"name": "Achats de matériel, équipements et travaux", "type": "charge"},
        "606000": {"name": "Achats non stockés", "type": "charge"},
        "607000": {"name": "Achats de services", "type": "charge"},
        "608000": {"name": "Frais accessoires d'achat", "type": "charge"},
        "609000": {"name": "Rabais, remises et ristournes obtenus", "type": "charge"},
        "611000": {"name": "Sous-traitance générale", "type": "charge"},
        "612000": {"name": "Redevances de crédit-bail", "type": "charge"},
        "613000": {"name": "Locations", "type": "charge"},
        "614000": {"name": "Charges locatives et de copropriété", "type": "charge"},
        "615000": {"name": "Entretien et réparations", "type": "charge"},
        "616000": {"name": "Primes d'assurances", "type": "charge"},
        "617000": {"name": "Études et recherches", "type": "charge"},
        "618000": {"name": "Documentation et divers", "type": "charge"},
        "621000": {"name": "Personnel extérieur à l'entreprise", "type": "charge"},
        "622000": {"name": "Rémunérations du personnel", "type": "charge"},
        "623000": {"name": "Charges sociales", "type": "charge"},
        "624000": {"name": "Formation du personnel", "type": "charge"},
        "625000": {"name": "Frais de déplacement", "type": "charge"},
        "626000": {"name": "Frais postaux et de télécommunications", "type": "charge"},
        "627000": {"name": "Services bancaires", "type": "charge"},  # BANK FEES
        "627100": {"name": "Commissions bancaires", "type": "charge"},  # BANK COMMISSIONS
        "627200": {"name": "Intérêts bancaires", "type": "charge"},  # BANK INTEREST
        "628000": {"name": "Divers", "type": "charge"},
        "631000": {"name": "Impôts et taxes directs", "type": "charge"},
        "632000": {"name": "Impôts et taxes indirects", "type": "charge"},
        "641000": {"name": "Charges de personnel", "type": "charge"},
        "651000": {"name": "Redevances pour concessions, brevets", "type": "charge"},
        "661000": {"name": "Charges d'intérêts", "type": "charge"},
        "671000": {"name": "Charges exceptionnelles", "type": "charge"},
        "681000": {"name": "Dotations aux amortissements", "type": "charge"},
        "691000": {"name": "Impôts sur les bénéfices", "type": "charge"},
        
        # Class 7: Revenue (Used in regularization entries)
        "701000": {"name": "Ventes de produits finis", "type": "produit"},
        "702000": {"name": "Ventes de produits intermédiaires", "type": "produit"},
        "703000": {"name": "Ventes de produits résiduels", "type": "produit"},
        "704000": {"name": "Ventes de marchandises", "type": "produit"},
        "705000": {"name": "Ventes de travaux", "type": "produit"},
        "706000": {"name": "Ventes d'études", "type": "produit"},
        "707000": {"name": "Ventes de prestations de services", "type": "produit"},
        "708000": {"name": "Produits des activités annexes", "type": "produit"},
        "709000": {"name": "Rabais, remises et ristournes accordés", "type": "produit"},
        "721000": {"name": "Production immobilisée", "type": "produit"},
        "731000": {"name": "Variation des stocks", "type": "produit"},
        "741000": {"name": "Subventions d'exploitation", "type": "produit"},
        "751000": {"name": "Autres produits d'exploitation", "type": "produit"},
        "761000": {"name": "Produits financiers", "type": "produit"},
        "768000": {"name": "Intérêts et produits assimilés", "type": "produit"},  # BANK INTEREST INCOME
        "771000": {"name": "Produits exceptionnels", "type": "produit"},
        "781000": {"name": "Reprises sur amortissements", "type": "produit"},
    }
    
    # Transaction category to PCN account mapping
    CATEGORY_TO_ACCOUNT = {
        "FRAIS_BANCAIRE": "627100",  # Bank fees
        "COMMISSION_BANCAIRE": "627100",  # Bank commission
        "INTERET_DEBITEUR": "627200",  # Debit interest
        "INTERET_CREDITEUR": "768000",  # Credit interest
        "VIREMENT_RECU": "471000",  # Incoming transfer (suspense)
        "VIREMENT_EMIS": "401000",  # Outgoing transfer (suppliers)
        "CHEQUE": "511200",  # Check
        "REMISE_CHEQUE": "511200",  # Check deposit
        "PRELEVEMENT": "401000",  # Direct debit
        "CARTE_BANCAIRE": "512000",  # Card payment
        "AUTRE": "471000",  # Other (suspense)
    }
    
    @classmethod
    def validate_account(cls, account_code: str) -> dict:
        """Validate if account code exists in PCN"""
        account_code = str(account_code).strip()
        
        if account_code in cls.PCN_ACCOUNTS:
            return {
                "valid": True,
                "account_code": account_code,
                "name": cls.PCN_ACCOUNTS[account_code]["name"],
                "type": cls.PCN_ACCOUNTS[account_code]["type"],
                "confidence": 1.0
            }
        
        # Try partial match (first 3-4 digits)
        for code, details in cls.PCN_ACCOUNTS.items():
            if code.startswith(account_code[:3]):
                return {
                    "valid": False,
                    "suggested_account": code,
                    "suggested_name": details["name"],
                    "confidence": 0.7,
                    "message": f"Account {account_code} not found. Did you mean {code}?"
                }
        
        return {
            "valid": False,
            "confidence": 0.0,
            "message": f"Account {account_code} not found in PCN"
        }
    
    @classmethod
    def get_account_for_category(cls, category: str) -> dict:
        """Get PCN account for transaction category"""
        account_code = cls.CATEGORY_TO_ACCOUNT.get(category, "471000")
        
        if account_code in cls.PCN_ACCOUNTS:
            return {
                "account_code": account_code,
                "name": cls.PCN_ACCOUNTS[account_code]["name"],
                "type": cls.PCN_ACCOUNTS[account_code]["type"],
                "confidence": 0.9
            }
        
        return {
            "account_code": "471000",
            "name": "Comptes transitoires ou d'attente",
            "type": "tiers",
            "confidence": 0.5
        }
    
    @classmethod
    def suggest_account_for_description(cls, description: str, amount: float) -> dict:
        """Suggest PCN account based on transaction description"""
        description_lower = description.lower()
        
        # Bank fees patterns
        if any(word in description_lower for word in ["frais", "commission", "agios", "tenue de compte"]):
            return cls.get_account_for_category("FRAIS_BANCAIRE")
        
        # Interest patterns
        if "interet" in description_lower or "intérêt" in description_lower:
            if amount > 0:
                return cls.get_account_for_category("INTERET_CREDITEUR")
            else:
                return cls.get_account_for_category("INTERET_DEBITEUR")
        
        # Transfer patterns
        if any(word in description_lower for word in ["virement", "vir", "transfer"]):
            if amount > 0:
                return cls.get_account_for_category("VIREMENT_RECU")
            else:
                return cls.get_account_for_category("VIREMENT_EMIS")
        
        # Check patterns
        if any(word in description_lower for word in ["cheque", "chèque", "chq"]):
            return cls.get_account_for_category("CHEQUE")
        
        # Card patterns
        if any(word in description_lower for word in ["carte", "card", "cb"]):
            return cls.get_account_for_category("CARTE_BANCAIRE")
        
        # Direct debit patterns
        if any(word in description_lower for word in ["prelevement", "prélèvement", "prlv"]):
            return cls.get_account_for_category("PRELEVEMENT")
        
        # Default to suspense account
        return cls.get_account_for_category("AUTRE")
    
    @classmethod
    def get_all_accounts(cls) -> dict:
        """Get all PCN accounts"""
        return cls.PCN_ACCOUNTS
    
    @classmethod
    def get_accounts_by_type(cls, account_type: str) -> dict:
        """Get accounts filtered by type"""
        return {
            code: details 
            for code, details in cls.PCN_ACCOUNTS.items() 
            if details["type"] == account_type
        }
