"""
Advanced 7-Stage RAG Service Implementation
Using only open-source components
"""
import asyncio
import re
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from app.constants import (
    CHITCHAT_KEYWORDS, NAVIGATIONAL_KEYWORDS, TRANSACTIONAL_KEYWORDS,
    STUDENT_CONTEXT_PATTERNS, STUDENT_ID_PATTERN,
    EMBEDDING_BATCH_SIZE, DEFAULT_SCORE_THRESHOLD, DEFAULT_SEARCH_LIMIT,
    RRF_K_VALUE, RERANK_TOP_K, HIERARCHY_EXPANSION_LIMIT,
    MAX_CONTEXT_RESULTS, MAX_EXPANDED_RESULTS,
    RESPONSE_TEMPLATES
)
from app.logging_config import ServiceLogger
from app.exceptions import (
    RAGPipelineError, VectorStoreError, EmbeddingError,
    handle_service_exception, safe_execute
)

class QueryIntent(Enum):
    NAVIGATIONAL = "navigational"
    INFORMATIONAL = "informational"
    TRANSACTIONAL = "transactional"
    CHITCHAT = "chitchat"

@dataclass
class SearchResult:
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]
    stage: str

class AdvancedRAGService:
    """7-Stage RAG Implementation"""
    
    def __init__(self):
        self.logger = ServiceLogger("AdvancedRAGService")
        self.student_context_patterns = STUDENT_CONTEXT_PATTERNS
    
    # ========== STAGE 1: Query Analysis ==========
    async def analyze_query(self, query: str) -> Tuple[QueryIntent, Dict[str, Any]]:
        """Classify intent and extract entities"""
        try:
            self.logger.info(f"Analyzing query: {query[:100]}...")
            query_lower = query.lower()
            
            # Intent classification
            if any(word in query_lower for word in CHITCHAT_KEYWORDS):
                self.logger.debug("Query classified as CHITCHAT")
                return QueryIntent.CHITCHAT, {}
            elif any(word in query_lower for word in NAVIGATIONAL_KEYWORDS):
                self.logger.debug("Query classified as NAVIGATIONAL")
                return QueryIntent.NAVIGATIONAL, {}
            elif any(word in query_lower for word in TRANSACTIONAL_KEYWORDS):
                self.logger.debug("Query classified as TRANSACTIONAL")
                return QueryIntent.TRANSACTIONAL, {}
            else:
                self.logger.debug("Query classified as INFORMATIONAL")
            
            # Entity extraction
            entities = {}
            for category, keywords in self.student_context_patterns.items():
                if any(keyword in query_lower for keyword in keywords):
                    entities['category'] = category
                    self.logger.debug(f"Extracted category: {category}")
                    break
            
            # Extract student ID if present
            student_id_match = re.search(STUDENT_ID_PATTERN, query_lower)
            if student_id_match:
                entities['student_id'] = student_id_match.group(1).upper()
                self.logger.debug(f"Extracted student_id: {entities['student_id']}")
            
            return QueryIntent.INFORMATIONAL, entities
            
        except Exception as e:
            self.logger.error("Failed to analyze query", exception=e)
            raise handle_service_exception("analyze_query", e, self.logger)
    
    # ========== STAGE 2: Query Expansion (HyDE) ==========
    async def expand_query_hyde(self, query: str) -> str:
        """Generate hypothetical document for better retrieval"""
        try:
            self.logger.info(f"Expanding query with HyDE: {query[:50]}...")
            
            expansion_prompt = f"""
            Based on the question: "{query}"
            
            Generate a hypothetical ideal answer that would contain the information needed:
            """
            
            # Use Ollama to generate hypothetical document
            from src.providers import get_provider
            provider = get_provider()
            response = await provider.generate(expansion_prompt, stream=False)
            hypothetical_doc = response.get("response", "")
            
            if hypothetical_doc:
                # Combine original query with hypothetical document
                expanded_query = f"{query} {hypothetical_doc}"
                self.logger.debug(f"Query expanded successfully")
                return expanded_query
            else:
                self.logger.warning("HyDE expansion returned empty response, using original query")
                return query
                
        except Exception as e:
            self.logger.error("Failed to expand query with HyDE", exception=e)
            # Fallback to original query if generation fails
            return query
    
    # ========== STAGE 3: Multi-Signal Retrieval ==========
    async def multi_signal_retrieval(self, query: str, entities: Dict[str, Any]) -> List[SearchResult]:
        """Parallel dense and sparse retrieval"""
        try:
            self.logger.info(f"Starting multi-signal retrieval for: {query[:50]}...")
            results = []
            
            # Dense Retrieval (Vector Search)
            try:
                dense_results = await self.dense_retrieval(query, entities)
                results.extend(dense_results)
                self.logger.debug(f"Dense retrieval found {len(dense_results)} results")
            except Exception as e:
                self.logger.error("Dense retrieval failed", exception=e)
                # Continue with sparse retrieval even if dense fails
            
            # Sparse Retrieval (BM25-like keyword matching)
            try:
                sparse_results = await self.sparse_retrieval(query, entities)
                results.extend(sparse_results)
                self.logger.debug(f"Sparse retrieval found {len(sparse_results)} results")
            except Exception as e:
                self.logger.error("Sparse retrieval failed", exception=e)
            
            self.logger.info(f"Multi-signal retrieval completed with {len(results)} total results")
            return results
            
        except Exception as e:
            self.logger.error("Multi-signal retrieval failed", exception=e)
            raise handle_service_exception("multi_signal_retrieval", e, self.logger)
    
    async def dense_retrieval(self, query: str, entities: Dict[str, Any]) -> List[SearchResult]:
        """Vector-based semantic search"""
        try:
            self.logger.debug("Starting dense retrieval")
            
            from app.services.embedding_service import OllamaEmbeddingService
            from app.services.vectorstore_service import StudentVectorStore
            
            # Generate embedding
            embedding_service = OllamaEmbeddingService()
            query_embedding = await embedding_service.generate_embedding(query)
            
            if not query_embedding or not query_embedding.embedding:
                self.logger.warning("Failed to generate query embedding")
                return []
            
            # Search in vector store
            vector_store = StudentVectorStore()
            if not vector_store.connect():
                raise VectorStoreError("Failed to connect to vector store")
            
            search_results = vector_store.search_similar_chunks(
                query_embedding=query_embedding.embedding,
                category=entities.get('category'),
                student_id=entities.get('student_id'),
                limit=DEFAULT_SEARCH_LIMIT,
                score_threshold=DEFAULT_SCORE_THRESHOLD
            )
            
            results = [
                SearchResult(
                    content=result['payload']['chunk_text'],
                    score=result['score'],
                    source='dense_vector',
                    metadata=result['payload'],
                    stage='dense_retrieval'
                )
                for result in search_results
            ]
            
            self.logger.debug(f"Dense retrieval completed with {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error("Dense retrieval failed", exception=e)
            raise handle_service_exception("dense_retrieval", e, self.logger)
    
    async def sparse_retrieval(self, query: str, entities: Dict[str, Any]) -> List[SearchResult]:
        """Keyword-based retrieval (BM25-like)"""
        try:
            self.logger.debug("Starting sparse retrieval")
            
            from app.services.chunking_service import DocumentChunker
            
            chunker = DocumentChunker()
            chunks = chunker.get_student_chunks(
                entities.get('student_id'),
                entities.get('category')
            )
            
            if not chunks:
                self.logger.debug("No chunks found for sparse retrieval")
                return []
            
            # Simple keyword matching (BM25 approximation)
            query_terms = set(query.lower().split())
            scored_chunks = []
            
            for chunk in chunks:
                chunk_text = chunk['chunk_text'].lower()
                chunk_terms = set(chunk_text.split())
                
                # Calculate relevance score based on term overlap
                overlap = len(query_terms & chunk_terms)
                if overlap > 0:
                    score = overlap / len(query_terms)
                    scored_chunks.append((chunk, score))
            
            # Sort by score and return top results
            scored_chunks.sort(key=lambda x: x[1], reverse=True)
            
            results = [
                SearchResult(
                    content=chunk['chunk_text'],
                    score=score,
                    source='sparse_keyword',
                    metadata=chunk,
                    stage='sparse_retrieval'
                )
                for chunk, score in scored_chunks[:DEFAULT_SEARCH_LIMIT]
            ]
            
            self.logger.debug(f"Sparse retrieval completed with {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error("Sparse retrieval failed", exception=e)
            raise handle_service_exception("sparse_retrieval", e, self.logger)
    
    # ========== STAGE 4: RRF Fusion ==========
    def rrf_fusion(self, results: List[SearchResult], k: int = RRF_K_VALUE) -> List[SearchResult]:
        """Reciprocal Rank Fusion of multiple search signals"""
        try:
            self.logger.debug(f"Starting RRF fusion with {len(results)} results")
            
            if not results:
                self.logger.debug("No results to fuse")
                return []
            
            # Group results by content
            content_groups = {}
            for result in results:
                content_key = result.content[:100]  # Use first 100 chars as key
                if content_key not in content_groups:
                    content_groups[content_key] = []
                content_groups[content_key].append(result)
            
            # Calculate RRF scores
            fused_results = []
            for content, group_results in content_groups.items():
                rrf_score = 0
                merged_result = group_results[0]  # Use first result as base
                
                for i, result in enumerate(group_results):
                    # Rank within each stage (simplified)
                    stage_rank = 1  # Would need actual ranking from each stage
                    rrf_score += 1.0 / (k + stage_rank)
                
                merged_result.score = rrf_score
                merged_result.stage = 'rrf_fusion'
                fused_results.append(merged_result)
            
            # Sort by RRF score
            fused_results.sort(key=lambda x: x.score, reverse=True)
            top_results = fused_results[:RERANK_TOP_K]  # Return top 30 for reranking
            
            self.logger.debug(f"RRF fusion completed with {len(top_results)} results")
            return top_results
            
        except Exception as e:
            self.logger.error("RRF fusion failed", exception=e)
            raise handle_service_exception("rrf_fusion", e, self.logger)
    
    # ========== STAGE 5: Cross-Encoder Reranking ==========
    async def rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Cross-encoder reranking for precision"""
        try:
            self.logger.debug(f"Starting reranking with {len(results)} results")
            
            if len(results) <= 1:
                self.logger.debug("Too few results to rerank")
                return results
            
            # Simplified reranking using semantic similarity
            from app.services.embedding_service import OllamaEmbeddingService
            
            embedding_service = OllamaEmbeddingService()
            query_embedding = await embedding_service.generate_embedding(query)
            
            if not query_embedding or not query_embedding.embedding:
                self.logger.warning("Failed to generate query embedding for reranking")
                return results[:10]
            
            reranked = []
            for result in results:
                try:
                    content_embedding = await embedding_service.generate_embedding(result.content)
                    
                    if content_embedding and content_embedding.embedding:
                        # Calculate cosine similarity
                        similarity = self.cosine_similarity(query_embedding.embedding, content_embedding.embedding)
                        result.score = similarity
                        result.stage = 'reranked'
                        reranked.append(result)
                    else:
                        self.logger.warning(f"Failed to generate content embedding for result")
                        
                except Exception as e:
                    self.logger.error(f"Failed to rerank individual result", exception=e)
                    # Keep original result with lower score
                    result.stage = 'reranking_failed'
                    reranked.append(result)
            
            reranked.sort(key=lambda x: x.score, reverse=True)
            top_results = reranked[:10]  # Return top 10
            
            self.logger.debug(f"Reranking completed with {len(top_results)} results")
            return top_results
            
        except Exception as e:
            self.logger.error("Reranking failed", exception=e)
            # Return original results if reranking fails
            return results[:10]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)
    
    # ========== STAGE 6: Hierarchy Expansion ==========
    async def expand_hierarchy(self, results: List[SearchResult]) -> List[SearchResult]:
        """Expand context with parent/sibling chunks"""
        try:
            self.logger.debug(f"Starting hierarchy expansion with {len(results)} results")
            expanded_results = []
            
            for result in results:
                expanded_results.append(result)
                
                # Get sibling chunks from same document
                try:
                    from app.services.chunking_service import DocumentChunker
                    
                    chunker = DocumentChunker()
                    document_id = result.metadata.get('document_id')
                    student_id = result.metadata.get('student_id')
                    
                    if document_id and student_id:
                        document_chunks = chunker.get_document_chunks(document_id)
                        
                        # Add surrounding chunks (±2 from current chunk)
                        current_index = result.metadata.get('chunk_index', 0)
                        
                        for chunk in document_chunks:
                            chunk_index = chunk.get('chunk_index', 0)
                            if abs(chunk_index - current_index) <= HIERARCHY_EXPANSION_LIMIT and chunk_index != current_index:
                                sibling_result = SearchResult(
                                    content=chunk['chunk_text'],
                                    score=0.8,  # Lower score for context
                                    source='hierarchy_expansion',
                                    metadata=chunk,
                                    stage='hierarchy_expansion'
                                )
                                expanded_results.append(sibling_result)
                                
                except Exception as e:
                    self.logger.error(f"Hierarchy expansion failed for document {document_id}", exception=e)
                    # Continue with other results even if expansion fails for one
            
            # Limit total results
            final_results = expanded_results[:MAX_EXPANDED_RESULTS]
            self.logger.debug(f"Hierarchy expansion completed with {len(final_results)} results")
            return final_results
            
        except Exception as e:
            self.logger.error("Hierarchy expansion failed", exception=e)
            # Return original results if expansion fails
            return results[:MAX_EXPANDED_RESULTS]
    
    # ========== STAGE 7: Enhanced LLM Generation ==========
    async def generate_response(self, query: str, context_results: List[SearchResult]) -> Dict[str, Any]:
        """Generate final response with rich context"""
        try:
            self.logger.debug(f"Generating response with {len(context_results)} context results")
            
            # Build context package
            context_text = "\n\n".join([
                f"[{result.stage.upper()}] {result.content}"
                for result in context_results[:MAX_CONTEXT_RESULTS]  # Use top results
            ])
            
            # Enhanced prompt
            prompt = f"""
            You are an AI assistant for student data analysis. Answer the following question using ONLY the provided context.
            
            Question: {query}
            
            Context:
            {context_text}
            
            Instructions:
            1. Answer based ONLY on the provided context
            2. If context doesn't contain the answer, say "I don't have enough information to answer this question"
            3. Provide specific details and evidence from the context
            4. Include relevant scores, metrics, or data points mentioned
            5. Be concise but comprehensive
            
            Answer:
            """
            
            from src.providers import get_provider
            provider = get_provider()
            response = await provider.generate(prompt, stream=False)
            
            answer = response.get("response", "")
            
            if not answer:
                self.logger.warning("LLM returned empty response")
                answer = RESPONSE_TEMPLATES["no_results"]
            
            return {
                "answer": answer,
                "sources_used": len(context_results),
                "context_preview": context_text[:500] + "..." if len(context_text) > 500 else context_text,
                "retrieval_stages": list(set(r.stage for r in context_results))
            }
            
        except Exception as e:
            self.logger.error("Failed to generate LLM response", exception=e)
            return {
                "answer": RESPONSE_TEMPLATES["error"],
                "sources_used": 0,
                "context_preview": "",
                "retrieval_stages": []
            }
    
    # ========== Complete Pipeline ==========
    async def advanced_rag_pipeline(self, query: str) -> Dict[str, Any]:
        """Complete 7-stage RAG pipeline"""
        start_time = time.time()
        stages_completed = []
        
        try:
            self.logger.info(f"Starting advanced RAG pipeline for: {query[:100]}...")
            
            # Stage 1: Query Analysis
            try:
                intent, entities = await self.analyze_query(query)
                stages_completed.append("query_analysis")
                self.logger.debug(f"Stage 1 completed: {intent.value}")
            except Exception as e:
                self.logger.error("Stage 1 (Query Analysis) failed", exception=e)
                raise handle_service_exception("query_analysis", e, self.logger)
            
            if intent == QueryIntent.CHITCHAT:
                self.logger.info("Query classified as chitchat, returning early response")
                return {
                    "answer": RESPONSE_TEMPLATES["chitchat"],
                    "intent": intent.value,
                    "stages_completed": stages_completed
                }
            
            # Stage 2: Query Expansion
            try:
                expanded_query = await self.expand_query_hyde(query)
                stages_completed.append("query_expansion")
                self.logger.debug("Stage 2 completed: query_expansion")
            except Exception as e:
                self.logger.error("Stage 2 (Query Expansion) failed", exception=e)
                # Continue with original query if expansion fails
                expanded_query = query
                stages_completed.append("query_expansion")
            
            # Stage 3: Multi-Signal Retrieval
            try:
                retrieval_results = await self.multi_signal_retrieval(expanded_query, entities)
                stages_completed.append("multi_signal_retrieval")
                self.logger.debug(f"Stage 3 completed: multi_signal_retrieval ({len(retrieval_results)} results)")
            except Exception as e:
                self.logger.error("Stage 3 (Multi-Signal Retrieval) failed", exception=e)
                retrieval_results = []
                stages_completed.append("multi_signal_retrieval")
            
            if not retrieval_results:
                self.logger.warning("No retrieval results found")
                return {
                    "answer": RESPONSE_TEMPLATES["no_results"],
                    "intent": intent.value,
                    "entities": entities,
                    "stages_completed": stages_completed
                }
            
            # Stage 4: RRF Fusion
            try:
                fused_results = self.rrf_fusion(retrieval_results)
                stages_completed.append("rrf_fusion")
                self.logger.debug(f"Stage 4 completed: rrf_fusion ({len(fused_results)} results)")
            except Exception as e:
                self.logger.error("Stage 4 (RRF Fusion) failed", exception=e)
                # Continue with original results if fusion fails
                fused_results = retrieval_results[:RERANK_TOP_K]
                stages_completed.append("rrf_fusion")
            
            # Stage 5: Reranking
            try:
                reranked_results = await self.rerank_results(query, fused_results)
                stages_completed.append("reranking")
                self.logger.debug(f"Stage 5 completed: reranking ({len(reranked_results)} results)")
            except Exception as e:
                self.logger.error("Stage 5 (Reranking) failed", exception=e)
                # Continue with fused results if reranking fails
                reranked_results = fused_results[:10]
                stages_completed.append("reranking")
            
            # Stage 6: Hierarchy Expansion
            try:
                expanded_results = await self.expand_hierarchy(reranked_results)
                stages_completed.append("hierarchy_expansion")
                self.logger.debug(f"Stage 6 completed: hierarchy_expansion ({len(expanded_results)} results)")
            except Exception as e:
                self.logger.error("Stage 6 (Hierarchy Expansion) failed", exception=e)
                # Continue with reranked results if expansion fails
                expanded_results = reranked_results
                stages_completed.append("hierarchy_expansion")
            
            # Stage 7: LLM Generation
            try:
                final_response = await self.generate_response(query, expanded_results)
                stages_completed.append("llm_generation")
                self.logger.debug("Stage 7 completed: llm_generation")
            except Exception as e:
                self.logger.error("Stage 7 (LLM Generation) failed", exception=e)
                final_response = {
                    "answer": RESPONSE_TEMPLATES["error"],
                    "sources_used": 0,
                    "context_preview": "",
                    "retrieval_stages": []
                }
                stages_completed.append("llm_generation")
            
            # Calculate total duration
            total_duration = time.time() - start_time
            self.logger.log_rag_pipeline(query, stages_completed, total_duration)
            
            return {
                **final_response,
                "intent": intent.value,
                "entities": entities,
                "original_query": query,
                "expanded_query": expanded_query[:200] + "..." if len(expanded_query) > 200 else expanded_query,
                "stages_completed": stages_completed,
                "retrieval_stats": {
                    "dense_results": len([r for r in retrieval_results if r.stage == 'dense_retrieval']),
                    "sparse_results": len([r for r in retrieval_results if r.stage == 'sparse_retrieval']),
                    "final_results": len(expanded_results)
                },
                "processing_time": total_duration
            }
            
        except Exception as e:
            total_duration = time.time() - start_time
            self.logger.error(f"Advanced RAG pipeline failed after {total_duration:.2f}s", exception=e)
            
            return {
                "answer": RESPONSE_TEMPLATES["error"],
                "error": str(e),
                "stages_completed": stages_completed,
                "processing_time": total_duration
            }
