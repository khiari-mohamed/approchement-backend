from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.upload_routes import router as upload_router
from routes.reconcile_routes import router as reconcile_router
from routes.ai_routes import router as ai_router
from routes.auth_routes import router as auth_router
from utils.logger import logger
import os

# Create storage directories
os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("storage/logs", exist_ok=True)
os.makedirs("storage/reports", exist_ok=True)

app = FastAPI(
    title="Rapprochement Bancaire API",
    description="Tunisian Bank Reconciliation System with AI Assistance",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(reconcile_router, prefix="/api", tags=["Reconciliation"])
app.include_router(ai_router, prefix="/api", tags=["AI Assistant"])

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Rapprochement Bancaire API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "CSV file upload and processing",
            "5-tier reconciliation engine",
            "AI-assisted matching",
            "Tunisian PCN validation",
            "Suspense account handling",
            "N° R (reconciliation numbers)"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "upload": "available",
            "reconciliation": "available",
            "ai_assistant": "available"
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Rapprochement Bancaire API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)