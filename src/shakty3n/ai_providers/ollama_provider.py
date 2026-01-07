"""
Ollama Local Model Provider Implementation
"""
from typing import List, Optional
import requests
import logging
from .base import AIProvider

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Ollama local model provider"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama2",
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        super().__init__(api_key, model)
        import os
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model
        self.timeout = timeout if timeout is not None else float(os.getenv("OLLAMA_TIMEOUT", 300))
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4000,
                 stop: Optional[List[str]] = None) -> str:
        """Generate response using Ollama API"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "temperature": temperature,
                "stream": False,
                "stop": stop or None
            }
            
            logger.info(f"Ollama request: {self.base_url}/api/generate, model={self.model}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers=headers,
                timeout=self.timeout  # 5 minute timeout for large models
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama error {response.status_code}: {response.text}")
                
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.Timeout:
            raise Exception(f"Ollama API error: Request timed out after {int(self.timeout)} seconds. The model '{self.model}' might be too slow for this hardware.")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.7, max_tokens: int = 4000):
        """Stream response using Ollama API"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "temperature": temperature,
                "stream": True
            }
            
            logger.info(f"Ollama stream request: {self.base_url}/api/generate, model={self.model}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers=headers,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse Ollama stream line: {line}")
        except requests.exceptions.Timeout:
            raise Exception(f"Ollama stream API error: Request timed out after {int(self.timeout)} seconds.")
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
            logger.warning("Ollama API error while fetching models: %s", e)
            return [
                "devstral:latest",
                "codestral:22b",
                "deepseek-coder:6.7b",
                "llama3.1:latest",
                "deepseek-r1:8b",
                "qwen2.5-coder",
                "codellama"
            ]
