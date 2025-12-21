"""
Code Validation Module
Validates generated code for syntax, structure, and dependencies
"""
import os
import json
import re
from typing import Dict, List, Optional
from pathlib import Path


class ValidationResult:
    """Container for validation results"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
        self.passed: bool = True
    
    def add_error(self, message: str):
        """Add an error"""
        self.errors.append(message)
        self.passed = False
    
    def add_warning(self, message: str):
        """Add a warning"""
        self.warnings.append(message)
    
    def add_suggestion(self, message: str):
        """Add a suggestion"""
        self.suggestions.append(message)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'passed': self.passed,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


class CodeValidator:
    """Base code validator"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.result = ValidationResult()
    
    def validate(self) -> ValidationResult:
        """Run all validations"""
        self._validate_structure()
        self._validate_files()
        self._validate_dependencies()
        return self.result
    
    def _validate_structure(self):
        """Validate project structure"""
        if not os.path.exists(self.project_dir):
            self.result.add_error(f"Project directory does not exist: {self.project_dir}")
    
    def _validate_files(self):
        """Validate individual files"""
        pass
    
    def _validate_dependencies(self):
        """Validate dependencies"""
        pass


class WebProjectValidator(CodeValidator):
    """Validator for web projects"""
    
    def _validate_structure(self):
        """Validate web project structure"""
        super()._validate_structure()
        
        required_dirs = ['src', 'public']
        for dir_name in required_dirs:
            dir_path = os.path.join(self.project_dir, dir_name)
            if not os.path.exists(dir_path):
                self.result.add_error(f"Missing required directory: {dir_name}")
    
    def _validate_files(self):
        """Validate web project files"""
        # Check package.json
        package_json_path = os.path.join(self.project_dir, 'package.json')
        if not os.path.exists(package_json_path):
            self.result.add_error("Missing package.json file")
        else:
            self._validate_package_json(package_json_path)
        
        # Check for main entry point
        entry_points = ['src/index.js', 'src/main.js', 'src/index.ts', 'src/main.ts']
        entry_found = False
        for entry in entry_points:
            if os.path.exists(os.path.join(self.project_dir, entry)):
                entry_found = True
                break
        
        if not entry_found:
            self.result.add_warning("No entry point file found (index.js/main.js)")
    
    def _validate_package_json(self, path: str):
        """Validate package.json"""
        try:
            with open(path, 'r') as f:
                package_data = json.load(f)
            
            # Check required fields
            required_fields = ['name', 'version']
            for field in required_fields:
                if field not in package_data:
                    self.result.add_error(f"package.json missing required field: {field}")
            
            # Check scripts
            if 'scripts' not in package_data:
                self.result.add_warning("package.json has no scripts defined")
            else:
                recommended_scripts = ['start', 'build', 'test']
                for script in recommended_scripts:
                    if script not in package_data['scripts']:
                        self.result.add_suggestion(f"Consider adding '{script}' script to package.json")
            
            # Check dependencies
            if 'dependencies' not in package_data and 'devDependencies' not in package_data:
                self.result.add_warning("No dependencies defined in package.json")
                
        except json.JSONDecodeError:
            self.result.add_error("Invalid JSON in package.json")
        except Exception as e:
            self.result.add_error(f"Error reading package.json: {str(e)}")
    
    def _validate_dependencies(self):
        """Validate web dependencies"""
        package_json_path = os.path.join(self.project_dir, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                # Check for security issues (basic check)
                dependencies = package_data.get('dependencies', {})
                dev_dependencies = package_data.get('devDependencies', {})
                
                # Warn about missing react/vue/angular if it's supposed to be there
                all_deps = {**dependencies, **dev_dependencies}
                
                if not all_deps:
                    self.result.add_warning("No dependencies installed")
                    
            except Exception:
                pass


class FlutterProjectValidator(CodeValidator):
    """Validator for Flutter projects"""
    
    def _validate_structure(self):
        """Validate Flutter project structure"""
        super()._validate_structure()
        
        required_dirs = ['lib', 'test']
        for dir_name in required_dirs:
            dir_path = os.path.join(self.project_dir, dir_name)
            if not os.path.exists(dir_path):
                self.result.add_error(f"Missing required directory: {dir_name}")
    
    def _validate_files(self):
        """Validate Flutter project files"""
        # Check pubspec.yaml
        pubspec_path = os.path.join(self.project_dir, 'pubspec.yaml')
        if not os.path.exists(pubspec_path):
            self.result.add_error("Missing pubspec.yaml file")
        else:
            self._validate_pubspec(pubspec_path)
        
        # Check for main.dart
        main_dart_path = os.path.join(self.project_dir, 'lib', 'main.dart')
        if not os.path.exists(main_dart_path):
            self.result.add_error("Missing lib/main.dart file")
    
    def _validate_pubspec(self, path: str):
        """Validate pubspec.yaml"""
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            # Basic checks for required fields
            required_fields = ['name:', 'description:', 'version:']
            for field in required_fields:
                if field not in content:
                    self.result.add_error(f"pubspec.yaml missing required field: {field.rstrip(':')}")
            
            # Check for Flutter SDK
            if 'sdk: flutter' not in content:
                self.result.add_warning("Flutter SDK not specified in pubspec.yaml")
                
        except Exception as e:
            self.result.add_error(f"Error reading pubspec.yaml: {str(e)}")
    
    def _validate_dependencies(self):
        """Validate Flutter dependencies"""
        pubspec_path = os.path.join(self.project_dir, 'pubspec.yaml')
        if os.path.exists(pubspec_path):
            try:
                with open(pubspec_path, 'r') as f:
                    content = f.read()
                
                if 'dependencies:' not in content:
                    self.result.add_warning("No dependencies defined in pubspec.yaml")
                    
            except Exception:
                pass


class AndroidProjectValidator(CodeValidator):
    """Validator for Android projects"""
    
    def _validate_structure(self):
        """Validate Android project structure"""
        super()._validate_structure()
        
        required_dirs = ['app/src/main', 'app/src/main/java', 'app/src/main/res']
        for dir_name in required_dirs:
            dir_path = os.path.join(self.project_dir, dir_name)
            if not os.path.exists(dir_path):
                self.result.add_warning(f"Missing typical directory: {dir_name}")
    
    def _validate_files(self):
        """Validate Android project files"""
        # Check for AndroidManifest.xml
        manifest_path = os.path.join(self.project_dir, 'app/src/main/AndroidManifest.xml')
        if not os.path.exists(manifest_path):
            self.result.add_error("Missing AndroidManifest.xml")
        
        # Check for build.gradle
        build_gradle_path = os.path.join(self.project_dir, 'app/build.gradle')
        if not os.path.exists(build_gradle_path):
            self.result.add_error("Missing app/build.gradle")


class IOSProjectValidator(CodeValidator):
    """Validator for iOS projects"""
    
    def _validate_structure(self):
        """Validate iOS project structure"""
        super()._validate_structure()
        
        # iOS projects have various structures
        # Basic check for common directories
        pass
    
    def _validate_files(self):
        """Validate iOS project files"""
        # Check for Info.plist
        info_plist_patterns = ['**/Info.plist']
        found = False
        for pattern in info_plist_patterns:
            if list(Path(self.project_dir).glob(pattern)):
                found = True
                break
        
        if not found:
            self.result.add_warning("No Info.plist file found")


class SyntaxValidator:
    """Syntax validator for different languages"""
    
    @staticmethod
    def _count_brackets_outside_strings(code: str, open_bracket: str, close_bracket: str) -> tuple:
        """Count brackets outside of strings and comments (basic implementation)"""
        in_string = False
        string_char = None
        open_count = 0
        close_count = 0
        i = 0
        
        while i < len(code):
            char = code[i]
            
            # Skip line comments
            if not in_string and i < len(code) - 1 and code[i:i+2] == '//':
                # Skip to end of line
                while i < len(code) and code[i] != '\n':
                    i += 1
                # Move past the newline if we found one
                if i < len(code):
                    i += 1
                continue
            
            # Skip block comments
            if not in_string and i < len(code) - 1 and code[i:i+2] == '/*':
                # Skip to end of comment
                while i < len(code) - 1:
                    if code[i:i+2] == '*/':
                        i += 2
                        break
                    i += 1
                continue
            
            # Track strings - count number of preceding backslashes
            if char in ['"', "'", '`']:
                # Count consecutive backslashes before this character
                num_backslashes = 0
                j = i - 1
                while j >= 0 and code[j] == '\\':
                    num_backslashes += 1
                    j -= 1
                
                # If even number of backslashes (or zero), the quote is not escaped
                if num_backslashes % 2 == 0:
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
            
            # Count brackets outside strings
            if not in_string:
                if char == open_bracket:
                    open_count += 1
                elif char == close_bracket:
                    close_count += 1
            
            i += 1
        
        return open_count, close_count
    
    @staticmethod
    def _validate_brackets(code: str) -> List[str]:
        """Validate bracket matching for code"""
        errors = []
        
        # Check curly braces
        open_count, close_count = SyntaxValidator._count_brackets_outside_strings(code, '{', '}')
        if open_count != close_count:
            errors.append(f"Mismatched curly braces ({open_count} open, {close_count} close)")
        
        # Check parentheses
        open_count, close_count = SyntaxValidator._count_brackets_outside_strings(code, '(', ')')
        if open_count != close_count:
            errors.append(f"Mismatched parentheses ({open_count} open, {close_count} close)")
        
        # Check square brackets
        open_count, close_count = SyntaxValidator._count_brackets_outside_strings(code, '[', ']')
        if open_count != close_count:
            errors.append(f"Mismatched square brackets ({open_count} open, {close_count} close)")
        
        return errors
    
    @staticmethod
    def validate_javascript(code: str) -> List[str]:
        """Basic JavaScript syntax validation"""
        return SyntaxValidator._validate_brackets(code)
    
    @staticmethod
    def validate_dart(code: str) -> List[str]:
        """Basic Dart syntax validation"""
        return SyntaxValidator._validate_brackets(code)


def create_validator(project_type: str, project_dir: str) -> CodeValidator:
    """Factory function to create appropriate validator"""
    project_type = project_type.lower()
    
    if 'flutter' in project_type:
        return FlutterProjectValidator(project_dir)
    elif 'android' in project_type:
        return AndroidProjectValidator(project_dir)
    elif 'ios' in project_type:
        return IOSProjectValidator(project_dir)
    elif any(web_type in project_type for web_type in ['web', 'react', 'vue', 'angular', 'svelte', 'next']):
        return WebProjectValidator(project_dir)
    else:
        return CodeValidator(project_dir)


__all__ = [
    'ValidationResult',
    'CodeValidator',
    'WebProjectValidator',
    'FlutterProjectValidator',
    'AndroidProjectValidator',
    'IOSProjectValidator',
    'SyntaxValidator',
    'create_validator'
]
