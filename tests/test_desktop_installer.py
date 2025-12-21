#!/usr/bin/env python3
"""
Tests for macOS GUI installer configuration in desktop generator
"""
import json
import sys
import tempfile
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shakty3n.generators.desktop_generator import DesktopAppGenerator


def test_electron_package_json_contains_macos_installer():
    """Ensure Electron generator emits macOS DMG configuration"""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DesktopAppGenerator(ai_provider=None, output_dir=tmpdir, platform="electron")
        generator.generate_project("Test mac installer", {})

        pkg_path = os.path.join(tmpdir, "package.json")
        with open(pkg_path, "r", encoding="utf-8") as f:
            package_json = json.load(f)

        scripts = package_json.get("scripts", {})
        assert "dist:mac" in scripts, "macOS installer script missing"

        mac_targets = package_json.get("build", {}).get("mac", {}).get("target", [])
        dmg_target = None
        for target in mac_targets:
            if isinstance(target, dict) and target.get("target") == "dmg":
                dmg_target = target
                break
        assert dmg_target is not None, "macOS DMG target not configured"

        arch_list = dmg_target.get("arch", [])
        assert "x64" in arch_list and "arm64" in arch_list, "Universal DMG arches missing"
