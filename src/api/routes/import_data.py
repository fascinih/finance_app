"""
Data Import Routes for Finance App API.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.models import get_db, ImportBatch
from src.api.middleware.auth import get_current_user
from src.config import settings

router = APIRouter()


class ImportBatchResponse(BaseModel):
    """Import batch response model."""
    id: str
    filename: str
    source_type: str
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    file_size: Optional[int]

    class Config:
        from_attributes = True


class ImportStatus(BaseModel):
    """Import status model."""
    batch_id: str
    status: str
    progress: float
    message: str
    errors: List[str] = []


@router.post("/upload", response_model=ImportBatchResponse)
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Upload a file for import processing.
    
    Supported formats:
    - CSV: Comma-separated values
    - OFX: Open Financial Exchange
    - XLSX/XLS: Excel spreadsheets
    """
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Validate source type
    valid_source_types = ["csv", "ofx", "xlsx", "xls", "api"]
    if source_type not in valid_source_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source type. Must be one of: {', '.join(valid_source_types)}"
        )
    
    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Generate unique filename
    batch_id = uuid.uuid4()
    safe_filename = f"{batch_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_FOLDER, safe_filename)
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create import batch record
    import_batch = ImportBatch(
        id=batch_id,
        filename=file.filename,
        source_type=source_type,
        status="uploaded",
        file_size=file_size,
        file_hash=None,  # TODO: Calculate file hash
        import_settings={
            "original_filename": file.filename,
            "file_path": file_path,
            "uploaded_by": user.get("id"),
            "upload_timestamp": datetime.utcnow().isoformat()
        }
    )
    
    db.add(import_batch)
    db.commit()
    db.refresh(import_batch)
    
    # TODO: Trigger async processing
    # For now, return the batch info
    
    return ImportBatchResponse(
        id=str(import_batch.id),
        filename=import_batch.filename,
        source_type=import_batch.source_type,
        total_records=import_batch.total_records,
        processed_records=import_batch.processed_records,
        successful_records=import_batch.successful_records,
        failed_records=import_batch.failed_records,
        status=import_batch.status,
        started_at=import_batch.started_at,
        completed_at=import_batch.completed_at,
        file_size=import_batch.file_size
    )


@router.get("/batches", response_model=List[ImportBatchResponse])
async def get_import_batches(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """
    Get list of import batches.
    """
    
    batches = db.query(ImportBatch).order_by(
        ImportBatch.started_at.desc()
    ).offset(offset).limit(limit).all()
    
    return [
        ImportBatchResponse(
            id=str(batch.id),
            filename=batch.filename,
            source_type=batch.source_type,
            total_records=batch.total_records,
            processed_records=batch.processed_records,
            successful_records=batch.successful_records,
            failed_records=batch.failed_records,
            status=batch.status,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            file_size=batch.file_size
        )
        for batch in batches
    ]


@router.get("/batches/{batch_id}", response_model=ImportBatchResponse)
async def get_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get specific import batch details.
    """
    
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid batch ID format")
    
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_uuid).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    
    return ImportBatchResponse(
        id=str(batch.id),
        filename=batch.filename,
        source_type=batch.source_type,
        total_records=batch.total_records,
        processed_records=batch.processed_records,
        successful_records=batch.successful_records,
        failed_records=batch.failed_records,
        status=batch.status,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        file_size=batch.file_size
    )


@router.post("/batches/{batch_id}/process")
async def process_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Start processing an uploaded import batch.
    """
    
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid batch ID format")
    
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_uuid).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    
    if batch.status != "uploaded":
        raise HTTPException(
            status_code=400, 
            detail=f"Batch cannot be processed. Current status: {batch.status}"
        )
    
    # Update status to processing
    batch.status = "processing"
    batch.started_at = datetime.utcnow()
    db.commit()
    
    # TODO: Implement actual file processing
    # This would typically be done asynchronously using Celery or similar
    
    return {
        "message": "Import processing started",
        "batch_id": batch_id,
        "status": "processing"
    }


@router.get("/batches/{batch_id}/status", response_model=ImportStatus)
async def get_import_status(
    batch_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get real-time import processing status.
    """
    
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid batch ID format")
    
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_uuid).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    
    # Calculate progress
    progress = 0.0
    if batch.total_records > 0:
        progress = (batch.processed_records / batch.total_records) * 100
    
    # Determine message
    message = "Import not started"
    if batch.status == "processing":
        message = f"Processing... {batch.processed_records}/{batch.total_records} records"
    elif batch.status == "completed":
        message = f"Completed. {batch.successful_records} successful, {batch.failed_records} failed"
    elif batch.status == "failed":
        message = "Import failed"
    
    # Get errors from error_log
    errors = []
    if batch.error_log:
        errors = batch.error_log.get("errors", [])
    
    return ImportStatus(
        batch_id=batch_id,
        status=batch.status,
        progress=progress,
        message=message,
        errors=errors[:10]  # Limit to first 10 errors
    )


@router.delete("/batches/{batch_id}")
async def delete_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Delete an import batch and its associated file.
    """
    
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid batch ID format")
    
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_uuid).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    
    # Don't allow deletion of processing batches
    if batch.status == "processing":
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete batch while processing"
        )
    
    # Delete associated file if it exists
    if batch.import_settings and "file_path" in batch.import_settings:
        file_path = batch.import_settings["file_path"]
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                # Log error but don't fail the deletion
                pass
    
    # Delete batch record
    db.delete(batch)
    db.commit()
    
    return {"message": "Import batch deleted successfully"}


@router.get("/templates/csv")
async def get_csv_template():
    """
    Download CSV template for transaction import.
    """
    
    template_content = """date,amount,description,type,category,counterpart_name,location,notes
2024-01-15,-50.00,Supermercado ABC,debit,Alimentação,Supermercado ABC,São Paulo,Compras mensais
2024-01-15,3000.00,Salário Janeiro,credit,Salário,Empresa XYZ,,Pagamento mensal
2024-01-16,-25.50,Uber viagem,debit,Transporte,Uber,São Paulo,Ida ao trabalho
"""
    
    from fastapi.responses import Response
    
    return Response(
        content=template_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transaction_template.csv"}
    )


@router.get("/formats")
async def get_supported_formats():
    """
    Get information about supported import formats.
    """
    
    return {
        "formats": [
            {
                "type": "csv",
                "name": "CSV (Comma Separated Values)",
                "description": "Standard CSV format with transaction data",
                "required_columns": ["date", "amount", "description"],
                "optional_columns": ["type", "category", "counterpart_name", "location", "notes"],
                "example": "/api/v1/import/templates/csv"
            },
            {
                "type": "ofx",
                "name": "OFX (Open Financial Exchange)",
                "description": "Standard banking format used by most banks",
                "required_columns": [],
                "optional_columns": [],
                "example": None
            },
            {
                "type": "xlsx",
                "name": "Excel Spreadsheet",
                "description": "Microsoft Excel format (.xlsx)",
                "required_columns": ["date", "amount", "description"],
                "optional_columns": ["type", "category", "counterpart_name", "location", "notes"],
                "example": None
            }
        ],
        "limits": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "allowed_extensions": settings.ALLOWED_EXTENSIONS
        }
    }

