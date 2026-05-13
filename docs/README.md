# AI Service Documentation

## Overview

AI Service is a configurable FastAPI application that provides a unified interface for multiple LLM providers. It supports both local Ollama instances and cloud-based OpenAI API through simple environment configuration.

## Features

- **Multi-Provider Support**: Switch between Ollama and OpenAI without code changes
- **Environment-Based Configuration**: All settings managed through environment variables
- **RESTful API**: Clean, well-documented endpoints
- **Health Monitoring**: Built-in health checks for provider connectivity
- **Model Discovery**: List available models from any provider
- **Streaming Support**: Optional streaming responses

## Project Structure

```
ai-service/
├── main.py                 # FastAPI application entry point
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic models
│   └── providers.py       # LLM provider implementations
├── docs/
│   └── README.md          # This documentation
├── .env.example           # Environment variables template
├── requirements.txt        # Python dependencies
└── venv/                  # Virtual environment
```

## Installation

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)
- For Ollama: Ollama installed locally

### Ollama Setup (for Local Models)

1. **Install Ollama**:
   ```bash
   # macOS
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: Download from https://ollama.ai/download
   ```

2. **Start Ollama Service**:
   ```bash
   # macOS/Linux
   ollama serve
   
   # Windows: Ollama typically starts automatically
   ```

3. **Download a Model**:
   ```bash
   # Download Qwen2.5 7B model (recommended)
   ollama pull qwen2.5:7b
   
   # Or other models
   ollama pull llama2
   ollama pull mistral
   ollama pull codellama
   ```

4. **Test Ollama**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Test with a model
   ollama run qwen2.5:7b "Hello, how are you?"
   ```

### AI Service Setup Steps

1. **Clone or create the project**:
   ```bash
   cd ai-service
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

#### For Ollama (Local Models)
```bash
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
```

#### For OpenAI (Cloud Models)
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

#### Optional Server Configuration
```bash
HOST=0.0.0.0
PORT=8000
```

## Running the Application

### Start the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start the service
python main.py
```

The server will start on `http://localhost:8000` (or configured HOST/PORT).

### Stop the Server

- **In terminal**: Press `Ctrl+C`
- **If running in background**: Find and kill the process
  ```bash
  # Find process on port 8000
  lsof -ti:8000
  
  # Kill the process
  kill -9 <PID>
  
  # Or kill all Python processes on port 8000
  lsof -ti:8000 | xargs kill -9
  ```

## API Endpoints

### 1. Service Information
```http
GET /
```

**Response**:
```json
{
  "message": "AI Service is running",
  "provider": "ollama",
  "model": "qwen2.5:7b"
}
```

### 2. Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "provider": "ollama",
  "connected": true
}
```

### 3. List Models
```http
GET /models
```

**Response**:
```json
[
  {
    "name": "qwen2.5:7b",
    "size": 4683087332,
    "modified_at": "2026-05-12T19:20:26.046131835+05:30"
  }
]
```

### 4. Chat/Generate
```http
POST /chat
Content-Type: application/json

{
  "prompt": "What is 2+2?",
  "model": "optional-override-model",
  "stream": false
}
```

**Response**:
```json
{
  "response": "4",
  "model": "qwen2.5:7b",
  "provider": "ollama",
  "created_at": "2026-05-12T14:22:58.907002Z"
}
```

### 5. Alternative Generate Endpoint
```http
POST /generate
```
Same as `/chat` endpoint.

## Testing

### Ollama Testing Commands

#### Test Ollama Installation
```bash
# Check if Ollama is installed
ollama --version

# Check if Ollama service is running
curl http://localhost:11434/api/tags

# List installed models
ollama list
```

#### Test Ollama Models
```bash
# Test model directly in terminal
ollama run qwen2.5:7b "What is 2+2?"

# Test model via API
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5:7b", "prompt": "Hello", "stream": false}'

# Test with streaming
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5:7b", "prompt": "Count to 5", "stream": true}'
```

#### Download and Test Different Models
```bash
# Download various models for testing
ollama pull llama2
ollama pull mistral
ollama pull codellama

# Test each model
ollama run llama2 "Explain AI"
ollama run mistral "What is Python?"
ollama run codellama "Write a hello world function"
```

### AI Service Testing

#### Test Service Health
```bash
# Start the service first
source venv/bin/activate && python main.py

# Test service endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/models
```

#### Test Chat Functionality
```bash
# Basic chat test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?"}'

# Test with different models
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain photosynthesis", "model": "qwen2.5:7b"}'

# Test streaming (if supported)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me a story", "stream": true}'
```

#### Comprehensive Test Suite
```bash
# Create a test script
cat > test_ai_service.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing AI Service..."

# Test 1: Service health
echo "1. Testing service health..."
curl -s http://localhost:8000/health | jq .

# Test 2: List models
echo "2. Testing models endpoint..."
curl -s http://localhost:8000/models | jq .

# Test 3: Basic chat
echo "3. Testing basic chat..."
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?"}' | jq .

# Test 4: Model override
echo "4. Testing model override..."
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "qwen2.5:7b"}' | jq .

echo "✅ Tests completed!"
EOF

chmod +x test_ai_service.sh
./test_ai_service.sh
```

### OpenAI Testing Commands

#### Test OpenAI API Access
```bash
# Set API key (replace with your actual key)
export OPENAI_API_KEY="your-api-key-here"

# Test OpenAI API directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Test OpenAI chat
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}' \
  https://api.openai.com/v1/chat/completions
```

#### Test AI Service with OpenAI
```bash
# Configure for OpenAI in .env
echo "LLM_PROVIDER=openai" > .env
echo "LLM_MODEL=gpt-3.5-turbo" >> .env
echo "OPENAI_API_KEY=your-api-key-here" >> .env

# Restart service and test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}'
```

## Usage Examples

### Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# List models
curl http://localhost:8000/models

# Chat with the AI
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?"}'

# Use specific model
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing", "model": "gpt-4o"}'
```

### Testing with Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Chat
response = requests.post(
    "http://localhost:8000/chat",
    json={"prompt": "What is the meaning of life?"}
)
print(response.json()["response"])
```

## Provider Switching

### Switch from Ollama to OpenAI

1. **Update `.env` file**:
   ```bash
   # Change from:
   LLM_PROVIDER=ollama
   LLM_MODEL=qwen2.5:7b
   
   # To:
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o
   OPENAI_API_KEY=sk-your-api-key-here
   ```

2. **Restart the service**:
   ```bash
   # Stop current service (Ctrl+C)
   # Start again
   python main.py
   ```

No code changes required!

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Environment variables not loading**:
   - Ensure `.env` file exists
   - Check variable names match exactly
   - Restart the service after changes

3. **Ollama connection failed**:
   - Verify Ollama is running: `ollama list`
   - Check URL: `curl http://localhost:11434/api/tags`

4. **OpenAI API key error**:
   - Verify API key is valid
   - Check for extra spaces or quotes
   - Ensure key has proper permissions

### Health Check Commands

```bash
# Check if service is running
curl http://localhost:8000/health

# Check if Ollama is accessible
curl http://localhost:11434/api/tags

# Check if OpenAI API is accessible (replace with your key)
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.openai.com/v1/models
```

## Development

### Project Structure Best Practices

- **Separation of Concerns**: Each module has a single responsibility
- **Configuration Management**: All settings in environment variables
- **Provider Abstraction**: Easy to add new LLM providers
- **Error Handling**: Comprehensive error responses
- **Type Safety**: Pydantic models for request/response validation

### Adding New Providers

1. Create new provider class in `src/providers.py`
2. Implement required abstract methods
3. Update `get_provider()` function
4. Add configuration options to `src/config.py`

## Security Considerations

- API keys should never be committed to version control
- Use environment variables for all sensitive data
- Consider adding authentication for production deployments
- Validate and sanitize all user inputs

## License

This project is provided as-is for educational and development purposes.
