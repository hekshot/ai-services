"""
LLM Provider implementations
"""
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import os


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, model: str):
        self.model = model
    
    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider for local models"""
    
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        super().__init__(model)
        self.base_url = base_url
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=10.0)
                if response.status_code != 200:
                    raise Exception(f"Ollama service unavailable: {response.status_code}")
                
                data = response.json()
                return data.get("models", [])
        except Exception as e:
            raise Exception(f"Error fetching Ollama models: {str(e)}")
    
    async def generate(self, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Generate text using Ollama"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Ollama service returned status {response.status_code}")
            
            return response.json()
    
    async def health_check(self) -> bool:
        """Check Ollama health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except:
            return False


class OpenAIProvider(LLMProvider):
    """OpenAI provider for cloud models"""
    
    def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1"):
        super().__init__(model)
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available OpenAI models"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/models", headers=self.headers, timeout=10.0)
                if response.status_code != 200:
                    raise Exception(f"OpenAI service unavailable: {response.status_code}")
                
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            raise Exception(f"Error fetching OpenAI models: {str(e)}")
    
    async def generate(self, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Generate text using OpenAI"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"OpenAI service returned status {response.status_code}")
            
            data = response.json()
            return {
                "response": data["choices"][0]["message"]["content"],
                "model": data["model"],
                "created_at": str(data["created"])
            }
    
    async def health_check(self) -> bool:
        """Check OpenAI health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/models", headers=self.headers, timeout=5.0)
                return response.status_code == 200
        except:
            return False


def get_provider() -> LLMProvider:
    """Get LLM provider based on environment configuration"""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    model = os.getenv("LLM_MODEL", "qwen2.5:7b")  # Use available Ollama model as default
    
    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaProvider(model, base_url)
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY environment variable is required")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return OpenAIProvider(model, api_key, base_url)
    else:
        raise Exception(f"Unsupported LLM provider: {provider}")
