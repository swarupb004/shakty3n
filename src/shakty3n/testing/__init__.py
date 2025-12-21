"""
Test Generator Module
Generates test files for different frameworks
"""
from typing import Dict, List
from abc import ABC, abstractmethod


class TestTemplate(ABC):
    """Base class for test templates"""
    
    @abstractmethod
    def generate_unit_test(self, component_name: str, description: str) -> str:
        """Generate a unit test"""
        pass
    
    @abstractmethod
    def generate_integration_test(self, feature_name: str, description: str) -> str:
        """Generate an integration test"""
        pass
    
    @abstractmethod
    def get_test_config(self) -> str:
        """Get test configuration file"""
        pass


class ReactTestTemplate(TestTemplate):
    """React testing template using Jest and React Testing Library"""
    
    def generate_unit_test(self, component_name: str, description: str) -> str:
        return f"""import {{ render, screen }} from '@testing-library/react';
import {component_name} from './{component_name}';

describe('{component_name}', () => {{
  test('renders without crashing', () => {{
    render(<{component_name} />);
    expect(screen.getByRole('main')).toBeInTheDocument();
  }});

  test('displays correct content', () => {{
    render(<{component_name} />);
    // Add your specific assertions here
  }});

  // Add more tests based on: {description}
}});
"""
    
    def generate_integration_test(self, feature_name: str, description: str) -> str:
        return f"""import {{ render, screen, fireEvent, waitFor }} from '@testing-library/react';
import App from '../App';

describe('{feature_name} Integration Tests', () => {{
  test('user can complete {feature_name.lower()} workflow', async () => {{
    render(<App />);
    
    // Test workflow: {description}
    // Add your integration test steps here
    
    await waitFor(() => {{
      expect(screen.getByText(/success/i)).toBeInTheDocument();
    }});
  }});
}});
"""
    
    def get_test_config(self) -> str:
        return """{
  "testEnvironment": "jsdom",
  "setupFilesAfterEnv": ["<rootDir>/src/setupTests.js"],
  "moduleNameMapper": {
    "\\\\.(css|less|scss|sass)$": "identity-obj-proxy"
  },
  "collectCoverageFrom": [
    "src/**/*.{js,jsx}",
    "!src/index.js",
    "!src/reportWebVitals.js"
  ],
  "coverageThreshold": {
    "global": {
      "branches": 70,
      "functions": 70,
      "lines": 70,
      "statements": 70
    }
  }
}
"""


class VueTestTemplate(TestTemplate):
    """Vue testing template using Vitest"""
    
    def generate_unit_test(self, component_name: str, description: str) -> str:
        return f"""import {{ describe, it, expect }} from 'vitest';
import {{ mount }} from '@vue/test-utils';
import {component_name} from '@/components/{component_name}.vue';

describe('{component_name}', () => {{
  it('renders properly', () => {{
    const wrapper = mount({component_name});
    expect(wrapper.exists()).toBe(true);
  }});

  it('displays correct content', () => {{
    const wrapper = mount({component_name});
    // Add your specific assertions here
  }});

  // Add more tests based on: {description}
}});
"""
    
    def generate_integration_test(self, feature_name: str, description: str) -> str:
        return f"""import {{ describe, it, expect }} from 'vitest';
import {{ mount }} from '@vue/test-utils';
import App from '@/App.vue';

describe('{feature_name} Integration Tests', () => {{
  it('user can complete {feature_name.lower()} workflow', async () => {{
    const wrapper = mount(App);
    
    // Test workflow: {description}
    // Add your integration test steps here
    
    await wrapper.vm.$nextTick();
    expect(wrapper.html()).toContain('success');
  }});
}});
"""
    
    def get_test_config(self) -> str:
        return """import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
  },
});
"""


class FlutterTestTemplate(TestTemplate):
    """Flutter testing template"""
    
    def generate_unit_test(self, component_name: str, description: str) -> str:
        return f"""import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/main.dart';

void main() {{
  group('{component_name} Tests', () {{
    test('{component_name} should initialize correctly', () {{
      // Add your unit tests here
      // Test description: {description}
    }});

    test('{component_name} should handle input correctly', () {{
      // Add assertions
    }});
  }});
}}
"""
    
    def generate_integration_test(self, feature_name: str, description: str) -> str:
        return f"""import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:your_app/main.dart' as app;

void main() {{
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('{feature_name} Integration Tests', () {{
    testWidgets('User can complete {feature_name.lower()} workflow',
        (WidgetTester tester) async {{
      app.main();
      await tester.pumpAndSettle();

      // Test workflow: {description}
      // Add your integration test steps here

      await tester.pumpAndSettle();
      expect(find.text('Success'), findsOneWidget);
    }});
  }});
}}
"""
    
    def get_test_config(self) -> str:
        return """# Test configuration is in pubspec.yaml
# Add these dependencies:
dev_dependencies:
  flutter_test:
    sdk: flutter
  integration_test:
    sdk: flutter
  mockito: ^5.0.0
"""


class TestGenerator:
    """Main test generator class"""
    
    def __init__(self, framework: str):
        self.framework = framework.lower()
        self.template = self._get_template()
    
    def _get_template(self) -> TestTemplate:
        """Get the appropriate test template"""
        templates = {
            'react': ReactTestTemplate(),
            'vue': VueTestTemplate(),
            'angular': ReactTestTemplate(),  # Similar to React
            'svelte': ReactTestTemplate(),  # Similar to React
            'nextjs': ReactTestTemplate(),  # Similar to React
            'flutter': FlutterTestTemplate(),
        }
        
        return templates.get(self.framework, ReactTestTemplate())
    
    def generate_tests(self, components: List[str], description: str) -> Dict[str, str]:
        """Generate tests for multiple components"""
        tests = {}
        
        # Generate unit tests
        for component in components:
            test_name = f"{component}.test.js" if self.framework in ['react', 'vue', 'angular', 'svelte', 'nextjs'] else f"{component}_test.dart"
            tests[test_name] = self.template.generate_unit_test(component, description)
        
        # Generate integration test
        integration_test_name = "integration.test.js" if self.framework in ['react', 'vue', 'angular', 'svelte', 'nextjs'] else "integration_test.dart"
        tests[integration_test_name] = self.template.generate_integration_test("Main Feature", description)
        
        # Generate test config
        config_name = "jest.config.json" if self.framework == 'react' else "vitest.config.js" if self.framework == 'vue' else "test_config.txt"
        tests[config_name] = self.template.get_test_config()
        
        return tests
    
    def get_setup_instructions(self) -> str:
        """Get setup instructions for running tests"""
        instructions = {
            'react': """# Running Tests

## Install Dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest

## Run Tests
npm test

## Run with Coverage
npm test -- --coverage
""",
            'vue': """# Running Tests

## Install Dependencies
npm install --save-dev vitest @vue/test-utils jsdom

## Run Tests
npm test

## Run with Coverage
npm test -- --coverage
""",
            'flutter': """# Running Tests

## Run Unit Tests
flutter test

## Run Integration Tests
flutter test integration_test/

## Run with Coverage
flutter test --coverage
""",
        }
        
        return instructions.get(self.framework, instructions['react'])


__all__ = ['TestGenerator', 'TestTemplate']
