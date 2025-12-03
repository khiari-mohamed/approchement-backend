from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from services.file_processor import FileProcessor
from services.database_service import DatabaseService
from utils.logger import log_upload, log_error
from config import UPLOAD_DIR
from routes.auth_routes import get_current_user
from db_models.users import User
from database import get_db

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.csv', '.pdf', '.xlsx', '.xls', '.png', '.jpg', '.jpeg']

router = APIRouter()
file_processor = FileProcessor()

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/bank")
async def upload_bank_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process bank file (CSV, PDF, Excel, Image)"""
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Format non supporté. Formats acceptés: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    try:
        upload_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{upload_id}_{file.filename}")
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process file (supports CSV, PDF, Excel, Images)
        df = file_processor.process_file(file_path, "bank")
        
        # Validate CSV structure
        validation = file_processor.validate_csv_structure(df, "bank")
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid CSV structure: {validation['errors']}")
        
        # Save to database
        db_service = DatabaseService(db)
        file_record = db_service.save_uploaded_file(
            filename=file.filename,
            file_path=file_path,
            file_type="bank",
            rows_count=len(df),
            user_id="system"
        )
        
        # Save processed CSV for reconciliation
        processed_path = os.path.join(UPLOAD_DIR, f"{file_record.id}_processed.csv")
        df.to_csv(processed_path, index=False)
        
        # Update file path to processed version
        file_record.file_path = processed_path
        db.commit()
        
        log_upload(file.filename, "bank", len(df))
        
        return {
            "uploadId": file_record.id,
            "filename": file.filename,
            "rowsCount": len(df),
            "preview": df.head(3).to_dict('records') if len(df) > 0 else [],
            "validation": validation
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_error(f"Bank file upload failed: {str(e)}\n{error_trace}", {"filename": file.filename})
        print(f"ERROR uploading bank file: {str(e)}")
        print(error_trace)
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.post("/upload/accounting")
async def upload_accounting_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process accounting file (CSV, PDF, Excel, Image)"""
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Format non supporté. Formats acceptés: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    try:
        upload_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{upload_id}_{file.filename}")
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process file (supports CSV, PDF, Excel, Images)
        df = file_processor.process_file(file_path, "accounting")
        
        # Validate CSV structure
        validation = file_processor.validate_csv_structure(df, "accounting")
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid CSV structure: {validation['errors']}")
        
        # Save to database
        db_service = DatabaseService(db)
        file_record = db_service.save_uploaded_file(
            filename=file.filename,
            file_path=file_path,
            file_type="accounting",
            rows_count=len(df),
            user_id="system"
        )
        
        # Save processed CSV for reconciliation
        processed_path = os.path.join(UPLOAD_DIR, f"{file_record.id}_processed.csv")
        df.to_csv(processed_path, index=False)
        
        # Update file path to processed version
        file_record.file_path = processed_path
        db.commit()
        
        log_upload(file.filename, "accounting", len(df))
        
        return {
            "uploadId": file_record.id,
            "filename": file.filename,
            "rowsCount": len(df),
            "preview": df.head(3).to_dict('records') if len(df) > 0 else [],
            "validation": validation
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_error(f"Accounting file upload failed: {str(e)}\n{error_trace}", {"filename": file.filename})
        print(f"ERROR uploading accounting file: {str(e)}")
        print(error_trace)
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.get("/uploads/{upload_id}")
async def get_upload_info(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """Get upload information"""
    db_service = DatabaseService(db)
    file_record = db_service.get_uploaded_file(upload_id)
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return {
        "uploadId": file_record.id,
        "filename": file_record.filename,
        "fileType": file_record.file_type,
        "rowsCount": file_record.rows_count,
        "uploadedAt": file_record.uploaded_at.isoformat(),
        "status": file_record.status
    }

@router.get("/uploads")
async def list_uploads(
    db: Session = Depends(get_db)
):
    """List all uploads"""
    # This would need a method in DatabaseService to list files by user
    return {"message": "List uploads endpoint - implement in DatabaseService"}