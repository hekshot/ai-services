"""
Embedding service for student data using Ollama
"""
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class EmbeddingRequest(BaseModel):
    text: str
    model: str = "nomic-embed-text"

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    model: str
    dimensions: int

class OllamaEmbeddingService:
    """Service for generating embeddings using Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "nomic-embed-text"
        self.embedding_url = f"{base_url}/api/embeddings"
    
    async def generate_embedding(self, text: str) -> EmbeddingResponse:
        """Generate embedding for a single text"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": text
                }
                
                async with session.post(self.embedding_url, json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")
                    
                    result = await response.json()
                    
                    if "embedding" not in result:
                        raise Exception("No embedding in response")
                    
                    embedding = result["embedding"]
                    
                    return EmbeddingResponse(
                        embedding=embedding,
                        model=self.model,
                        dimensions=len(embedding)
                    )
        
        except Exception as e:
            raise Exception(f"Error generating embedding: {str(e)}")
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        
        # Process in batches to avoid overwhelming the API
        batch_size = 5
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            # Process each text in the batch concurrently
            tasks = [self.generate_embedding(text) for text in batch]
            batch_embeddings = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for j, result in enumerate(batch_embeddings):
                if isinstance(result, Exception):
                    print(f"Error embedding text {i+j}: {str(result)}")
                    # Create a zero embedding as fallback
                    batch_embeddings[j] = EmbeddingResponse(
                        embedding=[0.0] * 768,  # Default dimension
                        model=self.model,
                        dimensions=768
                    )
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Embed document chunks"""
        if not chunks:
            return []
        
        # Extract chunk texts
        texts = [chunk["chunk_text"] for chunk in chunks]
        
        # Generate embeddings
        embeddings = await self.generate_embeddings_batch(texts)
        
        # Add embeddings to chunks
        embedded_chunks = []
        for i, (chunk, embedding_response) in enumerate(zip(chunks, embeddings)):
            embedded_chunk = chunk.copy()
            embedded_chunk["embedding"] = embedding_response.embedding
            embedded_chunk["embedding_model"] = embedding_response.model
            embedded_chunk["embedding_dimensions"] = embedding_response.dimensions
            embedded_chunks.append(embedded_chunk)
        
        return embedded_chunks
    
    def check_model_availability(self) -> bool:
        """Check if the embedding model is available"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model["name"].startswith("nomic-embed-text") for model in models)
            return False
        except Exception:
            return False
    
    async def get_embedding_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about embeddings"""
        if not chunks:
            return {"total_chunks": 0, "embedding_dimensions": 0}
        
        # Get first chunk's embedding info
        first_chunk = chunks[0] if chunks else {}
        embedding = first_chunk.get("embedding", [])
        
        return {
            "total_chunks": len(chunks),
            "embedding_dimensions": len(embedding),
            "embedding_model": self.model,
            "avg_embedding_norm": sum(sum(x**2 for x in chunk.get("embedding", []))**0.5 for chunk in chunks) / len(chunks) if chunks else 0
        }
