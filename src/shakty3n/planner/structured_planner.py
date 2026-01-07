"""
Structured Planning Module for Shakty3n Autonomous Coder

Implements a 7-phase planning architecture:
1. Prompt Understanding & Expansion
2. Requirement Decomposition
3. System Design & Architecture
4. Technology & Tool Selection
5. Task Breakdown (Executable Plan)
6. Risk & Complexity Analysis
7. Validation Checklist
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json
import logging

from .planning_prompts import (
    PROMPT_UNDERSTANDING_TEMPLATE,
    REQUIREMENTS_TEMPLATE,
    ARCHITECTURE_TEMPLATE,
    TECHNOLOGY_TEMPLATE,
    TASK_BREAKDOWN_TEMPLATE,
    RISK_ANALYSIS_TEMPLATE,
    VALIDATION_TEMPLATE,
    PLANNER_SYSTEM_PROMPT,
)
from .plan_schema import validate_plan, REQUIRED_PLAN_SECTIONS

logger = logging.getLogger(__name__)


class PlanningPhase(Enum):
    """Tracks which planning phase is active"""
    PROMPT_UNDERSTANDING = "prompt_understanding"
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    TECHNOLOGY = "technology"
    TASK_BREAKDOWN = "task_breakdown"
    RISK_ANALYSIS = "risk_analysis"
    VALIDATION = "validation"
    COMPLETE = "complete"


@dataclass
class ProblemUnderstanding:
    """Output of Phase 1: Prompt Understanding"""
    primary_goal: str
    secondary_goals: List[str] = field(default_factory=list)
    implicit_requirements: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_goal": self.primary_goal,
            "secondary_goals": self.secondary_goals,
            "implicit_requirements": self.implicit_requirements,
            "assumptions": self.assumptions,
            "unknowns": self.unknowns,
        }


@dataclass
class Requirements:
    """Output of Phase 2: Requirement Decomposition"""
    functional: List[str] = field(default_factory=list)
    non_functional: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "functional": self.functional,
            "non_functional": self.non_functional,
        }


@dataclass
class ArchitectureSpec:
    """Output of Phase 3: System Design & Architecture"""
    components: List[Dict[str, str]] = field(default_factory=list)
    data_flow: str = ""
    patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "components": self.components,
            "data_flow": self.data_flow,
            "patterns": self.patterns,
        }


@dataclass
class TechnologyChoices:
    """Output of Phase 4: Technology & Tool Selection"""
    language: str = ""
    framework: str = ""
    database: Optional[str] = None
    testing: str = ""
    additional_tools: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "framework": self.framework,
            "database": self.database,
            "testing": self.testing,
            "additional_tools": self.additional_tools,
        }


@dataclass
class ExecutableTask:
    """A single executable task in the plan"""
    step: int
    title: str
    description: str
    dependencies: List[int] = field(default_factory=list)
    testable_outcome: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "title": self.title,
            "description": self.description,
            "dependencies": self.dependencies,
            "testable_outcome": self.testable_outcome,
        }


@dataclass
class RiskAnalysis:
    """Output of Phase 6: Risk & Complexity Analysis"""
    risks: List[Dict[str, str]] = field(default_factory=list)
    complexity_score: int = 5  # 1-10 scale

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risks": self.risks,
            "complexity_score": self.complexity_score,
        }


@dataclass
class ValidationChecklist:
    """Output of Phase 7: Validation Checklist"""
    checks: List[Dict[str, bool]] = field(default_factory=list)
    is_valid: bool = False
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checks": self.checks,
            "is_valid": self.is_valid,
            "issues": self.issues,
        }


@dataclass
class PlanningOutput:
    """Complete planning output - contract for valid plans"""
    problem_understanding: ProblemUnderstanding
    requirements: Requirements
    architecture: ArchitectureSpec
    technology_choices: TechnologyChoices
    task_breakdown: List[ExecutableTask]
    risk_analysis: RiskAnalysis
    validation_checklist: ValidationChecklist

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_understanding": self.problem_understanding.to_dict(),
            "requirements": self.requirements.to_dict(),
            "architecture": self.architecture.to_dict(),
            "technology_choices": self.technology_choices.to_dict(),
            "task_breakdown": [t.to_dict() for t in self.task_breakdown],
            "risk_analysis": self.risk_analysis.to_dict(),
            "validation_checklist": self.validation_checklist.to_dict(),
        }

    def get_summary(self) -> str:
        """Generate a human-readable summary of the plan"""
        lines = [
            "=" * 60,
            "STRUCTURED DEVELOPMENT PLAN",
            "=" * 60,
            "",
            "📋 PRIMARY GOAL:",
            f"   {self.problem_understanding.primary_goal}",
            "",
            "📦 FUNCTIONAL REQUIREMENTS:",
        ]
        for req in self.requirements.functional[:5]:
            lines.append(f"   • {req}")
        
        lines.extend([
            "",
            "🏗️ ARCHITECTURE:",
            f"   Data Flow: {self.architecture.data_flow}",
            "",
            "🔧 TECHNOLOGY:",
            f"   Language: {self.technology_choices.language}",
            f"   Framework: {self.technology_choices.framework}",
            "",
            "📝 TASK BREAKDOWN:",
        ])
        for task in self.task_breakdown:
            lines.append(f"   {task.step}. {task.title}")
        
        lines.extend([
            "",
            f"⚠️ RISKS IDENTIFIED: {len(self.risk_analysis.risks)}",
            f"✅ PLAN VALID: {self.validation_checklist.is_valid}",
            "=" * 60,
        ])
        return "\n".join(lines)

    def get_tasks_for_executor(self) -> List[Dict[str, Any]]:
        """Convert task breakdown to format expected by TaskPlanner"""
        def _normalize_dependencies(deps: List[Any], current_index: int) -> List[int]:
            """Convert 1-based dependencies to 0-based and drop invalid/self refs."""
            normalized = []
            for dep in deps:
                if isinstance(dep, int):
                    dep_idx = dep - 1 if dep > 0 else dep
                    if 0 <= dep_idx < current_index:
                        normalized.append(dep_idx)
            return normalized

        return [
            {
                "title": task.title,
                "description": task.description,
                "dependencies": _normalize_dependencies(task.dependencies, idx),
            }
            for idx, task in enumerate(self.task_breakdown)
        ]


class StructuredPlanner:
    """
    7-phase structured planning system for autonomous coding.
    
    Converts vague user prompts into precise, actionable development plans
    with requirements, architecture, task breakdown, and risk analysis.
    """

    def __init__(self, ai_provider, multi_pass: bool = False):
        """
        Initialize the structured planner.
        
        Args:
            ai_provider: AI provider for generating plan content
            multi_pass: If True, use draft→critic→revise cycle for better quality
        """
        self.ai_provider = ai_provider
        self.multi_pass = multi_pass
        self.current_phase = PlanningPhase.PROMPT_UNDERSTANDING
        self.on_phase_change = None  # Callback for progress updates

    def create_structured_plan(
        self,
        description: str,
        project_type: str,
        requirements: Optional[Dict[str, Any]] = None,
        environment_context: Optional[Dict[str, Any]] = None,
    ) -> PlanningOutput:
        """
        Create a comprehensive structured plan using 7-phase architecture.
        
        Args:
            description: User's project description
            project_type: Type of project (web-react, android, etc.)
            requirements: Optional explicit requirements from user
            environment_context: Optional environment constraints
            
        Returns:
            PlanningOutput with complete structured plan
        """
        requirements = requirements or {}
        environment_context = environment_context or {}

        # Phase 1: Prompt Understanding
        self._set_phase(PlanningPhase.PROMPT_UNDERSTANDING)
        problem = self._phase1_prompt_understanding(description, requirements)

        # Phase 2: Requirements
        self._set_phase(PlanningPhase.REQUIREMENTS)
        reqs = self._phase2_requirements(problem, project_type)

        # Phase 3: Architecture
        self._set_phase(PlanningPhase.ARCHITECTURE)
        architecture = self._phase3_architecture(problem, reqs, project_type)

        # Phase 4: Technology
        self._set_phase(PlanningPhase.TECHNOLOGY)
        technology = self._phase4_technology(project_type, architecture, environment_context)

        # Phase 5: Task Breakdown
        self._set_phase(PlanningPhase.TASK_BREAKDOWN)
        tasks = self._phase5_task_breakdown(problem, reqs, architecture, technology)

        # Phase 6: Risk Analysis
        self._set_phase(PlanningPhase.RISK_ANALYSIS)
        risks = self._phase6_risk_analysis(problem, reqs, tasks)

        # Phase 7: Validation
        self._set_phase(PlanningPhase.VALIDATION)
        validation = self._phase7_validation(problem, reqs, architecture, technology, tasks, risks)

        self._set_phase(PlanningPhase.COMPLETE)

        output = PlanningOutput(
            problem_understanding=problem,
            requirements=reqs,
            architecture=architecture,
            technology_choices=technology,
            task_breakdown=tasks,
            risk_analysis=risks,
            validation_checklist=validation,
        )

        # Validate the complete plan
        is_valid, issues = validate_plan(output.to_dict())
        if not is_valid:
            logger.warning("Plan validation failed: %s", issues)
            output.validation_checklist.is_valid = False
            output.validation_checklist.issues.extend(issues)

        return output

    def _set_phase(self, phase: PlanningPhase) -> None:
        """Update current phase and notify observers"""
        self.current_phase = phase
        if self.on_phase_change:
            self.on_phase_change(phase.value)

    def _generate(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate content from AI provider with error handling"""
        try:
            response = self.ai_provider.generate(
                prompt=prompt,
                system_prompt=PLANNER_SYSTEM_PROMPT,
                temperature=temperature,
            )
            return response if isinstance(response, str) else str(response)
        except Exception as e:
            logger.error("AI generation failed: %s", e)
            return ""

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from AI response"""
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_str = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_str = text[start:end].strip()
        else:
            try:
                start = text.index("{")
                decoder = json.JSONDecoder()
                obj, idx = decoder.raw_decode(text[start:])
                return obj
            except (ValueError, json.JSONDecodeError):
                return {}

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {}

    # ========== Phase Implementations ==========

    def _phase1_prompt_understanding(
        self, description: str, requirements: Dict[str, Any]
    ) -> ProblemUnderstanding:
        """Phase 1: Convert short prompts into a detailed problem statement"""
        prompt = PROMPT_UNDERSTANDING_TEMPLATE.format(
            description=description,
            requirements=json.dumps(requirements, indent=2) if requirements else "None provided",
        )

        response = self._generate(prompt)
        data = self._extract_json(response)

        return ProblemUnderstanding(
            primary_goal=data.get("primary_goal", description),
            secondary_goals=data.get("secondary_goals", []),
            implicit_requirements=data.get("implicit_requirements", []),
            assumptions=data.get("assumptions", []),
            unknowns=data.get("unknowns", []),
        )

    def _phase2_requirements(
        self, problem: ProblemUnderstanding, project_type: str
    ) -> Requirements:
        """Phase 2: Break the problem into atomic requirements"""
        prompt = REQUIREMENTS_TEMPLATE.format(
            primary_goal=problem.primary_goal,
            secondary_goals=json.dumps(problem.secondary_goals),
            implicit_requirements=json.dumps(problem.implicit_requirements),
            project_type=project_type,
        )

        response = self._generate(prompt)
        data = self._extract_json(response)

        return Requirements(
            functional=data.get("functional", []),
            non_functional=data.get("non_functional", [
                "Secure password storage",
                "Stateless architecture",
                "Maintainable code structure",
            ]),
        )

    def _phase3_architecture(
        self, problem: ProblemUnderstanding, reqs: Requirements, project_type: str
    ) -> ArchitectureSpec:
        """Phase 3: Define how components interact"""
        prompt = ARCHITECTURE_TEMPLATE.format(
            primary_goal=problem.primary_goal,
            functional_requirements=json.dumps(reqs.functional),
            non_functional_requirements=json.dumps(reqs.non_functional),
            project_type=project_type,
        )

        response = self._generate(prompt)
        data = self._extract_json(response)

        return ArchitectureSpec(
            components=data.get("components", []),
            data_flow=data.get("data_flow", "Client → Controller → Service → Storage"),
            patterns=data.get("patterns", ["MVC", "Repository Pattern"]),
        )

    def _phase4_technology(
        self, project_type: str, architecture: ArchitectureSpec, 
        environment_context: Dict[str, Any]
    ) -> TechnologyChoices:
        """Phase 4: Lock technology choices early"""
        prompt = TECHNOLOGY_TEMPLATE.format(
            project_type=project_type,
            components=json.dumps(architecture.components),
            environment=json.dumps(environment_context) if environment_context else "Default",
        )

        response = self._generate(prompt)
        data = self._extract_json(response)

        # Apply defaults based on project type
        defaults = self._get_technology_defaults(project_type)

        return TechnologyChoices(
            language=data.get("language", defaults.get("language", "JavaScript")),
            framework=data.get("framework", defaults.get("framework", "")),
            database=data.get("database", defaults.get("database")),
            testing=data.get("testing", defaults.get("testing", "Jest")),
            additional_tools=data.get("additional_tools", []),
        )

    def _get_technology_defaults(self, project_type: str) -> Dict[str, str]:
        """Get sensible defaults based on project type"""
        defaults = {
            "web-react": {"language": "JavaScript", "framework": "React", "testing": "Jest"},
            "web-vue": {"language": "JavaScript", "framework": "Vue.js", "testing": "Vitest"},
            "web-nextjs": {"language": "TypeScript", "framework": "Next.js", "testing": "Jest"},
            "web-angular": {"language": "TypeScript", "framework": "Angular", "testing": "Jasmine"},
            "web-svelte": {"language": "JavaScript", "framework": "Svelte", "testing": "Vitest"},
            "android": {"language": "Kotlin", "framework": "Android SDK", "testing": "JUnit"},
            "android-kotlin": {"language": "Kotlin", "framework": "Android SDK", "testing": "JUnit"},
            "android-java": {"language": "Java", "framework": "Android SDK", "testing": "JUnit"},
            "ios": {"language": "Swift", "framework": "SwiftUI", "testing": "XCTest"},
            "flutter": {"language": "Dart", "framework": "Flutter", "testing": "flutter_test"},
            "desktop-electron": {"language": "JavaScript", "framework": "Electron", "testing": "Jest"},
            "desktop-python": {"language": "Python", "framework": "tkinter", "testing": "pytest"},
        }
        return defaults.get(project_type.lower(), {"language": "JavaScript", "framework": "", "testing": "Jest"})

    def _phase5_task_breakdown(
        self, problem: ProblemUnderstanding, reqs: Requirements,
        architecture: ArchitectureSpec, technology: TechnologyChoices
    ) -> List[ExecutableTask]:
        """Phase 5: Create ordered, atomic, testable tasks"""
        prompt = TASK_BREAKDOWN_TEMPLATE.format(
            primary_goal=problem.primary_goal,
            functional_requirements=json.dumps(reqs.functional),
            components=json.dumps(architecture.components),
            technology=json.dumps(technology.to_dict()),
        )

        response = self._generate(prompt)
        data = self._extract_json(response)

        tasks = []
        for idx, task_data in enumerate(data.get("tasks", [])):
            tasks.append(ExecutableTask(
                step=idx + 1,
                title=task_data.get("title", f"Task {idx + 1}"),
                description=task_data.get("description", ""),
                dependencies=task_data.get("dependencies", []),
                testable_outcome=task_data.get("testable_outcome", ""),
            ))

        # Ensure we have at least basic tasks
        if not tasks:
            tasks = self._generate_fallback_tasks(problem, technology)

        return tasks

    def _generate_fallback_tasks(
        self, problem: ProblemUnderstanding, technology: TechnologyChoices
    ) -> List[ExecutableTask]:
        """Generate fallback tasks if AI fails"""
        return [
            ExecutableTask(
                step=1,
                title="Initialize Project",
                description=f"Set up {technology.framework} project structure",
                dependencies=[],
                testable_outcome="Project directory exists with configuration files",
            ),
            ExecutableTask(
                step=2,
                title="Create Core Structure",
                description="Create main application entry point and folder structure",
                dependencies=[1],
                testable_outcome="src/ directory with main file exists",
            ),
            ExecutableTask(
                step=3,
                title="Implement Features",
                description=f"Implement: {problem.primary_goal}",
                dependencies=[2],
                testable_outcome="Core features are functional",
            ),
            ExecutableTask(
                step=4,
                title="Add Tests",
                description=f"Add {technology.testing} tests for core functionality",
                dependencies=[3],
                testable_outcome="Tests pass",
            ),
            ExecutableTask(
                step=5,
                title="Documentation",
                description="Create README with setup and usage instructions",
                dependencies=[3],
                testable_outcome="README.md exists",
            ),
        ]

    def _phase6_risk_analysis(
        self, problem: ProblemUnderstanding, reqs: Requirements, 
        tasks: List[ExecutableTask]
    ) -> RiskAnalysis:
        """Phase 6: Identify and mitigate common failures"""
        prompt = RISK_ANALYSIS_TEMPLATE.format(
            primary_goal=problem.primary_goal,
            unknowns=json.dumps(problem.unknowns),
            task_count=len(tasks),
            requirements_count=len(reqs.functional) + len(reqs.non_functional),
        )

        response = self._generate(prompt)
        data = self._extract_json(response)

        risks = data.get("risks", [
            {"risk": "Ambiguous requirements", "mitigation": "Clarify with user before execution"},
            {"risk": "Dependency issues", "mitigation": "Lock versions early"},
            {"risk": "Missing error handling", "mitigation": "Add try/catch blocks"},
        ])

        complexity = data.get("complexity_score", 5)
        if len(tasks) > 10:
            complexity = min(complexity + 2, 10)

        return RiskAnalysis(risks=risks, complexity_score=complexity)

    def _phase7_validation(
        self, problem: ProblemUnderstanding, reqs: Requirements,
        architecture: ArchitectureSpec, technology: TechnologyChoices,
        tasks: List[ExecutableTask], risks: RiskAnalysis
    ) -> ValidationChecklist:
        """Phase 7: Enable self-critique before coding begins"""
        checks = [
            {"check": "Primary goal is clear", "passed": bool(problem.primary_goal)},
            {"check": "Functional requirements defined", "passed": len(reqs.functional) > 0},
            {"check": "Architecture components identified", "passed": len(architecture.components) > 0},
            {"check": "Technology choices locked", "passed": bool(technology.language and technology.framework)},
            {"check": "Tasks are ordered and atomic", "passed": len(tasks) > 0},
            {"check": "Risks documented", "passed": len(risks.risks) > 0},
            {"check": "All tasks have dependencies resolved", "passed": all(
                all(d < t.step for d in t.dependencies) for t in tasks if t.dependencies
            )},
        ]

        issues = []
        for check in checks:
            if not check["passed"]:
                issues.append(f"Failed: {check['check']}")

        is_valid = all(c["passed"] for c in checks)

        return ValidationChecklist(checks=checks, is_valid=is_valid, issues=issues)


__all__ = [
    "StructuredPlanner",
    "PlanningPhase",
    "PlanningOutput",
    "ProblemUnderstanding",
    "Requirements",
    "ArchitectureSpec",
    "TechnologyChoices",
    "ExecutableTask",
    "RiskAnalysis",
    "ValidationChecklist",
]
