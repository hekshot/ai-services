# Student Data AI Service - Makefile

.PHONY: help setup dev prod test clean docker-build docker-up docker-down logs health

# Default target
help:
	@echo "Student Data AI Service - Development Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup      - Complete development setup"
	@echo "  install    - Install Python dependencies"
	@echo "  docker-setup - Setup Docker services"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev        - Start development server"
	@echo "  test       - Run tests"
	@echo "  lint       - Run code linting"
	@echo "  format     - Format code"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up    - Start Docker services"
	@echo "  docker-down  - Stop Docker services"
	@echo "  logs        - Show service logs"
	@echo ""
	@echo "Utility Commands:"
	@echo "  health     - Check service health"
	@echo "  clean      - Clean up temporary files"
	@echo "  models     - Pull required models"

# Complete setup
setup: install docker-setup models
	@echo "✅ Setup complete! Run 'make dev' to start development."

# Install Python dependencies
install:
	@echo "📦 Installing Python dependencies..."
	python -m venv venv
	@echo "source venv/bin/activate" > .activate
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	./venv/bin/pip install pandas pypdf
	@echo "✅ Dependencies installed"

# Setup Docker services
docker-setup:
	@echo "🐳 Setting up Docker services..."
	docker-compose up -d qdrant ollama
	sleep 10
	@echo "✅ Docker services started"

# Pull required models
models:
	@echo "🤖 Pulling AI models..."
	docker exec ai-service-ollama ollama pull nomic-embed-text
	docker exec ai-service-ollama ollama pull qwen2.5:7b
	@echo "✅ Models pulled"

# Development server
dev:
	@echo "🚀 Starting development server..."
	./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production server
prod:
	@echo "🚀 Starting production server..."
	./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Run tests
test:
	@echo "🧪 Running tests..."
	./venv/bin/python -m pytest tests/ -v --cov=app --cov-report=html

# Code linting
lint:
	@echo "🔍 Running linting..."
	./venv/bin/flake8 app/
	./venv/bin/mypy app/

# Code formatting
format:
	@echo "✨ Formatting code..."
	./venv/bin/black app/
	./venv/bin/isort app/

# Docker build
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t ai-service:latest .

# Docker up
docker-up:
	@echo "🐳 Starting all services..."
	docker-compose up -d

# Docker down
docker-down:
	@echo "🐳 Stopping all services..."
	docker-compose down

# Show logs
logs:
	docker-compose logs -f

# Health check
health:
	@echo "🏥 Checking service health..."
	@echo "=== API Health ==="
	curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API not responding"
	@echo ""
	@echo "=== Advanced RAG Health ==="
	curl -s http://localhost:8000/advanced-rag/health | python -m json.tool || echo "❌ Advanced RAG not responding"
	@echo ""
	@echo "=== Qdrant Health ==="
	curl -s http://localhost:6333/collections | python -m json.tool || echo "❌ Qdrant not responding"
	@echo ""
	@echo "=== Ollama Health ==="
	curl -s http://localhost:11434/api/tags | python -m json.tool || echo "❌ Ollama not responding"

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	@echo "✅ Clean up complete"

# Initialize database
init-db:
	@echo "🗄️ Initializing Qdrant collections..."
	./venv/bin/python -c "
from app.services.qdrant_storage_service import QdrantStorageService
storage = QdrantStorageService()
storage.setup_collections()
print('✅ Database initialized')
"

# Create sample data
sample-data:
	@echo "📄 Creating sample data..."
	mkdir -p sample-documents/{academic,wellness,extracurricular,placement}
	echo "Student STU001 has a GPA of 3.8 in Fall 2024 semester." > sample-documents/academic/stu001_grades.txt
	echo "Student shows signs of stress during exam period." > sample-documents/wellness/stu001_wellness.txt
	echo "Active member of coding club and volunteer tutor." > sample-documents/extracurricular/stu001_activities.txt
	echo "Interested in software engineering internships." > sample-documents/placement/stu001_placement.txt
	@echo "✅ Sample data created"

# Full reset
reset: clean docker-down
	@echo "🔄 Performing full reset..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Reset complete. Run 'make setup' to reinitialize."

# Development workflow
dev-setup: setup sample-data init-db
	@echo "🎉 Development environment ready!"

# Quick test
quick-test:
	@echo "⚡ Quick test..."
	curl -s http://localhost:8000/health > /dev/null && echo "✅ API healthy" || echo "❌ API unhealthy"
	curl -s http://localhost:6333/collections > /dev/null && echo "✅ Qdrant healthy" || echo "❌ Qdrant unhealthy"
	curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama healthy" || echo "❌ Ollama unhealthy"

# Backup data
backup:
	@echo "💾 Backing up data..."
	docker exec ai-service-qdrant qdrant-cli snapshot create
	@echo "✅ Backup complete"

# Monitor resources
monitor:
	@echo "📊 Resource usage:"
	docker stats --no-stream
