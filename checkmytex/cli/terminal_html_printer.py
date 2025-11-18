"""Terminal-styled HTML printer for CheckMyTex analysis results."""

from __future__ import annotations

import html
import os.path
import re
from collections import defaultdict
from pathlib import Path

from checkmytex import AnalyzedDocument
from checkmytex.finding import Problem


class TerminalHtmlPrinter:
    """Generate terminal-styled HTML output for CheckMyTex analysis."""

    def __init__(
        self,
        analysis: AnalyzedDocument,
        shorten: int | None = 5,
    ):
        self.analysis = analysis
        self.shorten = shorten
        self.file_prefix = os.path.commonpath(list(self.analysis.list_files()))
        self.html_parts: list[str] = []

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
        """Add HTML header with styles."""
        self.html_parts.append("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CheckMyTex Report</title>
    <style>
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

        .problem {
            color: #f48771;
            font-weight: bold;
            margin: 8px 0 8px 62px;
            padding: 8px 12px;
            background-color: #2a2a2a;
            border-left: 4px solid #f48771;
            border-radius: 2px;
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
    </style>
</head>
<body>
    <div class="container">""")

    def _add_footer(self) -> None:
        """Add HTML footer."""
        self.html_parts.append("""    </div>
</body>
</html>""")

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
        """Add a code block with line numbers."""
        self.html_parts.append('        <div class="code-block">')

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

        # Add problems
        for prob in problems:
            msg = html.escape(f">>> [{prob.tool}] {prob.message}")
            self.html_parts.append(f'        <div class="problem">{msg}</div>')

        self.html_parts.append("        </div>")

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

            # Add highlighted text (no LaTeX highlighting to keep it clear)
            highlight_text = html.escape(line_content[start:end])
            result.append(f'<span class="highlight">{highlight_text}</span>')
            pos = end

        # Add remaining text with LaTeX syntax highlighting
        if pos < len(line_content):
            after = html.escape(line_content[pos:])
            result.append(self._apply_latex_highlighting(after))

        return "".join(result)

    def _apply_latex_highlighting(self, content: str) -> str:
        """Apply basic LaTeX syntax highlighting."""
        # This is a simple highlighter - could be enhanced

        # Highlight comments
        content = re.sub(r"(%.*)", r'<span class="comment">\1</span>', content)

        # Highlight commands
        content = re.sub(r"(\\[a-zA-Z@]+)", r'<span class="command">\1</span>', content)

        # Highlight brackets
        return re.sub(r"([{}[\]])", r'<span class="bracket">\1</span>', content)

    def _add_orphaned_problems(self) -> None:
        """Add orphaned problems section."""
        problems = self.analysis.get_orphaned_problems()
        if not problems:
            return

        self.html_parts.append(
            '        <div class="separator">─────── Other problems ───────</div>'
        )
        for prob in problems:
            msg = html.escape(f">>> [{prob.tool}] {prob.message}")
            self.html_parts.append(f'        <div class="problem">{msg}</div>')
