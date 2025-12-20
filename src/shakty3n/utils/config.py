"""
Configuration management
"""
import os
from typing import Dict, Optional


class Config:
    """Application configuration"""
    
    def __init__(self):
        self.provider = os.getenv("DEFAULT_AI_PROVIDER", "openai")
        self.model = os.getenv("DEFAULT_MODEL", "gpt-4")
        self.auto_debug = os.getenv("AUTO_DEBUG", "true").lower() == "true"
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.verbose = os.getenv("VERBOSE", "true").lower() == "true"
        self.output_dir = os.getenv("OUTPUT_DIR", "./generated_projects")
    
    def get_provider_config(self, provider: Optional[str] = None) -> Dict:
        """Get configuration for a specific provider"""
        provider = provider or self.provider
        
        api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY")
        }
        
        return {
            "provider": provider,
            "api_key": api_keys.get(provider),
            "model": self.model
        }
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary"""
        return {
            "provider": self.provider,
            "model": self.model,
            "auto_debug": self.auto_debug,
            "max_retries": self.max_retries,
            "verbose": self.verbose,
            "output_dir": self.output_dir
        }
