"""
Agent Manager and IDE-style workspace utilities.

Provides:
- AgentManager: spawns and coordinates multiple autonomous executors
- AgentWorkspace: lightweight IDE surface (editor, terminal, browser stubs)
- AgentSession: runtime metadata, artifacts, and approval tracking
"""
from __future__ import annotations

import asyncio
import os
import shlex
import subprocess
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Union

from .ai_providers import AIProviderFactory
from .ai_providers.base import AIProvider
from .executor import AutonomousExecutor


@dataclass
class Artifact:
    """Verifiable artifact emitted by an agent."""

    type: str
    uri: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


@dataclass
class HumanApproval:
    """Tracks human-in-the-loop approvals."""

    id: str
    summary: str
    changes: Dict[str, Any]
    approved: Optional[bool] = None
    created_at: float = field(default_factory=time.time)
    approved_at: Optional[float] = None

    def approve(self, approved: bool = True) -> None:
        self.approved = approved
        self.approved_at = time.time()


class AgentWorkspace:
    """Lightweight IDE experience (editor, terminal, filesystem, browser stubs)."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.artifacts: List[Artifact] = []
        self.events: List[Dict[str, Any]] = []
        self.approvals: List[HumanApproval] = []
        os.makedirs(root_dir, exist_ok=True)

    def _record_event(self, kind: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        event = {
            "kind": kind,
            "message": message,
            "extra": extra or {},
            "timestamp": time.time(),
        }
        self.events.append(event)

    def open_file(self, relative_path: str) -> str:
        """Simulate editor read access."""
        full_path = os.path.join(self.root_dir, relative_path)
        with open(full_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        self._record_event("editor_read", f"Opened {relative_path}")
        return content

    def save_file(self, relative_path: str, content: str) -> str:
        """Simulate editor write access."""
        full_path = os.path.join(self.root_dir, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        self._record_event("editor_write", f"Saved {relative_path}")
        return full_path

    def run_terminal_command(
        self, command: Union[str, Sequence[str]], cwd: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """Run a terminal command and capture output."""
        if isinstance(command, str):
            cmd = shlex.split(command)
        else:
            cmd = list(command)

        result = subprocess.run(
            cmd,
            cwd=cwd or self.root_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        self._record_event(
            "terminal",
            " ".join(cmd),
            {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr},
        )
        return result

    def open_url(self, url: str) -> None:
        """Browser stub that records navigation."""
        self._record_event("browser", f"Visited {url}")

    def add_artifact(self, artifact_type: str, uri: str, metadata: Optional[Dict[str, Any]] = None) -> Artifact:
        artifact = Artifact(type=artifact_type, uri=uri, metadata=metadata or {})
        self.artifacts.append(artifact)
        return artifact

    def capture_screenshot(self, name: str, content: str = "Screenshot placeholder") -> Artifact:
        screenshots_dir = os.path.join(self.root_dir, "artifacts", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        path = os.path.join(screenshots_dir, f"{name}.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        self._record_event("screenshot", f"Captured {name}", {"path": path})
        return self.add_artifact("screenshot", path, {"label": name})

    def request_approval(self, summary: str, changes: Dict[str, Any]) -> HumanApproval:
        approval = HumanApproval(id=str(uuid.uuid4()), summary=summary, changes=changes)
        self.approvals.append(approval)
        self._record_event("approval_requested", summary, {"approval_id": approval.id})
        return approval

    def approve(self, approval_id: str, approved: bool = True) -> HumanApproval:
        for approval in self.approvals:
            if approval.id == approval_id:
                approval.approve(approved)
                self._record_event("approval_updated", approval_id, {"approved": approved})
                return approval
        raise ValueError(f"Approval with id {approval_id} not found")

    def snapshot(self) -> Dict[str, Any]:
        """Return a dashboard-friendly snapshot of workspace state."""
        return {
            "artifact_count": len(self.artifacts),
            "approval_count": len(self.approvals),
            "events": self.events[-10:],
        }


@dataclass
class AgentSession:
    """A running agent and its resources."""

    id: str
    name: str
    executor: AutonomousExecutor
    workspace: AgentWorkspace
    provider_name: str
    model: Optional[str] = None
    status: str = "idle"
    last_result: Optional[Dict[str, Any]] = None

    def record_artifact(self, artifact_type: str, uri: str, metadata: Optional[Dict[str, Any]] = None) -> Artifact:
        return self.workspace.add_artifact(artifact_type, uri, metadata)

    def request_approval(self, summary: str, changes: Dict[str, Any]) -> HumanApproval:
        return self.workspace.request_approval(summary, changes)


class AgentManager:
    """Coordinate multiple autonomous agents with observability and artifacts."""

    def __init__(self, base_output_dir: str = "./generated_projects"):
        self.base_output_dir = base_output_dir
        self.agents: Dict[str, AgentSession] = {}
        os.makedirs(self.base_output_dir, exist_ok=True)

    def spawn_agent(
        self,
        name: str,
        provider_name: str = "openai",
        model: Optional[str] = None,
        ai_provider: Optional[AIProvider] = None,
        output_dir: Optional[str] = None,
    ) -> AgentSession:
        """Create a new agent with its own workspace and executor."""
        agent_id = str(uuid.uuid4())
        agent_output_dir = output_dir or os.path.join(self.base_output_dir, name or agent_id)

        provider = ai_provider or AIProviderFactory.create_provider(provider_name, model=model)
        executor = AutonomousExecutor(provider, output_dir=agent_output_dir)
        workspace = AgentWorkspace(agent_output_dir)

        session = AgentSession(
            id=agent_id,
            name=name,
            executor=executor,
            workspace=workspace,
            provider_name=provider_name,
            model=model,
        )
        self.agents[agent_id] = session
        return session

    async def run_workflow(
        self,
        agent: AgentSession,
        description: str,
        project_type: str,
        requirements: Optional[Dict[str, Any]] = None,
        generate_tests: bool = False,
        validate_code: bool = False,
    ) -> Dict[str, Any]:
        """Plan, execute, and verify a workflow asynchronously."""
        agent.status = "running"
        agent.workspace._record_event("workflow_started", description, {"project_type": project_type})

        result = await asyncio.to_thread(
            agent.executor.execute_project,
            description,
            project_type,
            requirements or {},
            generate_tests,
            validate_code,
        )

        agent.status = "completed" if result.get("success") else "failed"
        agent.last_result = result
        agent.record_artifact("plan", "plan.json", {"plan": result.get("plan", [])})

        generation = result.get("generation", {})
        if generation.get("output_dir"):
            agent.record_artifact("code", generation["output_dir"], generation)

        validation = result.get("validation")
        if validation:
            artifact_type = "test_results" if validation.get("passed") else "validation"
            agent.record_artifact(artifact_type, generation.get("output_dir", agent.executor.output_dir), validation)

        agent.workspace._record_event("workflow_finished", agent.status, {"progress": result.get("progress", {})})
        return result

    async def run_parallel(self, runs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple agent workflows concurrently."""
        tasks = []
        for run in runs:
            agent = run["agent"]
            tasks.append(
                self.run_workflow(
                    agent=agent,
                    description=run["description"],
                    project_type=run["project_type"],
                    requirements=run.get("requirements"),
                    generate_tests=run.get("generate_tests", False),
                    validate_code=run.get("validate_code", False),
                )
            )
        return await asyncio.gather(*tasks)

    def get_dashboard_snapshot(self) -> Dict[str, Any]:
        """Aggregate agent state for a dashboard view."""
        agents_snapshot: List[Dict[str, Any]] = []
        for session in self.agents.values():
            agents_snapshot.append(
                {
                    "id": session.id,
                    "name": session.name,
                    "status": session.status,
                    "provider": session.provider_name,
                    "model": session.model,
                    "artifacts": [artifact.to_dict() for artifact in session.workspace.artifacts],
                    "approvals": [
                        {
                            "id": approval.id,
                            "summary": approval.summary,
                            "approved": approval.approved,
                            "approved_at": approval.approved_at,
                        }
                        for approval in session.workspace.approvals
                    ],
                    "workspace": session.workspace.snapshot(),
                }
            )

        return {
            "agent_count": len(self.agents),
            "agents": agents_snapshot,
            "timestamp": time.time(),
        }
