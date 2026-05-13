"""
Document upload and management API endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.services.document_service import DocumentProcessor

router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize document processor
doc_processor = DocumentProcessor()

class UploadResponse(BaseModel):
    success: bool
    document_id: str
    metadata: dict
    extracted_text_preview: bool
    file_path: str
    category: str

class DocumentList(BaseModel):
    student_id: str
    documents: List[dict]
    total_count: int

class DocumentText(BaseModel):
    document_id: str
    text: str
    metadata: dict

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    student_id: str = Query(..., description="Student ID"),
    document_type: str = Query(..., description="Type of document (academic_report, wellness_report, etc.)"),
    semester: Optional[str] = Query(None, description="Semester (e.g., Fall 2024)")
):
    """
    Upload a student document
    
    Supported file formats: PDF, CSV, TXT, MD
    Supported document types: academic_report, wellness_report, activities, placement_report, etc.
    
    The document will be:
    - Uploaded to the appropriate category folder
    - Text extracted and cleaned
    - Validated for student ID presence
    - Metadata saved
    """
    try:
        result = await doc_processor.process_uploaded_file(
            file=file,
            student_id=student_id,
            document_type=document_type,
            semester=semester
        )
        return UploadResponse(
            success=result["success"],
            document_id=result["document_id"],
            metadata=result["metadata"],
            extracted_text_preview=result["extracted_text_length"] > 0,
            file_path=f"qdrant:{result['document_id']}",
            category=result["category"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during upload: {str(e)}")

@router.get("/list/{student_id}", response_model=DocumentList)
async def list_student_documents(student_id: str):
    """
    List all documents for a specific student
    """
    try:
        documents = doc_processor.list_student_documents(student_id)
        return DocumentList(
            student_id=student_id,
            documents=documents,
            total_count=len(documents)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.get("/text/{document_id}", response_model=DocumentText)
async def get_document_text(
    document_id: str,
    category: str = Query(..., description="Document category (academic, wellness, extracurricular, placement)")
):
    """
    Get the extracted text for a specific document
    """
    try:
        text = doc_processor.get_document_text(document_id, category)
        
        # Get metadata
        metadata_path = doc_processor.upload_dir / category / f"{document_id}_metadata.json"
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Document metadata not found")
        
        import json
        with open(metadata_path, "r") as metadata_file:
            metadata = json.load(metadata_file)
        
        return DocumentText(
            document_id=document_id,
            text=text,
            metadata=metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document text: {str(e)}")

@router.get("/categories")
async def get_document_categories():
    """
    Get available document categories and types
    """
    return {
        "categories": doc_processor.allowed_types,
        "supported_formats": doc_processor.supported_formats
    }

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    category: str = Query(..., description="Document category")
):
    """
    Delete a document and its associated files
    """
    try:
        import os
        from pathlib import Path
        
        category_dir = doc_processor.upload_dir / category
        
        # Files to delete
        files_to_delete = [
            category_dir / f"{document_id}_metadata.json",
            category_dir / f"{document_id}_text.txt",
            # Find the actual uploaded file
        ]
        
        # Find the uploaded file
        for file_path in category_dir.glob(f"{document_id}_*"):
            if file_path.suffix in doc_processor.supported_formats:
                files_to_delete.append(file_path)
        
        deleted_files = []
        for file_path in files_to_delete:
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(str(file_path))
        
        return {
            "success": True,
            "document_id": document_id,
            "deleted_files": deleted_files,
            "message": f"Document {document_id} deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/health")
async def document_service_health():
    """
    Check document service health
    """
    try:
        # Check if upload directories exist
        upload_dirs_exist = all(
            (doc_processor.upload_dir / category).exists()
            for category in doc_processor.allowed_types.keys()
        )
        
        return {
            "status": "healthy",
            "upload_directories": "ready" if upload_dirs_exist else "missing",
            "supported_formats": doc_processor.supported_formats,
            "document_types": len([t for types in doc_processor.allowed_types.values() for t in types])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
