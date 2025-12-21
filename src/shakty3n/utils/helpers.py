"""
Utility functions and helpers
"""
import os
from typing import Optional


def load_env_vars():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider from environment"""
    env_vars = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY"
    }
    
    env_var = env_vars.get(provider.lower())
    if env_var:
        return os.getenv(env_var)
    return None


def validate_project_type(project_type: str) -> bool:
    """Validate project type"""
    valid_types = [
        "web", "react", "vue", "angular", "svelte", "nextjs", "next",
        "android", "ios", "flutter",
        "desktop", "electron", "python"
    ]
    
    project_type_lower = project_type.lower()
    return any(valid in project_type_lower for valid in valid_types)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
