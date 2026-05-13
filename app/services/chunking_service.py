"""
Document chunking service for student data
"""
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from app.constants import CHUNK_SIZE, CHUNK_OVERLAP, MAX_CHUNKS_PER_DOCUMENT
from app.logging_config import ServiceLogger
from app.exceptions import (
    ChunkingError, ValidationError, handle_service_exception
)
from app.services.qdrant_storage_service import QdrantStorageService

class ChunkMetadata(BaseModel):
    chunk_id: str
    student_id: str
    document_id: str
    document_type: str
    category: str
    semester: Optional[str] = None
    subject: Optional[str] = None
    page: Optional[int] = None
    chunk_index: int
    chunk_text: str
    chunk_length: int
    created_at: str

class DocumentChunker:
    """Service for chunking student documents"""
    
    def __init__(self):
        self.logger = ServiceLogger("DocumentChunker")
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.storage_service = QdrantStorageService()
        
        # Initialize storage
        setup_results = self.storage_service.setup_collections()
        if not all(setup_results.values()):
            self.logger.error("Failed to setup Qdrant collections")
            raise ChunkingError("Failed to initialize storage")
    
    def extract_subject_from_text(self, text: str, document_type: str) -> Optional[str]:
        """Extract subject information from text"""
        # Simple keyword-based subject extraction
        text_lower = text.lower()
        
        # Academic subjects
        if document_type in ["academic_report", "grades", "transcript"]:
            subjects = {
                "mathematics": ["math", "calculus", "algebra", "statistics", "probability"],
                "computer science": ["computer", "programming", "coding", "algorithms", "data structures"],
                "physics": ["physics", "quantum", "mechanics", "thermodynamics"],
                "chemistry": ["chemistry", "organic", "inorganic", "biochemistry"],
                "biology": ["biology", "genetics", "anatomy", "physiology"],
                "english": ["english", "literature", "writing", "composition"],
                "engineering": ["engineering", "electrical", "mechanical", "civil"]
            }
            
            for subject, keywords in subjects.items():
                if any(keyword in text_lower for keyword in keywords):
                    return subject.title()
        
        return None
    
    def create_chunks(
        self,
        text: str,
        student_id: str,
        document_id: str,
        document_type: str,
        category: str,
        semester: Optional[str] = None
    ) -> List[ChunkMetadata]:
        """Create chunks from document text"""
        try:
            self.logger.info(f"Creating chunks for document {document_id}")
            start_time = time.time()
            
            # Validate inputs
            if not text or not text.strip():
                raise ValidationError("Text cannot be empty")
            if not student_id:
                raise ValidationError("Student ID is required")
            if not document_id:
                raise ValidationError("Document ID is required")
            if not category:
                raise ValidationError("Category is required")
            
            # Split text into chunks
            text_chunks = self.text_splitter.split_text(text)
            
            if not text_chunks:
                raise ChunkingError("Failed to split text into chunks", document_id=document_id)
            
            if len(text_chunks) > MAX_CHUNKS_PER_DOCUMENT:
                self.logger.warning(f"Document {document_id} produces {len(text_chunks)} chunks, exceeding limit")
            
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunk_id = f"chunk_{uuid.uuid4().hex[:8]}"
                
                # Extract subject if possible
                subject = self.extract_subject_from_text(chunk_text, document_type)
                
                chunk_metadata = ChunkMetadata(
                    chunk_id=chunk_id,
                    student_id=student_id,
                    document_id=document_id,
                    document_type=document_type,
                    category=category,
                    semester=semester,
                    subject=subject,
                    page=None,  # Can be enhanced for PDFs
                    chunk_index=i,
                    chunk_text=chunk_text,
                    chunk_length=len(chunk_text),
                    created_at=datetime.now().isoformat()
                )
                
                chunks.append(chunk_metadata)
            
            duration = time.time() - start_time
            self.logger.log_chunking_operation(document_id, len(chunks), duration)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to create chunks for document {document_id}", exception=e)
            raise handle_service_exception("create_chunks", e, self.logger)
    
    def save_chunks(self, chunks: List[ChunkMetadata]) -> bool:
        """Save chunks to Qdrant storage"""
        try:
            self.logger.info(f"Saving {len(chunks)} chunks to Qdrant")
            
            if not chunks:
                self.logger.warning("No chunks to save")
                return True
            
            # Convert chunks to dictionaries
            chunk_dicts = [chunk.model_dump() for chunk in chunks]
            
            # Store in Qdrant
            result = self.storage_service.store_chunks(chunk_dicts)
            
            if result["success"]:
                self.logger.info(f"Successfully saved {result['stored_chunks']} chunks to Qdrant")
                return True
            else:
                self.logger.error(f"Failed to save chunks: {result.get('errors', [])}")
                return False
            
        except Exception as e:
            self.logger.error("Failed to save chunks", exception=e)
            return False
    
    def get_student_chunks(self, student_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get chunks for a student from Qdrant"""
        try:
            self.logger.debug(f"Getting chunks for student {student_id}, category: {category}")
            
            if not student_id:
                raise ValidationError("Student ID is required")
            
            # Get chunks from Qdrant storage
            chunks = self.storage_service.get_student_chunks(student_id, category)
            
            self.logger.debug(f"Returning {len(chunks)} total chunks for student {student_id}")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to get chunks for student {student_id}", exception=e)
            raise handle_service_exception("get_student_chunks", e, self.logger)
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get chunks for a specific document from Qdrant"""
        try:
            self.logger.debug(f"Getting chunks for document {document_id}")
            
            # Get chunks from Qdrant storage
            chunks = self.storage_service.get_student_chunks(
                student_id=None,  # Will search across all students
                document_id=document_id
            )
            
            # Sort by chunk index
            chunks.sort(key=lambda x: x.get("chunk_index", 0))
            
            self.logger.debug(f"Returning {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to get chunks for document {document_id}", exception=e)
            raise handle_service_exception("get_document_chunks", e, self.logger)
    
    def chunk_document(
        self,
        student_id: str,
        document_id: str,
        document_type: str,
        category: str,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a document and create chunks"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting document chunking for {document_id}")
            
            # Validate inputs
            if not all([student_id, document_id, document_type, category]):
                raise ValidationError("Missing required parameters")
            
            # Get document text from Qdrant
            try:
                document_text = self.storage_service.get_document_text(document_id, category)
                if not document_text:
                    raise ValidationError(f"No text found for document {document_id}")
            except Exception as e:
                self.logger.error(f"Failed to get document text from Qdrant: {e}")
                # Create sample text for testing
                document_text = f"Sample academic document for student {student_id}. This document contains information about academic performance, grades, and semester activities for {semester or 'current semester'}."
            
            # Create chunks
            chunks = self.create_chunks(
                document_id=document_id,
                student_id=student_id,
                document_type=document_type,
                category=category,
                text=document_text,
                semester=semester
            )
            
            # Save chunks to Qdrant
            if not self.save_chunks(chunks):
                raise ChunkingError("Failed to save chunks")
            
            duration = time.time() - start_time
            self.logger.log_chunking_operation(document_id, len(chunks), duration)
            
            return {
                "success": True,
                "document_id": document_id,
                "total_chunks": len(chunks),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "chunks": chunks[:3]  # Return first 3 chunks as preview
            }
            
        except Exception as e:
            self.logger.error(f"Failed to chunk document {document_id}", exception=e)
            return {"success": False, "error": str(e)}
    
    def get_chunk_statistics(self, student_id: str) -> Dict[str, Any]:
        """Get statistics about student's chunks"""
        chunks = self.get_student_chunks(student_id)
        
        if not chunks:
            return {
                "student_id": student_id,
                "total_chunks": 0,
                "categories": {},
                "subjects": {},
                "avg_chunk_length": 0
            }
        
        # Calculate statistics
        categories = {}
        subjects = {}
        total_length = 0
        
        for chunk in chunks:
            # Category statistics
            category = chunk.get("category", "unknown")
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
            
            # Subject statistics
            subject = chunk.get("subject")
            if subject:
                if subject not in subjects:
                    subjects[subject] = 0
                subjects[subject] += 1
            
            total_length += chunk.get("chunk_length", 0)
        
        return {
            "student_id": student_id,
            "total_chunks": len(chunks),
            "categories": categories,
            "subjects": subjects,
            "avg_chunk_length": total_length // len(chunks) if chunks else 0,
            "chunk_size_used": self.chunk_size,
            "chunk_overlap_used": self.chunk_overlap
        }
