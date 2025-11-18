"""Basic message extension that displays the standard problem message."""

from __future__ import annotations

import html

from ..extension_base import ExtensionContext, ProblemExtension


class BasicMessageExtension(ProblemExtension):
    """
    The standard problem message extension.

    Renders: >>> [tool] message

    This should typically be the first extension in the list (priority=0).
    """

    def render_line(self, context: ExtensionContext) -> str:
        """Always renders the basic problem message."""
        problem = context.problem
        tool = html.escape(problem.tool)
        message = html.escape(problem.message)
        return f'<span class="problem-message">>>> [{tool}] {message}</span>'

    def priority(self) -> int:
        """Always render first."""
        return 0

    def get_css(self) -> str:
        return """
        .problem-message {
            color: #f48771;
            font-weight: 600;
        }
        """
