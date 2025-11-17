# Contributing to CheckMyTex

Thank you for your interest in contributing to CheckMyTex! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip
- git

### Setting Up Your Development Environment

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/checkmytex.git
   cd checkmytex
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package in development mode with dev dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

   This will automatically run code quality checks before each commit.

## Development Workflow

### Running Tests

Run the test suite with pytest:

```bash
pytest
```

Run tests with coverage (requires `pytest-cov` from dev dependencies):

```bash
# Install dev dependencies if not already installed
pip install -e ".[dev]"

# Run with coverage
pytest --cov=checkmytex --cov-report=term-missing
```

Run tests across multiple Python versions with tox:

```bash
# Test all Python versions
tox

# Test specific Python version
tox -e py311

# Run linting only
tox -e lint

# Run type checking only
tox -e type
```

### Code Quality Tools

This project uses several tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter
- **mypy**: Static type checker
- **pytest**: Testing framework

Run these manually:

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy checkmytex tests
```

Or let pre-commit run them automatically on commit.

### Pre-commit Hooks

Pre-commit hooks will automatically run when you commit. To run them manually:

```bash
pre-commit run --all-files
```

To update hooks to their latest versions:

```bash
pre-commit autoupdate
```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/description` - for new features
- `fix/description` - for bug fixes
- `docs/description` - for documentation
- `refactor/description` - for refactoring

### Commit Messages

Write clear, descriptive commit messages following these guidelines:

- Use the imperative mood ("Add feature" not "Added feature")
- First line should be a short summary (50 chars or less)
- Optionally add a blank line and detailed description
- Reference issues when applicable

Examples:

```
feat: Add support for custom LaTeX commands

Implements #42
```

```
fix: Correct path handling on Windows

Fixes #123
```

### Code Style

- Follow PEP 8 style guidelines (enforced by ruff)
- Add type hints to new functions
- Write docstrings for public APIs
- Keep functions focused and reasonably sized

### Adding Tests

- Add tests for new features
- Update tests when modifying existing functionality
- Aim for good test coverage (we track coverage with pytest-cov)
- Tests should be in the `tests/` directory

## Submitting Changes

1. **Ensure all tests pass**

   ```bash
   pytest
   ```

2. **Ensure code quality checks pass**

   ```bash
   pre-commit run --all-files
   ```

3. **Update CHANGELOG.md**

   Add your changes to the "Unreleased" section

4. **Push your changes and create a pull request**

   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure CI checks pass

## Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Any relevant error messages

## Questions?

Feel free to open an issue for any questions about contributing!

## Code of Conduct

Please be respectful and constructive in all interactions. This project aims to be welcoming to contributors of all backgrounds and experience levels.
