"""
API package initialization
"""
from fastapi import APIRouter
from .student import router as student_router
from .documents import router as documents_router
from .chunking import router as chunking_router
from .advanced_rag import router as advanced_rag_router
from .data_management import router as data_management_router
from .health import router as health_router

api_router = APIRouter()
api_router.include_router(student_router)
api_router.include_router(documents_router)
api_router.include_router(chunking_router)
api_router.include_router(advanced_rag_router)
api_router.include_router(data_management_router)
api_router.include_router(health_router)
