# Student Data AI Service

A comprehensive AI-powered backend for student data analysis, placement tracking, and wellness monitoring using advanced RAG (Retrieval-Augmented Generation) with Qdrant vector database.

## 🚀 Features

- **7-Stage Advanced RAG Pipeline**: Query Analysis, HyDE Expansion, Multi-Signal Retrieval, RRF Fusion, Cross-Encoder Reranking, Hierarchy Expansion, LLM Generation
- **Qdrant Vector Database**: Unified storage for documents, chunks, vectors, and metadata
- **Multi-Modal Document Processing**: PDF, CSV, TXT, Markdown support
- **Student-Centric Architecture**: Academic, Wellness, Extracurricular, Placement data categories
- **Comprehensive Error Handling & Logging**: Production-ready with detailed observability
- **Open-Source Only**: No paid dependencies, fully self-hosted

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11+
- **Operating System**: macOS, Linux, Windows (WSL2)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 10GB free space

### Required Services
- **Qdrant**: Vector database (localhost:6333)
- **Ollama**: Local LLM inference (localhost:11434)
- **Docker**: For Qdrant container (recommended)

## 🛠️ Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/hekshot/ai-services.git
cd ai-services
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Additional dependencies for document processing
pip install pandas pypdf
```

### 4. Set Up Qdrant Vector Database

#### Option A: Docker (Recommended)
```bash
# Pull and run Qdrant
docker run -d --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

# Verify Qdrant is running
curl http://localhost:6333/collections
```

#### Option B: Local Installation
```bash
# Install Qdrant (macOS/Linux)
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-linux-x64.tar.gz | tar xz
./qdrant-linux-x64/qdrant &

# Or using Homebrew (macOS)
brew install qdrant
qdrant &
```

### 5. Set Up Ollama LLM Server

#### Install Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

#### Pull Required Models
```bash
# Start Ollama server
ollama serve &

# Pull embedding model
ollama pull nomic-embed-text

# Pull LLM model (choose one)
ollama pull qwen2.5:7b
# OR
ollama pull llama3.1:8b
# OR
ollama pull mistral:7b

# Verify models
ollama list
```

### 6. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**.env Configuration:**
```env
# LLM Provider Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Alternative: OpenAI (if needed)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_openai_api_key
# OPENAI_MODEL=gpt-3.5-turbo

# Vector Database Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
```

## 🚀 Running the Application

### Start Services
```bash
# 1. Start Qdrant (if not already running)
docker start qdrant

# 2. Start Ollama (if not already running)
ollama serve &

# 3. Start the AI Service
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Verify Setup
```bash
# Check API health
curl http://localhost:8000/health

# Check advanced RAG health
curl http://localhost:8000/advanced-rag/health

# Check available models
curl http://localhost:8000/models
```

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

#### Document Management
```bash
# Upload document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@sample.pdf" \
  -F "student_id=STU001" \
  -F "document_type=academic_report" \
  -F "semester=Fall2024"

# List student documents
curl "http://localhost:8000/documents/list/STU001"

# Get document text
curl "http://localhost:8000/documents/text/DOC123?category=academic"
```

#### Chunking & Embeddings
```bash
# Create chunks
curl -X POST "http://localhost:8000/chunks/create" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU001", "document_id": "DOC123", "category": "academic"}'

# Generate embeddings
curl -X POST "http://localhost:8000/chunks/embed" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU001", "category": "academic"}'

# Store in vector database
curl -X POST "http://localhost:8000/chunks/vector-store/setup"
```

#### Advanced RAG
```bash
# Query with advanced RAG
curl -X POST "http://localhost:8000/advanced-rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the student GPA?",
    "student_id": "STU001",
    "category": "academic"
  }'

# Compare basic vs advanced RAG
curl "http://localhost:8000/advanced-rag/compare?query=student%20performance&student_id=STU001"
```

## 🏗️ Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Advanced RAG   │    │   Qdrant DB     │
│   Backend       │───▶│   Service        │───▶│   (All Data)    │
│   (Port 8000)   │    │   (7 Stages)     │    │   (Port 6333)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Embedding     │    │   Chunking       │    │   Document      │
│   Service       │    │   Service        │    │   Service       │
│   (Ollama)      │    │   (LangChain)    │    │   (PyPDF)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow
1. **Document Upload** → Extract text → Store in Qdrant
2. **Chunking** → Split text → Store chunks in Qdrant
3. **Embedding** → Generate vectors → Store in Qdrant
4. **Query** → 7-stage RAG pipeline → Retrieve from Qdrant → Generate response

### Storage Architecture
```
Qdrant Collections:
├── student_academic     (Documents + Chunks + Vectors)
├── student_wellness     (Documents + Chunks + Vectors)
├── student_extracurricular (Documents + Chunks + Vectors)
└── student_placement    (Documents + Chunks + Vectors)
```

## 🧪 Development & Testing

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run individual test scripts
python test_embeddings.py
python test_search.py
python test_rag_pipeline.py
```

### Sample Data
```bash
# Create sample documents directory
mkdir -p sample-documents/{academic,wellness,extracurricular,placement}

# Add sample files (provided in repository)
cp sample-documents/* sample-documents/
```

### Development Tools
```bash
# Install development dependencies
pip install pytest black flake8 mypy

# Code formatting
black app/

# Linting
flake8 app/

# Type checking
mypy app/
```

## 🔧 Configuration

### Constants & Settings
All configurable values are in `app/constants.py`:

```python
# Chunking Configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Embedding Configuration  
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIMENSIONS = 768

# RAG Configuration
RRF_K_VALUE = 60
RERANK_TOP_K = 30
MAX_CONTEXT_RESULTS = 15
```

### Logging Configuration
```python
# In app/logging_config.py
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Qdrant Connection Failed
```bash
# Check if Qdrant is running
curl http://localhost:6333/collections

# Restart Qdrant
docker restart qdrant
```

#### 2. Ollama Model Not Found
```bash
# Check available models
ollama list

# Pull required model
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

#### 3. Import Errors
```bash
# Check virtual environment
which python

# Reinstall dependencies
pip install -r requirements.txt
```

#### 4. Permission Errors
```bash
# Fix file permissions
chmod -R 755 uploads/
chmod -R 755 chunks/
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
uvicorn main:app --reload --log-level debug
```

## 📖 Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Implementation Guide](docs/IMPLEMENTATION_COMPLETE.md)** - Detailed implementation docs
- **[Roadmap](docs/ROADMAP.md)** - Future development plans
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System architecture details

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and test
4. Submit pull request

### Code Standards
- Follow PEP 8 style guide
- Add comprehensive error handling
- Include logging for all operations
- Write tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Issues**: Report bugs on GitHub Issues
- **Documentation**: Check docs/ folder
- **API Reference**: http://localhost:8000/docs

### Community
- **Discussions**: GitHub Discussions
- **Wiki**: Project Wiki

## 🔄 Version History

- **v1.0.0** - Initial release with basic RAG
- **v2.0.0** - Advanced 7-stage RAG pipeline
- **v2.1.0** - Qdrant-only architecture migration
- **v2.2.0** - Enhanced error handling and logging

---

**Note**: This service is designed for educational and research purposes. Always ensure compliance with data privacy regulations when handling student information.
