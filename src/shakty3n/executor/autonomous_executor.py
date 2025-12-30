"""
Autonomous Execution Engine
"""
from typing import Dict, Optional
import ast
import os
import time
from ..planner import TaskPlanner, TaskStatus
from ..generators import (
    WebAppGenerator, AndroidAppGenerator, 
    IOSAppGenerator, DesktopAppGenerator, FlutterAppGenerator,
    StaticHTMLGenerator
)
from ..debugger import AutoDebugger


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
        self.output_dir = output_dir
        self.planner = TaskPlanner(ai_provider)
        self.debugger = AutoDebugger(ai_provider)
        self.on_log = None
        
        # Initialize tools
        from .tools import ToolRegistry
        self.tools = ToolRegistry(output_dir)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def _log(self, message: str):
        print(message)
        if self.on_log:
            self.on_log(message)

    def execute_project(self, description: str, project_type: str, 
                       requirements: Optional[Dict] = None, generate_tests: bool = False,
                       validate_code: bool = False, on_log=None) -> Dict:
        """Execute a project autonomously"""
        self.on_log = on_log
        
        self._log("\n" + "="*60)
        self._log("ANTIGRAVITY AGENT - Starting Execution")
        self._log("="*60 + "\n")
        
        # Phase 1: Planning
        self._log("📋 Phase 1: Planning...")
        try:
            tasks = self.planner.create_plan(description, project_type)
            self._log(f"✓ Plan created with {len(tasks)} tasks")
            self._log(self.planner.get_plan_summary())
        except Exception as e:
            return self._handle_error("Planning", str(e))
        
        # Phase 2: Execution (ReAct Loop)
        self._log("\n⚡ Phase 2: Autonomous Intent Execution...")
        
        # Initialize workspace (Scaffold if needed)
        self._initialize_workspace()
        
        max_iterations = 50 
        iteration = 0
        
        while not self.planner.is_plan_complete() and iteration < max_iterations:
            iteration += 1
            task = self.planner.get_next_task()
            if not task:
                break
            
            self._log(f"\n▶ Executing Task {task.id}: {task.title}")
            self.planner.update_task_status(task.id, TaskStatus.IN_PROGRESS)
            
            try:
                # ReAct Loop for single task
                success = self._execute_react_task(task, description)
                
                if success:
                    self.planner.update_task_status(task.id, TaskStatus.COMPLETED)
                    self._log(f"✓ Task {task.id} completed")
                else:
                    self.planner.update_task_status(task.id, TaskStatus.FAILED)
                    self._log(f"✗ Task {task.id} failed")
                    
            except Exception as e:
                self.planner.update_task_status(task.id, TaskStatus.FAILED, error=str(e))
                self._log(f"✗ Error executing task: {str(e)}")
        
        # Phase 3: Finalization
        self._log("\n" + "="*60)
        self._log("EXECUTION COMPLETE")
        self._log("="*60)
        
        return {
            "success": self.planner.is_plan_complete(),
            "plan": [task.to_dict() for task in self.planner.tasks],
            "generation": {"output_dir": self.output_dir, "success": True}
        }

    def _initialize_workspace(self):
        """Setup initial workspace state"""
        if not os.path.exists(os.path.join(self.output_dir, "package.json")):
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
                raise ValueError("Invalid tool invocation")

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
    
    def _validate_code(self, project_type: str, project_dir: str) -> Dict:
        """Validate generated code"""
        from ..validation import create_validator
        
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
