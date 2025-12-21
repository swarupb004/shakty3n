"""
Virtual environment helper for isolated testing
"""
from __future__ import annotations

import os
import shlex
import subprocess
import sys
import venv
from typing import Iterable, Optional, Sequence, Union


class VirtualEnvManager:
    """Create and run commands inside a Python virtual environment."""

    def __init__(self, env_dir: str = ".shakty3n_venv", with_pip: bool = True):
        self.env_dir = env_dir
        self.with_pip = with_pip

    @property
    def python_path(self) -> str:
        """Return the path to the environment's Python executable."""
        if os.name == "nt":
            return os.path.join(self.env_dir, "Scripts", "python.exe")
        return os.path.join(self.env_dir, "bin", "python")

    def create(self, recreate: bool = True) -> str:
        """Create the virtual environment."""
        if recreate and os.path.exists(self.env_dir):
            # venv with clear=True removes existing files safely
            builder = venv.EnvBuilder(with_pip=self.with_pip, clear=True)
        else:
            builder = venv.EnvBuilder(with_pip=self.with_pip)

        builder.create(self.env_dir)
        return self.env_dir

    def _build_command(self, command: Union[str, Sequence[str]]) -> Sequence[str]:
        """Compose a command that runs inside the environment."""
        if isinstance(command, str):
            args: Iterable[str] = shlex.split(command)
        else:
            args = command
        return [self.python_path, *args]

    def run_command(
        self,
        command: Union[str, Sequence[str]],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a command inside the virtual environment."""
        cmd = self._build_command(command)
        return subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            check=check,
            capture_output=True,
            text=True,
        )

    def install_requirements(self, requirements_path: str) -> subprocess.CompletedProcess:
        """Install dependencies from a requirements file inside the environment."""
        return self.run_command(["-m", "pip", "install", "-r", requirements_path])

    def install_local_package(self, editable: bool = True) -> subprocess.CompletedProcess:
        """Install the current project into the environment."""
        args = ["-m", "pip", "install"]
        if editable:
            args.append("-e")
        args.append(".")
        return self.run_command(args)
