# Quick Reference Commands

## Application Management

### Start the Service
```bash
cd ai-service
source venv/bin/activate
python main.py
```

### Stop the Service
```bash
# In terminal: Ctrl+C
# Or if running in background:
lsof -ti:8000 | xargs kill -9
```

### Check if Service is Running
```bash
curl http://localhost:8000/health
```

## API Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### List Models
```bash
curl http://localhost:8000/models
```

### Chat with AI
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your question here"}'
```

### Use Specific Model
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your question", "model": "gpt-4o"}'
```

## Environment Setup

### Switch to Ollama
```bash
# Edit .env file:
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
```

### Switch to OpenAI
```bash
# Edit .env file:
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=your-api-key-here
```

## Ollama Management

### Install Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai/download
```

### Start Ollama Service
```bash
# macOS/Linux
ollama serve

# Windows: Usually starts automatically
# Check if running: http://localhost:11434
```

### Manage Models
```bash
# List installed models
ollama list

# Download new models
ollama pull qwen2.5:7b
ollama pull llama2
ollama pull mistral
ollama pull codellama

# Remove models
ollama rm llama2

# Test models directly
ollama run qwen2.5:7b "Hello, how are you?"
```

### Ollama Health Checks
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check Ollama version
ollama --version

# Test model via API
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5:7b", "prompt": "Test", "stream": false}'
```

## Troubleshooting

### Port Already in Use
```bash
lsof -ti:8000 | xargs kill -9
```

### Ollama Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama (macOS/Linux)
brew services restart ollama

# Or kill and restart
pkill ollama && ollama serve
```

### Check OpenAI API Access
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.openai.com/v1/models
```

### View Logs
The service logs to stdout, so you'll see logs directly in your terminal when running.

### Complete Test Sequence
```bash
# 1. Test Ollama
curl http://localhost:11434/api/tags

# 2. Test AI Service
curl http://localhost:8000/health

# 3. Test full chat flow
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test message"}'
```

## Process Management

### Find Python Processes on Port 8000
```bash
lsof -i:8000
```

### Kill All Python Processes
```bash
pkill -f python
```

### Check Virtual Environment
```bash
which python
# Should show: /path/to/ai-service/venv/bin/python
```
