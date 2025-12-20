"""
AI Provider Factory and Manager
"""
from typing import Optional
from .base import AIProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from .ollama_provider import OllamaProvider


class AIProviderFactory:
    """Factory for creating AI providers"""
    
    @staticmethod
    def create_provider(provider_name: str, api_key: Optional[str] = None, 
                       model: Optional[str] = None) -> AIProvider:
        """Create an AI provider instance"""
        provider_name = provider_name.lower()
        
        if provider_name == "openai":
            model = model or "gpt-4"
            return OpenAIProvider(api_key=api_key, model=model)
        elif provider_name == "anthropic":
            model = model or "claude-3-opus-20240229"
            return AnthropicProvider(api_key=api_key, model=model)
        elif provider_name == "google":
            model = model or "gemini-pro"
            return GoogleProvider(api_key=api_key, model=model)
        elif provider_name == "ollama":
            model = model or "llama2"
            return OllamaProvider(model=model)
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
    
    @staticmethod
    def get_available_providers():
        """Get list of available providers"""
        return ["openai", "anthropic", "google", "ollama"]
