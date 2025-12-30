"""
AI Provider Abstract Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 4000,
                 stop: Optional[List[str]] = None) -> str:
        """Generate a response from the AI model"""
        pass
    
    @abstractmethod
    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.7, max_tokens: int = 4000):
        """Stream response from the AI model"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider"""
        pass
