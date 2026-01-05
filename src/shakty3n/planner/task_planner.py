"""
Autonomous Task Planner
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """Represents a single task in the plan"""
    id: int
    title: str
    description: str
    dependencies: List[int] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    subtasks: List['Task'] = field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "subtasks": [st.to_dict() for st in self.subtasks],
            "result": self.result,
            "error": self.error
        }


class TaskPlanner:
    """Autonomous task planning system"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.tasks: List[Task] = []
        self.task_counter = 0
    
    def create_plan(self, project_description: str, project_type: str) -> List[Task]:
        """Create a comprehensive plan for the project"""
        system_prompt = """You are an expert software architect and project planner.
Your job is to create a detailed, step-by-step plan for building software projects.
Break down the project into logical tasks with clear dependencies.
Return the plan in JSON format with the following structure:
{
  "tasks": [
    {
      "title": "Task title",
      "description": "Detailed description",
      "dependencies": [list of task IDs this depends on],
      "subtasks": [optional array of subtasks with same structure]
    }
  ]
}"""
        
        prompt = f"""Create a detailed, actionable development plan for the following project:

Project Type: {project_type}
Description: {project_description}

You are an Autonomous Agent that uses tools (read_file, write_file, run_command).
Break down the project into concrete, executable tasks. 
Avoid vague tasks like "Development" or "Testing". 
Instead, use specific tasks like "Initialize Node.js project", "Create src/index.js", "Implement login component".

Return the plan in JSON format with strictly ordered dependencies.
Use 3-10 tasks depending on complexity."""

        try:
            response = self.ai_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            # Extract JSON from response
            plan_data = self._extract_json(response)
            
            # Convert to Task objects
            self.tasks = self._parse_tasks(plan_data.get("tasks", []))
            return self.tasks
            
        except Exception as e:
            raise Exception(f"Failed to create plan: {str(e)}")
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from AI response"""
        # Try to find JSON in markdown code blocks
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
                json_str = text[start:start+idx]
            except (ValueError, json.JSONDecodeError):
                json_str = "{}"
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.debug("Failed to parse planner JSON payload: %s", e)
            # Fallback: create basic plan
            return {
                "tasks": [
                    {
                        "title": "Initialize Project",
                        "description": "Set up project structure and configuration",
                        "dependencies": []
                    },
                    {
                        "title": "Implement Features",
                        "description": "Write code files based on requirements",
                        "dependencies": [0]
                    }
                ]
            }
    
    def _parse_tasks(self, tasks_data: List[Dict]) -> List[Task]:
        """Parse task data into Task objects"""
        tasks = []
        for idx, task_data in enumerate(tasks_data):
            task = Task(
                id=idx,
                title=task_data.get("title", f"Task {idx}"),
                description=task_data.get("description", ""),
                dependencies=task_data.get("dependencies", [])
            )
            
            # Parse subtasks recursively
            if "subtasks" in task_data:
                task.subtasks = self._parse_subtasks(task_data["subtasks"], idx)
            
            tasks.append(task)
        
        return tasks
    
    def _parse_subtasks(self, subtasks_data: List[Dict], parent_id: int) -> List[Task]:
        """Parse subtasks recursively"""
        subtasks = []
        for idx, subtask_data in enumerate(subtasks_data):
            self.task_counter += 1
            subtask = Task(
                id=self.task_counter,
                title=subtask_data.get("title", f"Subtask {idx}"),
                description=subtask_data.get("description", ""),
                dependencies=subtask_data.get("dependencies", [])
            )
            subtasks.append(subtask)
        return subtasks

    def load_plan(self, tasks_data: List[Dict]) -> List[Task]:
        """
        Load an existing plan from serialized task dictionaries.

        Args:
            tasks_data: List of dictionaries previously produced via Task.to_dict().

        Returns:
            The list of Task objects with statuses restored for resumption.
        """
        loaded_tasks: List[Task] = []
        for idx, task_data in enumerate(tasks_data):
            status_value = task_data.get("status", TaskStatus.PENDING.value)
            try:
                status = TaskStatus(status_value)
            except ValueError:
                status = TaskStatus.PENDING
            task_id = task_data.get("id")
            if task_id is None:
                task_id = self.task_counter
                self.task_counter += 1
            else:
                self.task_counter = max(self.task_counter, task_id + 1)
            task = Task(
                id=task_id,
                title=task_data.get("title", f"Task {idx}"),
                description=task_data.get("description", ""),
                dependencies=task_data.get("dependencies", []),
                status=status,
                result=task_data.get("result"),
                error=task_data.get("error"),
            )
            loaded_tasks.append(task)

        self.tasks = loaded_tasks
        return self.tasks
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next task to execute"""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                # Check if dependencies are met
                if self._are_dependencies_met(task):
                    return task
        return None
    
    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if task dependencies are completed"""
        for dep_id in task.dependencies:
            if dep_id < len(self.tasks):
                dep_task = self.tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
        return True
    
    def update_task_status(self, task_id: int, status: TaskStatus, 
                          result: Optional[str] = None, error: Optional[str] = None):
        """Update task status"""
        if task_id < len(self.tasks):
            task = self.tasks[task_id]
            task.status = status
            if result:
                task.result = result
            if error:
                task.error = error
    
    def get_plan_summary(self) -> str:
        """Get a formatted summary of the plan"""
        lines = ["=" * 60, "PROJECT PLAN", "=" * 60, ""]
        
        for task in self.tasks:
            status_symbol = {
                TaskStatus.PENDING: "⏸",
                TaskStatus.IN_PROGRESS: "▶",
                TaskStatus.COMPLETED: "✓",
                TaskStatus.FAILED: "✗",
                TaskStatus.SKIPPED: "⊘"
            }.get(task.status, "?")
            
            lines.append(f"[{status_symbol}] Task {task.id}: {task.title}")
            lines.append(f"    {task.description}")
            if task.dependencies:
                lines.append(f"    Dependencies: {task.dependencies}")
            if task.subtasks:
                for subtask in task.subtasks:
                    lines.append(f"    - {subtask.title}")
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def is_plan_complete(self) -> bool:
        """Check if all tasks are completed"""
        return all(task.status == TaskStatus.COMPLETED for task in self.tasks)
    
    def get_progress(self) -> Dict:
        """Get progress statistics"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "pending": total - completed - in_progress - failed,
            "percentage": (completed / total * 100) if total > 0 else 0
        }
