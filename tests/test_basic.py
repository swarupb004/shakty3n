#!/usr/bin/env python3
"""
Basic functionality tests for Shakty3n
Run this to verify the installation is working correctly
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from shakty3n import (
            AIProviderFactory,
            TaskPlanner,
            Task,
            TaskStatus,
            WebAppGenerator,
            AndroidAppGenerator,
            IOSAppGenerator,
            DesktopAppGenerator,
            AutoDebugger,
            AutonomousExecutor,
            Config,
            load_env_vars
        )
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_ai_provider_factory():
    """Test AI provider factory"""
    print("\nTesting AI Provider Factory...")
    
    try:
        from shakty3n import AIProviderFactory
        
        # Test getting available providers
        providers = AIProviderFactory.get_available_providers()
        assert len(providers) > 0, "No providers available"
        assert "openai" in providers, "OpenAI provider not found"
        
        print(f"✓ Available providers: {providers}")
        return True
    except Exception as e:
        print(f"✗ AI Provider Factory test failed: {e}")
        return False


def test_task_planner():
    """Test task planner (without AI)"""
    print("\nTesting Task Planner...")
    
    try:
        from shakty3n import Task, TaskStatus
        
        # Create a simple task
        task = Task(
            id=1,
            title="Test Task",
            description="This is a test task",
            dependencies=[],
            status=TaskStatus.PENDING
        )
        
        assert task.title == "Test Task"
        assert task.status == TaskStatus.PENDING
        
        # Update status
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED
        
        print("✓ Task creation and management works")
        return True
    except Exception as e:
        print(f"✗ Task Planner test failed: {e}")
        return False


def test_config():
    """Test configuration"""
    print("\nTesting Configuration...")
    
    try:
        from shakty3n import Config
        
        config = Config()
        assert hasattr(config, 'provider')
        assert hasattr(config, 'model')
        
        config_dict = config.to_dict()
        assert 'provider' in config_dict
        
        print(f"✓ Configuration works (provider: {config.provider})")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_code_generator_structure():
    """Test code generator structure (without AI)"""
    print("\nTesting Code Generator Structure...")
    
    try:
        from shakty3n.generators import CodeGenerator
        import tempfile
        
        # Create a mock AI provider
        class MockAIProvider:
            def generate(self, prompt, **kwargs):
                return "Mock response"
        
        # Test with temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Can't instantiate abstract class directly, but we can verify it exists
            assert hasattr(CodeGenerator, 'generate_project')
            assert hasattr(CodeGenerator, 'create_file')
            
            print("✓ Code generator structure is valid")
            return True
    except Exception as e:
        print(f"✗ Code generator test failed: {e}")
        return False


def test_debugger():
    """Test debugger error parsing"""
    print("\nTesting Auto Debugger...")
    
    try:
        # Create a mock AI provider
        class MockAIProvider:
            def generate(self, prompt, **kwargs):
                return "Fix the syntax error by adding a closing parenthesis."
        
        from shakty3n import AutoDebugger
        
        debugger = AutoDebugger(MockAIProvider())
        
        # Test error parsing
        error_msg = "SyntaxError: invalid syntax at line 42"
        error_info = debugger._parse_error(error_msg)
        
        assert error_info['type'] == 'SyntaxError'
        assert error_info['line'] == 42
        
        print("✓ Auto debugger error parsing works")
        return True
    except Exception as e:
        print(f"✗ Auto debugger test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("Shakty3n Basic Functionality Tests")
    print("="*60)
    
    tests = [
        test_imports,
        test_ai_provider_factory,
        test_task_planner,
        test_config,
        test_code_generator_structure,
        test_debugger
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    print("Test Results")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Shakty3n is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
