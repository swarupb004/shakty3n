#!/usr/bin/env python3
"""
Tests for macOS GUI installer configuration in desktop generator
"""
import os
import sys
import json
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_electron_package_json_contains_macos_installer():
    """Ensure Electron generator emits macOS DMG configuration"""
    from shakty3n.generators import DesktopAppGenerator

    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DesktopAppGenerator(ai_provider=None, output_dir=tmpdir, platform="electron")
        generator.generate_project("Test mac installer", {})

        pkg_path = os.path.join(tmpdir, "package.json")
        with open(pkg_path, "r", encoding="utf-8") as f:
            package_json = json.load(f)

        scripts = package_json.get("scripts", {})
        assert "dist:mac" in scripts, "macOS installer script missing"

        mac_targets = package_json.get("build", {}).get("mac", {}).get("target", [])
        dmg_targets = [t for t in mac_targets if isinstance(t, dict) and t.get("target") == "dmg"]
        assert dmg_targets, "macOS DMG target not configured"

        arch_list = dmg_targets[0].get("arch", [])
        assert "x64" in arch_list and "arm64" in arch_list, "Universal DMG arches missing"
