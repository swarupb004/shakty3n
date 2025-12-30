"""
Ollama Local Model Provider Implementation
"""
from typing import List, Optional
import requests
from .base import AIProvider


class OllamaProvider(AIProvider):
    """Ollama local model provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama2", 
                 base_url: Optional[str] = None):
        super().__init__(api_key, model)
        import os
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4000,
                 stop: Optional[List[str]] = None) -> str:
        """Generate response using Ollama API"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "temperature": temperature,
                    "stream": False,
                    "stop": stop or None
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.7, max_tokens: int = 4000):
        """Stream response using Ollama API"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "temperature": temperature,
                    "stream": True
                },
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """Get available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        except Exception as e:
            print(f"DEBUG: Ollama API Error: {e}")
            return [
                "devstral:latest",
                "codestral:22b",
                "deepseek-coder:6.7b",
                "llama3.1:latest",
                "deepseek-r1:8b",
                "qwen2.5-coder",
                "codellama"
            ]
