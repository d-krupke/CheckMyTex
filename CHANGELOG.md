# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Streamlit Web Interface**: Student-friendly web interface for interactive document checking
  - Secure ZIP file upload with validation
  - Interactive problem viewer with action buttons
  - Todo list manager with comments and priorities
  - Export capabilities (JSON, CSV, Markdown)
  - Progress tracking during analysis
  - Comprehensive security features for file handling
- Modern build system using PEP 621 (pyproject.toml)
- Type hints for public API functions and magic methods
- PEP 561 compliance with py.typed marker file
- Coverage reporting with pytest-cov
- Dependabot configuration for automated dependency updates
- CHANGELOG.md for tracking project changes
- CONTRIBUTING.md with comprehensive development guidelines
- Support for Python 3.11 and 3.12 in CI/CD
- Optional dependency groups (dev, test) in pyproject.toml
- Tox configuration for multi-version testing
- EditorConfig for consistent code formatting across editors
- `from __future__ import annotations` to critical modules for modern type hints
- Badges to README (PyPI, CI status, Python versions, license, code style)
- `__version__` attribute in package `__init__.py`

### Changed
- **BREAKING**: Minimum Python version raised to 3.8
- Migrated from setup.py to modern pyproject.toml (PEP 621)
- Updated GitHub Actions to latest versions (checkout@v4, setup-python@v5)
- Replaced flake8 with ruff for faster linting
- Updated pre-commit hooks to latest versions
- Modernized PyPI publishing workflow to use `python -m build`
- Fixed mypy and ruff configuration paths (src → checkmytex)
- Deprecated setup.py (kept for backward compatibility)
- Modernized path handling to use pathlib instead of os.path
- Updated requirements.txt to match pyproject.toml versions
- Enhanced README with modern structure and links to documentation

### Removed
- Removed irrelevant pre-commit hooks (cmake-format, PyBind capitalization checks)
- Removed direct os.path usage in favor of pathlib

### Fixed
- Corrected pre-commit mypy file path patterns
- Updated Python version targets in tool configurations
- Made pytest-cov optional (removed from default pytest config)
- Improved comparison protocol in magic methods (use NotImplemented)

## [0.10.5] - Previous Release

See git history for changes prior to this version.

[Unreleased]: https://github.com/d-krupke/checkmytex/compare/v0.10.5...HEAD
[0.10.5]: https://github.com/d-krupke/checkmytex/releases/tag/v0.10.5
