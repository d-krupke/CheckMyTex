"""
DEPRECATED: This setup.py is kept for backward compatibility only.
Please use modern build tools: pip install . or python -m build

All configuration has been moved to pyproject.toml (PEP 621).
"""

import warnings

warnings.warn(
    "setup.py is deprecated. Use 'pip install .' or 'python -m build' instead. "
    "All configuration is now in pyproject.toml.",
    DeprecationWarning,
    stacklevel=2,
)

# Import setuptools to ensure backward compatibility for old tools
from setuptools import setup

# All metadata is now in pyproject.toml
setup()
