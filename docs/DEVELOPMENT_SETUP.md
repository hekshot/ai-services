# Development Setup Guide

This guide provides comprehensive setup instructions for developers working on the Student Data AI Service.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Git

### One-Command Setup
```bash
# Clone and setup everything
git clone https://github.com/hekshot/ai-services.git
cd ai-services
make setup
```

## 📋 Detailed Setup

### 1. System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB free
- **OS**: macOS 10.15+, Ubuntu 20.04+, Windows 10+ (WSL2)

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 20GB+ free
- **GPU**: Apple Silicon M1/M2 or NVIDIA GPU (for faster inference)

### 2. Docker Setup

#### Install Docker
```bash
# macOS
brew install --cask docker

# Ubuntu
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Windows
# Download Docker Desktop from https://docker.com
```

#### Verify Docker
```bash
docker --version
docker-compose --version
```

### 3. Project Setup

#### Clone Repository
```bash
git clone https://github.com/hekshot/ai-services.git
cd ai-services
```

#### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required .env variables:**
```env
# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Application
DEBUG=true
LOG_LEVEL=INFO
```

### 4. Docker Services Setup

#### Create Docker Compose File
```yaml
# docker-compose.yml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai-service-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/collections"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    container_name: ai-service-ollama
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    container_name: ai-service-redis
    ports:
      - "6379:6379"
    volumes:
      - ./redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

volumes:
  qdrant_storage:
  ollama_data:
  redis_data:
```

#### Start Services
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Python Environment Setup

#### Create Virtual Environment
```bash
# Create venv
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

#### Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

#### requirements-dev.txt
```txt
# Development tools
pytest==7.4.0
pytest-asyncio==0.21.0
black==23.7.0
flake8==6.0.0
mypy==1.5.0
pre-commit==3.3.3

# Testing tools
httpx==0.24.1
coverage==7.3.0
pytest-cov==4.1.0

# Documentation
mkdocs==1.5.0
mkdocs-material==9.1.0
```

### 6. Model Setup

#### Pull Ollama Models
```bash
# Wait for Ollama to start
sleep 10

# Pull embedding model
docker exec ai-service-ollama ollama pull nomic-embed-text

# Pull LLM model
docker exec ai-service-ollama ollama pull qwen2.5:7b

# Verify models
docker exec ai-service-ollama ollama list
```

#### Alternative: Local Ollama Setup
```bash
# Install Ollama locally (if not using Docker)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve &

# Pull models
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

### 7. Application Setup

#### Initialize Database
```bash
# Setup Qdrant collections
python -c "
from app.services.qdrant_storage_service import QdrantStorageService
storage = QdrantStorageService()
storage.setup_collections()
print('Qdrant collections initialized')
"
```

#### Create Sample Data
```bash
# Create sample documents
python scripts/create_sample_data.py

# Or manually create
mkdir -p sample-documents/{academic,wellness,extracurricular,placement}
echo "Sample academic data..." > sample-documents/academic/sample.txt
```

### 8. Development Server

#### Start Application
```bash
# Activate virtual environment
source venv/bin/activate

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Verify Setup
```bash
# Health check
curl http://localhost:8000/health

# Advanced RAG health
curl http://localhost:8000/advanced-rag/health

# Available models
curl http://localhost:8000/models
```

## 🛠️ Development Workflow

### Code Quality Tools

#### Pre-commit Setup
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

#### .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Testing Setup

#### Test Configuration
```bash
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

#### Run Tests
```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_rag_service.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific markers
pytest -m "unit"
pytest -m "integration"
```

### Debugging Setup

#### VS Code Configuration
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

#### VS Code Debug Configuration
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI",
            "type": "python",
            "request": "launch",
            "program": "uvicorn",
            "args": ["main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

## 🐳 Docker Development

### Development Dockerfile
```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Development Commands
```bash
# Build development image
docker build -f Dockerfile.dev -t ai-service:dev .

# Run with development settings
docker run -it --rm \
  -p 8000:8000 \
  -v $(pwd):/app \
  ai-service:dev
```

## 📊 Monitoring & Logging

### Log Configuration
```python
# Enable debug logging
export LOG_LEVEL=DEBUG

# Structured logging
export LOG_FORMAT=json

# File logging
export LOG_FILE=logs/app.log
```

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Dependencies health
curl http://localhost:8000/advanced-rag/health

# System resources
docker stats
```

## 🔧 Common Issues & Solutions

### Docker Issues
```bash
# Container won't start
docker-compose logs qdrant
docker-compose logs ollama

# Port conflicts
lsof -i :6333
lsof -i :11434

# Permission issues
sudo chown -R $USER:$USER qdrant_storage
```

### Python Issues
```bash
# Import errors
pip install -r requirements.txt --force-reinstall

# Virtual environment issues
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Model Issues
```bash
# Ollama model not found
docker exec ai-service-ollama ollama pull nomic-embed-text

# Model download slow
# Use local Ollama or faster internet connection
```

## 🚀 Performance Optimization

### Development Performance
```bash
# Use faster reload
uvicorn main:app --reload --reload-dir app

# Enable caching
export REDIS_URL=redis://localhost:6379

# Parallel processing
export WORKERS=4
```

### Production Preparation
```bash
# Build production image
docker build -t ai-service:prod .

# Run with multiple workers
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000

# Enable monitoring
export PROMETHEUS_ENABLED=true
```

## 📚 Additional Resources

### Documentation
- [API Reference](API_REFERENCE.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Troubleshooting](TROUBLESHOOTING.md)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Ollama Documentation](https://ollama.ai/documentation)
- [LangChain Documentation](https://python.langchain.com/)

### Community
- [GitHub Issues](https://github.com/hekshot/ai-services/issues)
- [GitHub Discussions](https://github.com/hekshot/ai-services/discussions)

---

**Happy Coding! 🎉**
