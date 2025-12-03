import logging
import json
from datetime import datetime
from config import LOG_DIR
import os

# Create logs directory
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOG_DIR}/reconciliation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('reconciliation')

def log_upload(filename: str, file_type: str, rows: int):
    """Log file upload"""
    logger.info(f"File uploaded: {filename} ({file_type}) - {rows} rows")

def log_matching_step(step: str, data: dict):
    """Log matching engine steps"""
    logger.info(f"Matching step: {step} - {json.dumps(data)}")

def log_ai_call(function: str, input_data: dict, result):
    """Log AI assistant calls"""
    logger.info(f"AI call: {function} - Input: {json.dumps(input_data)} - Result: {result}")

def log_error(error: str, context: dict = None):
    """Log errors"""
    context_str = json.dumps(context) if context else ""
    logger.error(f"Error: {error} - Context: {context_str}")

def log_reconciliation_complete(job_id: str, summary: dict):
    """Log reconciliation completion"""
    logger.info(f"Reconciliation complete: {job_id} - {json.dumps(summary)}")