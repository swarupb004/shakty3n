"""
Planner module initialization

Provides both the original TaskPlanner for backward compatibility
and the new StructuredPlanner for enhanced 7-phase planning.
"""
from .task_planner import TaskPlanner, Task, TaskStatus
from .structured_planner import (
    StructuredPlanner,
    PlanningPhase,
    PlanningOutput,
    ProblemUnderstanding,
    Requirements,
    ArchitectureSpec,
    TechnologyChoices,
    ExecutableTask,
    RiskAnalysis,
    ValidationChecklist,
)
from .plan_schema import (
    validate_plan,
    validate_task_dependencies,
    get_plan_quality_score,
    REQUIRED_PLAN_SECTIONS,
)

__all__ = [
    # Original planner (backward compatible)
    'TaskPlanner',
    'Task',
    'TaskStatus',
    # New structured planner
    'StructuredPlanner',
    'PlanningPhase',
    'PlanningOutput',
    'ProblemUnderstanding',
    'Requirements',
    'ArchitectureSpec',
    'TechnologyChoices',
    'ExecutableTask',
    'RiskAnalysis',
    'ValidationChecklist',
    # Validation utilities
    'validate_plan',
    'validate_task_dependencies',
    'get_plan_quality_score',
    'REQUIRED_PLAN_SECTIONS',
]
