"""
A simple CLI to deal with the problems. Can be easily replaced by your own.
"""

from .arguments import create_default_argument_parser, parse_arguments
from .cli import cli

__all__ = [
    "cli",
    "create_default_argument_parser",
    "parse_arguments",
]
