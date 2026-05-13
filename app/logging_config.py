"""
Logging configuration for the student data AI service
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from app.constants import LOG_LEVEL, LOG_FORMAT

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Add color to levelname
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)

def setup_logging(
    level: str = LOG_LEVEL,
    log_format: str = LOG_FORMAT,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_colors: bool = True
) -> None:
    """Setup logging configuration"""
    
    # Create logs directory if file logging is enabled
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if enable_colors and enable_console:
        formatter = ColoredFormatter(log_format)
    else:
        formatter = logging.Formatter(log_format)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)

class ServiceLogger:
    """Enhanced logger with additional functionality"""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.name = name
    
    def debug(self, message: str, **kwargs):
        """Log debug message with additional context"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with additional context"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with additional context"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with exception details"""
        if exception:
            self.logger.error(f"{message}: {str(exception)}", exc_info=True, extra=kwargs)
        else:
            self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message with exception details"""
        if exception:
            self.logger.critical(f"{message}: {str(exception)}", exc_info=True, extra=kwargs)
        else:
            self.logger.critical(message, extra=kwargs)
    
    def log_api_request(self, method: str, endpoint: str, student_id: Optional[str] = None):
        """Log API request"""
        message = f"API {method} {endpoint}"
        if student_id:
            message += f" (student: {student_id})"
        self.info(message)
    
    def log_api_response(self, method: str, endpoint: str, status_code: int, duration: float):
        """Log API response"""
        message = f"API {method} {endpoint} -> {status_code} ({duration:.2f}s)"
        self.info(message)
    
    def log_document_processing(self, document_id: str, student_id: str, stage: str, status: str):
        """Log document processing stage"""
        message = f"Document {document_id} ({student_id}) - {stage}: {status}"
        self.info(message)
    
    def log_chunking_operation(self, document_id: str, chunk_count: int, duration: float):
        """Log chunking operation"""
        message = f"Chunked {document_id} into {chunk_count} chunks ({duration:.2f}s)"
        self.info(message)
    
    def log_embedding_generation(self, chunk_count: int, duration: float):
        """Log embedding generation"""
        message = f"Generated embeddings for {chunk_count} chunks ({duration:.2f}s)"
        self.info(message)
    
    def log_vector_search(self, query: str, results_count: int, duration: float):
        """Log vector search operation"""
        message = f"Vector search for '{query[:50]}...' found {results_count} results ({duration:.2f}s)"
        self.info(message)
    
    def log_rag_pipeline(self, query: str, stages_completed: list, duration: float):
        """Log RAG pipeline execution"""
        message = f"RAG pipeline for '{query[:50]}...' completed stages: {', '.join(stages_completed)} ({duration:.2f}s)"
        self.info(message)

# Initialize logging on import
setup_logging()
