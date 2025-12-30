"""
Docker Model Runner Provider Implementation
Uses Docker Desktop's Model Runner with OpenAI-compatible API
Works on macOS/Windows with Docker Desktop 4.40+
"""
from typing import List, Optional, Generator
import os
import json
import httpx
from .base import AIProvider


class DockerModelRunnerProvider(AIProvider):
    """Docker Desktop Model Runner provider (OpenAI-compatible API)"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "ai/qwen3-coder:latest", 
                 base_url: Optional[str] = None):
        super().__init__(api_key or "docker-model-runner", model)
        self.model = model
        
        # Determine connection method
        if base_url:
            self.base_url = base_url
        elif self._is_running_in_docker():
            # Inside Docker container - use internal DNS
            self.base_url = os.getenv("DOCKER_MODEL_RUNNER_URL", "http://model-runner.docker.internal")
        else:
            # Host machine - use localhost with TCP port (requires: docker desktop enable model-runner --tcp=12434)
            self.base_url = os.getenv("DOCKER_MODEL_RUNNER_URL", "http://localhost:12434")
        
        # API path for llama.cpp engine
        self.api_path = "/engines/llama.cpp/v1"
    
    def _is_running_in_docker(self) -> bool:
        """Check if running inside Docker container"""
        return os.path.exists("/.dockerenv")
    
    def _get_client(self, timeout: float = 300.0) -> httpx.Client:
        """Create an httpx client"""
        return httpx.Client(timeout=timeout)
    
    def _get_full_url(self, endpoint: str) -> str:
        """Get full URL for an endpoint"""
        return f"{self.base_url}{self.api_path}{endpoint}"
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4000,
                 stop: Optional[List[str]] = None) -> str:
        """Generate response using Docker Model Runner (OpenAI-compatible API)"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            with self._get_client(timeout=300.0) as client:
                response = client.post(
                    self._get_full_url("/chat/completions"),
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": False,
                        "stop": stop or None
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            raise Exception("Docker Model Runner timeout - the model may be loading. Try again in a moment.")
        except httpx.ConnectError:
            raise Exception(
                "Cannot connect to Docker Model Runner. "
                "On the host, ensure Docker Desktop model runner is enabled with "
                "`docker desktop enable model-runner --tcp=12434` and reachable at the configured port. "
                "Inside Docker, set DOCKER_MODEL_RUNNER_URL or confirm model-runner.docker.internal resolves."
            )
        except Exception as e:
            raise Exception(f"Docker Model Runner API error: {str(e)}")
    
    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.7, max_tokens: int = 4000) -> Generator[str, None, None]:
        """Stream response using Docker Model Runner"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            with self._get_client(timeout=300.0) as client:
                with client.stream(
                    "POST",
                    self._get_full_url("/chat/completions"),
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": True
                    }
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line and line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            raise Exception(f"Docker Model Runner API error: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """Get available models from Docker Model Runner"""
        try:
            with self._get_client(timeout=10.0) as client:
                response = client.get(self._get_full_url("/models"))
                response.raise_for_status()
                models = response.json().get("data", [])
                return [model["id"] for model in models]
        except:
            # Return known Docker Desktop models as fallback
            return [
                "ai/qwen3-coder:latest",
                "ai/llama3:8b",
                "ai/mistral:7b",
                "ai/gemma:7b"
            ]
