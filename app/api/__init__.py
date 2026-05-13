"""
API package initialization
"""
from fastapi import APIRouter
from .student import router as student_router
from .documents import router as documents_router
from .chunking import router as chunking_router
from .advanced_rag import router as advanced_rag_router

api_router = APIRouter()
api_router.include_router(student_router)
api_router.include_router(documents_router)
api_router.include_router(chunking_router)
api_router.include_router(advanced_rag_router)
