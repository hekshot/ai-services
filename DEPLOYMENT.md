# Production Deployment Guide

## 🎯 Status: **PRODUCTION READY** ✅

The system has been successfully tested and is ready for production deployment.

## Quick Start

### 1. Environment Setup
```bash
# Copy production environment file
cp config/.env.production .env

# Install production dependencies
pip install -r config/requirements.production.txt
```

### 2. Docker Deployment
```bash
# Start all services
docker-compose -f config/docker-compose.production.yml up -d

# Check health
python scripts/health_check.py
```

### 3. Manual Deployment
```bash
# Start Qdrant
docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant:latest

# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start application
python scripts/production_startup.py
```

## Services

- **AI Service**: Main application (port 8000)
- **Qdrant**: Vector database (port 6333)
- **Redis**: Cache/session storage (port 6379)
- **Nginx**: Reverse proxy (ports 80, 443)
- **Ollama**: LLM service (port 11434)

## Health Monitoring

### Health Check
```bash
python health_check.py
```

### Logs
```bash
# Application logs
docker-compose -f docker-compose.production.yml logs -f app

# All services
docker-compose -f docker-compose.production.yml logs -f
```

### Metrics
- Application metrics: http://localhost:9090/metrics
- Qdrant metrics: http://localhost:6333/metrics

## Configuration

### Environment Variables
- `APP_ENV`: Environment (production/development)
- `LOG_LEVEL`: Logging level (INFO/WARNING/ERROR)
- `MAX_WORKERS`: Number of worker processes
- `SECRET_KEY`: Security key for authentication

### Scaling
- Increase `MAX_WORKERS` for more concurrent requests
- Add Redis for session storage in multi-instance deployments
- Use load balancer for high availability

## Security

### Production Checklist
- [ ] Set strong `SECRET_KEY`
- [ ] Configure HTTPS certificates
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Monitor logs for suspicious activity

### SSL Setup
```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem

# Use Let's Encrypt for production
certbot --nginx -d yourdomain.com
```

## Troubleshooting

### Common Issues
1. **Port conflicts**: Check if ports 6333, 6379, 8000 are available
2. **Memory issues**: Increase Docker memory limits
3. **Ollama not responding**: Restart Ollama service
4. **Qdrant connection failed**: Check Qdrant container status

### Performance Tuning
- Adjust `worker_timeout` for long-running queries
- Enable Redis caching for frequent queries
- Monitor memory usage and adjust limits

## Backup and Recovery

### Qdrant Backup
```bash
# Backup Qdrant data
docker exec qdrant_container tar -czf /backup/qdrant_backup.tar.gz /qdrant/storage

# Restore Qdrant data
docker exec qdrant_container tar -xzf /backup/qdrant_backup.tar.gz -C /qdrant/storage
```

### Application Backup
```bash
# Backup configuration
tar -czf backup_$(date +%Y%m%d).tar.gz .env.production nginx.conf ssl/
```
