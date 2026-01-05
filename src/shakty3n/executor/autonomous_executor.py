"""
Autonomous Execution Engine
"""
from typing import Dict, Optional
import ast
import json
import os
import time
from pathlib import Path
from ..planner import TaskPlanner, TaskStatus
from ..generators import (
    WebAppGenerator, AndroidAppGenerator, 
    IOSAppGenerator, DesktopAppGenerator, FlutterAppGenerator,
    StaticHTMLGenerator
)
from ..debugger import AutoDebugger
from ..autonomy import (
    IntentAnalyzer,
    AutonomyMemory,
    ExecutionObserver,
    SecurityGuard,
    ArchitectureDesigner,
    CollaborativeOrchestrator,
    CICDOrchestrator,
)


# Keywords that indicate a simple static HTML request
SIMPLE_REQUEST_KEYWORDS = [
    "html page", "html5 page", "static page", "simple page", "single page",
    "hello world", "landing page", "basic page", "plain html", "just html",
    "one file", "single file", "minimal"
]

# Keywords that indicate a complex framework request
COMPLEX_REQUEST_KEYWORDS = [
    "react", "vue", "angular", "svelte", "next", "dashboard", "app",
    "application", "spa", "component", "redux", "state management",
    "authentication", "api", "backend", "database", "crud"
]


def _is_simple_request(description: str, project_type: str) -> bool:
    """Detect if this is a simple request that doesn't need a full framework"""
    desc_lower = description.lower()
    type_lower = project_type.lower()
    
    # Check for complex keywords first (they take priority)
    for kw in COMPLEX_REQUEST_KEYWORDS:
        if kw in desc_lower or kw in type_lower:
            return False
    
    # Check for simple keywords
    for kw in SIMPLE_REQUEST_KEYWORDS:
        if kw in desc_lower or kw in type_lower:
            return True
    
    # If project type explicitly mentions html/static
    if "html" in type_lower or "static" in type_lower:
        return True
    
    return False


class AutonomousExecutor:
    """Autonomous execution engine using ReAct loop"""
    
    def __init__(self, ai_provider, output_dir: str = "./generated_projects"):
        self.ai_provider = ai_provider
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.artifacts_dir = os.path.join(self.output_dir, "artifacts")
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self.state_file = os.path.join(self.artifacts_dir, "plan_state.json")
        self.planner = TaskPlanner(ai_provider)
        self.debugger = AutoDebugger(ai_provider)
        self.on_log = None
        self.intent_analyzer = IntentAnalyzer(ai_provider)
        self.memory = AutonomyMemory(os.path.join(self.artifacts_dir, "memory.json"))
        self.observer = ExecutionObserver()
        self.security_guard = SecurityGuard()
        self.architect = ArchitectureDesigner(ai_provider)
        self.collaborator = CollaborativeOrchestrator()
        self.cicd = CICDOrchestrator()
        self.retry_counts: Dict[int, int] = {}
        self._interrupt_requested = False
        self._pending_update: Optional[str] = None
        
        # Initialize tools
        from .tools import ToolRegistry
        self.tools = ToolRegistry(self.output_dir)
        
    def _log(self, message: str):
        print(message)
        if self.on_log:
            self.on_log(message)

    def _analyze_intent(self, description: str, requirements: Dict) -> "IntentSpec":
        intent = self.intent_analyzer.analyze(description, requirements)
        self.memory.remember_decision("Intent analyzed", {"success_criteria": intent.success_criteria})
        self.memory.set_preference("project_description", description)
        return intent

    def execute_project(
        self,
        description: str,
        project_type: str,
        requirements: Optional[Dict] = None,
        generate_tests: bool = False,
        validate_code: bool = False,
        on_log=None,
        resume: bool = False,
        updated_instructions: Optional[str] = None,
    ) -> Dict:
        """Execute a project autonomously"""
        self.on_log = on_log
        self._pending_update = updated_instructions
        interrupted = False
        # Clear interrupt flag when resuming
        if resume:
            self._interrupt_requested = False
        
        self._log("\n" + "="*60)
        self._log("ANTIGRAVITY AGENT - Starting Execution")
        self._log("="*60 + "\n")

        self.observer.start("intent_understanding")
        state_payload = self._load_plan_state() if resume else None
        if resume and state_payload:
            description = description or state_payload.get("description")
            project_type = project_type or state_payload.get("project_type")
            requirements = requirements or state_payload.get("requirements", {})
            self.planner.load_plan(state_payload.get("plan", []))
        if updated_instructions:
            self.memory.reflect(f"Instruction update received: {updated_instructions}")
            requirements = requirements or {}
            requirements["instruction_update"] = updated_instructions

        intent = self._analyze_intent(description, requirements or {})
        architecture = self.architect.design(intent, project_type)
        team = self.collaborator.build_team(intent)
        self.intent = intent
        self.architecture = architecture
        self.team = team
        self.observer.finish("intent_understanding", {"success_criteria": len(intent.success_criteria)})
        
        # Phase 1: Planning
        self._log("📋 Phase 1: Planning...")
        self.observer.start("planning")
        try:
            if not resume or not self.planner.tasks:
                tasks = self.planner.create_plan(description, project_type)
                self._persist_plan_state(description, project_type, requirements or {}, tasks)
            else:
                tasks = self.planner.tasks
                self._persist_plan_state(description, project_type, requirements or {}, tasks)
            self._log(f"✓ Plan created with {len(tasks)} tasks")
            self._log(self.planner.get_plan_summary())
            self.memory.remember_decision("Plan created", {"task_count": len(tasks)})
        except Exception as e:
            return self._handle_error("Planning", str(e))
        self.observer.finish("planning", {"tasks": len(tasks)})
        
        # Phase 2: Execution (ReAct Loop)
        self._log("\n⚡ Phase 2: Autonomous Intent Execution...")
        
        # Initialize workspace (Scaffold if needed)
        self._initialize_workspace(project_type)
        
        max_iterations = 50 
        iteration = 0
        
        while not self.planner.is_plan_complete() and iteration < max_iterations:
            if self._interrupt_requested:
                interrupted = True
                self.memory.reflect("Execution interrupted by user")
                if self._pending_update:
                    self.memory.reflect(f"Pending update: {self._pending_update}")
                break

            iteration += 1
            task = self.planner.get_next_task()
            if not task:
                break
            
            self._log(f"\n▶ Executing Task {task.id}: {task.title}")
            self.planner.update_task_status(task.id, TaskStatus.IN_PROGRESS)
            self.observer.record("task", "started", {"task_id": task.id, "title": task.title})
            
            heal = False
            try:
                # ReAct Loop for single task
                success = self._execute_react_task(task, description)
                
                if success:
                    self.planner.update_task_status(task.id, TaskStatus.COMPLETED)
                    self._log(f"✓ Task {task.id} completed")
                    self.memory.remember_decision(f"Task {task.id} completed", {"title": task.title})
                else:
                    heal = self._self_heal_task(task)
                    self.planner.update_task_status(task.id, TaskStatus.FAILED)
                    if heal:
                        self._log(f"⚠ Task {task.id} queued for retry after self-heal suggestions")
                    else:
                        self._log(f"✗ Task {task.id} failed")
                    
            except Exception as e:
                self.planner.update_task_status(task.id, TaskStatus.FAILED, error=str(e))
                self._log(f"✗ Error executing task: {str(e)}")
            
            self._reflect_and_replan(task, allow_retry=heal)
            self.observer.record(
                "task",
                task.status.value,
                {"task_id": task.id, "title": task.title, "status": task.status.value},
            )
            self._persist_plan_state(description, project_type, requirements or {}, self.planner.tasks)
        
        # Phase 3: Finalization
        self._log("\n" + "="*60)
        self._log("EXECUTION COMPLETE")
        self._log("="*60)

        validation_result = None
        if validate_code and not interrupted:
            self.observer.start("validation")
            validation_result = self._validate_code(project_type, self.output_dir, enabled=validate_code)
            self.observer.finish("validation", {"passed": validation_result.get("passed", False)})

        security_result = self._run_security_checks()
        pipeline_plan = self.cicd.generate_plan(project_type, self.output_dir)

        progress = self.planner.get_progress()
        observability = self.observer.snapshot(progress, validation_result, security_result)

        if not interrupted:
            if os.path.exists(self.state_file):
                try:
                    os.remove(self.state_file)
                except FileNotFoundError:
                    pass
                except OSError as err:
                    self._log(f"State cleanup skipped: {err}")
            self._interrupt_requested = False
        
        return {
            "success": self.planner.is_plan_complete() and not interrupted,
            "status": "interrupted" if interrupted else "completed",
            "plan": [task.to_dict() for task in self.planner.tasks],
            "generation": {"output_dir": self.output_dir, "success": True},
            "intent": {
                "description": intent.description,
                "success_criteria": intent.success_criteria,
                "definition_of_done": intent.definition_of_done,
            },
            "architecture": architecture.__dict__,
            "team": team,
            "validation": validation_result,
            "security": security_result,
            "cicd": pipeline_plan,
            "observability": observability,
            "confidence": observability["confidence"],
            "memory": self.memory.snapshot(),
            "progress": progress,
        }

    def _initialize_workspace(self, project_type: str):
        """Setup initial workspace state"""
        js_like = any(
            kw in project_type.lower()
            for kw in ["web", "react", "vue", "angular", "svelte", "next", "electron"]
        )
        if js_like and not os.path.exists(os.path.join(self.output_dir, "package.json")):
            self.tools.run_command("npm init -y")

    def _execute_react_task(self, task, project_context: str) -> bool:
        """Execute a task using ReAct (Reason, Act, Observe) loop"""
        
        history = []
        max_steps = 15
        
        system_prompt = f"""You are an expert autonomous developer.
        
{self.tools.get_tool_definitions()}

Your Goal: Complete the task: "{task.title}"
Description: {task.description}
Context: {project_context}

Follow this cycle:
1. Thought: Plan your next step.
2. Action: Use a tool if needed. e.g. <tool_code>run_command("ls")</tool_code>
3. Observation: I will provide the result.

When you are done, output:
Action: <tool_code>finish()</tool_code>
"""

        for i in range(max_steps):
            # Construct prompt
            prompt = "\n".join(history) + "\nYour turn:\nThought:"
            
            # Generate
            response = self.ai_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                stop=["Observation:"]
            )
            
            # Parse Thought and Action
            # Expected format: "Thought: ... \nAction: <tool_code>...</tool_code>"
            if "Thought:" not in response:
                response = "Thought: " + response
                
            self._log(f"🤖 {response}")
            history.append(response)
            
            # Extract tool usage
            tool_code = self._extract_tool_code(response)
            
            if not tool_code:
                # Agent just thought, didn't act. 
                # If it says "finish", we are done.
                if "finish()" in response or "finished" in response.lower():
                    return True
                continue
                
            if "finish()" in tool_code:
                return True
                
            # Execute tool
            observation = self._execute_tool_code(tool_code)
            self._log(f"👀 Observation: {observation[:200]}..." if len(observation) > 200 else f"👀 Observation: {observation}")
            
            history.append(f"Observation: {observation}")
            
        return False

    def _extract_tool_code(self, text: str) -> Optional[str]:
        """Extract code from within <tool_code> tags"""
        if "<tool_code>" in text and "</tool_code>" in text:
            start = text.find("<tool_code>") + 11
            end = text.find("</tool_code>", start)
            return text[start:end].strip()
        return None

    def _execute_tool_code(self, code: str) -> str:
        """Safe execution of tool code"""
        try:
            # Create a safe local scope
            local_scope = {
                "read_file": self.tools.read_file,
                "write_file": self.tools.write_file,
                "list_dir": self.tools.list_dir,
                "run_command": self.tools.run_command,
                "finish": lambda: "Task Completed"
            }
            
            parsed = ast.parse(code, mode="eval")
            if not isinstance(parsed.body, ast.Call) or not isinstance(parsed.body.func, ast.Name):
                raise ValueError("Tool invocations must be simple function calls like run_command(\"ls\")")

            func_name = parsed.body.func.id
            if func_name not in local_scope:
                raise ValueError(f"Tool '{func_name}' not allowed")

            args = []
            for arg in parsed.body.args:
                if isinstance(arg, ast.Constant):
                    args.append(arg.value)
                else:
                    raise ValueError("Only literal arguments are supported")

            kwargs = {}
            for kw in parsed.body.keywords:
                if not isinstance(kw.value, ast.Constant):
                    raise ValueError("Only literal keyword arguments are supported")
                kwargs[kw.arg] = kw.value.value

            return str(local_scope[func_name](*args, **kwargs))
            
        except Exception as e:
            return f"Tool Execution Error: {str(e)}"

    def _self_heal_task(self, task) -> bool:
        """Attempt auto-debug and self-heal for a failed task."""
        try:
            analysis = self.debugger.analyze_error(
                error_message=f"Task {task.id} failed",
                code_context=task.description,
            )
            self.memory.remember_bug(f"Task {task.id} failure", analysis.get("error_message"))
            # If suggestions exist, we consider the agent to have adjusted the plan.
            return bool(analysis.get("suggestions"))
        except Exception as e:
            self.memory.remember_bug(f"Self-heal skipped for task {task.id}", str(e))
            return False

    def _reflect_and_replan(self, task, allow_retry: bool = False) -> None:
        """Record reflections and reprioritize pending tasks if needed."""
        note = f"Task {task.id} -> {task.status.value}"
        self.memory.reflect(note)
        if task.status == TaskStatus.FAILED and allow_retry:
            # Move failed task to end for a retry opportunity
            idx = next((i for i, t in enumerate(self.planner.tasks) if t.id == task.id), None)
            retries = self.retry_counts.get(task.id, 0)
            if retries < 1 and idx is not None:
                self.retry_counts[task.id] = retries + 1
                failed_task = self.planner.tasks.pop(idx)
                self.planner.tasks.append(failed_task)
            elif retries >= 1:
                self.memory.remember_bug(f"Retry limit reached for task {task.id}", task.description)

    def _run_security_checks(self) -> Dict:
        """Run lightweight security and compliance checks."""
        try:
            return self.security_guard.check_workspace(self.output_dir)
        except Exception as e:
            return {"issues": [f"Security scan failed: {e}"], "secrets": [], "scanned_files": 0}
    
    def _handle_error(self, phase: str, error: str) -> Dict:
        """Handle execution errors"""
        self._log(f"\n✗ Error in {phase} phase: {error}")
        
        return {
            "success": False,
            "phase": phase,
            "error": error,
            "plan": [],
            "progress": {"total": 0, "completed": 0, "percentage": 0}
        }
    
    def _validate_code(self, project_type: str, project_dir: str, enabled: bool = True) -> Optional[Dict]:
        """Validate generated code"""
        from ..validation import create_validator
        
        if not enabled:
            return None

        try:
            validator = create_validator(project_type, project_dir)
            result = validator.validate()
            
            # Display validation results
            if result.errors:
                print(f"   Errors found:")
                for error in result.errors[:5]:  # Show first 5 errors
                    print(f"   - {error}")
            
            if result.warnings:
                print(f"   Warnings:")
                for warning in result.warnings[:3]:  # Show first 3 warnings
                    print(f"   - {warning}")
            
            return result.to_dict()
            
        except Exception as e:
            print(f"   Validation error: {str(e)}")
            return {
                "passed": False,
                "errors": [str(e)],
                "warnings": [],
                "suggestions": [],
                "error_count": 1,
                "warning_count": 0
            }

    def request_interrupt(self, note: Optional[str] = None) -> None:
        """
        Signal the executor to stop after the current task loop.

        Args:
            note: Optional human-readable context explaining why the pause was requested.
        """
        self._pending_update = note
        self._interrupt_requested = True

    def _persist_plan_state(self, description: str, project_type: str, requirements: Dict, tasks) -> None:
        """
        Persist the current plan state for resumable execution.

        The payload includes the intent description, project type, requirements,
        and the serialized task list so a later run can continue where it stopped.
        """
        payload = {
            "description": description,
            "project_type": project_type,
            "requirements": requirements,
            "plan": [t.to_dict() for t in tasks],
        }
        Path(self.artifacts_dir).mkdir(parents=True, exist_ok=True)
        Path(self.state_file).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_plan_state(self) -> Optional[Dict]:
        """
        Load persisted plan state if present.

        Returns:
            Dict containing description, project_type, requirements, and plan fields,
            or None when no state is available or it fails to load cleanly.
        """
        if not os.path.exists(self.state_file):
            return None
        try:
            return json.loads(Path(self.state_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
