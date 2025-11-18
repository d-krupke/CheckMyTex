"""Test version consistency across package files."""

from __future__ import annotations

import re
from pathlib import Path

import checkmytex


def test_version_consistency():
    """Verify that __version__ in __init__.py matches version in pyproject.toml."""
    # Get version from __init__.py
    init_version = checkmytex.__version__

    # Get version from pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    pyproject_content = pyproject_path.read_text(encoding="utf-8")

    # Extract version from pyproject.toml using regex
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_content, re.MULTILINE)
    assert match is not None, "Could not find version in pyproject.toml"
    pyproject_version = match.group(1)

    # Verify they match
    assert init_version == pyproject_version, (
        f"Version mismatch: __init__.py has {init_version}, pyproject.toml has {pyproject_version}"
    )
