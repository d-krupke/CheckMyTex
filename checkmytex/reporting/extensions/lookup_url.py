"""Lookup URL extension for problems."""

from __future__ import annotations

import html

from ..extension_base import ExtensionContext, ProblemExtension


class LookupUrlExtension(ProblemExtension):
    """
    Show helpful link if problem has a look_up_url.

    Checkers may provide various types of URLs:
    - Rule documentation (LanguageTool)
    - Search links (spelling checkers)
    - Reference materials
    """

    def render_line(self, context: ExtensionContext) -> str | None:
        """Render helpful link if available."""
        problem = context.problem

        if not problem.look_up_url:
            return None  # Skip - no URL available

        escaped_url = html.escape(problem.look_up_url)
        return (
            f'<a href="{escaped_url}" class="lookup-link" '
            f'target="_blank" rel="noopener noreferrer">'
            f'<svg class="icon-external" viewBox="0 0 24 24">'
            f'<path d="M14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3m-2 16H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7h-2v7z"/>'
            f"</svg>"
            f"Learn more"
            f"</a>"
        )

    def priority(self) -> int:
        """Render after ChatGPT link."""
        return 150

    def get_css(self) -> str:
        return """
        .lookup-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: #4a5568;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .lookup-link:hover {
            background: #2d3748;
            transform: translateY(-1px);
        }
        .icon-external {
            width: 14px;
            height: 14px;
            fill: white;
        }
        """
