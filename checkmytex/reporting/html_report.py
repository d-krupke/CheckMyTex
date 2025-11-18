"""HTML report generator for CheckMyTex analysis results."""

from __future__ import annotations

import html
import os.path
import re
from collections import defaultdict
from pathlib import Path

from checkmytex import AnalyzedDocument
from checkmytex.finding import Problem
from checkmytex.reporting.extension_base import ExtensionContext, ProblemExtension


class HtmlReportGenerator:
    """Generate HTML reports for CheckMyTex analysis with extension support."""

    def __init__(
        self,
        analysis: AnalyzedDocument,
        extensions: list[ProblemExtension] | None = None,
        shorten: int | None = 5,
    ):
        """
        Args:
            analysis: The analyzed document
            extensions: List of problem extensions to apply
            shorten: Number of context lines around problems (None = all)
        """
        self.analysis = analysis
        self.extensions = self._sort_extensions(extensions or [])
        self.shorten = shorten
        self.file_prefix = os.path.commonpath(list(self.analysis.list_files()))
        self.html_parts: list[str] = []

    def _sort_extensions(
        self,
        extensions: list[ProblemExtension],
    ) -> list[ProblemExtension]:
        """Sort extensions by priority."""
        return sorted(extensions, key=lambda e: e.priority())

    def to_html(self, path: str) -> None:
        """Generate and save HTML report to file."""
        html_content = self.render()
        with Path(path).open("w", encoding="utf-8") as f:
            f.write(html_content)

    def render(self) -> str:
        """Generate the report and return it as an HTML string."""
        self.html_parts = []
        self._generate_html()
        return "\n".join(self.html_parts)

    def _generate_html(self) -> None:
        """Generate the complete HTML document."""
        self._add_header()
        self._add_title()
        self._add_file_overview()
        self._add_rule_count()

        for filename in self.analysis.list_files():
            self._add_file_section(filename)

        self._add_orphaned_problems()
        self._add_footer()

    def _add_header(self) -> None:
        """Add HTML header with base styles + extension styles."""
        # Collect CSS from all extensions
        css_parts = [self._get_base_css()]
        for extension in self.extensions:
            ext_css = extension.get_css()
            if ext_css:
                css_parts.append(ext_css)

        combined_css = "\n".join(css_parts)

        self.html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CheckMyTex Report</title>
    <style>
{combined_css}
    </style>
</head>
<body>
    <div class="container">""")

    def _get_base_css(self) -> str:
        """Base CSS for report structure."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background-color: #0d1117;
            color: #d4d4d4;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: #1e1e1e;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .title {
            color: #569cd6;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            font-style: italic;
        }

        .section-title {
            color: #4ec9b0;
            font-size: 16px;
            font-style: italic;
            text-align: center;
            margin: 30px 0 10px 0;
        }

        .separator {
            color: #4fc1ff;
            margin: 30px 0 20px 0;
            text-align: center;
            padding: 10px;
            background-color: #252525;
            border-top: 2px solid #404040;
            border-bottom: 2px solid #404040;
            font-weight: bold;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0 20px 0;
            background-color: #252525;
        }

        table th {
            color: #d4d4d4;
            font-weight: bold;
            text-align: left;
            padding: 8px 12px;
            border-bottom: 1px solid #404040;
        }

        table th:last-child {
            text-align: right;
        }

        table td {
            color: #d4d4d4;
            padding: 6px 12px;
            border-bottom: 1px solid #333;
        }

        table td:last-child {
            text-align: right;
        }

        table tr:hover {
            background-color: #2d2d2d;
        }

        .code-block {
            background-color: #252525;
            margin: 15px 0;
            padding: 15px;
            border: 1px solid #404040;
            border-radius: 4px;
        }

        .code-line {
            display: flex;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin-bottom: 2px;
        }

        .line-number {
            color: #858585;
            text-align: right;
            padding-right: 12px;
            user-select: none;
            min-width: 50px;
            flex-shrink: 0;
        }

        .line-content {
            color: #d4d4d4;
            flex: 1;
            overflow-wrap: break-word;
            word-break: break-word;
        }

        .highlight {
            background-color: #5a1e1e;
            color: #ffffff;
            padding: 0 2px;
            border-radius: 2px;
        }

        /* Syntax highlighting within problem highlights */
        .highlight .command { color: #dcdcaa; }
        .highlight .bracket { color: #ffd700; }
        .highlight .comment { color: #6a9955; }

        .problem-box {
            margin: 12px 0 12px 62px;
            padding: 12px;
            background-color: #2a2a2a;
            border-left: 4px solid #f48771;
            border-radius: 4px;
        }

        .problem-line {
            padding: 4px 0;
        }

        .problem-line:not(:last-child) {
            margin-bottom: 8px;
        }

        .ellipsis {
            color: #858585;
            text-align: center;
            margin: 5px 0;
        }

        /* Syntax highlighting */
        .keyword { color: #c586c0; }
        .string { color: #ce9178; }
        .comment { color: #6a9955; }
        .command { color: #dcdcaa; }
        .bracket { color: #ffd700; }
        .parameter { color: #9cdcfe; }
        """

    def _add_footer(self) -> None:
        """Add HTML footer."""
        extension_js = self._get_extension_js()
        script_block = ""
        if extension_js:
            script_block = f"\n    <script>\n{extension_js}\n    </script>"

        self.html_parts.append(f"""    </div>{script_block}
</body>
</html>""")

    def _get_extension_js(self) -> str:
        """Collect JavaScript snippets from extensions."""
        scripts: list[str] = []
        for extension in self.extensions:
            script = extension.get_js()
            if script:
                scripts.append(script)
        return "\n".join(scripts)

    def _add_title(self) -> None:
        """Add report title."""
        self.html_parts.append('        <div class="title">CheckMyTex</div>')

    def _add_file_overview(self) -> None:
        """Add table of problems by file."""
        self.html_parts.append(
            '        <div class="section-title">Problems by file</div>'
        )
        self.html_parts.append("        <table>")
        self.html_parts.append("            <thead>")
        self.html_parts.append("                <tr><th>File</th><th>Count</th></tr>")
        self.html_parts.append("            </thead>")
        self.html_parts.append("            <tbody>")

        for file in self.analysis.list_files():
            filename = html.escape(str(file[len(self.file_prefix) :]))
            count = len(self.analysis.get_problems(file))
            self.html_parts.append(
                f"                <tr><td>{filename}</td><td>{count}</td></tr>"
            )

        if self.analysis.get_orphaned_problems():
            count = len(self.analysis.get_orphaned_problems())
            self.html_parts.append(
                f"                <tr><td>UNKNOWN</td><td>{count}</td></tr>"
            )

        self.html_parts.append("            </tbody>")
        self.html_parts.append("        </table>")

    def _add_rule_count(self) -> None:
        """Add table of problems by type."""
        self.html_parts.append(
            '        <div class="section-title">Problems by type</div>'
        )
        self.html_parts.append("        <table>")
        self.html_parts.append("            <thead>")
        self.html_parts.append(
            "                <tr><th>Tool</th><th>Rule</th><th>Count</th></tr>"
        )
        self.html_parts.append("            </thead>")
        self.html_parts.append("            <tbody>")

        problem_counts: defaultdict[str, defaultdict[str, int]] = defaultdict(
            lambda: defaultdict(lambda: 0)
        )
        for prob in self.analysis.get_problems():
            problem_counts[prob.tool][prob.rule] += 1

        for tool, rules in problem_counts.items():
            first = True
            for rule, count in rules.items():
                tool_display = html.escape(str(tool)) if first else ""
                rule_display = html.escape(str(rule))
                self.html_parts.append(
                    f"                <tr><td>{tool_display}</td><td>{rule_display}</td><td>{count}</td></tr>"
                )
                first = False

        self.html_parts.append("            </tbody>")
        self.html_parts.append("        </table>")

    def _add_file_section(self, filename: str) -> None:
        """Add section for a specific file."""
        display_name = filename[len(self.file_prefix) :]
        separator = "─" * 50 + " " + display_name + " " + "─" * 50
        self.html_parts.append(f'        <div class="separator">{separator}</div>')

        last_printed_line = -1
        problematic_lines = sorted(
            {
                prob.origin.get_file_line()
                for prob in self.analysis.get_problems(filename)
            }
        )

        for line_num in problematic_lines:
            if self.shorten is not None:
                start_line = max(last_printed_line + 1, line_num - self.shorten)
            else:
                start_line = last_printed_line + 1

            if start_line != 0 and start_line != last_printed_line + 1:
                self.html_parts.append('        <div class="ellipsis">...</div>')

            problems = self.analysis.get_problems(filename, line_num)

            # Get highlight ranges for this line
            highlights = [
                (
                    prob.origin.begin.file.position.line_offset,
                    prob.origin.end.file.position.line_offset,
                )
                for prob in problems
            ]

            self._add_code_block(
                filename, start_line, line_num + 1, line_num, highlights, problems
            )
            last_printed_line = line_num

    def _add_code_block(
        self,
        filename: str,
        start_line: int,
        end_line: int,
        highlight_line: int,
        highlights: list[tuple[int, int]],
        problems: list[Problem],
    ) -> None:
        """Add a code block with line numbers and extension-based problem boxes."""
        self.html_parts.append('        <div class="code-block">')

        # Render code lines
        for line_idx in range(start_line, end_line):
            line_content = self.analysis.document.get_file_content(filename, line_idx)
            if line_content and line_content.endswith("\n"):
                line_content = line_content[:-1]

            self.html_parts.append('            <div class="code-line">')
            self.html_parts.append(
                f'                <span class="line-number">{line_idx}</span>'
            )

            # Apply highlights if this is the problem line
            if line_idx == highlight_line and line_content:
                highlighted_content = self._highlight_ranges(line_content, highlights)
            else:
                escaped_content = html.escape(line_content) if line_content else ""
                highlighted_content = self._apply_latex_highlighting(escaped_content)

            self.html_parts.append(
                f'                <span class="line-content">{highlighted_content}</span>'
            )
            self.html_parts.append("            </div>")

        # Render EACH problem as a separate box (multiple problems per line!)
        for prob in problems:
            problem_html = self._render_problem_box(
                problem=prob,
                filename=filename,
                line_number=highlight_line,
            )
            if problem_html:  # Extensions might skip rendering
                self.html_parts.append(problem_html)

        self.html_parts.append("        </div>")

    def _render_problem_box(
        self,
        problem: Problem,
        filename: str | None = None,
        line_number: int | None = None,
    ) -> str:
        """
        Render ONE problem as a box with stacked extension lines.

        Called multiple times within _add_code_block() - once per problem.
        """
        # Build context for this specific problem
        code_snippet = (
            self._get_code_snippet(filename, line_number)
            if filename and line_number is not None
            else None
        )
        context = ExtensionContext(
            problem=problem,
            filename=filename,
            line_number=line_number,
            code_snippet=code_snippet,
            document=self.analysis.document,
        )

        # Collect lines from ALL extensions
        lines = []
        for extension in self.extensions:
            line_html = extension.render_line(context)
            if line_html:  # Extension can return None to skip
                lines.append(line_html)

        # If no extensions rendered anything, skip this problem box entirely
        if not lines:
            return ""

        # Wrap each line in a div and assemble the box
        lines_html = "\n".join(
            f'            <div class="problem-line">{line}</div>' for line in lines
        )

        return f'        <div class="problem-box">\n{lines_html}\n        </div>'

    def _get_code_snippet(
        self,
        filename: str,
        line_number: int,
        lines_before: int = 3,
        lines_after: int = 3,
    ) -> str:
        """Get code snippet around a line."""
        snippet_lines = []
        for offset in range(-lines_before, lines_after + 1):
            line_idx = line_number + offset

            # Skip negative line numbers
            if line_idx < 0:
                continue

            try:
                content = self.analysis.document.get_file_content(filename, line_idx)
                if content:
                    snippet_lines.append(f"{line_idx}: {content.rstrip()}")
            except (IndexError, KeyError):
                # Line doesn't exist (beyond file end or invalid file)
                continue

        return "\n".join(snippet_lines)

    def _highlight_ranges(
        self, line_content: str, highlights: list[tuple[int, int]]
    ) -> str:
        """Highlight specific character ranges in a line."""
        # Merge overlapping ranges
        if not highlights:
            escaped = html.escape(line_content)
            return self._apply_latex_highlighting(escaped)

        # Sort ranges and merge overlapping ones
        sorted_ranges = sorted(highlights)
        merged = [sorted_ranges[0]]
        for start, end in sorted_ranges[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end:
                merged[-1] = (last_start, max(end, last_end))
            else:
                merged.append((start, end))

        # Build the highlighted string
        result = []
        pos = 0

        for start, end in merged:
            # Add text before highlight with LaTeX syntax highlighting
            if pos < start:
                before = html.escape(line_content[pos:start])
                result.append(self._apply_latex_highlighting(before))

            # Add highlighted text with LaTeX syntax highlighting
            highlight_text = html.escape(line_content[start:end])
            highlight_text = self._apply_latex_highlighting(highlight_text)
            result.append(f'<span class="highlight">{highlight_text}</span>')
            pos = end

        # Add remaining text with LaTeX syntax highlighting
        if pos < len(line_content):
            after = html.escape(line_content[pos:])
            result.append(self._apply_latex_highlighting(after))

        return "".join(result)

    def _apply_latex_highlighting(self, content: str) -> str:
        """Apply basic LaTeX syntax highlighting."""
        # Split content into comment and non-comment parts to avoid
        # highlighting commands inside comments

        comment_pattern = r"%.*"
        parts = []
        last_end = 0

        for match in re.finditer(comment_pattern, content):
            # Add non-comment part before this comment
            if match.start() > last_end:
                non_comment = content[last_end : match.start()]
                # Apply command and bracket highlighting to non-comment part
                non_comment = re.sub(
                    r"(\\[a-zA-Z@]+)", r'<span class="command">\1</span>', non_comment
                )
                non_comment = re.sub(
                    r"([{}[\]])", r'<span class="bracket">\1</span>', non_comment
                )
                parts.append(non_comment)

            # Add comment part (wrapped in comment span)
            comment = match.group(0)
            parts.append(f'<span class="comment">{comment}</span>')
            last_end = match.end()

        # Add any remaining non-comment part
        if last_end < len(content):
            non_comment = content[last_end:]
            non_comment = re.sub(
                r"(\\[a-zA-Z@]+)", r'<span class="command">\1</span>', non_comment
            )
            non_comment = re.sub(
                r"([{}[\]])", r'<span class="bracket">\1</span>', non_comment
            )
            parts.append(non_comment)

        return "".join(parts)

    def _add_orphaned_problems(self) -> None:
        """Add orphaned problems section with extension support."""
        problems = self.analysis.get_orphaned_problems()
        if not problems:
            return

        self.html_parts.append(
            '        <div class="separator">─────── Other problems ───────</div>'
        )

        for prob in problems:
            problem_html = self._render_problem_box(problem=prob)
            if problem_html:
                self.html_parts.append(problem_html)
