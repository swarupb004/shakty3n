"""
Autonomy orchestration utilities.

Provides intent analysis, long-term memory, observability, security
guardrails, CI/CD planning, and collaboration helpers to make the agent
production-ready without forcing breaking changes on existing flows.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

RESPONSE_TRUNCATION_LIMIT = 160
DEFAULT_MEMORY_STATE = {"decisions": [], "bugs": [], "preferences": {}, "reflections": []}
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*=\s*[A-Za-z0-9_\-]{12,}", re.IGNORECASE),
    re.compile(r"secret\s*=\s*[A-Za-z0-9_\-]{12,}", re.IGNORECASE),
]


def _fresh_memory_state() -> Dict[str, Any]:
    return {
        key: ([] if isinstance(value, list) else {} if isinstance(value, dict) else value)
        for key, value in DEFAULT_MEMORY_STATE.items()
    }


def _truncate_at_word(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    truncated = text[:limit].rsplit(" ", 1)[0]
    return truncated if truncated else text[:limit]


# ---------- Intent & Architecture ----------

@dataclass
class IntentSpec:
    """Structured understanding of user intent and success criteria."""

    description: str
    requirements: Dict[str, Any] = field(default_factory=dict)
    success_criteria: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    definition_of_done: str = ""


class IntentAnalyzer:
    """Deterministic intent analysis with optional AI refinement."""

    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    def analyze(self, description: str, requirements: Optional[Dict[str, Any]] = None) -> IntentSpec:
        requirements = requirements or {}
        success_criteria = []

        # Convert explicit requirements into verifiable criteria
        for key, value in requirements.items():
            success_criteria.append(f"{key} ⇒ {value}")

        if not success_criteria:
            # Provide guard-railed defaults
            success_criteria = [
                "Implements requested features end-to-end",
                "Includes runnable instructions or scripts",
                "Passes generated or existing automated tests",
                "No critical lint or security violations",
            ]

        risks = [
            "Ambiguous requirements",
            "Third-party dependency instability",
            "Missing credentials for external services",
        ]

        definition_of_done = (
            "All success criteria validated, automated tests passing, and security checks clean."
        )

        # Optional AI refinement is wrapped so failures do not block autonomy
        if self.ai_provider:
            try:
                response = self.ai_provider.generate(
                    prompt=f"Summarize intent and refine success criteria for: {description}",
                    temperature=0.2,
                )
                if isinstance(response, str) and response.strip():
                    success_criteria.append(_truncate_at_word(response.strip(), RESPONSE_TRUNCATION_LIMIT))
            except Exception:
                # Safe fallback – never block execution on provider errors
                pass

        return IntentSpec(
            description=description,
            requirements=requirements,
            success_criteria=success_criteria,
            risks=risks,
            definition_of_done=definition_of_done,
        )


@dataclass
class ArchitectureBlueprint:
    """Lightweight architecture guidance for downstream generators."""

    layers: List[str]
    patterns: List[str]
    data_flow: str
    decisions: List[str] = field(default_factory=list)


class ArchitectureDesigner:
    """Provides deterministic architecture scaffolds per project type."""

    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    def design(self, intent: IntentSpec, project_type: str) -> ArchitectureBlueprint:
        layers = ["presentation", "application", "domain", "infrastructure"]
        patterns = ["12-factor configs", "logging middleware", "health checks"]
        data_flow = "client → controller → service → persistence → telemetry"
        decisions = [f"Project type: {project_type}", f"Definition of done: {intent.definition_of_done}"]

        if "web" in project_type:
            decisions.append("Use SPA router + state store for predictable flows")
        if "api" in project_type or "backend" in project_type:
            decisions.append("Expose OpenAPI/Swagger for contract testing")

        return ArchitectureBlueprint(layers=layers, patterns=patterns, data_flow=data_flow, decisions=decisions)


# ---------- Long-term Memory ----------

class AutonomyMemory:
    """File-backed memory for preferences, decisions, and bug history."""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.state: Dict[str, Any] = _fresh_memory_state()
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                self.state.update(json.loads(self.storage_path.read_text(encoding="utf-8")))
            except Exception:
                # Corrupt memory should not block execution; reinitialize.
                self.state = _fresh_memory_state()

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def remember_decision(self, summary: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        entry = {"summary": summary, "metadata": metadata or {}, "timestamp": time.time()}
        self.state.setdefault("decisions", []).append(entry)
        self._save()

    def remember_bug(self, description: str, resolution: Optional[str] = None) -> None:
        entry = {"description": description, "resolution": resolution, "timestamp": time.time()}
        self.state.setdefault("bugs", []).append(entry)
        self._save()

    def set_preference(self, key: str, value: Any) -> None:
        self.state.setdefault("preferences", {})[key] = value
        self._save()

    def reflect(self, note: str) -> None:
        self.state.setdefault("reflections", []).append({"note": note, "timestamp": time.time()})
        self._save()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "decisions": self.state.get("decisions", [])[-5:],
            "bugs": self.state.get("bugs", [])[-5:],
            "preferences": self.state.get("preferences", {}),
            "reflections": self.state.get("reflections", [])[-5:],
        }


# ---------- Observability ----------

class ExecutionObserver:
    """Captures execution timeline and computes a confidence score."""

    def __init__(self):
        self.timeline: List[Dict[str, Any]] = []

    def record(self, phase: str, status: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self.timeline.append(
            {
                "phase": phase,
                "status": status,
                "meta": meta or {},
                "timestamp": time.time(),
            }
        )

    def start(self, phase: str) -> None:
        self.record(phase, "started")

    def finish(self, phase: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self.record(phase, "completed", meta)

    def confidence_score(
        self, progress: Dict[str, Any], validation: Optional[Dict[str, Any]], security: Optional[Dict[str, Any]]
    ) -> int:
        score = 40
        score += int(progress.get("percentage", 0) * 0.4)

        if validation:
            if validation.get("passed"):
                score += 15
            else:
                score -= 10

        if security:
            issues = len(security.get("issues", [])) + len(security.get("secrets", []))
            score -= min(issues * 5, 20)

        return max(0, min(100, score))

    def snapshot(self, progress: Dict[str, Any], validation: Optional[Dict[str, Any]], security: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "timeline": self.timeline[-25:],
            "progress": progress,
            "validation": validation,
            "security": security,
            "confidence": self.confidence_score(progress, validation, security),
        }


# ---------- Security & Compliance ----------

class SecurityGuard:
    """Static security checks for secrets, risky files, and dependency hints."""

    def __init__(self, max_files: int = 200):
        self.max_files = max_files
        self.patterns: Sequence[re.Pattern] = SECRET_PATTERNS

    def check_workspace(self, root_dir: str) -> Dict[str, Any]:
        issues: List[str] = []
        secrets: List[str] = []
        scanned = 0

        for base, _, files in os.walk(root_dir):
            if scanned >= self.max_files:
                break
            for name in files:
                if scanned >= self.max_files:
                    break
                scanned += 1
                path = Path(base) / name
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                for pattern in self.patterns:
                    for _ in pattern.finditer(content):
                        secrets.append(f"{path}: secret-like value detected")

                if name.endswith((".pem", ".p12", ".key")):
                    issues.append(f"Key material present: {path}")

        if scanned >= self.max_files:
            issues.append(f"Scan truncated for performance (limit: {self.max_files} files).")

        return {"issues": issues, "secrets": secrets, "scanned_files": scanned}


# ---------- Collaboration & Delivery ----------

class CollaborativeOrchestrator:
    """Defines role-based collaboration plans without spawning heavy agents."""

    def build_team(self, intent: IntentSpec) -> List[Dict[str, Any]]:
        base_roles = [
            ("architect", "Shape architecture and non-functional requirements."),
            ("backend", "Implement services and APIs."),
            ("frontend", "Deliver UX flows and state."),
            ("qa", "Author tests and validation gates."),
            ("security", "Run threat modelling and secret scans."),
            ("devops", "Automate CI/CD and observability hooks."),
        ]
        return [
            {"role": role, "responsibility": resp, "focus": intent.description}
            for role, resp in base_roles
        ]


class CICDOrchestrator:
    """Generates deterministic CI/CD scaffolds and delivery steps."""

    def generate_plan(self, project_type: str, output_dir: str) -> Dict[str, Any]:
        steps = [
            "lint",
            "unit_tests",
            "security_scan",
            "package_artifacts",
        ]
        if "web" in project_type or "frontend" in project_type:
            steps.append("build_static_assets")

        pipeline = {
            "name": "autonomy-pipeline",
            "on": ["push"],
            "steps": steps,
        }

        artifacts_dir = Path(output_dir) / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / "pipeline.plan.json").write_text(json.dumps(pipeline, indent=2), encoding="utf-8")
        return pipeline


__all__ = [
    "IntentSpec",
    "IntentAnalyzer",
    "ArchitectureBlueprint",
    "ArchitectureDesigner",
    "AutonomyMemory",
    "ExecutionObserver",
    "SecurityGuard",
    "CollaborativeOrchestrator",
    "CICDOrchestrator",
]
