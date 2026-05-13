"""
Chunking and embedding API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.chunking_service import DocumentChunker
from app.services.embedding_service import OllamaEmbeddingService
from app.services.vectorstore_service import StudentVectorStore

router = APIRouter(prefix="/chunks", tags=["chunking"])

# Initialize services
chunker = DocumentChunker()
embedding_service = OllamaEmbeddingService()
vector_store = StudentVectorStore()

class ChunkingRequest(BaseModel):
    student_id: str
    document_id: str
    document_type: str
    category: str
    semester: Optional[str] = None

class ChunkingResponse(BaseModel):
    success: bool
    document_id: str
    total_chunks: int
    chunk_size: int
    chunk_overlap: int
    chunks_preview: List[Dict[str, Any]]
    error: Optional[str] = None

class EmbeddingRequest(BaseModel):
    student_id: str
    category: Optional[str] = None
    document_id: Optional[str] = None

class EmbeddingResponse(BaseModel):
    success: bool
    total_chunks: int
    embedded_chunks: int
    embedding_dimensions: int
    embedding_model: str
    error: Optional[str] = None

class VectorStoreRequest(BaseModel):
    student_id: str
    category: Optional[str] = None

class VectorStoreResponse(BaseModel):
    success: bool
    stored_points: int
    total_chunks: int
    errors: List[str]

class SearchRequest(BaseModel):
    query: str
    student_id: Optional[str] = None
    category: Optional[str] = None
    limit: int = 5
    score_threshold: float = 0.7

class SearchResponse(BaseModel):
    success: bool
    query: str
    results: List[Dict[str, Any]]
    total_found: int

@router.post("/create", response_model=ChunkingResponse)
async def create_chunks(
    student_id: str = Query(...),
    document_id: str = Query(...),
    document_type: str = Query(...),
    category: str = Query(...),
    semester: Optional[str] = Query(None)
):
    """
    Create chunks from a document
    """
    try:
        result = chunker.chunk_document(
            student_id=student_id,
            document_id=document_id,
            document_type=document_type,
            category=category,
            semester=semester
        )
        
        if result.get("success"):
            return ChunkingResponse(
                success=True,
                document_id=result["document_id"],
                total_chunks=result["total_chunks"],
                chunk_size=result["chunk_size"],
                chunk_overlap=result["chunk_overlap"],
                chunks_preview=result["chunks"]
            )
        else:
            return ChunkingResponse(
                success=False,
                document_id=document_id,
                total_chunks=0,
                chunk_size=0,
                chunk_overlap=0,
                chunks_preview=[],
                error=result.get("error", "Unknown error")
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating chunks: {str(e)}")

@router.get("/list/{student_id}")
async def list_student_chunks(
    student_id: str,
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get chunks for a student
    """
    try:
        chunks = chunker.get_student_chunks(student_id, category)
        return {
            "student_id": student_id,
            "category": category,
            "total_chunks": len(chunks),
            "chunks": chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing chunks: {str(e)}")

@router.get("/statistics/{student_id}")
async def get_chunk_statistics(student_id: str):
    """
    Get statistics about student's chunks
    """
    try:
        stats = chunker.get_chunk_statistics(student_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@router.post("/embed", response_model=EmbeddingResponse)
async def embed_chunks(
    student_id: str = Query(...),
    category: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None)
):
    """
    Generate embeddings for student chunks
    """
    try:
        # Get chunks
        chunks = chunker.get_student_chunks(
            student_id=student_id,
            category=category
        )
        
        if not chunks:
            return EmbeddingResponse(
                success=False,
                total_chunks=0,
                embedded_chunks=0,
                embedding_dimensions=0,
                embedding_model="",
                error="No chunks found"
            )
        
        # Filter by document_id if specified
        if request.document_id:
            chunks = [chunk for chunk in chunks if chunk.get("document_id") == request.document_id]
        
        # Generate embeddings
        embedded_chunks = await embedding_service.embed_chunks(chunks)
        
        # Save embeddings back to chunks
        for i, chunk in enumerate(chunks):
            if i < len(embedded_chunks):
                chunk.update(embedded_chunks[i])
        
        # Save updated chunks
        if chunker.save_chunks([chunk for chunk in chunks if "embedding" in chunk]):
            stats = await embedding_service.get_embedding_stats(embedded_chunks)
            return EmbeddingResponse(
                success=True,
                total_chunks=len(chunks),
                embedded_chunks=len(embedded_chunks),
                embedding_dimensions=stats["embedding_dimensions"],
                embedding_model=stats["embedding_model"]
            )
        else:
            return EmbeddingResponse(
                success=False,
                total_chunks=len(chunks),
                embedded_chunks=0,
                embedding_dimensions=0,
                embedding_model="",
                error="Failed to save embedded chunks"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error embedding chunks: {str(e)}")

@router.post("/store", response_model=VectorStoreResponse)
async def store_in_vector_db(request: VectorStoreRequest):
    """
    Store embedded chunks in vector database
    """
    try:
        # Connect to vector store
        if not vector_store.connect():
            raise HTTPException(status_code=500, detail="Failed to connect to vector database")
        
        # Get embedded chunks
        chunks = chunker.get_student_chunks(
            student_id=request.student_id,
            category=request.category
        )
        
        # Filter chunks that have embeddings
        embedded_chunks = [chunk for chunk in chunks if "embedding" in chunk]
        
        if not embedded_chunks:
            return VectorStoreResponse(
                success=False,
                stored_points=0,
                total_chunks=len(chunks),
                errors=["No embedded chunks found"]
            )
        
        # Store in vector database
        result = vector_store.store_chunks(embedded_chunks)
        
        return VectorStoreResponse(
            success=result["success"],
            stored_points=result["stored_points"],
            total_chunks=result["total_chunks"],
            errors=result.get("errors", [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing in vector database: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def search_chunks(request: SearchRequest):
    """
    Search for similar chunks using semantic search
    """
    try:
        # Connect to vector store
        if not vector_store.connect():
            raise HTTPException(status_code=500, detail="Failed to connect to vector database")
        
        # Generate embedding for query
        query_embedding = await embedding_service.generate_embedding(request.query)
        
        # Search for similar chunks
        results = vector_store.search_similar_chunks(
            query_embedding=query_embedding.embedding,
            category=request.category,
            student_id=request.student_id,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        return SearchResponse(
            success=True,
            query=request.query,
            results=results,
            total_found=len(results)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching chunks: {str(e)}")

@router.get("/vector-store/summary/{student_id}")
async def get_vector_store_summary(student_id: str):
    """
    Get summary of student's data in vector store
    """
    try:
        if not vector_store.connect():
            raise HTTPException(status_code=500, detail="Failed to connect to vector database")
        
        summary = vector_store.get_student_chunks_summary(student_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")

@router.post("/vector-store/setup")
async def setup_vector_store():
    """
    Setup vector database collections
    """
    try:
        if not vector_store.connect():
            raise HTTPException(status_code=500, detail="Failed to connect to vector database")
        
        results = vector_store.create_collections()
        collection_info = vector_store.get_collection_info()
        
        return {
            "success": all(results.values()),
            "collections_created": results,
            "collection_info": collection_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting up vector store: {str(e)}")

@router.get("/embedding/model-status")
async def get_embedding_model_status():
    """
    Check if embedding model is available
    """
    try:
        model_available = embedding_service.check_model_availability()
        return {
            "model": embedding_service.model,
            "available": model_available,
            "base_url": embedding_service.base_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking model status: {str(e)}")
