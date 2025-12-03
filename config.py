import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reconciliation.db")

# Authentication
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Directories
UPLOAD_DIR = "storage/uploads"
REPORT_DIR = "storage/reports"
LOG_DIR = "storage/logs"

# Reconciliation Rules
DEFAULT_RULES = {
    "amount_tolerance": 0.01,
    "date_tolerance_days": 1,
    "fuzzy_date_tolerance_days": 3,
    "weak_date_tolerance_days": 7,
    "label_similarity_threshold": 0.95,
    "fuzzy_label_threshold": 0.80,
    "weak_label_threshold": 0.60,
    "enable_group_matching": True,
    "max_group_size": 5
}

# AI Settings
AI_CONFIG = {
    "temperature": 0.1,
    "max_output_tokens": 50,
    "model_name": "gemini-2.0-flash-exp"
}