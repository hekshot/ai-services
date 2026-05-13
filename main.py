"""
Student Data AI Service - FastAPI service for student data analysis
"""
from fastapi import FastAPI, HTTPException
from src.providers import get_provider
from src.models import ChatRequest, ChatResponse, ModelInfo, HealthResponse
from src.config import Config
from app.api import api_router
import os

# Validate configuration
Config.validate()

app = FastAPI(
    title="Student Data AI Service",
    description="AI-powered student data analysis and placement assistance",
    version="1.0.0"
)

# Include student API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Get service information"""
    return {
        "message": "AI Service is running",
        "provider": Config.LLM_PROVIDER,
        "model": Config.LLM_MODEL
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if LLM provider is accessible"""
    try:
        provider_instance = get_provider()
        is_healthy = await provider_instance.health_check()
        
        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            provider=Config.LLM_PROVIDER,
            connected=is_healthy
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            provider=Config.LLM_PROVIDER,
            connected=False,
            error=str(e)
        )


@app.get("/models", response_model=list[ModelInfo])
async def list_models():
    """List available LLM models"""
    try:
        provider_instance = get_provider()
        models = await provider_instance.list_models()
        
        return [
            ModelInfo(
                name=model.get("name", ""),
                size=model.get("size"),
                modified_at=model.get("modified_at")
            )
            for model in models
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a prompt to LLM provider and get a response"""
    try:
        provider_instance = get_provider()
        
        # Use request model if provided, otherwise use configured model
        model_to_use = request.model if request.model else provider_instance.model
        
        # Temporarily update provider model if different
        original_model = provider_instance.model
        provider_instance.model = model_to_use
        
        try:
            data = await provider_instance.generate(request.prompt, request.stream)
            return ChatResponse(
                response=data.get("response", ""),
                model=data.get("model", model_to_use),
                provider=Config.LLM_PROVIDER,
                created_at=data.get("created_at", "")
            )
        finally:
            # Restore original model
            provider_instance.model = original_model
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@app.post("/generate")
async def generate_text(request: ChatRequest):
    """Alternative endpoint for text generation"""
    return await chat(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
