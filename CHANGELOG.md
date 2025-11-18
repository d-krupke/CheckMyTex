# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-11-18

🎉 **First stable release!** CheckMyTex is now production-ready with comprehensive features, excellent test coverage, and a modern web interface.

### Added
- **FastAPI Web Interface**: Modern web interface for document checking
  - Secure ZIP file upload with size validation
  - Configurable checkers and filters via UI
  - Terminal-styled HTML output with syntax highlighting
  - Inline character-level error highlighting
  - ChatGPT integration for suggestions
  - Open-source attribution and licensing information
  - Clean, responsive design
- HTML report generator with extension system for custom problem rendering
- Modern build system using PEP 621 (pyproject.toml)
- Type hints for public API functions and magic methods
- PEP 561 compliance with py.typed marker file
- Coverage reporting with pytest-cov
- Dependabot configuration for automated dependency updates
- CHANGELOG.md for tracking project changes
- CONTRIBUTING.md with comprehensive development guidelines
- Support for Python 3.11, 3.12, and 3.13 in CI/CD
- Optional dependency groups (dev, test) in pyproject.toml
- Tox configuration for multi-version testing
- EditorConfig for consistent code formatting across editors
- `from __future__ import annotations` to critical modules for modern type hints
- Badges to README (PyPI, CI status, Python versions, license, code style)
- `__version__` attribute in package `__init__.py`

### Changed
- **BREAKING**: Minimum Python version raised to 3.10
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
- Development status upgraded to Production/Stable

### Removed
- Removed irrelevant pre-commit hooks (cmake-format, PyBind capitalization checks)
- Removed direct os.path usage in favor of pathlib
- Removed unused `terminal_html_printer.py` module (dead code)

### Fixed
- HTML syntax highlighting: Commands in LaTeX comments are no longer incorrectly highlighted
- HTML syntax highlighting: Commands within problem highlights now properly display with syntax coloring
- Corrected pre-commit mypy file path patterns
- Updated Python version targets in tool configurations
- Made pytest-cov optional (removed from default pytest config)
- Improved comparison protocol in magic methods (use NotImplemented)
- Removed unused `document` parameter from `Languagetool._get_languagetool_json()` method

## [0.10.5] - Previous Release

See git history for changes prior to this version.

[Unreleased]: https://github.com/d-krupke/checkmytex/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/d-krupke/checkmytex/compare/v0.10.5...v1.0.0
[0.10.5]: https://github.com/d-krupke/checkmytex/releases/tag/v0.10.5
