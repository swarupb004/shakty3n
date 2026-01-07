"""
Plan Schema and Validation for Structured Planner

Defines the required sections for a valid plan and provides
validation utilities to reject incomplete plans.
"""
from typing import Any, Dict, List, Tuple

# Required sections that must be present in every valid plan
REQUIRED_PLAN_SECTIONS = [
    "problem_understanding",
    "requirements",
    "architecture",
    "technology_choices",
    "task_breakdown",
    "risk_analysis",
]

# Minimum requirements for each section
SECTION_REQUIREMENTS = {
    "problem_understanding": {
        "required_fields": ["primary_goal"],
        "min_items": None,
    },
    "requirements": {
        "required_fields": [],
        "min_items": {"functional": 1},
    },
    "architecture": {
        "required_fields": ["data_flow"],
        "min_items": {"components": 1},
    },
    "technology_choices": {
        "required_fields": ["language", "framework"],
        "min_items": None,
    },
    "task_breakdown": {
        "required_fields": [],
        "min_items": None,
        "min_list_length": 3,
    },
    "risk_analysis": {
        "required_fields": [],
        "min_items": {"risks": 1},
    },
}


def validate_plan(plan_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a plan dictionary against the required schema.
    
    Args:
        plan_dict: Dictionary representation of a PlanningOutput
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check all required sections are present
    for section in REQUIRED_PLAN_SECTIONS:
        if section not in plan_dict:
            issues.append(f"Missing required section: {section}")
            continue
            
        section_data = plan_dict[section]
        if section_data is None:
            issues.append(f"Section is null: {section}")
            continue
            
        # Validate section requirements
        section_issues = _validate_section(section, section_data)
        issues.extend(section_issues)
    
    return len(issues) == 0, issues


def _validate_section(section_name: str, section_data: Any) -> List[str]:
    """Validate a single section against its requirements"""
    issues = []
    
    if section_name not in SECTION_REQUIREMENTS:
        return issues
        
    reqs = SECTION_REQUIREMENTS[section_name]
    
    # Check required fields
    for field in reqs.get("required_fields", []):
        if isinstance(section_data, dict):
            value = section_data.get(field)
            if not value:
                issues.append(f"{section_name}.{field} is missing or empty")
    
    # Check minimum items for dict fields
    min_items = reqs.get("min_items")
    if min_items and isinstance(section_data, dict):
        for field, min_count in min_items.items():
            items = section_data.get(field, [])
            if not items or (isinstance(items, list) and len(items) < min_count):
                issues.append(f"{section_name}.{field} must have at least {min_count} item(s)")
    
    # Check minimum list length (for task_breakdown which is a list)
    min_list_length = reqs.get("min_list_length")
    if min_list_length and isinstance(section_data, list):
        if len(section_data) < min_list_length:
            issues.append(f"{section_name} must have at least {min_list_length} items")
    
    return issues


def validate_task_dependencies(tasks: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate that task dependencies are valid (no cycles, all references exist).
    
    Args:
        tasks: List of task dictionaries with 'step' and 'dependencies' fields
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    task_steps = {t.get("step", i+1) for i, t in enumerate(tasks)}
    
    for task in tasks:
        step = task.get("step", 0)
        deps = task.get("dependencies", [])
        
        for dep in deps:
            # Check dependency exists
            if dep not in task_steps:
                issues.append(f"Task {step} depends on non-existent task {dep}")
            # Check no self-dependency
            if dep == step:
                issues.append(f"Task {step} cannot depend on itself")
            # Check dependency is earlier (simple cycle check)
            if dep >= step:
                issues.append(f"Task {step} depends on later task {dep} (potential cycle)")
    
    return len(issues) == 0, issues


def get_plan_quality_score(plan_dict: Dict[str, Any]) -> int:
    """
    Calculate a quality score (0-100) for a plan.
    
    Higher scores indicate more complete and detailed plans.
    """
    score = 0
    
    # Basic section presence (max 40 points)
    for section in REQUIRED_PLAN_SECTIONS:
        if section in plan_dict and plan_dict[section]:
            score += 6
    
    # Problem understanding depth (max 10 points)
    problem = plan_dict.get("problem_understanding", {})
    if problem.get("primary_goal"):
        score += 3
    if len(problem.get("secondary_goals", [])) > 0:
        score += 2
    if len(problem.get("implicit_requirements", [])) > 0:
        score += 2
    if len(problem.get("assumptions", [])) > 0:
        score += 3
    
    # Requirements completeness (max 15 points)
    reqs = plan_dict.get("requirements", {})
    functional = reqs.get("functional", [])
    non_functional = reqs.get("non_functional", [])
    score += min(len(functional) * 2, 10)
    score += min(len(non_functional) * 1, 5)
    
    # Architecture detail (max 10 points)
    arch = plan_dict.get("architecture", {})
    score += min(len(arch.get("components", [])) * 2, 6)
    if arch.get("data_flow"):
        score += 4
    
    # Task coverage (max 15 points)
    tasks = plan_dict.get("task_breakdown", [])
    score += min(len(tasks) * 2, 15)
    
    # Risk awareness (max 10 points)
    risks = plan_dict.get("risk_analysis", {})
    score += min(len(risks.get("risks", [])) * 3, 10)
    
    return min(score, 100)


__all__ = [
    "REQUIRED_PLAN_SECTIONS",
    "SECTION_REQUIREMENTS",
    "validate_plan",
    "validate_task_dependencies",
    "get_plan_quality_score",
]
