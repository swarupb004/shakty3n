"""
Google Gemini Provider Implementation
"""
from typing import List, Optional
from .base import AIProvider

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GoogleProvider(AIProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        super().__init__(api_key, model)
        if genai is None:
            raise ImportError("Google GenerativeAI package not installed. Run: pip install google-generativeai")
        genai.configure(api_key=api_key)
        self.model_instance = genai.GenerativeModel(model)
        self.model = model
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """Generate response using Google Gemini API"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = self.model_instance.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")
    
    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.7, max_tokens: int = 4000):
        """Stream response using Google Gemini API"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = self.model_instance.generate_content(
                full_prompt,
                generation_config=generation_config,
                stream=True
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """Get available Google models"""
        return ["gemini-3.0-pro", "gemini-pro", "gemini-pro-vision", "gemini-ultra"]
