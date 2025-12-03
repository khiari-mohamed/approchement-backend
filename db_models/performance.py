from sqlalchemy import Column, String, Integer, Float, JSON
from db_models.base import BaseModel

class PerformanceMetrics(BaseModel):
    """Performance metrics tracking for Cahier des Charges compliance"""
    __tablename__ = "performance_metrics"
    
    reconciliation_id = Column(String, nullable=False, unique=True)
    
    # Efficacité du matching
    auto_match_rate = Column(Float, default=0.0)  # Taux de matching automatique (%)
    avg_processing_time = Column(Float, default=0.0)  # Temps moyen de processing (seconds)
    manual_interventions = Column(Integer, default=0)  # Nombre d'interventions manuelles
    reconciliation_success_rate = Column(Float, default=0.0)  # Taux de réussite du rapprochement
    
    # Qualité des résultats
    validated_matches_accuracy = Column(Float, default=0.0)  # Exactitude des matches validés
    pcn_compliance_rate = Column(Float, default=0.0)  # Conformité PCN des écritures
    gap_calculation_precision = Column(Float, default=0.0)  # Précision des calculs d'écarts
    
    # AI Performance (Surveillance Gemini)
    ai_avg_response_time = Column(Float, default=0.0)  # Temps de réponse moyen (ms)
    ai_success_rate = Column(Float, default=0.0)  # Taux de succès des requêtes (%)
    ai_suggestion_quality = Column(Float, default=0.0)  # Qualité des suggestions (validation utilisateur)
    ai_hallucination_count = Column(Integer, default=0)  # Détection d'hallucinations
    ai_resource_usage = Column(JSON)  # Utilisation des ressources
    
    # Validation metrics
    duplicate_matches_found = Column(Integer, default=0)
    date_range_violations = Column(Integer, default=0)
    debit_credit_imbalances = Column(Integer, default=0)
    
    # Alertes
    alerts_generated = Column(JSON)  # List of alerts
    critical_errors = Column(Integer, default=0)
