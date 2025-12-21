"""
Shakty3n - Autonomous Agentic Coder
"""

__version__ = "1.0.0"
__author__ = "Shakty3n Team"
__description__ = "Autonomous Agentic Coder for building applications"

from .ai_providers import AIProviderFactory
from .planner import TaskPlanner, Task, TaskStatus
from .generators import (
    CodeGenerator,
    WebAppGenerator,
    AndroidAppGenerator,
    IOSAppGenerator,
    DesktopAppGenerator,
    FlutterAppGenerator
)
from .debugger import AutoDebugger
from .executor import AutonomousExecutor
from .utils import Config, load_env_vars

__all__ = [
    'AIProviderFactory',
    'TaskPlanner',
    'Task',
    'TaskStatus',
    'CodeGenerator',
    'WebAppGenerator',
    'AndroidAppGenerator',
    'IOSAppGenerator',
    'DesktopAppGenerator',
    'FlutterAppGenerator',
    'AutoDebugger',
    'AutonomousExecutor',
    'Config',
    'load_env_vars'
]
