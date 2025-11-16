"""
A simple CLI to deal with the problems. Can be easily replaced by your own.
"""

# ruff: noqa: F401
from .arguments import create_default_argument_parser, parse_arguments
from .cli import cli
