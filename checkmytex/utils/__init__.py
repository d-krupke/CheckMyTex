"""
Utils do not have any dependencies and could be copy and pasted to other
projects.
"""

from .choice import OptionPrompt
from .editor import Editor

__all__ = [
    "Editor",
    "OptionPrompt",
]
