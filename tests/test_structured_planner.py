#!/usr/bin/env python3
"""
Unit tests for the Structured Planner module.

Tests the 7-phase planning architecture:
1. Prompt Understanding & Expansion
2. Requirement Decomposition
3. System Design & Architecture
4. Technology & Tool Selection
5. Task Breakdown
6. Risk & Complexity Analysis
7. Validation Checklist
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from shakty3n.planner import (
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
    validate_plan,
    validate_task_dependencies,
    get_plan_quality_score,
    REQUIRED_PLAN_SECTIONS,
)


class MockAIProvider:
    """Mock AI provider that returns structured JSON responses"""
    
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_count = 0
        
    def generate(self, prompt, system_prompt=None, temperature=0.3, **kwargs):
        self.call_count += 1
        
        # Return appropriate mock responses based on what the prompt is asking for
        if "primary_goal" in prompt.lower() or "analyze" in prompt.lower():
            return '''```json
{
    "primary_goal": "Build a user authentication system",
    "secondary_goals": ["Add password reset", "Support social login"],
    "implicit_requirements": ["Secure password storage", "Session management"],
    "assumptions": ["Web-based application", "REST API"],
    "unknowns": ["Third-party OAuth configuration"]
}
```'''
        elif "functional" in prompt.lower() and "requirements" in prompt.lower():
            return '''```json
{
    "functional": [
        "User can register with email and password",
        "User can login with credentials",
        "User can logout",
        "Session tokens are validated"
    ],
    "non_functional": [
        "Passwords hashed with bcrypt",
        "API response under 200ms",
        "Support 100 concurrent users"
    ]
}
```'''
        elif "architecture" in prompt.lower() or "components" in prompt.lower():
            return '''```json
{
    "components": [
        {"name": "API Layer", "responsibility": "Handle HTTP requests"},
        {"name": "Auth Service", "responsibility": "Authentication logic"},
        {"name": "Database", "responsibility": "User persistence"}
    ],
    "data_flow": "Client → API → Auth Service → Database",
    "patterns": ["MVC", "Repository Pattern"]
}
```'''
        elif "technology" in prompt.lower() or "language" in prompt.lower():
            return '''```json
{
    "language": "Python",
    "framework": "FastAPI",
    "database": "SQLite",
    "testing": "pytest",
    "additional_tools": ["bcrypt", "PyJWT"]
}
```'''
        elif "tasks" in prompt.lower() or "breakdown" in prompt.lower():
            return '''```json
{
    "tasks": [
        {
            "title": "Initialize project structure",
            "description": "Create folder structure and requirements.txt",
            "dependencies": [],
            "testable_outcome": "Project directory exists"
        },
        {
            "title": "Create FastAPI application",
            "description": "Set up main.py with FastAPI app",
            "dependencies": [1],
            "testable_outcome": "python main.py runs"
        },
        {
            "title": "Implement user model",
            "description": "Create User model with SQLAlchemy",
            "dependencies": [2],
            "testable_outcome": "Database tables created"
        },
        {
            "title": "Add authentication endpoints",
            "description": "Create /register and /login endpoints",
            "dependencies": [3],
            "testable_outcome": "Endpoints respond to requests"
        },
        {
            "title": "Add tests",
            "description": "Write pytest tests for auth flow",
            "dependencies": [4],
            "testable_outcome": "Tests pass"
        }
    ]
}
```'''
        elif "risk" in prompt.lower():
            return '''```json
{
    "risks": [
        {"risk": "SQL injection", "mitigation": "Use parameterized queries"},
        {"risk": "Weak passwords", "mitigation": "Enforce password policy"}
    ],
    "complexity_score": 5
}
```'''
        else:
            return '''```json
{
    "checks": [
        {"check": "Primary goal clear", "passed": true},
        {"check": "Requirements defined", "passed": true}
    ],
    "is_valid": true,
    "issues": []
}
```'''


class TestStructuredPlanner:
    """Tests for the StructuredPlanner class"""
    
    def test_planner_initialization(self):
        """Test that planner initializes correctly"""
        provider = MockAIProvider()
        planner = StructuredPlanner(provider)
        
        assert planner.ai_provider == provider
        assert planner.current_phase == PlanningPhase.PROMPT_UNDERSTANDING
        
    def test_create_structured_plan(self):
        """Test creating a complete structured plan"""
        provider = MockAIProvider()
        planner = StructuredPlanner(provider)
        
        result = planner.create_structured_plan(
            description="Build a user authentication API",
            project_type="web-react",
        )
        
        assert isinstance(result, PlanningOutput)
        assert result.problem_understanding.primary_goal
        assert len(result.requirements.functional) > 0
        # Architecture might use fallback if mock doesn't match exactly
        assert result.architecture.data_flow  # Data flow should always be set
        assert result.technology_choices.language
        assert len(result.task_breakdown) > 0
        assert len(result.risk_analysis.risks) > 0
        # Validation checklist should exist
        assert isinstance(result.validation_checklist, ValidationChecklist)
        
    def test_plan_to_dict(self):
        """Test that plan can be serialized to dict"""
        provider = MockAIProvider()
        planner = StructuredPlanner(provider)
        
        result = planner.create_structured_plan(
            description="Simple todo app",
            project_type="web-react",
        )
        
        plan_dict = result.to_dict()
        
        assert "problem_understanding" in plan_dict
        assert "requirements" in plan_dict
        assert "architecture" in plan_dict
        assert "technology_choices" in plan_dict
        assert "task_breakdown" in plan_dict
        assert "risk_analysis" in plan_dict
        
    def test_get_tasks_for_executor(self):
        """Test that tasks are converted to executor format"""
        provider = MockAIProvider()
        planner = StructuredPlanner(provider)
        
        result = planner.create_structured_plan(
            description="Build API",
            project_type="web-react",
        )
        
        tasks = result.get_tasks_for_executor()
        
        assert len(tasks) > 0
        assert all("title" in t for t in tasks)
        assert all("description" in t for t in tasks)
        
    def test_get_summary(self):
        """Test that summary generation works"""
        provider = MockAIProvider()
        planner = StructuredPlanner(provider)
        
        result = planner.create_structured_plan(
            description="Build API",
            project_type="web-react",
        )
        
        summary = result.get_summary()
        
        assert "PRIMARY GOAL" in summary
        assert "FUNCTIONAL REQUIREMENTS" in summary
        assert "TASK BREAKDOWN" in summary


class TestPlanValidation:
    """Tests for plan validation utilities"""
    
    def test_validate_complete_plan(self):
        """Test validating a complete plan"""
        plan = {
            "problem_understanding": {"primary_goal": "Build app"},
            "requirements": {"functional": ["Feature 1"], "non_functional": []},
            "architecture": {"components": [{"name": "API"}], "data_flow": "A → B"},
            "technology_choices": {"language": "Python", "framework": "Flask"},
            "task_breakdown": [
                {"step": 1, "title": "Init", "description": "Setup"},
                {"step": 2, "title": "Build", "description": "Code"},
                {"step": 3, "title": "Test", "description": "Verify"},
            ],
            "risk_analysis": {"risks": [{"risk": "Bug"}], "complexity_score": 5},
        }
        
        is_valid, issues = validate_plan(plan)
        
        assert is_valid
        assert len(issues) == 0
        
    def test_validate_incomplete_plan(self):
        """Test that incomplete plans are rejected"""
        plan = {
            "problem_understanding": {"primary_goal": ""},  # Empty goal
            "requirements": {"functional": []},  # No requirements
        }
        
        is_valid, issues = validate_plan(plan)
        
        assert not is_valid
        assert len(issues) > 0
        
    def test_validate_task_dependencies(self):
        """Test task dependency validation"""
        # Valid dependencies
        tasks = [
            {"step": 1, "dependencies": []},
            {"step": 2, "dependencies": [1]},
            {"step": 3, "dependencies": [1, 2]},
        ]
        
        is_valid, issues = validate_task_dependencies(tasks)
        assert is_valid
        
        # Invalid: depends on non-existent task
        tasks_invalid = [
            {"step": 1, "dependencies": [99]},
        ]
        
        is_valid, issues = validate_task_dependencies(tasks_invalid)
        assert not is_valid
        
    def test_plan_quality_score(self):
        """Test plan quality scoring"""
        # Minimal plan
        minimal_plan = {
            "problem_understanding": {"primary_goal": "X"},
            "requirements": {"functional": ["A"]},
            "architecture": {"components": [{"name": "C"}], "data_flow": "A"},
            "technology_choices": {"language": "Python", "framework": "Flask"},
            "task_breakdown": [{"step": 1}],
            "risk_analysis": {"risks": [{}]},
        }
        
        score = get_plan_quality_score(minimal_plan)
        assert 0 <= score <= 100
        
        # More complete plan should score higher
        complete_plan = {
            "problem_understanding": {
                "primary_goal": "Build comprehensive system",
                "secondary_goals": ["Goal 1", "Goal 2"],
                "implicit_requirements": ["Req 1"],
                "assumptions": ["Assumption 1"],
            },
            "requirements": {
                "functional": ["F1", "F2", "F3", "F4", "F5"],
                "non_functional": ["NF1", "NF2", "NF3"],
            },
            "architecture": {
                "components": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
                "data_flow": "A → B → C",
            },
            "technology_choices": {"language": "Python", "framework": "FastAPI"},
            "task_breakdown": [{} for _ in range(8)],
            "risk_analysis": {"risks": [{}, {}, {}]},
        }
        
        better_score = get_plan_quality_score(complete_plan)
        assert better_score > score


class TestDataClasses:
    """Tests for planning data classes"""
    
    def test_problem_understanding(self):
        """Test ProblemUnderstanding dataclass"""
        problem = ProblemUnderstanding(
            primary_goal="Build app",
            secondary_goals=["Feature A"],
            implicit_requirements=["Security"],
            assumptions=["Web-based"],
        )
        
        d = problem.to_dict()
        assert d["primary_goal"] == "Build app"
        assert "secondary_goals" in d
        
    def test_executable_task(self):
        """Test ExecutableTask dataclass"""
        task = ExecutableTask(
            step=1,
            title="Init project",
            description="Create structure",
            dependencies=[],
            testable_outcome="Dir exists",
        )
        
        d = task.to_dict()
        assert d["step"] == 1
        assert d["title"] == "Init project"
        
    def test_risk_analysis(self):
        """Test RiskAnalysis dataclass"""
        risk = RiskAnalysis(
            risks=[{"risk": "Bug", "mitigation": "Test"}],
            complexity_score=7,
        )
        
        d = risk.to_dict()
        assert d["complexity_score"] == 7
        assert len(d["risks"]) == 1


def run_structured_planner_tests():
    """Run all structured planner tests"""
    print("=" * 60)
    print("Structured Planner Unit Tests")
    print("=" * 60)
    
    # Run tests using pytest
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=False
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_structured_planner_tests())
