# Scripts Directory

## Overview
This directory contains utility scripts for the AI Service.

## Available Scripts

### Data Upload Scripts
- **direct_upload.py**: Direct data upload without API server
- **data_upload.py**: API-based data upload (requires server running)
- **test_csv_upload.py**: Test CSV upload workflow

### Server Management Scripts
- **dev_startup.py**: Development server startup
- **production_startup.py**: Production server startup
- **health_check.py**: System health monitoring

## Usage

### Development Mode
```bash
python scripts/dev_startup.py
```

### Production Mode
```bash
python scripts/production_startup.py
```

### Data Upload
```bash
# Direct upload (no server needed)
python scripts/direct_upload.py

# API upload (server required)
python scripts/data_upload.py
```

### Health Check
```bash
python scripts/health_check.py
```

## Testing
```bash
# Test CSV upload workflow
python scripts/test_csv_upload.py
```

## Script Dependencies
- All scripts require the project root in PYTHONPATH
- Some scripts require external services (Qdrant, Ollama)
- Check individual script requirements before running
