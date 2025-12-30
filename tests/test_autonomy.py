import json
from pathlib import Path

from shakty3n.autonomy import (
    AutonomyMemory,
    CICDOrchestrator,
    CollaborativeOrchestrator,
    ExecutionObserver,
    IntentAnalyzer,
    IntentSpec,
    SecurityGuard,
)


def test_intent_analysis_and_memory(tmp_path):
    analyzer = IntentAnalyzer(ai_provider=None)
    intent = analyzer.analyze("Build a secure todo app", {"auth": "required", "persistence": "sqlite"})

    assert isinstance(intent, IntentSpec)
    assert any("auth" in criterion for criterion in intent.success_criteria)
    assert intent.definition_of_done

    memory = AutonomyMemory(tmp_path / "memory.json")
    memory.remember_decision("Drafted plan", {"tasks": 3})
    memory.remember_bug("Sample bug", "Fixed")
    memory.reflect("Ensure idempotent writes")

    snapshot = memory.snapshot()
    assert snapshot["decisions"]
    assert snapshot["bugs"]
    assert snapshot["reflections"]
    assert (tmp_path / "memory.json").exists()


def test_security_guard_detects_secrets(tmp_path):
    secret_file = tmp_path / "config.txt"
    secret_file.write_text("API_KEY=ABCDEFGHIJKLMNOPQRSTUVWXYZ", encoding="utf-8")

    guard = SecurityGuard()
    report = guard.check_workspace(str(tmp_path))

    assert report["scanned_files"] >= 1
    assert report["secrets"], "Expected secret pattern to be detected"


def test_execution_observer_confidence():
    observer = ExecutionObserver()
    observer.start("planning")
    observer.finish("planning")

    progress = {"percentage": 80}
    validation = {"passed": True}
    security = {"issues": [], "secrets": []}

    snapshot = observer.snapshot(progress, validation, security)
    assert snapshot["confidence"] <= 100
    assert snapshot["timeline"], "Timeline should capture recorded events"


def test_collaboration_and_cicd_plan(tmp_path):
    intent = IntentAnalyzer(None).analyze("Deploy a web dashboard", {})

    collaborator = CollaborativeOrchestrator()
    team = collaborator.build_team(intent)
    assert len(team) >= 5

    cicd = CICDOrchestrator()
    plan = cicd.generate_plan("web-react", str(tmp_path))
    assert plan["steps"]
    pipeline_file = Path(tmp_path) / "artifacts" / "pipeline.plan.json"
    assert pipeline_file.exists()
    pipeline_payload = json.loads(pipeline_file.read_text(encoding="utf-8"))
    assert pipeline_payload["name"] == "autonomy-pipeline"
