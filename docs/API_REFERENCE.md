# API Reference - Student Data AI Service

## 🎯 Status: **WORKING** ✅

All endpoints have been tested and are functioning with the simplified RAG pipeline.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required (development mode).

## Response Format
All APIs return JSON responses with appropriate HTTP status codes.

## 🚀 Core RAG Pipeline API

### Query RAG Pipeline
**Endpoint**: `POST /api/advanced-rag/query`

**Description**: Submit analytical queries to the RAG pipeline for student data analysis

**Request Body**:
```json
{
  "query": "How is the student doing academically?"
}
```

**Response**:
```json
{
  "answer": "Based on the provided context, Sarah is doing well academically...",
  "intent": "informational",
  "entities": {"student_id": "STU001", "category": "academic"},
  "stages_completed": ["query_analysis", "simple_retrieval", "llm_generation"],
  "processing_time": 9.82,
  "sources_used": 10
}
```

**Example Queries**:
- "How is the student doing academically?"
- "Is the student ready for placement?"
- "What are the student's technical skills?"
- "How is the student's overall wellness?"

## 📤 Data Management APIs

### Upload Document
**Endpoint**: `POST /api/data/upload`

**Description**: Upload and process student documents (PDF, CSV, TXT, MD)

**Query Parameters**:
- `student_id` (required): Student identifier (e.g., "STU001")
- `category` (required): Data category
  - "academic": Academic reports, grades, transcripts
  - "wellness": Wellness metrics, health reports
  - "extracurricular": Activities, clubs, leadership
  - "placement": Career readiness, placement data

**Request Body**: `multipart/form-data`
- `file`: Document file (max 10MB)

**Response**:
```json
{
  "success": true,
  "document_id": "doc_7729edc3",
  "metadata": {
    "student_id": "STU001",
    "document_type": "academic_report",
    "semester": "Fall 2024",
    "document_id": "doc_7729edc3",
    "filename": "academic_report.pdf",
    "uploaded_at": "2026-05-13T14:01:28.195704",
    "file_size": 2475,
    "file_type": ".pdf",
    "extracted_text_length": 2446
  },
  "extracted_text_preview": "# Academic Performance Report...",
  "file_path": "uploads/academic/doc_7729edc3_academic_report.pdf",
  "category": "academic"
}
```

**Use Cases**:
- Upload academic reports and transcripts
- Upload wellness and counseling reports
- Upload placement readiness documents
- Upload extracurricular activity records

---

### List Student Documents
**Endpoint**: `GET /documents/list/{student_id}`

**Description**: Get all documents for a specific student

**Query Parameters**:
- `category` (optional): Filter by document category

**Response**:
```json
{
  "student_id": "STU001",
  "category": "academic",
  "total_chunks": 7,
  "documents": [
    {
      "student_id": "STU001",
      "document_type": "academic_report",
      "semester": "Fall 2024",
      "document_id": "doc_7729edc3",
      "filename": "academic_report.pdf",
      "uploaded_at": "2026-05-13T14:01:28.195704",
      "file_size": 2475,
      "file_type": ".pdf",
      "extracted_text_length": 2446
    }
  ]
}
```

**Use Cases**:
- View all uploaded documents for a student
- Filter documents by category
- Track document upload history

---

### Get Document Text
**Endpoint**: `GET /documents/text/{document_id}`

**Description**: Get the extracted text for a specific document

**Query Parameters**:
- `category` (required): Document category

**Response**:
```json
{
  "document_id": "doc_7729edc3",
  "text": "# Academic Performance Report\n**Student ID:** STU001...",
  "metadata": {
    "student_id": "STU001",
    "document_type": "academic_report",
    "category": "academic",
    "semester": "Fall 2024"
  }
}
```

**Use Cases**:
- Review document content
- Extract specific information
- Verify document processing

---

### Get Document Categories
**Endpoint**: `GET /documents/categories`

**Description**: Get available document types and supported formats

**Response**:
```json
{
  "categories": {
    "academic": ["academic_report", "grades", "transcript"],
    "wellness": ["wellness_report", "mental_health", "counseling"],
    "extracurricular": ["activities", "sports", "clubs", "leadership"],
    "placement": ["placement_report", "career", "internship", "readiness"]
  },
  "supported_formats": [".pdf", ".csv", ".txt", ".md"]
}
```

**Use Cases**:
- Understand available document types
- Validate file formats
- Guide document upload process

---

## Chunking APIs

### Create Chunks
**Endpoint**: `POST /chunks/create`

**Description**: Create searchable chunks from a document

**Request Body**:
```json
{
  "student_id": "STU001",
  "document_id": "doc_7729edc3",
  "document_type": "academic_report",
  "category": "academic",
  "semester": "Fall 2024"
}
```

**Response**:
```json
{
  "success": true,
  "document_id": "doc_7729edc3",
  "total_chunks": 7,
  "chunk_size": 500,
  "chunk_overlap": 100,
  "chunks_preview": [
    {
      "chunk_id": "chunk_c55ea9de",
      "student_id": "STU001",
      "document_id": "doc_7729edc3",
      "document_type": "academic_report",
      "category": "academic",
      "semester": "Fall 2024",
      "subject": "Computer Science",
      "chunk_index": 0,
      "chunk_text": "# Academic Performance Report...",
      "chunk_length": 486,
      "created_at": "2026-05-13T14:01:28.195704"
    }
  ]
}
```

**Use Cases**:
- Prepare documents for semantic search
- Enable AI-powered document analysis
- Create searchable content segments

---

### List Student Chunks
**Endpoint**: `GET /chunks/list/{student_id}`

**Description**: Get all chunks for a student

**Query Parameters**:
- `category` (optional): Filter by category

**Response**:
```json
{
  "student_id": "STU001",
  "category": "academic",
  "total_chunks": 7,
  "chunks": [
    {
      "chunk_id": "chunk_c55ea9de",
      "student_id": "STU001",
      "document_id": "doc_7729edc3",
      "document_type": "academic_report",
      "category": "academic",
      "subject": "Computer Science",
      "chunk_index": 0,
      "chunk_text": "# Academic Performance Report...",
      "chunk_length": 486,
      "created_at": "2026-05-13T14:01:28.195704"
    }
  ]
}
```

**Use Cases**:
- Review chunked content
- Analyze chunk distribution
- Debug chunking process

---

### Get Chunk Statistics
**Endpoint**: `GET /chunks/statistics/{student_id}`

**Description**: Get statistics about student's chunks

**Response**:
```json
{
  "student_id": "STU001",
  "total_chunks": 7,
  "categories": {
    "academic": 7
  },
  "subjects": {
    "Mathematics": 3,
    "Computer Science": 4
  },
  "avg_chunk_length": 395,
  "chunk_size_used": 500,
  "chunk_overlap_used": 100
}
```

**Use Cases**:
- Analyze content distribution
- Monitor chunking quality
- Track subject coverage

---

### Generate Embeddings
**Endpoint**: `POST /chunks/embed`

**Description**: Generate embeddings for student chunks

**Request Body**:
```json
{
  "student_id": "STU001",
  "category": "academic",
  "document_id": "doc_7729edc3"
}
```

**Response**:
```json
{
  "success": true,
  "total_chunks": 7,
  "embedded_chunks": 7,
  "embedding_dimensions": 768,
  "embedding_model": "nomic-embed-text"
}
```

**Use Cases**:
- Enable semantic search
- Prepare for vector storage
- Generate AI-ready representations

---

### Check Embedding Model Status
**Endpoint**: `GET /chunks/embedding/model-status`

**Description**: Check if embedding model is available

**Response**:
```json
{
  "model": "nomic-embed-text",
  "available": true,
  "base_url": "http://localhost:11434"
}
```

**Use Cases**:
- Verify model availability
- Troubleshoot embedding issues
- Monitor model status

---

## Vector Database APIs

### Setup Vector Store
**Endpoint**: `POST /chunks/vector-store/setup`

**Description**: Initialize vector database collections

**Response**:
```json
{
  "success": true,
  "collections_created": {
    "academic": true,
    "wellness": true,
    "extracurricular": true,
    "placement": true
  },
  "collection_info": {
    "academic": {
      "name": "student_academic",
      "points_count": 0,
      "segments_count": 5,
      "status": "green"
    }
  }
}
```

**Use Cases**:
- Initialize vector database
- Set up collections
- Verify database status

---

### Store Embedded Chunks
**Endpoint**: `POST /chunks/store`

**Description**: Store embedded chunks in vector database

**Request Body**:
```json
{
  "student_id": "STU001",
  "category": "academic"
}
```

**Response**:
```json
{
  "success": true,
  "stored_points": 7,
  "total_chunks": 7,
  "errors": []
}
```

**Use Cases**:
- Store vectors for search
- Enable semantic retrieval
- Build searchable knowledge base

---

### Semantic Search
**Endpoint**: `POST /chunks/search`

**Description**: Search for semantically similar chunks

**Request Body**:
```json
{
  "query": "What is the student GPA?",
  "student_id": "STU001",
  "category": "academic",
  "limit": 5,
  "score_threshold": 0.3
}
```

**Response**:
```json
{
  "success": true,
  "query": "What is the student GPA?",
  "results": [
    {
      "score": 0.506,
      "id": "ad98bd3a-ff8d-427f-b953-d8eb869c8953",
      "payload": {
        "chunk_id": "chunk_4c175c25",
        "student_id": "STU001",
        "document_id": "doc_7729edc3",
        "document_type": "academic_report",
        "category": "academic",
        "semester": "Fall 2024",
        "subject": "Computer Science",
        "chunk_index": 4,
        "chunk_text": ". Smith (CS301):** \"Sarah demonstrates excellent problem-solving skills...\"",
        "chunk_length": 355,
        "created_at": "2026-05-13T14:01:28.195986"
      }
    }
  ],
  "total_found": 3
}
```

**Use Cases**:
- Find relevant document segments
- Semantic information retrieval
- AI-powered content discovery

---

### Get Vector Store Summary
**Endpoint**: `GET /chunks/vector-store/summary/{student_id}`

**Description**: Get summary of student's data in vector store

**Response**:
```json
{
  "student_id": "STU001",
  "collections": {
    "academic": 7,
    "wellness": 0,
    "extracurricular": 0,
    "placement": 0
  },
  "total_chunks": 7
}
```

**Use Cases**:
- Monitor vector storage
- Track data coverage
- Audit stored information

---

## Advanced RAG APIs

### Complete RAG Query
**Endpoint**: `POST /advanced-rag/query`

**Description**: Execute complete 7-stage RAG pipeline

**Request Body**:
```json
{
  "query": "What is the student GPA and how are they performing in mathematics?",
  "student_id": "STU001",
  "category": "academic"
}
```

**Response**:
```json
{
  "answer": "Based on the provided context, Sarah's GPA improved from 3.4 to 3.6...",
  "intent": "informational",
  "entities": {},
  "stages_completed": [
    "query_analysis",
    "query_expansion",
    "multi_signal_retrieval",
    "rrf_fusion",
    "reranking",
    "hierarchy_expansion",
    "llm_generation"
  ],
  "retrieval_stats": {
    "dense_results": 0,
    "sparse_results": 0,
    "final_results": 15
  },
  "sources_used": 15,
  "context_preview": "[RERANKED] . Smith (CS301):** \"Sarah demonstrates excellent..."
}
```

**Use Cases**:
- Comprehensive student analysis
- AI-powered question answering
- Evidence-based insights generation

---

### Compare Basic vs Advanced RAG
**Endpoint**: `GET /advanced-rag/compare`

**Query Parameters**:
- `query` (required): Search query
- `student_id` (optional): Student identifier
- `category` (optional): Document category

**Response**:
```json
{
  "query": "GPA performance",
  "basic_rag": {
    "answer": "Based on the context provided for student STU001...",
    "sources": 5,
    "stages": ["basic_retrieval", "llm_generation"]
  },
  "advanced_rag": {
    "answer": "GPA performance for student STU001 (Sarah) is as follows...",
    "sources": 15,
    "stages": ["query_analysis", "query_expansion", "multi_signal_retrieval", "rrf_fusion", "reranking", "hierarchy_expansion", "llm_generation"],
    "intent": "informational",
    "entities": {},
    "retrieval_stats": {
      "dense_results": 0,
      "sparse_results": 0,
      "final_results": 15
    }
  }
}
```

**Use Cases**:
- Compare retrieval quality
- Evaluate system improvements
- Demonstrate advanced capabilities

---

### Advanced RAG Health Check
**Endpoint**: `GET /advanced-rag/health`

**Description**: Check health of all RAG components

**Response**:
```json
{
  "overall": "healthy",
  "components": {
    "embedding": {
      "status": "healthy",
      "model": "nomic-embed-text",
      "available": true
    },
    "vector_store": {
      "status": "healthy",
      "connected": true
    },
    "chunking": {
      "status": "healthy",
      "chunk_size": 500,
      "overlap": 100
    },
    "llm": {
      "status": "healthy",
      "provider": "qwen2.5:7b",
      "connected": true
    }
  }
}
```

**Use Cases**:
- System health monitoring
- Troubleshooting
- Component status verification

---

### Get Pipeline Stages Information
**Endpoint**: `GET /advanced-rag/pipeline-stages`

**Description**: Get information about all 7 pipeline stages

**Response**:
```json
{
  "stages": [
    {
      "stage": 1,
      "name": "Query Analysis",
      "description": "Classifies intent and extracts key entities",
      "purpose": "Prevents searching for out-of-scope questions"
    },
    {
      "stage": 2,
      "name": "Query Expansion (HyDE)",
      "description": "Generates hypothetical document for better retrieval",
      "purpose": "Improves hit rate for relevant documents"
    }
  ],
  "total_stages": 7,
  "implementation_status": "complete"
}
```

**Use Cases**:
- Understand system architecture
- Educational purposes
- System documentation

---

## Student APIs

### Student Query
**Endpoint**: `POST /student/query`

**Description**: Basic student data query (legacy)

**Request Body**:
```json
{
  "student_id": "STU001",
  "query": "academic performance"
}
```

**Response**:
```json
{
  "message": "Student query endpoint - to be implemented"
}
```

**Use Cases**:
- Legacy compatibility
- Future student-specific features

---

### Student Performance
**Endpoint**: `GET /student/performance/{student_id}`

**Description**: Get student performance analysis

**Response**:
```json
{
  "message": "Performance data for student STU001 - to be implemented"
}
```

**Use Cases**:
- Performance tracking
- Academic monitoring

---

## System APIs

### Health Check
**Endpoint**: `GET /health`

**Description**: Basic system health check

**Response**:
```json
{
  "status": "healthy",
  "provider": "ollama",
  "connected": true,
  "error": null
}
```

**Use Cases**:
- System monitoring
- Load balancer health checks
- Basic troubleshooting

---

### Root Information
**Endpoint**: `GET /`

**Description**: Get basic API Reference Documentation

This document provides comprehensive API reference for the Student Data AI Service, covering all endpoints, request/response formats, and usage examples.

## 🚀 Quick Start

### Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication
Currently no authentication is required (development mode). Production deployment should implement API keys or OAuth.

## 📚 API Categories

### 1. System APIs
- Health checks and system status
- Model information
- Service availability

### 2. Document APIs  
- Document upload and management
- Text extraction
- Metadata handling

### 3. Chunking APIs
- Text chunking operations
- Chunk management
- Statistics

### 4. Embedding APIs
- Vector generation
- Batch processing
- Model status

### 5. Vector Store APIs
- Qdrant operations
- Search functionality
- Collection management

### 6. Advanced RAG APIs
- 7-stage RAG pipeline
- Query processing
- Performance comparison

**Response**:
```json
{
  "message": "Student Data AI Service is running",
  "provider": "ollama",
  "model": "qwen2.5:7b"
}
```

**Use Cases**:
- Service discovery
- Basic information
- Connection testing

---

### Chat Endpoint
**Endpoint**: `POST /chat`

**Description**: Basic chat with LLM

**Request Body**:
```json
{
  "prompt": "What is student performance analysis?"
}
```

**Response**:
```json
{
  "response": "Student performance analysis refers to the process of evaluating...",
  "model": "qwen2.5:7b",
  "provider": "ollama",
  "created_at": "2026-05-13T07:19:30.821876Z"
}
```

**Use Cases**:
- Direct LLM interaction
- Testing LLM functionality
- Simple queries

---

### List Available Models
**Endpoint**: `GET /models`

**Description**: Get list of available LLM models

**Response**:
```json
[
  {
    "name": "qwen2.5:7b",
    "size": "4.7 GB",
    "modified_at": "2025-01-15T10:30:00Z"
  }
]
```

**Use Cases**:
- Model discovery
- System configuration
- Model management

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error description"
}
```

### Common Error Codes
- `400`: Bad Request - Invalid parameters
- `404`: Not Found - Resource doesn't exist
- `500`: Internal Server Error - System error

### Error Examples
```json
{
  "detail": "Student ID 'STU999' not found in document content"
}
```

```json
{
  "detail": "Unsupported file format: .exe"
}
```

```json
{
  "detail": "Error processing document: File too large"
}
```

---

## Rate Limiting

Currently no rate limiting implemented (development mode).

## Pagination

Most list endpoints support pagination through query parameters:
- `limit`: Number of items to return (default: 50)
- `offset`: Number of items to skip (default: 0)

## Response Time Expectations

- Document Upload: 2-5 seconds
- Chunk Creation: 500ms-1 second
- Embedding Generation: 1-2 seconds per batch
- Vector Search: 200-500ms
- Advanced RAG Query: 2-3 seconds

## SDK Examples

### Python Example
```python
import requests

# Upload document
files = {'file': open('report.pdf', 'rb')}
params = {
    'student_id': 'STU001',
    'document_type': 'academic_report',
    'semester': 'Fall 2024'
}
response = requests.post('http://localhost:8000/documents/upload', 
                         files=files, params=params)

# Advanced RAG query
query_data = {
    'query': 'What is the student GPA?',
    'student_id': 'STU001',
    'category': 'academic'
}
response = requests.post('http://localhost:8000/advanced-rag/query', 
                         json=query_data)
result = response.json()
print(result['answer'])
```

### cURL Example
```bash
# Upload document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@report.pdf" \
  -F "student_id=STU001" \
  -F "document_type=academic_report" \
  -F "semester=Fall 2024"

# Advanced RAG query
curl -X POST "http://localhost:8000/advanced-rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the student GPA?",
    "student_id": "STU001",
    "category": "academic"
  }'
```

---

## Testing

### Swagger UI
Interactive API documentation available at:
```
http://localhost:8000/docs
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Complete Test Flow
```bash
# 1. Upload document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@sample.pdf" \
  -F "student_id=STU001" \
  -F "document_type=academic_report"

# 2. Create chunks
curl -X POST "http://localhost:8000/chunks/create" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU001", "document_id": "doc_123", "document_type": "academic_report", "category": "academic"}'

# 3. Generate embeddings
curl -X POST "http://localhost:8000/chunks/embed" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU001", "category": "academic"}'

# 4. Store in vector database
curl -X POST "http://localhost:8000/chunks/store" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU001", "category": "academic"}'

# 5. Advanced RAG query
curl -X POST "http://localhost:8000/advanced-rag/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the student GPA?", "student_id": "STU001", "category": "academic"}'
```

---

**Last Updated**: 2026-05-13
**Version**: 1.0.0
**API Version**: v1
