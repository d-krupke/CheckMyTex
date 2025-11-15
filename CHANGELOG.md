# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Modern build system using PEP 621 (pyproject.toml)
- Type hints for public API functions
- PEP 561 compliance with py.typed marker file
- Coverage reporting with pytest-cov
- Dependabot configuration for automated dependency updates
- CHANGELOG.md for tracking project changes
- Support for Python 3.11 and 3.12 in CI/CD
- Optional dependency groups (dev, test) in pyproject.toml

### Changed
- **BREAKING**: Minimum Python version raised to 3.8
- Migrated from setup.py to modern pyproject.toml (PEP 621)
- Updated GitHub Actions to latest versions (checkout@v4, setup-python@v5)
- Replaced flake8 with ruff for faster linting
- Updated pre-commit hooks to latest versions
- Modernized PyPI publishing workflow to use `python -m build`
- Fixed mypy and ruff configuration paths (src → checkmytex)
- Deprecated setup.py (kept for backward compatibility)

### Removed
- Removed irrelevant pre-commit hooks (cmake-format, PyBind capitalization checks)

### Fixed
- Corrected pre-commit mypy file path patterns
- Updated Python version targets in tool configurations

## [0.10.5] - Previous Release

See git history for changes prior to this version.

[Unreleased]: https://github.com/d-krupke/checkmytex/compare/v0.10.5...HEAD
[0.10.5]: https://github.com/d-krupke/checkmytex/releases/tag/v0.10.5
