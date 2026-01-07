"""
Planning Prompts for Structured Planner

Fixed system prompts and templates for each planning phase.
These prompts are designed to work well with local LLMs like
Qwen Coder and DeepSeek Coder.
"""

# Main system prompt for the planner
PLANNER_SYSTEM_PROMPT = """You are a senior software architect acting as a planning agent.
Your task is to convert a development request into a detailed, step-by-step development plan.

Rules:
- Do NOT write code
- Clarify assumptions
- Break down requirements
- Produce an executable task list
- Highlight risks and dependencies
- Use clear structured sections
- Always respond in valid JSON format when asked

You are helping plan code for an autonomous coding agent that will execute your plan.
Be specific and actionable - avoid vague tasks like "Development" or "Testing".
Instead, use specific tasks like "Initialize Node.js project", "Create src/index.js"."""


# Phase 1: Prompt Understanding & Expansion
PROMPT_UNDERSTANDING_TEMPLATE = """Analyze this development request and extract a structured understanding.

## User Request
{description}

## Explicit Requirements
{requirements}

## Your Task
Convert this into a detailed problem statement. Identify:
1. Primary goal - the main objective
2. Secondary goals - additional features or nice-to-haves
3. Implicit requirements - things not stated but expected
4. Assumptions - what you're assuming about the project
5. Unknowns - things that need clarification

Respond in JSON format:
```json
{{
  "primary_goal": "Clear statement of the main objective",
  "secondary_goals": ["goal1", "goal2"],
  "implicit_requirements": ["req1", "req2"],
  "assumptions": ["assumption1", "assumption2"],
  "unknowns": ["unknown1", "unknown2"]
}}
```"""


# Phase 2: Requirements Decomposition
REQUIREMENTS_TEMPLATE = """Break down these goals into atomic requirements.

## Primary Goal
{primary_goal}

## Secondary Goals
{secondary_goals}

## Implicit Requirements Already Identified
{implicit_requirements}

## Project Type
{project_type}

## Your Task
Create a complete list of functional and non-functional requirements.

Functional requirements describe WHAT the system does.
Non-functional requirements describe HOW it does it (performance, security, etc.).

Respond in JSON format:
```json
{{
  "functional": [
    "User can register with email and password",
    "User can login with credentials",
    "System stores user sessions"
  ],
  "non_functional": [
    "Passwords must be hashed before storage",
    "API responses under 200ms",
    "Support 100 concurrent users"
  ]
}}
```"""


# Phase 3: System Design & Architecture
ARCHITECTURE_TEMPLATE = """Design the system architecture for this project.

## Primary Goal
{primary_goal}

## Functional Requirements
{functional_requirements}

## Non-Functional Requirements
{non_functional_requirements}

## Project Type
{project_type}

## Your Task
Define the high-level architecture:
1. Components - major parts of the system
2. Data flow - how data moves through the system
3. Patterns - design patterns to use

Respond in JSON format:
```json
{{
  "components": [
    {{"name": "API Layer", "responsibility": "Handle HTTP requests and routing"}},
    {{"name": "Auth Service", "responsibility": "User authentication and session management"}},
    {{"name": "Database Layer", "responsibility": "Data persistence and queries"}}
  ],
  "data_flow": "Client → API → Service → Database → Response",
  "patterns": ["MVC", "Repository Pattern", "Middleware"]
}}
```"""


# Phase 4: Technology & Tool Selection
TECHNOLOGY_TEMPLATE = """Select appropriate technologies for this project.

## Project Type
{project_type}

## Architecture Components
{components}

## Environment Context
{environment}

## Your Task
Lock in technology choices. Be specific about versions when relevant.

Respond in JSON format:
```json
{{
  "language": "Python",
  "framework": "FastAPI",
  "database": "SQLite",
  "testing": "pytest",
  "additional_tools": ["bcrypt", "PyJWT", "uvicorn"]
}}
```"""


# Phase 5: Task Breakdown (Executable Plan)
TASK_BREAKDOWN_TEMPLATE = """Create an ordered list of executable tasks.

## Primary Goal
{primary_goal}

## Functional Requirements
{functional_requirements}

## Architecture Components
{components}

## Technology Choices
{technology}

## Your Task
Break this down into specific, ordered, testable tasks that an autonomous coding agent can execute.

Rules:
- Tasks must be ordered (dependencies resolved)
- Each task must be atomic (one clear action)
- Each task must be testable (verifiable outcome)
- Use 5-12 tasks depending on complexity

Respond in JSON format:
```json
{{
  "tasks": [
    {{
      "title": "Initialize project structure",
      "description": "Create folder structure and package.json/requirements.txt",
      "dependencies": [],
      "testable_outcome": "Project directory with config files exists"
    }},
    {{
      "title": "Create main application entry",
      "description": "Create src/main.py with FastAPI app initialization",
      "dependencies": [1],
      "testable_outcome": "python src/main.py runs without errors"
    }}
  ]
}}
```"""


# Phase 6: Risk Analysis
RISK_ANALYSIS_TEMPLATE = """Analyze risks and complexity for this project.

## Primary Goal
{primary_goal}

## Unknowns Identified
{unknowns}

## Task Count
{task_count}

## Requirements Count
{requirements_count}

## Your Task
Identify potential risks and mitigation strategies.

Respond in JSON format:
```json
{{
  "risks": [
    {{"risk": "Ambiguous requirements", "mitigation": "Clarify with user before execution"}},
    {{"risk": "Third-party API changes", "mitigation": "Use versioned API endpoints"}},
    {{"risk": "Missing error handling", "mitigation": "Add comprehensive try/catch blocks"}}
  ],
  "complexity_score": 6
}}
```

Complexity score is 1-10 where:
- 1-3: Simple project, few moving parts
- 4-6: Medium complexity, some integration needed
- 7-10: Complex project, many components and risks"""


# Phase 7: Validation Checklist
VALIDATION_TEMPLATE = """Validate the completeness of this development plan.

## Problem Understanding
Primary Goal: {primary_goal}

## Requirements
Functional Count: {functional_count}
Non-Functional Count: {non_functional_count}

## Architecture
Components: {component_count}
Data Flow Defined: {has_data_flow}

## Technology
Language: {language}
Framework: {framework}

## Tasks
Task Count: {task_count}

## Risks
Risk Count: {risk_count}

## Your Task
Verify the plan is complete and ready for execution.

Respond in JSON format:
```json
{{
  "checks": [
    {{"check": "Primary goal is clear", "passed": true}},
    {{"check": "All requirements are testable", "passed": true}},
    {{"check": "Tasks cover all requirements", "passed": true}},
    {{"check": "Dependencies are acyclic", "passed": true}}
  ],
  "is_valid": true,
  "issues": []
}}
```"""


__all__ = [
    "PLANNER_SYSTEM_PROMPT",
    "PROMPT_UNDERSTANDING_TEMPLATE",
    "REQUIREMENTS_TEMPLATE",
    "ARCHITECTURE_TEMPLATE",
    "TECHNOLOGY_TEMPLATE",
    "TASK_BREAKDOWN_TEMPLATE",
    "RISK_ANALYSIS_TEMPLATE",
    "VALIDATION_TEMPLATE",
]
