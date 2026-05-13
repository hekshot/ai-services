"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    """Chat request model"""
    prompt: str
    model: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    model: str
    provider: str
    created_at: str


class ModelInfo(BaseModel):
    """Model information model"""
    name: str
    size: Optional[int] = None
    modified_at: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    provider: str
    connected: bool
    error: Optional[str] = None
