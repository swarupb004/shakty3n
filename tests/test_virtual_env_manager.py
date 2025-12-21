#!/usr/bin/env python3
"""
Virtual environment sandbox tests
"""
import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_virtual_env_creation_and_command():
    """Ensure virtual environment creation and command execution works"""
    print("\nTesting VirtualEnvManager sandbox...")

    from shakty3n import VirtualEnvManager

    with tempfile.TemporaryDirectory() as tmpdir:
        env_dir = os.path.join(tmpdir, "env")
        manager = VirtualEnvManager(env_dir)
        manager.create()

        assert os.path.exists(manager.python_path), "Python binary missing in virtual environment"

        result = manager.run_command(["-c", "print('sandbox-ready')"])
        assert "sandbox-ready" in result.stdout

    print("✓ VirtualEnvManager can create env and run commands")
