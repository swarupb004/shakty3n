#!/usr/bin/env python3
"""
Agent manager and workspace tests.
"""
import asyncio
import os
import pytest
from typing import Any, Generator, List, Optional

from shakty3n.agent_manager import AgentManager, AgentWorkspace
from shakty3n.ai_providers.base import AIProvider


class MockAIProvider(AIProvider):
    """Deterministic provider used for offline tests."""

    def generate(
        self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4000
    ) -> str:
        if "package.json" in prompt:
            return '{"name":"demo-app","version":"1.0.0","scripts":{"start":"echo start"},"dependencies":{}}'
        if "Create a detailed development plan" in prompt or "development plan" in prompt:
            return '{"tasks":[{"title":"Plan","description":"Plan work","dependencies":[]},{"title":"Build","description":"Implement","dependencies":[0]}]}'
        if "React component" in prompt:
            return "import React from 'react';\nexport default function App(){return <div>App</div>;}"
        if "Execute the following task" in prompt:
            return "Task executed successfully."
        return "Mock response"

    def stream_generate(
        self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4000
    ) -> Generator[str, None, None]:
        yield self.generate(prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens)

    def get_available_models(self) -> List[str]:
        return ["mock-model"]


def test_workspace_supports_editor_terminal_browser(tmp_path):
    workspace = AgentWorkspace(str(tmp_path))

    workspace.save_file("notes/demo.txt", "hello world")
    assert "hello world" in workspace.open_file("notes/demo.txt")

    result = workspace.run_terminal_command(["echo", "ready"], cwd=str(tmp_path))
    assert "ready" in (result.stdout or "")

    workspace.open_url("https://example.com")
    screenshot = workspace.capture_screenshot("demo")
    assert os.path.exists(screenshot.uri)

    approval = workspace.request_approval("Review change", {"files": ["notes/demo.txt"]})
    workspace.approve(approval.id)

    snapshot = workspace.snapshot()
    assert snapshot["artifact_count"] >= 1
    assert snapshot["approval_count"] == 1


def test_agent_manager_runs_parallel_workflows(tmp_path):
    provider = MockAIProvider()
    manager = AgentManager(base_output_dir=str(tmp_path))

    agent = manager.spawn_agent(
        "agent-a",
        provider_name="mock",
        model="mock-model",
        ai_provider=provider,
        output_dir=str(tmp_path / "agent-a"),
    )

    results = asyncio.run(
        manager.run_parallel(
            [
                {
                    "agent": agent,
                    "description": "Demo web app",
                    "project_type": "web-react",
                    "requirements": {"features": ["dashboard"]},
                    "generate_tests": False,
                    "validate_code": False,
                }
            ]
        )
    )

    assert results[0]["success"]

    dashboard = manager.get_dashboard_snapshot()
    assert dashboard["agent_count"] == 1
    artifacts = dashboard["agents"][0]["artifacts"]
    assert any(item["type"] == "plan" for item in artifacts)
    assert any(item["type"] == "code" for item in artifacts)
