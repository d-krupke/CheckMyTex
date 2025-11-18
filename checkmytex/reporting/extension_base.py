"""
Base classes for problem display extensions.

Extensions add functionality to problem displays in HTML reports.
Each extension can render a line of HTML for a problem, or skip by returning None.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from checkmytex.finding import Problem


@dataclass
class ExtensionContext:
    """
    Context information provided to extensions when rendering.

    Attributes:
        problem: The problem being rendered
        filename: Source file containing the problem (if known)
        line_number: Line number of the problem (if known)
        code_snippet: Surrounding code context
        document: Full analyzed document (for advanced extensions)
    """

    problem: Problem
    filename: str | None = None
    line_number: int | None = None
    code_snippet: str | None = None
    document: Any = None

    @property
    def has_location(self) -> bool:
        """Check if file location is available."""
        return self.filename is not None and self.line_number is not None

    def estimate_url_size(self, base_chars: int = 100) -> int:
        """
        Estimate URL size if context is included.

        Useful for extensions that generate URLs with context
        (e.g., ChatGPT links have ~2000 char browser limits).

        Args:
            base_chars: Base URL size without context

        Returns:
            Estimated total URL size in characters
        """
        context_size = len(self.code_snippet) if self.code_snippet else 0
        # Account for URL encoding (conservative estimate: 3x)
        return base_chars + context_size * 3


class ProblemExtension(abc.ABC):
    """
    Base class for problem display extensions.

    Extensions render individual lines within a problem box.
    Each extension is called sequentially and can:
    - Return HTML for a line (rendered as a new line in the box)
    - Return None (skip this extension for this problem)

    The basic problem message is itself an extension (BasicMessageExtension).

    Example extensions:
    - BasicMessageExtension: Shows >>> [tool] message
    - ChatGptLinkExtension: Adds ChatGPT help links
    - LookupUrlExtension: Shows documentation links
    """

    @abc.abstractmethod
    def render_line(
        self,
        context: ExtensionContext,
    ) -> str | None:
        """
        Render a single line for this extension.

        Args:
            context: Context with problem, location, code snippet, etc.

        Returns:
            - HTML string for this line (will be auto-wrapped in div)
            - None to skip rendering this extension for this problem

        Examples:
            >>> return ">>> [tool] Error message"
            >>> return '<a href="...">Help link</a>'
            >>> return None  # Skip for this problem
        """

    def get_css(self) -> str:
        """
        Return CSS styles needed by this extension.

        Returns:
            CSS string (without <style> tags). Empty string if no CSS needed.
        """
        return ""

    def get_js(self) -> str:
        """Return JavaScript required by this extension."""
        return ""

    def priority(self) -> int:
        """
        Rendering priority (lower = rendered first).

        Default: 100
        BasicMessage: 0 (always first)
        Links/Actions: 100-200 (after message)
        Advanced: 500+ (last)

        Returns:
            Integer priority
        """
        return 100
