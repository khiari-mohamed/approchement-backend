import google.generativeai as genai
from config import GEMINI_API_KEY, AI_CONFIG
from utils.logger import log_ai_call
import json
import time
from typing import Dict, Optional
from threading import Lock
from collections import deque

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(AI_CONFIG["model_name"])
else:
    model = None

# AI Performance tracking (Cahier des Charges)
ai_metrics = {
    "total_calls": 0,
    "successful_calls": 0,
    "failed_calls": 0,
    "total_response_time": 0,
    "hallucinations_detected": 0,
    "fallback_used": 0
}

# Rate limiting: 10 requests per minute for Gemini free tier
rate_limit_lock = Lock()
request_timestamps = deque(maxlen=10)
MAX_REQUESTS_PER_MINUTE = 8  # Conservative limit (10 is max, use 8 for safety)
MIN_REQUEST_INTERVAL = 60.0 / MAX_REQUESTS_PER_MINUTE  # ~7.5 seconds

def wait_for_rate_limit():
    """Enforce rate limiting to prevent quota errors"""
    with rate_limit_lock:
        current_time = time.time()
        
        # Remove timestamps older than 60 seconds
        while request_timestamps and current_time - request_timestamps[0] > 60:
            request_timestamps.popleft()
        
        # If we've hit the limit, wait
        if len(request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (current_time - request_timestamps[0]) + 1
            if sleep_time > 0:
                time.sleep(sleep_time)
                request_timestamps.clear()
        
        # Add current request timestamp
        request_timestamps.append(time.time())

def compare_labels(label1: str, label2: str) -> Dict:
    """Compare similarity between two transaction labels using AI with monitoring"""
    ai_metrics["total_calls"] += 1
    start_time = time.time()
    
    if not model:
        ai_metrics["fallback_used"] += 1
        return {"score": 0.0, "fallback": True, "response_time_ms": 0}
    
    # Rate limiting
    wait_for_rate_limit()
    
    prompt = f"""Compare similarity between these bank transaction labels:
Label A: "{label1}"
Label B: "{label2}"

Return only a number between 0 and 1 representing similarity.
Examples:
- "VIREMENT SALAIRE" vs "SALAIRE NOVEMBRE" = 0.85
- "CHEQUE 123456" vs "CHEQUE 654321" = 0.70
- "FRAIS BANCAIRE" vs "COMMISSION" = 0.60

Number only:"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": AI_CONFIG["temperature"],
                "max_output_tokens": 10
            },
            request_options={"timeout": 5}  # 5 second timeout as per Cahier des Charges
        )
        
        response_time = (time.time() - start_time) * 1000  # milliseconds
        ai_metrics["total_response_time"] += response_time
        
        score_text = response.text.strip()
        score = float(score_text)
        
        # Hallucination detection: score must be between 0 and 1
        if score < 0 or score > 1:
            ai_metrics["hallucinations_detected"] += 1
            score = max(0.0, min(1.0, score))
        
        ai_metrics["successful_calls"] += 1
        log_ai_call("compare_labels", {"label1": label1, "label2": label2}, score)
        
        return {
            "score": max(0.0, min(1.0, score)),
            "response_time_ms": int(response_time),
            "fallback": False,
            "success": True
        }
    except Exception as e:
        ai_metrics["failed_calls"] += 1
        ai_metrics["fallback_used"] += 1
        response_time = (time.time() - start_time) * 1000
        log_ai_call("compare_labels", {"error": str(e)}, 0.0)
        
        # Fallback to manual mode
        return {
            "score": 0.0,
            "response_time_ms": int(response_time),
            "fallback": True,
            "success": False,
            "error": str(e)
        }

def categorize_transaction(description: str) -> dict:
    """Categorize transaction into predefined categories with monitoring"""
    ai_metrics["total_calls"] += 1
    start_time = time.time()
    
    if not model:
        ai_metrics["fallback_used"] += 1
        return {"category": "AUTRE", "confidence": 0.0, "fallback": True}
    
    # Rate limiting
    wait_for_rate_limit()
    
    prompt = f"""Categorize this Tunisian bank transaction into ONE category:

Categories:
- FRAIS_BANCAIRE (bank fees, commissions)
- VIREMENT_RECU (incoming transfer)
- VIREMENT_EMIS (outgoing transfer)  
- CHEQUE (check payment)
- REMISE_CHEQUE (check deposit)
- PRELEVEMENT (direct debit)
- CARTE_BANCAIRE (card payment)
- AUTRE (other)

Transaction: "{description}"

Return JSON format: {{"category": "CATEGORY_NAME", "confidence": 0.85}}"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": AI_CONFIG["temperature"],
                "max_output_tokens": 30
            },
            request_options={"timeout": 5}
        )
        
        response_time = (time.time() - start_time) * 1000
        ai_metrics["total_response_time"] += response_time
        
        result = json.loads(response.text.strip())
        
        # Validate category is in allowed list
        valid_categories = ["FRAIS_BANCAIRE", "VIREMENT_RECU", "VIREMENT_EMIS", 
                          "CHEQUE", "REMISE_CHEQUE", "PRELEVEMENT", "CARTE_BANCAIRE", "AUTRE"]
        if result.get("category") not in valid_categories:
            ai_metrics["hallucinations_detected"] += 1
            result["category"] = "AUTRE"
        
        ai_metrics["successful_calls"] += 1
        result["response_time_ms"] = int(response_time)
        result["fallback"] = False
        log_ai_call("categorize_transaction", {"description": description}, result)
        return result
    except Exception as e:
        ai_metrics["failed_calls"] += 1
        ai_metrics["fallback_used"] += 1
        response_time = (time.time() - start_time) * 1000
        log_ai_call("categorize_transaction", {"error": str(e)}, {"category": "AUTRE", "confidence": 0.0})
        return {"category": "AUTRE", "confidence": 0.0, "fallback": True, "response_time_ms": int(response_time)}

def validate_pcn_account(account_code: str) -> dict:
    """Validate PCN account code for Tunisia"""
    if not model:
        return {"valid": False, "confidence": 0.0}
    
    prompt = f"""Is "{account_code}" a valid Tunisian PCN account code?

PCN Structure:
- Class 1: Capital accounts (10xxxx)
- Class 2: Fixed assets (2xxxxx)
- Class 3: Inventory (3xxxxx)
- Class 4: Third parties (4xxxxx)
- Class 5: Financial accounts (5xxxxx)
- Class 6: Expenses (6xxxxx)
- Class 7: Revenue (7xxxxx)

Return JSON: {{"valid": true/false, "confidence": 0.90}}"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": AI_CONFIG["temperature"],
                "max_output_tokens": 20
            }
        )
        
        result = json.loads(response.text.strip())
        log_ai_call("validate_pcn_account", {"account_code": account_code}, result)
        return result
    except Exception as e:
        log_ai_call("validate_pcn_account", {"error": str(e)}, {"valid": False, "confidence": 0.0})
        return {"valid": False, "confidence": 0.0}

def suggest_account_mapping(description: str, amount: float) -> dict:
    """Suggest PCN account for a transaction with monitoring"""
    ai_metrics["total_calls"] += 1
    start_time = time.time()
    
    if not model:
        ai_metrics["fallback_used"] += 1
        return {"account": "580000", "confidence": 0.0, "fallback": True}
    
    # Rate limiting
    wait_for_rate_limit()
    
    prompt = f"""Suggest Tunisian PCN account for this transaction:
Description: "{description}"
Amount: {amount} TND

Common accounts:
- 512000: Bank account
- 627000: Bank fees
- 411000: Customers
- 401000: Suppliers
- 580000: Suspense account

Return JSON: {{"account": "512000", "confidence": 0.80}}"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": AI_CONFIG["temperature"],
                "max_output_tokens": 25
            },
            request_options={"timeout": 5}
        )
        
        response_time = (time.time() - start_time) * 1000
        ai_metrics["total_response_time"] += response_time
        
        result = json.loads(response.text.strip())
        
        # Validate account format (6 digits)
        if not result.get("account", "").isdigit() or len(result.get("account", "")) != 6:
            ai_metrics["hallucinations_detected"] += 1
            result["account"] = "580000"  # Fallback to suspense
        
        ai_metrics["successful_calls"] += 1
        result["response_time_ms"] = int(response_time)
        result["fallback"] = False
        log_ai_call("suggest_account_mapping", {"description": description, "amount": amount}, result)
        return result
    except Exception as e:
        ai_metrics["failed_calls"] += 1
        ai_metrics["fallback_used"] += 1
        response_time = (time.time() - start_time) * 1000
        log_ai_call("suggest_account_mapping", {"error": str(e)}, {"account": "580000", "confidence": 0.0})
        return {"account": "580000", "confidence": 0.0, "fallback": True, "response_time_ms": int(response_time)}

def get_ai_metrics() -> Dict:
    """Get AI performance metrics for monitoring dashboard"""
    avg_response_time = (ai_metrics["total_response_time"] / ai_metrics["total_calls"]) if ai_metrics["total_calls"] > 0 else 0
    success_rate = (ai_metrics["successful_calls"] / ai_metrics["total_calls"] * 100) if ai_metrics["total_calls"] > 0 else 0
    
    return {
        "total_calls": ai_metrics["total_calls"],
        "successful_calls": ai_metrics["successful_calls"],
        "failed_calls": ai_metrics["failed_calls"],
        "success_rate": round(success_rate, 2),
        "avg_response_time_ms": round(avg_response_time, 2),
        "hallucinations_detected": ai_metrics["hallucinations_detected"],
        "fallback_used": ai_metrics["fallback_used"],
        "status": "healthy" if success_rate > 90 else "degraded" if success_rate > 70 else "critical"
    }

def reset_ai_metrics():
    """Reset AI metrics (for testing or new session)"""
    global ai_metrics
    ai_metrics = {
        "total_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "total_response_time": 0,
        "hallucinations_detected": 0,
        "fallback_used": 0
    }