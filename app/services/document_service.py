"""
Document processing service for student data
"""
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import pypdf
import pandas as pd

from app.logging_config import ServiceLogger
from app.exceptions import DocumentProcessingError, ValidationError, handle_service_exception
from app.services.qdrant_storage_service import QdrantStorageService

class DocumentMetadata(BaseModel):
    student_id: str
    document_type: str
    semester: Optional[str] = None
    document_id: str
    filename: str
    uploaded_at: str
    file_size: int
    file_type: str
    extracted_text_length: int

class DocumentProcessor:
    """Service for processing student documents"""
    
    def __init__(self):
        self.logger = ServiceLogger("DocumentProcessor")
        self.storage_service = QdrantStorageService()
        
        # No filesystem storage - everything in Qdrant
        self.categories = {
            "academic": ["academic_report", "grades", "transcript"],
            "wellness": ["wellness_report", "mental_health", "counseling"],
            "extracurricular": ["activities", "sports", "clubs", "leadership"],
            "placement": ["placement_report", "career", "internship", "readiness"]
        }
        
        # Initialize Qdrant storage
        setup_results = self.storage_service.setup_collections()
        if not all(setup_results.values()):
            self.logger.error("Failed to setup Qdrant collections")
            raise DocumentProcessingError("Failed to initialize storage")
    
    def validate_document_type(self, document_type: str) -> bool:
        """Validate document type"""
        # Accept both category names and document types
        if document_type in self.categories:
            return True
        
        for category, types in self.categories.items():
            if document_type in types:
                return True
        return False
    
    def get_category_from_type(self, document_type: str) -> str:
        """Get category from document type"""
        # If document_type is already a category, return it
        if document_type in self.categories:
            return document_type
        
        # Find category from document type
        for category, types in self.categories.items():
            if document_type in types:
                return category
        return document_type  # fallback 
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {e}")
            raise DocumentProcessingError(f"Error extracting PDF text: {str(e)}")
        return text
    
    def extract_text_from_csv(self, file_path: Path) -> str:
        """Extract text from CSV file"""
        try:
            text = ""
            with open(file_path, "r", encoding="utf-8") as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    text += ",".join(row) + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text from CSV: {str(e)}")
    
    def extract_text_from_text_file(self, file_path: Path) -> str:
        """Extract text from text/markdown file"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading text file: {str(e)}")
    
    def extract_text(self, file_path: Path, file_type: str) -> str:
        """Extract text based on file type"""
        if file_type == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type == ".csv":
            return self.extract_text_from_csv(file_path)
        elif file_type in [".txt", ".md"]:
            return self.extract_text_from_text_file(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
    
    def extract_text_from_content(self, file_content: bytes, file_type: str) -> str:
        """Extract text from file content without filesystem"""
        try:
            if file_type == ".pdf":
                return self.extract_pdf_text_from_content(file_content)
            elif file_type == ".csv":
                return self.extract_csv_text_from_content(file_content)
            elif file_type in [".txt", ".md"]:
                return self.extract_text_from_content_bytes(file_content)
            else:
                raise DocumentProcessingError(f"Unsupported file type: {file_type}")
        except Exception as e:
            self.logger.error(f"Error extracting text from content", exception=e)
            raise DocumentProcessingError(f"Error extracting text: {str(e)}")
    
    def extract_text_from_content_bytes(self, file_content: bytes) -> str:
        """Extract text from text/markdown content without filesystem"""
        try:
            return file_content.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error extracting text from content: {e}")
            raise DocumentProcessingError(f"Error extracting text: {str(e)}")
    
    def extract_csv_text_from_content(self, file_content: bytes) -> str:
        """Extract text from CSV content without filesystem"""
        try:
            import io
            csv_stream = io.StringIO(file_content.decode('utf-8'))
            df = pd.read_csv(csv_stream)
            return df.to_string()
        except Exception as e:
            self.logger.error(f"Error extracting CSV text from content: {e}")
            raise DocumentProcessingError(f"Error extracting CSV text: {str(e)}")
    
    def extract_text_from_file(self, file_path: Path, file_type: str) -> str:
        """Extract text from uploaded file (legacy method)"""
        try:
            if file_type == ".pdf":
                return self.extract_pdf_text(file_path)
            elif file_type == ".csv":
                return self.extract_csv_text(file_path)
            elif file_type in [".txt", ".md"]:
                return self.extract_text_file(file_path)
            else:
                raise DocumentProcessingError(f"Unsupported file type: {file_type}")
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}", exception=e)
            raise DocumentProcessingError(f"Error extracting text: {str(e)}")
    
    def validate_student_id(self, text: str, student_id: str) -> bool:
        """Validate student ID exists in document text"""
        # Simple validation - check if student ID appears in text
        return student_id.lower() in text.lower()
    
    def clean_text(self, text: str) -> str:
        """Clean and structure extracted text"""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Remove special characters that might cause issues
        text = text.replace("\x00", "")
        return text.strip()
    
    def generate_document_id(self) -> str:
        """Generate unique document ID"""
        return f"doc_{uuid.uuid4().hex[:8]}"
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        return file_path.stat().st_size
    
    async def process_uploaded_file(
        self,
        file,
        student_id: str,
        document_type: str,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process uploaded document file directly without filesystem storage"""
        try:
            self.logger.info(f"Processing uploaded file: {file.filename}")
            
            # Validate document type
            if not self.validate_document_type(document_type):
                raise ValidationError(f"Invalid document type: {document_type}")
            
            # Get file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in [".pdf", ".csv", ".txt", ".md"]:
                raise ValidationError(f"Unsupported file type: {file_ext}")
            
            # Generate document ID
            document_id = f"doc_{uuid.uuid4().hex[:8]}"
            
            # Get category from document type
            category = self.get_category_from_type(document_type)
            
            # Read file content directly
            file_content = file.file.read()
            
            # Extract text from file content
            extracted_text = self.extract_text_from_content(file_content, file_ext)
            cleaned_text = self.clean_text(extracted_text)
            
            # Create metadata
            metadata = DocumentMetadata(
                student_id=student_id,
                document_type=document_type,
                semester=semester,
                document_id=document_id,
                filename=file.filename,
                uploaded_at=datetime.now().isoformat(),
                file_size=len(file_content),
                file_type=file_ext,
                extracted_text_length=len(cleaned_text)
            )
            
            # Store everything in Qdrant
            try:
                result = self.storage_service.store_document(
                    student_id=metadata.student_id,
                    document_id=metadata.document_id,
                    document_type=metadata.document_type,
                    category=category,
                    filename=metadata.filename,
                    file_size=metadata.file_size,
                    extracted_text=cleaned_text,
                    semester=metadata.semester
                )
                if not result["success"]:
                    raise DocumentProcessingError("Failed to save document to Qdrant")
            except Exception as e:
                raise DocumentProcessingError(f"Failed to save document to Qdrant: {str(e)}")
            
            return {
                "success": True,
                "document_id": document_id,
                "metadata": metadata.model_dump(),
                "extracted_text_length": len(cleaned_text),
                "category": category
            }
            
        except Exception as e:
            self.logger.error(f"Error processing uploaded file {file.filename}", exception=e)
            raise DocumentProcessingError(f"Error processing file: {str(e)}")
            if text_path.exists():
                text_path.unlink()
            
            raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    
    def list_student_documents(self, student_id: str) -> List[Dict[str, Any]]:
        """List all documents for a student"""
        documents = []
        
        for category in self.allowed_types.keys():
            category_dir = self.upload_dir / category
            if not category_dir.exists():
                continue
            
            for file_path in category_dir.glob("*_metadata.json"):
                try:
                    with open(file_path, "r") as metadata_file:
                        metadata = json.load(metadata_file)
                        if metadata.get("student_id") == student_id:
                            documents.append({
                                "category": category,
                                **metadata
                            })
                except Exception:
                    continue
        
        # Sort by upload date (newest first)
        documents.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
        return documents
    
    def _save_document_to_qdrant(self, metadata: DocumentMetadata, extracted_text: str) -> bool:
        """Save document metadata and extracted text to Qdrant"""
        try:
            self.logger.info(f"Saving document {metadata.document_id} to Qdrant")
            
            # Store in Qdrant
            result = self.storage_service.store_document(
                student_id=metadata.student_id,
                document_id=metadata.document_id,
                document_type=metadata.document_type,
                category=metadata.category,
                filename=metadata.filename,
                file_size=metadata.file_size,
                extracted_text=extracted_text,
                semester=metadata.semester
            )
            
            return result["success"]
            
        except Exception as e:
            self.logger.error(f"Failed to save document to Qdrant: {e}")
            return False
    
    def get_document_text(self, document_id: str, category: str) -> str:
        """Get extracted text for a document from Qdrant"""
        try:
            self.logger.debug(f"Getting text for document {document_id} from Qdrant")
            
            # Get text from Qdrant storage
            text = self.storage_service.get_document_text(document_id, category)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Failed to get text for document {document_id}", exception=e)
            raise DocumentProcessingError(f"Error retrieving document text: {str(e)}")
