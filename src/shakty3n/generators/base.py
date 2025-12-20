"""
Base Code Generator
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import os


class CodeGenerator(ABC):
    """Abstract base class for code generators"""
    
    def __init__(self, ai_provider, output_dir: str):
        self.ai_provider = ai_provider
        self.output_dir = output_dir
        self.generated_files = []
    
    @abstractmethod
    def generate_project(self, description: str, requirements: Dict) -> Dict:
        """Generate a complete project"""
        pass
    
    def create_file(self, filepath: str, content: str):
        """Create a file with content"""
        full_path = os.path.join(self.output_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.generated_files.append(filepath)
        return full_path
    
    def create_directory(self, dirpath: str):
        """Create a directory"""
        full_path = os.path.join(self.output_dir, dirpath)
        os.makedirs(full_path, exist_ok=True)
        return full_path
    
    def get_generated_files(self) -> List[str]:
        """Get list of generated files"""
        return self.generated_files
