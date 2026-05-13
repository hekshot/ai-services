# Configuration Directory

## Overview
This directory contains configuration files for different deployment environments.

## Configuration Files

### Environment Files
- **.env.production**: Production environment variables
- **.env.example**: Example environment template (root directory)

### Docker Configuration
- **docker-compose.production.yml**: Production Docker setup
- **nginx.conf**: Nginx reverse proxy configuration

### Dependencies
- **requirements.production.txt**: Production Python dependencies

### Server Configuration
- **production_startup.py**: Production server startup script (moved to scripts/)
- **health_check.py**: Health monitoring script (moved to scripts/)

## Environment Variables

### Production Configuration
```bash
# Application
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000

# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434

# Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Performance
MAX_WORKERS=4
WORKER_TIMEOUT=120
KEEPALIVE=2

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

## Usage

### Production Deployment
```bash
# Copy production config
cp config/.env.production .env

# Start production stack
docker-compose -f config/docker-compose.production.yml up -d
```

### Manual Deployment
```bash
# Install production dependencies
pip install -r config/requirements.production.txt

# Start services
python scripts/production_startup.py
```

## Security Notes

- Replace default values in production
- Use strong SECRET_KEY
- Configure proper CORS origins
- Set up SSL certificates
- Monitor logs regularly
