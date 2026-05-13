"""
API package initialization
"""
from fastapi import APIRouter
from .student import router as student_router

api_router = APIRouter()
api_router.include_router(student_router)
