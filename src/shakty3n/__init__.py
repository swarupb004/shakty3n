"""
Shakty3n - Autonomous Agentic Coder
"""

__version__ = "1.1.0"
__author__ = "Shakty3n Team"
__description__ = "Autonomous Agentic Coder for building applications"

from .ai_providers import AIProviderFactory
from .planner import (
    TaskPlanner,
    Task,
    TaskStatus,
    StructuredPlanner,
    PlanningPhase,
    PlanningOutput,
)
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
from .utils import Config, VirtualEnvManager, load_env_vars
from .agent_manager import AgentManager, AgentWorkspace, AgentSession
from .autonomy import (
    IntentSpec,
    IntentAnalyzer,
    ArchitectureBlueprint,
    ArchitectureDesigner,
    AutonomyMemory,
    ExecutionObserver,
    SecurityGuard,
    CollaborativeOrchestrator,
    CICDOrchestrator,
)

__all__ = [
    'AIProviderFactory',
    # Original planner
    'TaskPlanner',
    'Task',
    'TaskStatus',
    # New structured planner
    'StructuredPlanner',
    'PlanningPhase',
    'PlanningOutput',
    # Generators
    'CodeGenerator',
    'WebAppGenerator',
    'AndroidAppGenerator',
    'IOSAppGenerator',
    'DesktopAppGenerator',
    'FlutterAppGenerator',
    # Core
    'AutoDebugger',
    'AutonomousExecutor',
    'Config',
    'VirtualEnvManager',
    'load_env_vars',
    # Agent management
    'AgentManager',
    'AgentWorkspace',
    'AgentSession',
    # Autonomy components
    'IntentSpec',
    'IntentAnalyzer',
    'ArchitectureBlueprint',
    'ArchitectureDesigner',
    'AutonomyMemory',
    'ExecutionObserver',
    'SecurityGuard',
    'CollaborativeOrchestrator',
    'CICDOrchestrator',
]

