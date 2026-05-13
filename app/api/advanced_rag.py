"""
Advanced RAG API endpoints - 7-Stage Implementation
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from app.services.advanced_rag_service import AdvancedRAGService

router = APIRouter(prefix="/advanced-rag", tags=["advanced-rag"])

# Initialize advanced RAG service
rag_service = AdvancedRAGService()

class QueryRequest(BaseModel):
    query: str
    student_id: str = None
    category: str = None

class QueryResponse(BaseModel):
    answer: str
    intent: str
    entities: Dict[str, Any]
    stages_completed: list
    retrieval_stats: Dict[str, Any]
    sources_used: int
    context_preview: str

@router.post("/query", response_model=QueryResponse)
async def advanced_rag_query(request: QueryRequest):
    """
    Execute complete 7-stage RAG pipeline
    
    This endpoint implements:
    1. Query Analysis & Intent Classification
    2. HyDE Query Expansion
    3. Multi-Signal Retrieval (Dense + Sparse)
    4. RRF Fusion
    5. Cross-Encoder Reranking
    6. Hierarchy Expansion
    7. Enhanced LLM Generation
    """
    try:
        # Include student_id and category in query for entity extraction
        enhanced_query = request.query
        if request.student_id:
            enhanced_query += f" student:{request.student_id}"
        if request.category:
            enhanced_query += f" category:{request.category}"
        
        result = await rag_service.advanced_rag_pipeline(enhanced_query)
        
        return QueryResponse(
            answer=result.get("answer", ""),
            intent=result.get("intent", "unknown"),
            entities=result.get("entities", {}),
            stages_completed=result.get("stages_completed", []),
            retrieval_stats=result.get("retrieval_stats", {}),
            sources_used=result.get("sources_used", 0),
            context_preview=result.get("context_preview", "")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in advanced RAG query: {str(e)}")

@router.get("/compare")
async def compare_basic_vs_advanced(query: str, student_id: str = None, category: str = None):
    """
    Compare basic RAG vs advanced 7-stage RAG
    """
    try:
        # Enhanced query with entities
        enhanced_query = query
        if student_id:
            enhanced_query += f" student:{student_id}"
        if category:
            enhanced_query += f" category:{category}"
        
        # Basic RAG (current implementation)
        basic_result = await basic_rag_query(enhanced_query)
        
        # Advanced RAG
        advanced_result = await rag_service.advanced_rag_pipeline(enhanced_query)
        
        return {
            "query": query,
            "basic_rag": {
                "answer": basic_result.get("answer", ""),
                "sources": basic_result.get("sources_used", 0),
                "stages": ["basic_retrieval", "llm_generation"]
            },
            "advanced_rag": {
                "answer": advanced_result.get("answer", ""),
                "sources": advanced_result.get("sources_used", 0),
                "stages": advanced_result.get("stages_completed", []),
                "intent": advanced_result.get("intent", ""),
                "entities": advanced_result.get("entities", {}),
                "retrieval_stats": advanced_result.get("retrieval_stats", {})
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in comparison: {str(e)}")

async def basic_rag_query(query: str) -> Dict[str, Any]:
    """Basic RAG implementation for comparison"""
    try:
        from app.services.embedding_service import OllamaEmbeddingService
        from app.services.vectorstore_service import StudentVectorStore
        
        # Simple vector search
        embedding_service = OllamaEmbeddingService()
        query_embedding = await embedding_service.generate_embedding(query)
        
        vector_store = StudentVectorStore()
        if not vector_store.connect():
            return {"answer": "Vector store not available", "sources_used": 0}
        
        search_results = vector_store.search_similar_chunks(
            query_embedding=query_embedding.embedding,
            limit=5,
            score_threshold=0.3
        )
        
        if not search_results:
            return {"answer": "No relevant information found", "sources_used": 0}
        
        # Simple context building
        context = "\n".join([result['payload']['chunk_text'] for result in search_results[:3]])
        
        # Basic LLM generation
        prompt = f"Answer this question based on the context: {query}\n\nContext: {context}"
        
        from src.providers import get_provider
        provider = get_provider()
        response = await provider.generate(prompt, stream=False)
        
        return {
            "answer": response.get("response", ""),
            "sources_used": len(search_results)
        }
        
    except Exception as e:
        return {"answer": f"Basic RAG error: {str(e)}", "sources_used": 0}

@router.get("/health")
async def advanced_rag_health():
    """
    Check health of all RAG components
    """
    health_status = {
        "overall": "healthy",
        "components": {}
    }
    
    # Check embedding service
    try:
        from app.services.embedding_service import OllamaEmbeddingService
        embedding_service = OllamaEmbeddingService()
        model_available = embedding_service.check_model_availability()
        health_status["components"]["embedding"] = {
            "status": "healthy" if model_available else "unhealthy",
            "model": embedding_service.model,
            "available": model_available
        }
    except Exception as e:
        health_status["components"]["embedding"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"
    
    # Check vector store
    try:
        from app.services.vectorstore_service import StudentVectorStore
        vector_store = StudentVectorStore()
        connected = vector_store.connect()
        health_status["components"]["vector_store"] = {
            "status": "healthy" if connected else "unhealthy",
            "connected": connected
        }
    except Exception as e:
        health_status["components"]["vector_store"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"
    
    # Check chunking service
    try:
        from app.services.chunking_service import DocumentChunker
        chunker = DocumentChunker()
        health_status["components"]["chunking"] = {
            "status": "healthy",
            "chunk_size": chunker.chunk_size,
            "overlap": chunker.chunk_overlap
        }
    except Exception as e:
        health_status["components"]["chunking"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"
    
    # Check LLM provider
    try:
        from src.providers import get_provider
        provider = get_provider()
        healthy = await provider.health_check()
        health_status["components"]["llm"] = {
            "status": "healthy" if healthy else "unhealthy",
            "provider": provider.model,
            "connected": healthy
        }
    except Exception as e:
        health_status["components"]["llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "degraded"
    
    return health_status

@router.get("/pipeline-stages")
async def get_pipeline_stages():
    """
    Get information about all 7 pipeline stages
    """
    return {
        "stages": [
            {
                "stage": 1,
                "name": "Query Analysis",
                "description": "Classifies intent and extracts key entities",
                "purpose": "Prevents searching for out-of-scope questions"
            },
            {
                "stage": 2,
                "name": "Query Expansion (HyDE)",
                "description": "Generates hypothetical document for better retrieval",
                "purpose": "Improves hit rate for relevant documents"
            },
            {
                "stage": 3,
                "name": "Multi-Signal Retrieval",
                "description": "Parallel dense (vector) and sparse (keyword) search",
                "purpose": "Combines semantic and lexical search signals"
            },
            {
                "stage": 4,
                "name": "RRF Fusion",
                "description": "Reciprocal Rank Fusion of multiple signals",
                "purpose": "Normalizes scores into single ranked list"
            },
            {
                "stage": 5,
                "name": "Cross-Encoder Reranking",
                "description": "Deep semantic comparison of query and chunks",
                "purpose": "Improves precision over bi-encoder retrieval"
            },
            {
                "stage": 6,
                "name": "Hierarchy Expansion",
                "description": "Fetches parent document and sibling chunks",
                "purpose": "Provides full context preventing tunnel vision"
            },
            {
                "stage": 7,
                "name": "LLM Generation",
                "description": "Enhanced response generation with rich context",
                "purpose": "Produces comprehensive, evidence-based answers"
            }
        ],
        "total_stages": 7,
        "implementation_status": "complete"
    }
