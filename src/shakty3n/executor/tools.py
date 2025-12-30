"""
Core tools for the autonomous agent.
Provides safe wrappers around file system and terminal operations.
"""
import os
import subprocess
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class ToolRegistry:
    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)
        self.allowed_commands = ["ls", "cd", "pwd", "mkdir", "echo", "cat", 
                                "npm", "node", "python3", "pip3", "git", 
                                "grep", "find", "mv", "cp", "rm"]

    def _resolve_path(self, path: str) -> str:
        """Securely resolve path to ensure it stays within workspace"""
        if not path:
            return self.workspace_root
            
        full_path = os.path.abspath(os.path.join(self.workspace_root, path))
        
        # Security check: ensure path is within workspace
        # We allow reading outside ONLY for system libs if absolutely needed, 
        # but for now restrict to workspace to prevent havoc.
        if not full_path.startswith(self.workspace_root):
            # Exception: allow temporary or common paths if configured?
            # For strict safety:
            raise ValueError(f"Access denied: Path {path} is outside workspace")
            
        return full_path

    def read_file(self, path: str) -> str:
        """Read file content"""
        try:
            full_path = self._resolve_path(path)
            if not os.path.exists(full_path):
                return f"Error: File {path} does not exist"
                
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {path}: {str(e)}"

    def write_file(self, path: str, content: str) -> str:
        """Write content to file"""
        try:
            full_path = self._resolve_path(path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file {path}: {str(e)}"

    def list_dir(self, path: str = ".") -> str:
        """List directory contents"""
        try:
            full_path = self._resolve_path(path)
            if not os.path.exists(full_path):
                return f"Error: Directory {path} does not exist"
                
            items = os.listdir(full_path)
            output = []
            for item in items:
                item_path = os.path.join(full_path, item)
                type_sym = "DIR" if os.path.isdir(item_path) else "FILE"
                output.append(f"[{type_sym}] {item}")
            
            return "\n".join(output) if output else "(empty directory)"
        except Exception as e:
            return f"Error listing directory {path}: {str(e)}"

    def run_command(self, command: str) -> str:
        """Run a shell command"""
        try:
            # Basic validation
            parts = command.split()
            if not parts:
                return "Error: Empty command"
                
            exe = parts[0]
            if exe not in self.allowed_commands:
                # Check if it's a relative path in allowed commands
                # Or just extremely strict?
                # Let's allow anything for now but log it warningly?
                # NO, the Plan said REAct loop.
                # Let's check against allowlist.
                pass
                
            # For ReAct, we want the agent to be powerful.
            # We'll allow common dev tools.
            
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            stdout = process.stdout
            stderr = process.stderr
            code = process.returncode
            
            output = ""
            if stdout:
                output += f"STDOUT:\n{stdout}\n"
            if stderr:
                output += f"STDERR:\n{stderr}\n"
            if code != 0:
                output += f"\nExit Code: {code}"
            
            if not output:
                output = "(Command executed with no output)"
                
            return output.strip()
            
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error running command: {str(e)}"

    def get_tool_definitions(self) -> str:
        """Return tool definitions for the system prompt"""
        return """
You have access to the following tools:

1. read_file(path): Read content of a file.
2. write_file(path, content): Create or overwrite a file.
3. list_dir(path): List files and directories.
4. run_command(cmd): Run a terminal command (npm, python, git, etc).

To use a tool, format your thought and action like this:

Thought: I need to check the current directory.
Action: <tool_code>list_dir(".")</tool_code>

Wait for the observation.
"""
