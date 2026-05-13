"""
Retrieval service for sparse and dense retrieval in RAG pipeline
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.logging_config import ServiceLogger
from app.exceptions import RetrievalError, handle_service_exception
from app.constants import DEFAULT_SEARCH_LIMIT, DEFAULT_SCORE_THRESHOLD

@dataclass
class RetrievalResult:
    """Result from retrieval operation"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]
    retrieval_method: str

class SparseRetriever:
    """Sparse retrieval using keyword matching and BM25-like scoring"""
    
    def __init__(self):
        self.logger = ServiceLogger("SparseRetriever")
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in self.stop_words and len(word) > 2]
        return list(set(keywords))  # Remove duplicates
    
    def calculate_keyword_score(self, query_keywords: List[str], document_keywords: List[str]) -> float:
        """Calculate keyword matching score"""
        if not query_keywords:
            return 0.0
        
        # Calculate overlap
        matches = len(set(query_keywords) & set(document_keywords))
        total_query = len(query_keywords)
        
        # BM25-like scoring
        score = matches / total_query
        
        # Bonus for exact phrase matches
        return score
    
    def retrieve(self, query: str, documents: List[Dict[str, Any]], limit: int = DEFAULT_SEARCH_LIMIT) -> List[RetrievalResult]:
        """Retrieve documents using sparse retrieval"""
        try:
            self.logger.debug(f"Starting sparse retrieval for: {query[:50]}...")
            
            # Extract keywords from query
            query_keywords = self.extract_keywords(query)
            self.logger.debug(f"Query keywords: {query_keywords}")
            
            results = []
            
            for doc in documents:
                # Extract text from document
                text = doc.get('extracted_text', '') or doc.get('content', '')
                if not text:
                    continue
                
                # Extract keywords from document
                doc_keywords = self.extract_keywords(text)
                
                # Calculate score
                score = self.calculate_keyword_score(query_keywords, doc_keywords)
                
                # Apply threshold
                if score >= DEFAULT_SCORE_THRESHOLD:
                    result = RetrievalResult(
                        content=text[:500] + "..." if len(text) > 500 else text,
                        score=score,
                        source=doc.get('filename', 'unknown'),
                        metadata=doc,
                        retrieval_method="sparse"
                    )
                    results.append(result)
            
            # Sort by score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            self.logger.error("Sparse retrieval failed", exception=e)
            raise handle_service_exception("sparse_retrieve", e, self.logger)
    
    def batch_retrieve(self, queries: List[str], documents: List[Dict[str, Any]], limit: int = DEFAULT_SEARCH_LIMIT) -> Dict[str, List[RetrievalResult]]:
        """Batch retrieve for multiple queries"""
        results = {}
        for query in queries:
            results[query] = self.retrieve(query, documents, limit)
        return results

class DenseRetriever:
    """Dense retrieval using embeddings (placeholder for future implementation)"""
    
    def __init__(self):
        self.logger = ServiceLogger("DenseRetriever")
    
    def retrieve(self, query: str, documents: List[Dict[str, Any]], limit: int = DEFAULT_SEARCH_LIMIT) -> List[RetrievalResult]:
        """Retrieve documents using dense retrieval (simplified)"""
        try:
            self.logger.debug(f"Starting dense retrieval for: {query[:50]}...")
            
            # For now, use simple text similarity as placeholder
            # In production, this would use actual embeddings
            results = []
            
            for doc in documents:
                text = doc.get('extracted_text', '') or doc.get('content', '')
                if not text:
                    continue
                
                # Simple similarity calculation (placeholder)
                query_lower = query.lower()
                text_lower = text.lower()
                
                # Calculate simple similarity
                common_words = set(query_lower.split()) & set(text_lower.split())
                score = len(common_words) / len(query_lower.split()) if query_lower.split() else 0
                
                if score >= DEFAULT_SCORE_THRESHOLD:
                    result = RetrievalResult(
                        content=text[:500] + "..." if len(text) > 500 else text,
                        score=score,
                        source=doc.get('filename', 'unknown'),
                        metadata=doc,
                        retrieval_method="dense"
                    )
                    results.append(result)
            
            # Sort by score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            self.logger.error("Dense retrieval failed", exception=e)
            raise handle_service_exception("dense_retrieve", e, self.logger)

class HybridRetriever:
    """Hybrid retrieval combining sparse and dense methods"""
    
    def __init__(self):
        self.logger = ServiceLogger("HybridRetriever")
        self.sparse_retriever = SparseRetriever()
        self.dense_retriever = DenseRetriever()
    
    def retrieve(self, query: str, documents: List[Dict[str, Any]], limit: int = DEFAULT_SEARCH_LIMIT) -> List[RetrievalResult]:
        """Retrieve using hybrid approach"""
        try:
            self.logger.debug(f"Starting hybrid retrieval for: {query[:50]}...")
            
            # Get sparse results
            sparse_results = self.sparse_retriever.retrieve(query, documents, limit * 2)
            
            # Get dense results
            dense_results = self.dense_retriever.retrieve(query, documents, limit * 2)
            
            # Combine and deduplicate
            all_results = {}
            
            # Add sparse results
            for result in sparse_results:
                key = result.content[:100]  # Use first 100 chars as key
                if key not in all_results:
                    all_results[key] = result
                else:
                    # Combine scores (weighted average)
                    existing = all_results[key]
                    existing.score = (existing.score + result.score) / 2
            
            # Add dense results
            for result in dense_results:
                key = result.content[:100]
                if key not in all_results:
                    all_results[key] = result
                else:
                    # Combine scores (weighted average)
                    existing = all_results[key]
                    existing.score = (existing.score + result.score) / 2
            
            # Convert to list and sort
            combined_results = list(all_results.values())
            combined_results.sort(key=lambda x: x.score, reverse=True)
            
            # Update retrieval method
            for result in combined_results:
                result.retrieval_method = "hybrid"
            
            return combined_results[:limit]
            
        except Exception as e:
            self.logger.error("Hybrid retrieval failed", exception=e)
            raise handle_service_exception("hybrid_retrieve", e, self.logger)
