"""
Autonomous Execution Engine
"""
from typing import Dict, Optional
import os
import time
from ..planner import TaskPlanner, TaskStatus
from ..generators import (
    WebAppGenerator, AndroidAppGenerator, 
    IOSAppGenerator, DesktopAppGenerator
)
from ..debugger import AutoDebugger


class AutonomousExecutor:
    """Autonomous task execution engine"""
    
    def __init__(self, ai_provider, output_dir: str = "./generated_projects"):
        self.ai_provider = ai_provider
        self.output_dir = output_dir
        self.planner = TaskPlanner(ai_provider)
        self.debugger = AutoDebugger(ai_provider)
        self.execution_log = []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def execute_project(self, description: str, project_type: str, 
                       requirements: Optional[Dict] = None) -> Dict:
        """Execute a complete project autonomously"""
        
        print("\n" + "="*60)
        print("AUTONOMOUS AGENTIC CODER - Starting Execution")
        print("="*60 + "\n")
        
        # Phase 1: Planning
        print("📋 Phase 1: Creating Project Plan...")
        try:
            tasks = self.planner.create_plan(description, project_type)
            print(f"✓ Plan created with {len(tasks)} tasks")
            print(self.planner.get_plan_summary())
        except Exception as e:
            return self._handle_error("Planning", str(e))
        
        # Phase 2: Autonomous Execution
        print("\n⚡ Phase 2: Autonomous Execution...")
        
        max_iterations = 100  # Safety limit
        iteration = 0
        
        while not self.planner.is_plan_complete() and iteration < max_iterations:
            iteration += 1
            
            # Get next task
            task = self.planner.get_next_task()
            if not task:
                break
            
            print(f"\n▶ Executing Task {task.id}: {task.title}")
            
            # Update task status
            self.planner.update_task_status(task.id, TaskStatus.IN_PROGRESS)
            
            # Execute task
            try:
                result = self._execute_task(task, description, requirements or {})
                self.planner.update_task_status(
                    task.id, 
                    TaskStatus.COMPLETED,
                    result=result
                )
                print(f"✓ Task {task.id} completed")
                
            except Exception as e:
                print(f"✗ Task {task.id} failed: {str(e)}")
                
                # Attempt auto-debug
                print(f"🔧 Attempting auto-fix...")
                debug_result = self.debugger.analyze_error(str(e))
                
                # Try to fix and retry
                if debug_result.get("suggestions"):
                    print(f"   Suggestions: {len(debug_result['suggestions'])} fixes found")
                    # For now, mark as failed - in a full implementation, we'd retry
                    self.planner.update_task_status(
                        task.id,
                        TaskStatus.FAILED,
                        error=str(e)
                    )
                else:
                    self.planner.update_task_status(
                        task.id,
                        TaskStatus.FAILED,
                        error=str(e)
                    )
            
            # Show progress
            progress = self.planner.get_progress()
            print(f"   Progress: {progress['completed']}/{progress['total']} tasks completed ({progress['percentage']:.1f}%)")
        
        # Phase 3: Code Generation
        print("\n🏗️  Phase 3: Generating Code...")
        generation_result = self._generate_code(description, project_type, requirements or {})
        
        # Final summary
        print("\n" + "="*60)
        print("EXECUTION COMPLETE")
        print("="*60)
        
        progress = self.planner.get_progress()
        print(f"\nTasks Completed: {progress['completed']}/{progress['total']}")
        print(f"Success Rate: {progress['percentage']:.1f}%")
        
        if generation_result.get("success"):
            print(f"\n✓ Project generated at: {generation_result['output_dir']}")
            print(f"✓ Files created: {len(generation_result.get('files', []))}")
        
        error_summary = self.debugger.get_error_summary()
        if error_summary['total_errors'] > 0:
            print(f"\n⚠ Errors encountered: {error_summary['total_errors']}")
            print(f"   Most common: {error_summary.get('most_common_error', 'N/A')}")
        
        return {
            "success": progress['percentage'] >= 70,
            "plan": [task.to_dict() for task in self.planner.tasks],
            "progress": progress,
            "generation": generation_result,
            "errors": error_summary
        }
    
    def _execute_task(self, task, description: str, requirements: Dict) -> str:
        """Execute a single task"""
        
        # Log execution
        self.execution_log.append({
            "task_id": task.id,
            "task_title": task.title,
            "timestamp": time.time()
        })
        
        # Task execution logic
        system_prompt = "You are an expert software developer executing project tasks."
        
        prompt = f"""Execute the following task:

Task: {task.title}
Description: {task.description}
Project Context: {description}
Requirements: {requirements}

Provide a brief summary of what was accomplished."""

        result = self.ai_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5
        )
        
        return result
    
    def _generate_code(self, description: str, project_type: str, 
                      requirements: Dict) -> Dict:
        """Generate the actual code for the project"""
        
        project_type = project_type.lower()
        project_output_dir = os.path.join(self.output_dir, "project")
        
        try:
            if "web" in project_type or "react" in project_type or "vue" in project_type:
                framework = "react"
                if "vue" in project_type:
                    framework = "vue"
                elif "angular" in project_type:
                    framework = "angular"
                
                generator = WebAppGenerator(self.ai_provider, project_output_dir, framework)
                result = generator.generate_project(description, requirements)
                
            elif "android" in project_type:
                language = "kotlin" if "kotlin" in project_type else "java"
                generator = AndroidAppGenerator(self.ai_provider, project_output_dir, language)
                result = generator.generate_project(description, requirements)
                
            elif "ios" in project_type or "iphone" in project_type:
                generator = IOSAppGenerator(self.ai_provider, project_output_dir)
                result = generator.generate_project(description, requirements)
                
            elif "desktop" in project_type or "electron" in project_type:
                platform = "electron"
                if "python" in project_type:
                    platform = "python"
                generator = DesktopAppGenerator(self.ai_provider, project_output_dir, platform)
                result = generator.generate_project(description, requirements)
                
            else:
                # Default to web app
                generator = WebAppGenerator(self.ai_provider, project_output_dir, "react")
                result = generator.generate_project(description, requirements)
            
            return {
                "success": True,
                "output_dir": project_output_dir,
                "files": result.get("files", []),
                "details": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output_dir": project_output_dir
            }
    
    def _handle_error(self, phase: str, error: str) -> Dict:
        """Handle execution errors"""
        print(f"\n✗ Error in {phase} phase: {error}")
        
        return {
            "success": False,
            "phase": phase,
            "error": error,
            "plan": [],
            "progress": {"total": 0, "completed": 0, "percentage": 0}
        }
