"""
Health check endpoints for monitoring
"""
from fastapi import APIRouter
import httpx

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/qdrant")
async def qdrant_health():
    """Qdrant health check endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:6333/health", timeout=5.0)
            if response.status_code == 200:
                return {"status": "healthy", "service": "qdrant"}
            else:
                return {"status": "unhealthy", "service": "qdrant", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "unreachable", "service": "qdrant", "error": str(e)}

@router.get("/ollama")
async def ollama_health():
    """Ollama health check endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "status": "healthy", 
                    "service": "ollama",
                    "models_available": len(models),
                    "models": [model.get("name") for model in models]
                }
            else:
                return {"status": "unhealthy", "service": "ollama", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "unreachable", "service": "ollama", "error": str(e)}
