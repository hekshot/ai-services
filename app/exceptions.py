"""
Custom exceptions for the student data AI service
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.constants import ERROR_MESSAGES, HTTP_STATUS_CODES

class StudentDataServiceException(Exception):
    """Base exception for student data service"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

class DocumentProcessingError(StudentDataServiceException):
    """Exception raised during document processing"""
    
    def __init__(self, message: str, document_id: str = None, student_id: str = None):
        super().__init__(message)
        self.document_id = document_id
        self.student_id = student_id

class ChunkingError(StudentDataServiceException):
    """Exception raised during chunking operations"""
    
    def __init__(self, message: str, document_id: str = None, chunk_count: int = None):
        super().__init__(message)
        self.document_id = document_id
        self.chunk_count = chunk_count

class EmbeddingError(StudentDataServiceException):
    """Exception raised during embedding generation"""
    
    def __init__(self, message: str, chunk_count: int = None, model: str = None):
        super().__init__(message)
        self.chunk_count = chunk_count
        self.model = model

class VectorStoreError(StudentDataServiceException):
    """Exception raised during vector database operations"""
    
    def __init__(self, message: str, collection: str = None, operation: str = None):
        super().__init__(message)
        self.collection = collection
        self.operation = operation

class RAGPipelineError(StudentDataServiceException):
    """Exception raised during RAG pipeline execution"""
    
    def __init__(self, message: str, stage: str = None, query: str = None):
        super().__init__(message)
        self.stage = stage
        self.query = query

class ValidationError(StudentDataServiceException):
    """Exception raised during input validation"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value

class ConfigurationError(StudentDataServiceException):
    """Exception raised due to configuration issues"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message)
        self.config_key = config_key

class ExternalServiceError(StudentDataServiceException):
    """Exception raised when external services are unavailable"""
    
    def __init__(self, message: str, service: str = None, status_code: int = None):
        super().__init__(message)
        self.service = service
        self.status_code = status_code

def create_http_exception(
    error: StudentDataServiceException,
    status_code: int = HTTP_STATUS_CODES["INTERNAL_ERROR"]
) -> HTTPException:
    """Create HTTPException from custom exception"""
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error.message,
            "error_code": error.error_code,
            "details": error.details
        }
    )

def handle_service_exception(
    func_name: str,
    exception: Exception,
    logger
) -> StudentDataServiceException:
    """Convert generic exceptions to service-specific exceptions"""
    
    if isinstance(exception, StudentDataServiceException):
        return exception
    
    # Handle common exceptions
    if "FileNotFoundError" in str(type(exception)):
        return DocumentProcessingError(
            ERROR_MESSAGES["document_not_found"],
            details={"original_error": str(exception)}
        )
    
    if "PermissionError" in str(type(exception)):
        return ValidationError(
            "Permission denied",
            details={"original_error": str(exception)}
        )
    
    if "TimeoutError" in str(type(exception)):
        return ExternalServiceError(
            ERROR_MESSAGES["service_unavailable"],
            service=func_name,
            status_code=HTTP_STATUS_CODES["SERVICE_UNAVAILABLE"]
        )
    
    if "ValueError" in str(type(exception)):
        return ValidationError(
            "Invalid input value",
            details={"original_error": str(exception)}
        )
    
    # Log unexpected exceptions
    logger.error(f"Unexpected exception in {func_name}", exception=exception)
    
    return StudentDataServiceException(
        ERROR_MESSAGES["service_unavailable"],
        details={"original_error": str(exception)}
    )

def safe_execute(
    func,
    *args,
    logger=None,
    error_handler=None,
    **kwargs
):
    """Safely execute a function with error handling"""
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if logger:
            logger.error(f"Error executing {func.__name__}", exception=e)
        
        if error_handler:
            return error_handler(e)
        
        raise e
