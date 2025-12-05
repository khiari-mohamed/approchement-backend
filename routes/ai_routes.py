from fastapi import APIRouter, HTTPException
from models import AIRequest, CategoryRequest, PCNRequest
from services.ai_assistant import compare_labels, categorize_transaction, validate_pcn_account, suggest_account_mapping
from utils.logger import log_ai_call
from datetime import datetime

router = APIRouter()

@router.post("/ai/similarity")
async def get_label_similarity(request: AIRequest):
    """Compare similarity between two transaction labels"""
    try:
        result = compare_labels(request.label1, request.label2)
        score = result.get("score", 0.0) if isinstance(result, dict) else result
        return {
            "label1": request.label1,
            "label2": request.label2,
            "similarity": score,
            "confidence": "high" if score > 0.8 else "medium" if score > 0.6 else "low",
            "fallback": result.get("fallback", False) if isinstance(result, dict) else False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI similarity check failed: {str(e)}")

@router.post("/ai/categorize")
async def categorize_transaction_endpoint(request: CategoryRequest):
    """Categorize a transaction description"""
    try:
        result = categorize_transaction(request.description)
        return {
            "description": request.description,
            "category": result.get("category", "AUTRE"),
            "confidence": result.get("confidence", 0.0),
            "suggestions": {
                "FRAIS_BANCAIRE": "Bank fees and commissions",
                "VIREMENT_RECU": "Incoming wire transfer",
                "VIREMENT_EMIS": "Outgoing wire transfer",
                "CHEQUE": "Check payment",
                "REMISE_CHEQUE": "Check deposit",
                "PRELEVEMENT": "Direct debit",
                "CARTE_BANCAIRE": "Card payment",
                "AUTRE": "Other transaction"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI categorization failed: {str(e)}")

@router.post("/ai/validate-pcn")
async def validate_pcn_endpoint(request: PCNRequest):
    """Validate a PCN account code"""
    try:
        result = validate_pcn_account(request.account_code)
        return {
            "accountCode": request.account_code,
            "valid": result.get("valid", False),
            "confidence": result.get("confidence", 0.0),
            "pcnInfo": {
                "class1": "Capital and reserves (10xxxx)",
                "class2": "Fixed assets (2xxxxx)",
                "class3": "Inventory (3xxxxx)",
                "class4": "Third parties (4xxxxx)",
                "class5": "Financial accounts (5xxxxx)",
                "class6": "Expenses (6xxxxx)",
                "class7": "Revenue (7xxxxx)"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PCN validation failed: {str(e)}")

@router.post("/ai/suggest-account")
async def suggest_account_endpoint(description: str, amount: float):
    """Suggest PCN account for a transaction"""
    try:
        result = suggest_account_mapping(description, amount)
        return {
            "description": description,
            "amount": amount,
            "suggestedAccount": result.get("account", "580000"),
            "confidence": result.get("confidence", 0.0),
            "commonAccounts": {
                "512000": "Bank account",
                "627000": "Bank fees",
                "411000": "Customers",
                "401000": "Suppliers",
                "580000": "Suspense account",
                "658000": "Other financial expenses"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Account suggestion failed: {str(e)}")

@router.get("/ai/health")
async def ai_health_check():
    """Check AI service health"""
    try:
        # Test AI with simple request
        test_result = compare_labels("test", "test")
        return {
            "status": "healthy",
            "aiEnabled": test_result.get("success", False) if isinstance(test_result, dict) else test_result is not None,
            "testScore": test_result.get("score") if isinstance(test_result, dict) else test_result,
            "services": {
                "similarity": "available",
                "categorization": "available",
                "pcnValidation": "available",
                "accountSuggestion": "available"
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "aiEnabled": False,
            "error": str(e),
            "services": {
                "similarity": "unavailable",
                "categorization": "unavailable", 
                "pcnValidation": "unavailable",
                "accountSuggestion": "unavailable"
            }
        }

@router.get("/ai/metrics")
async def get_ai_performance_metrics():
    """Get AI performance metrics for monitoring dashboard (Cahier des Charges)"""
    from services.ai_assistant import get_ai_metrics
    
    try:
        metrics = get_ai_metrics()
        return {
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI metrics: {str(e)}")