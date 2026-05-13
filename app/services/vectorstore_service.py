"""
Vector database service using Qdrant for student data
"""
import uuid
from typing import List, Dict, Any, Optional, Union
from qdrant_client.models import Filter, FieldCondition, MatchValue
from pydantic import BaseModel

from app.constants import (
    QDRANT_HOST, QDRANT_PORT, VECTOR_SIZE, VECTOR_DISTANCE,
    ACADEMIC_COLLECTION, WELLNESS_COLLECTION, EXTRACURRICULAR_COLLECTION, PLACEMENT_COLLECTION,
    DEFAULT_SCORE_THRESHOLD, DEFAULT_SEARCH_LIMIT
)
from app.logging_config import ServiceLogger
from app.exceptions import (
    VectorStoreError, handle_service_exception
)
from app.services.qdrant_storage_service import QdrantStorageService

class VectorStoreConfig(BaseModel):
    host: str = "localhost"
    port: int = 6333
    collection_prefix: str = "student_"

class StudentVectorStore:
    """Service for managing student data vectors in Qdrant"""
    
    def __init__(self, config: Optional[VectorStoreConfig] = None):
        self.logger = ServiceLogger("StudentVectorStore")
        self.config = config or VectorStoreConfig()
        self.storage_service = QdrantStorageService()
        self.collections = {
            "academic": ACADEMIC_COLLECTION,
            "wellness": WELLNESS_COLLECTION, 
            "extracurricular": EXTRACURRICULAR_COLLECTION,
            "placement": PLACEMENT_COLLECTION
        }
        self.vector_size = VECTOR_SIZE
    
    def connect(self) -> bool:
        """Connect to Qdrant"""
        try:
            return self.storage_service.connect()
        except Exception as e:
            self.logger.error("Failed to connect to Qdrant", exception=e)
            return False
    
    def create_collections(self) -> Dict[str, bool]:
        """Create student data collections"""
        try:
            self.logger.info("Creating Qdrant collections")
            return self.storage_service.setup_collections()
        except Exception as e:
            self.logger.error("Failed to create collections", exception=e)
            return {category: False for category in self.collections.keys()}
    
    def store_chunks(self, embedded_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store embedded chunks in vector database"""
        try:
            self.logger.info(f"Storing {len(embedded_chunks)} embedded chunks")
            
            if not embedded_chunks:
                return {"success": False, "error": "No chunks to store"}
            
            # Extract embeddings and chunk data
            chunks = []
            embeddings = []
            
            for chunk in embedded_chunks:
                chunk_data = {
                    "chunk_id": chunk.get("chunk_id"),
                    "student_id": chunk.get("student_id"),
                    "document_id": chunk.get("document_id"),
                    "document_type": chunk.get("document_type"),
                    "category": chunk.get("category"),
                    "semester": chunk.get("semester"),
                    "subject": chunk.get("subject"),
                    "chunk_index": chunk.get("chunk_index"),
                    "chunk_text": chunk.get("chunk_text"),
                    "chunk_length": chunk.get("chunk_length"),
                    "created_at": chunk.get("created_at")
                }
                chunks.append(chunk_data)
                embeddings.append(chunk.get("embedding", []))
            
            # Store in Qdrant
            result = self.storage_service.store_chunks(chunks, embeddings)
            
            if result["success"]:
                self.logger.info(f"Successfully stored {result['stored_chunks']} chunks")
                return {
                    "success": True,
                    "stored_points": result["stored_chunks"],
                    "total_chunks": len(embedded_chunks),
                    "errors": result.get("errors", [])
                }
            else:
                self.logger.error(f"Failed to store chunks: {result.get('errors', [])}")
                return {
                    "success": False,
                    "stored_points": 0,
                    "total_chunks": len(embedded_chunks),
                    "errors": result.get("errors", ["Unknown error"])
                }
                
        except Exception as e:
            self.logger.error("Failed to store embedded chunks", exception=e)
            return {
                "success": False,
                "stored_points": 0,
                "total_chunks": len(embedded_chunks),
                "errors": [str(e)]
            }
    
    def search_similar_chunks(
        self,
        query_embedding: List[float],
        category: Optional[str] = None,
        student_id: Optional[str] = None,
        limit: int = DEFAULT_SEARCH_LIMIT,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity"""
        try:
            self.logger.debug(f"Searching similar chunks with limit {limit}, threshold {score_threshold}")
            
            # Use Qdrant storage service for search
            results = self.storage_service.search_chunks(
                query_vector=query_embedding,
                student_id=student_id,
                category=category,
                limit=limit,
                score_threshold=score_threshold
            )
            
            self.logger.debug(f"Found {len(results)} search results")
            return results
            
        except Exception as e:
            self.logger.error("Failed to search similar chunks", exception=e)
            return []
    
    def get_student_chunks_summary(self, student_id: str) -> Dict[str, Any]:
        """Get summary of student's chunks in vector store"""
        if not self.client:
            return {"error": "Not connected to Qdrant"}
        
        summary = {
            "student_id": student_id,
            "collections": {},
            "total_chunks": 0
        }
        
        for category, collection_name in self.collections.items():
            try:
                # Count points for this student
                count_result = self.client.count(
                    collection_name=collection_name,
                    count_filter=Filter(
                        must=[
                            FieldCondition(
                                key="student_id",
                                match=MatchValue(value=student_id)
                            )
                        ]
                    )
                )
                
                chunk_count = count_result.count
                summary["collections"][category] = chunk_count
                summary["total_chunks"] += chunk_count
                
            except Exception as e:
                summary["collections"][category] = f"Error: {str(e)}"
        
        return summary
    
    def delete_student_chunks(self, student_id: str) -> Dict[str, Any]:
        """Delete all chunks for a student"""
        if not self.client:
            return {"success": False, "error": "Not connected to Qdrant"}
        
        deleted_counts = {}
        total_deleted = 0
        
        for category, collection_name in self.collections.items():
            try:
                # Find points to delete
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key="student_id",
                            match=MatchValue(value=student_id)
                        )
                    ]
                )
                
                # Get points count before deletion
                count_result = self.client.count(
                    collection_name=collection_name,
                    count_filter=filter_condition
                )
                
                # Delete points
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=filter_condition
                )
                
                deleted_count = count_result.count
                deleted_counts[category] = deleted_count
                total_deleted += deleted_count
                
            except Exception as e:
                deleted_counts[category] = f"Error: {str(e)}"
        
        return {
            "success": True,
            "total_deleted": total_deleted,
            "deleted_by_category": deleted_counts
        }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about all collections"""
        if not self.client:
            return {"error": "Not connected to Qdrant"}
        
        info = {}
        
        for category, collection_name in self.collections.items():
            try:
                collection_info = self.client.get_collection(collection_name)
                info[category] = {
                    "name": collection_name,
                    "points_count": collection_info.points_count,
                    "segments_count": collection_info.segments_count,
                    "status": str(collection_info.status)
                }
            except Exception as e:
                info[category] = {"error": str(e)}
        
        return info
