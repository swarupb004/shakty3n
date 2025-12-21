"""
Flutter Application Generator
"""
from typing import Dict
from .base import CodeGenerator


class FlutterAppGenerator(CodeGenerator):
    """Generator for Flutter cross-platform applications"""
    
    def __init__(self, ai_provider, output_dir: str, generate_tests: bool = False):
        super().__init__(ai_provider, output_dir)
        self.generate_tests = generate_tests
    
    def generate_project(self, description: str, requirements: Dict) -> Dict:
        """Generate a Flutter application project"""
        
        # Generate project structure
        structure = self._generate_structure()
        
        # Generate pubspec.yaml
        pubspec = self._generate_pubspec(description, requirements)
        self.create_file("pubspec.yaml", pubspec)
        
        # Generate main.dart
        main_dart = self._generate_main_dart(description, requirements)
        self.create_file("lib/main.dart", main_dart)
        
        # Generate README
        readme = self._generate_readme(description)
        self.create_file("README.md", readme)
        
        # Generate analysis_options.yaml
        analysis_options = self._generate_analysis_options()
        self.create_file("analysis_options.yaml", analysis_options)
        
        # Generate .gitignore
        gitignore = self._generate_gitignore()
        self.create_file(".gitignore", gitignore)
        
        # Generate tests if requested
        if self.generate_tests:
            self._generate_tests(description)
        
        return {
            "platform": "flutter",
            "files": self.generated_files,
            "structure": structure,
            "tests_generated": self.generate_tests
        }
    
    def _generate_structure(self) -> Dict:
        """Create project directory structure"""
        dirs = [
            "lib",
            "lib/screens",
            "lib/widgets",
            "lib/models",
            "lib/services",
            "lib/utils",
            "test",
            "assets",
            "assets/images",
            "android",
            "ios",
            "web"
        ]
        
        for dir_path in dirs:
            self.create_directory(dir_path)
        
        return {"directories": dirs}
    
    def _generate_pubspec(self, description: str, requirements: Dict) -> str:
        """Generate pubspec.yaml"""
        prompt = f"""Generate a pubspec.yaml file for a Flutter application.

Project Description: {description}
Requirements: {requirements}

Include all necessary dependencies for Flutter development.
Return only the YAML content, no explanations."""

        system_prompt = "You are an expert Flutter developer. Generate valid pubspec.yaml files."
        
        response = self.ai_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3
        )
        
        # Extract YAML content
        if "```yaml" in response:
            start = response.find("```yaml") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        
        return response.strip()
    
    def _generate_main_dart(self, description: str, requirements: Dict) -> str:
        """Generate main.dart using AI"""
        prompt = f"""Generate a main.dart file for a Flutter application.

Project Description: {description}
Requirements: {requirements}

Generate a complete, functional Flutter application with:
- Material Design
- Proper widget structure
- State management
- Modern Flutter best practices

Return only the Dart code, no explanations."""

        system_prompt = "You are an expert Flutter developer. Generate clean, modern Flutter applications."
        
        response = self.ai_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4
        )
        
        # Extract code content
        if "```dart" in response:
            start = response.find("```dart") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        
        return response.strip()
    
    def _generate_analysis_options(self) -> str:
        """Generate analysis_options.yaml"""
        return """include: package:flutter_lints/flutter.yaml

linter:
  rules:
    - prefer_const_constructors
    - prefer_const_literals_to_create_immutables
    - avoid_print
    - prefer_single_quotes
"""
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore for Flutter"""
        return """# Miscellaneous
*.class
*.log
*.pyc
*.swp
.DS_Store
.atom/
.buildlog/
.history
.svn/

# IntelliJ related
*.iml
*.ipr
*.iws
.idea/

# Flutter/Dart/Pub related
**/doc/api/
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.packages
.pub-cache/
.pub/
build/

# Android related
**/android/**/gradle-wrapper.jar
**/android/.gradle
**/android/captures/
**/android/gradlew
**/android/gradlew.bat
**/android/local.properties
**/android/**/GeneratedPluginRegistrant.java

# iOS/XCode related
**/ios/**/*.mode1v3
**/ios/**/*.mode2v3
**/ios/**/*.moved-aside
**/ios/**/*.pbxuser
**/ios/**/*.perspectivev3
**/ios/**/*sync/
**/ios/**/.sconsign.dblite
**/ios/**/.tags*
**/ios/**/.vagrant/
**/ios/**/DerivedData/
**/ios/**/Icon?
**/ios/**/Pods/
**/ios/**/.symlinks/
**/ios/**/profile
**/ios/**/xcuserdata
**/ios/.generated/
**/ios/Flutter/App.framework
**/ios/Flutter/Flutter.framework
**/ios/Flutter/Flutter.podspec
**/ios/Flutter/Generated.xcconfig
**/ios/Flutter/app.flx
**/ios/Flutter/app.zip
**/ios/Flutter/flutter_assets/
**/ios/Flutter/flutter_export_environment.sh
**/ios/ServiceDefinitions.json
**/ios/Runner/GeneratedPluginRegistrant.*

# Exceptions to above rules.
!**/ios/**/default.mode1v3
!**/ios/**/default.mode2v3
!**/ios/**/default.pbxuser
!**/ios/**/default.perspectivev3
"""
    
    def _generate_readme(self, description: str) -> str:
        """Generate README.md"""
        return f"""# Flutter Application

{description}

## Platform
Cross-platform (iOS, Android, Web, Desktop)

## Setup

### Prerequisites
- Flutter SDK installed
- Dart SDK (comes with Flutter)

### Installation

```bash
# Get dependencies
flutter pub get
```

## Development

```bash
# Run on connected device/emulator
flutter run

# Run on specific platform
flutter run -d chrome      # Web
flutter run -d macos       # macOS
flutter run -d windows     # Windows
flutter run -d linux       # Linux
```

## Build

```bash
# Build for Android
flutter build apk
flutter build appbundle

# Build for iOS
flutter build ios

# Build for Web
flutter build web

# Build for Desktop
flutter build macos
flutter build windows
flutter build linux
```

## Testing

```bash
# Run tests
flutter test

# Run with coverage
flutter test --coverage
```

## Features

- Cross-platform Flutter application
- Material Design UI
- Responsive layout
- Ready for deployment

## Generated by Shakty3n
Autonomous Agentic Coder
"""
    
    def _generate_tests(self, description: str):
        """Generate test files for the Flutter project"""
        from ..testing import TestGenerator
        
        # Create test generator
        test_gen = TestGenerator('flutter')
        
        # Generate tests for main components
        components = ['MainApp']
        tests = test_gen.generate_tests(components, description)
        
        # Write test files
        for test_file, test_content in tests.items():
            if test_file.endswith('.dart'):
                file_path = f"test/{test_file}"
            elif test_file == 'test_config.txt':
                file_path = "test/README.md"
            else:
                file_path = f"test/{test_file}"
            self.create_file(file_path, test_content)
        
        # Add test instructions
        test_instructions = test_gen.get_setup_instructions()
        self.create_file("TESTING.md", test_instructions)
