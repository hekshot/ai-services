"""
Qdrant-based storage service for all data (documents, chunks, vectors, metadata)
"""
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, HasIdCondition

from app.constants import (
    QDRANT_HOST, QDRANT_PORT, VECTOR_SIZE, VECTOR_DISTANCE,
    ACADEMIC_COLLECTION, WELLNESS_COLLECTION, EXTRACURRICULAR_COLLECTION, PLACEMENT_COLLECTION
)
from app.logging_config import ServiceLogger
from app.exceptions import (
    VectorStoreError, ValidationError, handle_service_exception
)

class QdrantStorageService:
    """Unified storage service using Qdrant for all data"""
    
    def __init__(self):
        self.logger = ServiceLogger("QdrantStorageService")
        self.client = None
        self.collections = {
            "academic": ACADEMIC_COLLECTION,
            "wellness": WELLNESS_COLLECTION,
            "extracurricular": EXTRACURRICULAR_COLLECTION,
            "placement": PLACEMENT_COLLECTION
        }
    
    def connect(self) -> bool:
        """Connect to Qdrant"""
        try:
            self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            # Test connection
            self.client.get_collections()
            self.logger.info("Connected to Qdrant successfully")
            return True
        except Exception as e:
            self.logger.error("Failed to connect to Qdrant", exception=e)
            return False
    
    def setup_collections(self) -> Dict[str, bool]:
        """Setup all collections with proper schemas"""
        if not self.connect():
            return {category: False for category in self.collections.keys()}
        
        results = {}
        
        for category, collection_name in self.collections.items():
            try:
                # Check if collection exists
                try:
                    self.client.get_collection(collection_name)
                    results[category] = True
                    self.logger.debug(f"Collection {collection_name} already exists")
                    continue
                except:
                    pass  # Collection doesn't exist, create it
                
                # Create collection with vector configuration
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=getattr(Distance, VECTOR_DISTANCE)
                    )
                )
                results[category] = True
                self.logger.info(f"Created collection: {collection_name}")
                
            except Exception as e:
                self.logger.error(f"Error creating collection {collection_name}", exception=e)
                results[category] = False
        
        return results
    
    def store_document(
        self,
        student_id: str,
        document_id: str,
        document_type: str,
        category: str,
        filename: str,
        file_size: int,
        extracted_text: str,
        semester: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store document metadata and text in Qdrant"""
        try:
            self.logger.info(f"Storing document {document_id} in Qdrant")
            
            if category not in self.collections:
                raise ValidationError(f"Invalid category: {category}")
            
            # Create a zero vector for document storage (not used for search)
            zero_vector = [0.0] * VECTOR_SIZE
            
            # Prepare payload
            payload = {
                "type": "document",
                "student_id": student_id,
                "document_id": document_id,
                "document_type": document_type,
                "category": category,
                "filename": filename,
                "file_size": file_size,
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "semester": semester,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Create point
            point = PointStruct(
                id=f"doc_{document_id}",
                vector=zero_vector,
                payload=payload
            )
            
            # Store in Qdrant
            collection_name = self.collections[category]
            self.client.upsert(collection_name=collection_name, points=[point])
            
            self.logger.info(f"Successfully stored document {document_id}")
            return {"success": True, "document_id": document_id}
            
        except Exception as e:
            self.logger.error(f"Failed to store document {document_id}", exception=e)
            raise handle_service_exception("store_document", e, self.logger)
    
    def store_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ) -> Dict[str, Any]:
        """Store chunks with optional embeddings in Qdrant"""
        try:
            self.logger.info(f"Storing {len(chunks)} chunks in Qdrant")
            
            if not chunks:
                return {"success": True, "stored_chunks": 0}
            
            # Group chunks by category
            chunks_by_category = {}
            for chunk in chunks:
                category = chunk.get("category")
                if category not in chunks_by_category:
                    chunks_by_category[category] = []
                chunks_by_category[category].append(chunk)
            
            total_stored = 0
            errors = []
            
            for category, category_chunks in chunks_by_category.items():
                if category not in self.collections:
                    errors.append(f"Invalid category: {category}")
                    continue
                
                try:
                    collection_name = self.collections[category]
                    points = []
                    
                    for i, chunk in enumerate(category_chunks):
                        # Use provided embedding or create zero vector
                        vector = embeddings[i] if embeddings and i < len(embeddings) else [0.0] * VECTOR_SIZE
                        
                        point = PointStruct(
                            id=chunk.get("chunk_id", f"chunk_{uuid.uuid4().hex[:8]}"),
                            vector=vector,
                            payload={
                                "type": "chunk",
                                **chunk,
                                "created_at": chunk.get("created_at", datetime.now().isoformat()),
                                "updated_at": datetime.now().isoformat()
                            }
                        )
                        points.append(point)
                    
                    # Batch upsert
                    self.client.upsert(collection_name=collection_name, points=points)
                    total_stored += len(points)
                    self.logger.debug(f"Stored {len(points)} chunks in {collection_name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to store chunks in {category}", exception=e)
                    errors.append(f"Error storing {category}: {str(e)}")
            
            self.logger.info(f"Successfully stored {total_stored} chunks")
            return {
                "success": total_stored > 0,
                "stored_chunks": total_stored,
                "total_chunks": len(chunks),
                "errors": errors
            }
            
        except Exception as e:
            self.logger.error("Failed to store chunks", exception=e)
            raise handle_service_exception("store_chunks", e, self.logger)
    
    def get_student_documents(
        self,
        student_id: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all documents for a student"""
        try:
            self.logger.debug(f"Getting documents for student {student_id}, category: {category}")
            
            documents = []
            collections_to_search = [category] if category else list(self.collections.keys())
            
            for cat in collections_to_search:
                if cat not in self.collections:
                    continue
                
                try:
                    collection_name = self.collections[cat]
                    
                    # Query for documents
                    filter_condition = Filter(
                        must=[
                            FieldCondition(key="student_id", match=MatchValue(value=student_id)),
                            FieldCondition(key="type", match=MatchValue(value="document"))
                        ]
                    )
                    
                    results = self.client.scroll(
                        collection_name=collection_name,
                        scroll_filter=filter_condition,
                        limit=1000  # Adjust as needed
                    )
                    
                    for point in results[0]:
                        documents.append(point.payload)
                    
                    self.logger.debug(f"Found {len(results[0])} documents in {cat}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to get documents from {cat}", exception=e)
                    # Continue with other categories
            
            # Sort by creation date (newest first)
            documents.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            self.logger.debug(f"Returning {len(documents)} documents for student {student_id}")
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to get documents for student {student_id}", exception=e)
            raise handle_service_exception("get_student_documents", e, self.logger)
    
    def get_student_chunks(
        self,
        student_id: str,
        category: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get chunks for a student"""
        try:
            self.logger.debug(f"Getting chunks for student {student_id}, category: {category}, document_id: {document_id}")
            
            chunks = []
            collections_to_search = [category] if category else list(self.collections.keys())
            
            for cat in collections_to_search:
                if cat not in self.collections:
                    continue
                
                try:
                    collection_name = self.collections[cat]
                    
                    # Build filter conditions
                    must_conditions = [
                        FieldCondition(key="student_id", match=MatchValue(value=student_id)),
                        FieldCondition(key="type", match=MatchValue(value="chunk"))
                    ]
                    
                    if document_id:
                        must_conditions.append(
                            FieldCondition(key="document_id", match=MatchValue(value=document_id))
                        )
                    
                    filter_condition = Filter(must=must_conditions)
                    
                    results = self.client.scroll(
                        collection_name=collection_name,
                        scroll_filter=filter_condition,
                        limit=5000  # Adjust as needed
                    )
                    
                    for point in results[0]:
                        chunks.append(point.payload)
                    
                    self.logger.debug(f"Found {len(results[0])} chunks in {cat}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to get chunks from {cat}", exception=e)
                    # Continue with other categories
            
            # Sort by creation date (newest first)
            chunks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            self.logger.debug(f"Returning {len(chunks)} chunks for student {student_id}")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to get chunks for student {student_id}", exception=e)
            raise handle_service_exception("get_student_chunks", e, self.logger)
    
    def get_document_text(self, document_id: str, category: str) -> str:
        """Get extracted text for a document"""
        try:
            self.logger.debug(f"Getting text for document {document_id}")
            
            if category not in self.collections:
                raise ValidationError(f"Invalid category: {category}")
            
            collection_name = self.collections[category]
            
            # Query for specific document
            filter_condition = Filter(
                must=[
                    FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                    FieldCondition(key="type", match=MatchValue(value="document"))
                ]
            )
            
            results = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,
                limit=1
            )
            
            if not results[0]:
                raise VectorStoreError(f"Document {document_id} not found")
            
            document = results[0][0].payload
            text = document.get("extracted_text", "")
            
            self.logger.debug(f"Retrieved {len(text)} characters for document {document_id}")
            return text
            
        except Exception as e:
            self.logger.error(f"Failed to get text for document {document_id}", exception=e)
            raise handle_service_exception("get_document_text", e, self.logger)
    
    def search_chunks(
        self,
        query_vector: List[float],
        student_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10,
        score_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search for chunks using vector similarity"""
        try:
            self.logger.debug(f"Searching chunks with vector similarity")
            
            results = []
            collections_to_search = [category] if category else list(self.collections.keys())
            
            for cat in collections_to_search:
                if cat not in self.collections:
                    continue
                
                try:
                    collection_name = self.collections[cat]
                    
                    # Build filter conditions
                    must_conditions = [FieldCondition(key="type", match=MatchValue(value="chunk"))]
                    
                    if student_id:
                        must_conditions.append(
                            FieldCondition(key="student_id", match=MatchValue(value=student_id))
                        )
                    
                    filter_condition = Filter(must=must_conditions) if must_conditions else None
                    
                    search_results = self.client.query_points(
                        collection_name=collection_name,
                        query=query_vector,
                        query_filter=filter_condition,
                        limit=limit,
                        score_threshold=score_threshold
                    )
                    
                    for hit in search_results.points:
                        if hit.score >= score_threshold:
                            result = {
                                "score": hit.score,
                                "id": hit.id,
                                "payload": hit.payload
                            }
                            results.append(result)
                    
                    self.logger.debug(f"Found {len(search_results.points)} results in {cat}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to search in {cat}", exception=e)
                    # Continue with other categories
            
            # Sort by score (highest first)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Return top results
            final_results = results[:limit]
            self.logger.debug(f"Returning {len(final_results)} search results")
            return final_results
            
        except Exception as e:
            self.logger.error("Failed to search chunks", exception=e)
            raise handle_service_exception("search_chunks", e, self.logger)
    
    def delete_student_data(self, student_id: str) -> Dict[str, Any]:
        """Delete all data for a student"""
        try:
            self.logger.info(f"Deleting all data for student {student_id}")
            
            deleted_counts = {}
            total_deleted = 0
            
            for category, collection_name in self.collections.items():
                try:
                    # Find all points for this student
                    filter_condition = Filter(
                        must=[
                            FieldCondition(key="student_id", match=MatchValue(value=student_id))
                        ]
                    )
                    
                    # Get count before deletion
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
                    
                    self.logger.debug(f"Deleted {deleted_count} points from {category}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to delete from {category}", exception=e)
                    deleted_counts[category] = f"Error: {str(e)}"
            
            self.logger.info(f"Deleted {total_deleted} total points for student {student_id}")
            return {
                "success": True,
                "total_deleted": total_deleted,
                "deleted_by_category": deleted_counts
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete student data for {student_id}", exception=e)
            raise handle_service_exception("delete_student_data", e, self.logger)
    
    def get_storage_statistics(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            self.logger.debug("Getting storage statistics")
            
            stats = {
                "collections": {},
                "total_points": 0
            }
            
            for category, collection_name in self.collections.items():
                try:
                    collection_info = self.client.get_collection(collection_name)
                    
                    if student_id:
                        # Count points for specific student
                        filter_condition = Filter(
                            must=[
                                FieldCondition(key="student_id", match=MatchValue(value=student_id))
                            ]
                        )
                        count_result = self.client.count(
                            collection_name=collection_name,
                            count_filter=filter_condition
                        )
                        stats["collections"][category] = count_result.count
                    else:
                        # Total points in collection
                        stats["collections"][category] = collection_info.points_count
                    
                    stats["total_points"] += stats["collections"][category]
                    
                except Exception as e:
                    self.logger.error(f"Failed to get stats for {category}", exception=e)
                    stats["collections"][category] = f"Error: {str(e)}"
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get storage statistics", exception=e)
            raise handle_service_exception("get_storage_statistics", e, self.logger)
