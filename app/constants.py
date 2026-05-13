"""
Application constants and configuration values
"""

# Chunking Configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MAX_CHUNKS_PER_DOCUMENT = 100

# Embedding Configuration
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIMENSIONS = 768
EMBEDDING_BATCH_SIZE = 5
EMBEDDING_TIMEOUT = 30

# Vector Database Configuration
VECTOR_SIZE = 768
VECTOR_DISTANCE = "COSINE"
DEFAULT_SCORE_THRESHOLD = 0.3
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 50

# RAG Configuration
RRF_K_VALUE = 60
RERANK_TOP_K = 30
HIERARCHY_EXPANSION_LIMIT = 2
MAX_CONTEXT_RESULTS = 15
MAX_EXPANDED_RESULTS = 15

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_FILE_TYPES = [".pdf", ".csv", ".txt", ".md"]
SUPPORTED_DOCUMENT_TYPES = {
    "academic": ["academic_report", "grades", "transcript"],
    "wellness": ["wellness_report", "mental_health", "counseling"],
    "extracurricular": ["activities", "sports", "clubs", "leadership"],
    "placement": ["placement_report", "career", "internship", "readiness"]
}

# Query Analysis Configuration
CHITCHAT_KEYWORDS = ["hello", "hi", "how are you", "chat"]
NAVIGATIONAL_KEYWORDS = ["show me", "navigate", "find", "get"]
TRANSACTIONAL_KEYWORDS = ["analyze", "compare", "summarize", "recommend"]

STUDENT_CONTEXT_PATTERNS = {
    'academic': ['gpa', 'grade', 'course', 'semester', 'exam', 'assignment', 'faculty'],
    'wellness': ['stress', 'mental', 'health', 'counseling', 'wellness', 'support'],
    'placement': ['job', 'career', 'placement', 'company', 'skills', 'internship'],
    'extracurricular': ['activity', 'club', 'sport', 'leadership', 'volunteer']
}

# Student ID Pattern
STUDENT_ID_PATTERN = r'(stu\d{3}|student\s*\d+)'

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# API Configuration
DEFAULT_API_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 1

# Ollama Configuration
OLLAMA_DEFAULT_MODEL = "qwen2.5:7b"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 60

# Qdrant Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION_PREFIX = "student_"
QDRANT_TIMEOUT = 10

# Collection Names
ACADEMIC_COLLECTION = "student_academic"
WELLNESS_COLLECTION = "student_wellness"
EXTRACURRICULAR_COLLECTION = "student_extracurricular"
PLACEMENT_COLLECTION = "student_placement"

# Error Messages
ERROR_MESSAGES = {
    "document_not_found": "Document not found",
    "student_not_found": "Student not found",
    "invalid_file_type": "Unsupported file type",
    "file_too_large": "File size exceeds limit",
    "embedding_failed": "Failed to generate embeddings",
    "vector_store_error": "Vector database error",
    "chunking_failed": "Failed to chunk document",
    "query_analysis_failed": "Failed to analyze query",
    "llm_generation_failed": "Failed to generate response",
    "invalid_student_id": "Invalid student ID format",
    "service_unavailable": "Service temporarily unavailable"
}

# Response Templates
RESPONSE_TEMPLATES = {
    "chitchat": "I'm here to help with student data analysis. Please ask me about academic performance, wellness, placement, or extracurricular activities.",
    "no_results": "I couldn't find relevant information to answer your question.",
    "error": "An error occurred while processing your request. Please try again.",
}

# Guardrails Thresholds
MIN_CONTEXT_SCORE = 0.3
MIN_ANSWER_QUALITY_SCORE = 0.5
MAX_HALLUCINATION_RISK = 0.4
MIN_FACTUAL_ACCURACY = 0.6

# Status Codes
HTTP_STATUS_CODES = {
    "OK": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "INTERNAL_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503
}
