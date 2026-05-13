"""
Data Management API endpoints
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from app.services.document_service import DocumentProcessor
from app.services.chunking_service import DocumentChunker
from app.services.qdrant_storage_service import QdrantStorageService
from app.logging_config import ServiceLogger

router = APIRouter(prefix="/api/data", tags=["data_management"])
logger = ServiceLogger("DataManagementAPI")

@router.post("/upload")
async def upload_student_data(
    file: UploadFile = File(...),
    student_id: str = Form(...),
    category: str = Form(...)
):
    """Upload student data file and create chunks"""
    try:
        logger.info(f"Uploading file {file.filename} for student {student_id} in category {category}")
        
        # Initialize services
        doc_processor = DocumentProcessor()
        storage = QdrantStorageService()
        storage.connect()
        
        # Process document
        result = await doc_processor.process_uploaded_file(file, student_id, category)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Upload failed"))
        
        document_id = result.get("document_id")
        
        # Create chunks
        chunker = DocumentChunker()
        chunk_result = chunker.chunk_document(document_id)
        
        return {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "student_id": student_id,
            "category": category,
            "chunks_created": chunk_result.get("chunks_created", 0),
            "message": "File uploaded and processed successfully"
        }
        
    except Exception as e:
        logger.error("Failed to upload student data", exception=e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/students/{student_id}/documents")
async def get_student_documents(student_id: str, category: Optional[str] = None):
    """Get all documents for a student"""
    try:
        storage = QdrantStorageService()
        storage.connect()
        
        documents = storage.get_student_documents(student_id, category)
        
        return {
            "success": True,
            "student_id": student_id,
            "category": category,
            "documents": documents,
            "total_documents": len(documents)
        }
        
    except Exception as e:
        logger.error("Failed to get student documents", exception=e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/students/{student_id}/chunks")
async def get_student_chunks(student_id: str, category: Optional[str] = None):
    """Get all chunks for a student"""
    try:
        storage = QdrantStorageService()
        storage.connect()
        
        chunks = storage.get_student_chunks(student_id, category)
        
        return {
            "success": True,
            "student_id": student_id,
            "category": category,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }
        
    except Exception as e:
        logger.error("Failed to get student chunks", exception=e)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks"""
    try:
        storage = QdrantStorageService()
        storage.connect()
        
        # Delete document
        storage.delete_document(document_id)
        
        return {
            "success": True,
            "document_id": document_id,
            "message": "Document deleted successfully"
        }
        
    except Exception as e:
        logger.error("Failed to delete document", exception=e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_data_statistics():
    """Get data statistics"""
    try:
        storage = QdrantStorageService()
        storage.connect()
        
        collections = storage.client.get_collections()
        
        stats = {}
        total_documents = 0
        total_chunks = 0
        
        for collection in collections.collections:
            collection_name = collection.name
            collection_info = storage.client.get_collection(collection_name)
            
            # Count points by type
            document_count = 0
            chunk_count = 0
            
            # Scroll through collection to count
            points, _ = storage.client.scroll(
                collection_name=collection_name,
                limit=10000
            )
            
            for point in points:
                if point.payload.get("type") == "document":
                    document_count += 1
                elif point.payload.get("type") == "chunk":
                    chunk_count += 1
            
            stats[collection_name] = {
                "documents": document_count,
                "chunks": chunk_count,
                "total_points": len(points)
            }
            
            total_documents += document_count
            total_chunks += chunk_count
        
        return {
            "success": True,
            "statistics": {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "collections": stats
            }
        }
        
    except Exception as e:
        logger.error("Failed to get data statistics", exception=e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-upload")
async def batch_upload_student_data(
    files: List[UploadFile] = File(...),
    student_id: str = Form(...),
    category: str = Form(...)
):
    """Batch upload multiple files for a student"""
    try:
        logger.info(f"Batch uploading {len(files)} files for student {student_id}")
        
        results = []
        
        for file in files:
            try:
                # Process each file
                doc_processor = DocumentProcessor()
                result = await doc_processor.process_uploaded_file(file, student_id, category)
                
                if result.get("success", False):
                    document_id = result.get("document_id")
                    
                    # Create chunks
                    chunker = DocumentChunker()
                    chunk_result = chunker.chunk_document(document_id)
                    
                    results.append({
                        "filename": file.filename,
                        "success": True,
                        "document_id": document_id,
                        "chunks_created": chunk_result.get("chunks_created", 0)
                    })
                else:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": result.get("error", "Upload failed")
                    })
                    
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        successful_uploads = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "student_id": student_id,
            "category": category,
            "total_files": len(files),
            "successful_uploads": successful_uploads,
            "failed_uploads": len(files) - successful_uploads,
            "results": results
        }
        
    except Exception as e:
        logger.error("Failed to batch upload student data", exception=e)
        raise HTTPException(status_code=500, detail=str(e))
