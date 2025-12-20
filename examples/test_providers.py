"""
Example: Using Multiple AI Providers
"""
from shakty3n import (
    AIProviderFactory,
    load_env_vars
)

# Load environment variables
load_env_vars()

def test_provider(provider_name, model=None):
    """Test an AI provider"""
    print(f"\n{'='*60}")
    print(f"Testing {provider_name}")
    print('='*60)
    
    try:
        # Create provider
        provider = AIProviderFactory.create_provider(
            provider_name=provider_name,
            api_key=None,  # Use from environment
            model=model
        )
        
        # Test prompt
        prompt = "Write a simple 'Hello World' function in Python."
        print(f"\nPrompt: {prompt}")
        
        # Generate response
        print("\nGenerating response...")
        response = provider.generate(
            prompt=prompt,
            temperature=0.3
        )
        
        print(f"\nResponse:\n{response[:300]}...")
        print(f"\n✓ {provider_name} working correctly!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error with {provider_name}: {e}")
        return False


def main():
    print("Testing Multiple AI Providers")
    print("="*60)
    
    # Test OpenAI
    test_provider("openai", "gpt-4")
    
    # Test Anthropic
    test_provider("anthropic", "claude-3-opus-20240229")
    
    # Test Google
    test_provider("google", "gemini-pro")
    
    # Test Ollama (if installed)
    test_provider("ollama", "llama2")
    
    print("\n" + "="*60)
    print("Testing Complete")
    print("="*60)


if __name__ == "__main__":
    main()
