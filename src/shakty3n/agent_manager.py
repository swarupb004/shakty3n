"""
Agent Manager and IDE-style workspace utilities.

Provides:
- AgentManager: spawns and coordinates multiple autonomous executors
- AgentWorkspace: lightweight IDE surface (editor, terminal, browser stubs)
- AgentSession: runtime metadata, artifacts, and approval tracking
"""
from __future__ import annotations

import asyncio
import json
import os
import shlex
import shutil
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
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

    def __init__(self, root_dir: str, allowed_commands: Optional[Sequence[str]] = None):
        self.root_dir = root_dir
        self.artifacts: List[Artifact] = []
        self.events: List[Dict[str, Any]] = []
        self.approvals: List[HumanApproval] = []
        self.allowed_commands = set(
            allowed_commands
            or ["echo", "python", "python3", "pip", "pip3", "pytest", "npm", "yarn", "pnpm", "ls", "pwd", "git"]
        )
        os.makedirs(root_dir, exist_ok=True)

    def _record_event(self, kind: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        event = {
            "kind": kind,
            "message": message,
            "extra": extra or {},
            "timestamp": time.time(),
        }
        self.events.append(event)

    def _resolve_path(self, relative_path: str) -> str:
        """Resolve and validate that a path stays inside the workspace root."""
        root = Path(self.root_dir).resolve()
        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            raise ValueError("Path escapes workspace root")
        return str(candidate)

    def open_file(self, relative_path: str) -> str:
        """Simulate editor read access."""
        full_path = self._resolve_path(relative_path)
        with open(full_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        self._record_event("editor_read", f"Opened {relative_path}")
        return content

    def save_file(self, relative_path: str, content: str) -> str:
        """Simulate editor write access."""
        full_path = self._resolve_path(relative_path)
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

        if not cmd:
            raise ValueError("Command must not be empty")

        executable = cmd[0]
        if os.sep in executable or (os.altsep and os.altsep in executable):
            raise ValueError("Executable path must not contain directory separators")

        resolved_executable = shutil.which(executable)
        if not resolved_executable:
            raise ValueError(f"Command '{executable}' not found on PATH")

        executable_name = os.path.basename(resolved_executable)
        if executable_name not in self.allowed_commands:
            raise ValueError(f"Command '{executable}' not permitted in workspace terminal")

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
        screenshots_dir = self._resolve_path(os.path.join("artifacts", "screenshots"))
        os.makedirs(screenshots_dir, exist_ok=True)
        path = self._resolve_path(os.path.join("artifacts", "screenshots", f"{name}.txt"))
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
        name: Optional[str] = None,
        provider_name: str = "openai",
        model: Optional[str] = None,
        ai_provider: Optional[AIProvider] = None,
        output_dir: Optional[str] = None,
        agent_id: Optional[str] = None,  # Allow custom ID for persistence
    ) -> AgentSession:
        """Create a new agent with its own workspace and executor."""
        agent_id = agent_id or str(uuid.uuid4())
        agent_dir_name = name if name else agent_id
        agent_output_dir = output_dir or os.path.join(self.base_output_dir, agent_dir_name)

        provider = ai_provider or AIProviderFactory.create_provider(provider_name, model=model)
        executor = AutonomousExecutor(provider, output_dir=agent_output_dir)
        workspace = AgentWorkspace(agent_output_dir)

        session = AgentSession(
            id=agent_id,
            name=name or agent_dir_name,
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

        loop = asyncio.get_running_loop()
        
        # Helper to bridge log events to workspace
        def on_log(msg: str):
             # Record as a terminal event so it shows up in UI
             # We use loop.call_soon_threadsafe because this runs in a thread
             loop.call_soon_threadsafe(
                 agent.workspace._record_event, "terminal", msg
             )
        
        result = await loop.run_in_executor(
            None,
            lambda: agent.executor.execute_project(
                description=description,
                project_type=project_type,
                requirements=requirements or {},
                generate_tests=generate_tests,
                validate_code=validate_code,
                on_log=on_log
            ),
        )

        agent.status = "completed" if result.get("success") else "failed"
        agent.last_result = result
        plan_rel_path = os.path.join("artifacts", "plans", f"{agent.id}.json")
        plan_path = agent.workspace._resolve_path(plan_rel_path)
        os.makedirs(os.path.dirname(plan_path), exist_ok=True)
        with open(plan_path, "w", encoding="utf-8") as handle:
            json.dump(result.get("plan", []), handle, indent=2)
        agent.workspace.add_artifact("plan", plan_path, {"plan": result.get("plan", [])})

        observability = result.get("observability")
        if observability:
            obs_rel_path = os.path.join("artifacts", "observability", f"{agent.id}.json")
            obs_path = agent.workspace._resolve_path(obs_rel_path)
            os.makedirs(os.path.dirname(obs_path), exist_ok=True)
            with open(obs_path, "w", encoding="utf-8") as handle:
                json.dump(observability, handle, indent=2)
            agent.workspace.add_artifact(
                "observability",
                obs_path,
                {"confidence": observability.get("confidence"), "timeline": observability.get("timeline", [])},
            )

        security = result.get("security")
        if security:
            sec_rel_path = os.path.join("artifacts", "security", f"{agent.id}.json")
            sec_path = agent.workspace._resolve_path(sec_rel_path)
            os.makedirs(os.path.dirname(sec_path), exist_ok=True)
            with open(sec_path, "w", encoding="utf-8") as handle:
                json.dump(security, handle, indent=2)
            agent.workspace.add_artifact("security", sec_path, security)

        generation = result.get("generation", {})
        if generation.get("output_dir"):
            agent.workspace.add_artifact("code", generation["output_dir"], generation)

        validation = result.get("validation")
        if validation:
            artifact_type = "test_results" if validation.get("passed") else "validation"
            agent.workspace.add_artifact(
                artifact_type, generation.get("output_dir", agent.executor.output_dir), validation
            )

        # Human-in-the-loop gate for risky runs
        confidence = result.get("confidence", 100)
        if confidence < 60 or (security and (security.get("issues") or security.get("secrets"))):
            summary = "Approval required: low confidence or security findings"
            changes = {"confidence": confidence, "security": security}
            agent.workspace.request_approval(summary, changes)

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
                    "artifacts": [asdict(artifact) for artifact in session.workspace.artifacts],
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
