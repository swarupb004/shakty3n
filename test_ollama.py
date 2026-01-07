
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from shakty3n.ai_providers.ollama_provider import OllamaProvider

def test_ollama():
    # Use a small model if available, otherwise use codestral
    model = "codestral:latest" 
    print(f"Testing Ollama with model: {model}")
    
    provider = OllamaProvider(model=model)
    try:
        response = provider.generate("Say hello!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ollama()
