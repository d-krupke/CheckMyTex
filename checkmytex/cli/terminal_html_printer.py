"""Terminal-styled HTML printer for CheckMyTex analysis results."""

from __future__ import annotations

import html
import os.path
import typing
from collections import defaultdict

from checkmytex import AnalyzedDocument
from checkmytex.finding import Problem


class TerminalHtmlPrinter:
    """Generate terminal-styled HTML output for CheckMyTex analysis."""

    def __init__(
        self,
        analysis: AnalyzedDocument,
        shorten: typing.Optional[int] = 5,
    ):
        self.analysis = analysis
        self.shorten = shorten
        self.file_prefix = os.path.commonpath(list(self.analysis.list_files()))
        self.html_parts = []

    def to_html(self, path: str) -> None:
        """Generate and save HTML report to file."""
        self.html_parts = []
        self._generate_html()
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.html_parts))

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
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
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
            margin: 20px 0;
            text-align: center;
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
            background-color: #1e1e1e;
            margin: 15px 0;
            padding: 10px;
            overflow-x: auto;
        }

        .code-line {
            display: flex;
            white-space: pre;
        }

        .line-number {
            color: #858585;
            text-align: right;
            padding-right: 12px;
            user-select: none;
            min-width: 50px;
        }

        .line-content {
            color: #d4d4d4;
            flex: 1;
        }

        .highlight {
            background-color: #5a1e1e;
            color: #ffffff;
        }

        .problem {
            color: #f48771;
            font-weight: bold;
            margin: 8px 0 8px 62px;
            padding: 6px;
            background-color: #2d2d2d;
            border-left: 3px solid #f48771;
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
        self.html_parts.append('        <div class="section-title">Problems by file</div>')
        self.html_parts.append('        <table>')
        self.html_parts.append('            <thead>')
        self.html_parts.append('                <tr><th>File</th><th>Count</th></tr>')
        self.html_parts.append('            </thead>')
        self.html_parts.append('            <tbody>')

        for file in self.analysis.list_files():
            filename = html.escape(str(file[len(self.file_prefix):]))
            count = len(self.analysis.get_problems(file))
            self.html_parts.append(f'                <tr><td>{filename}</td><td>{count}</td></tr>')

        if self.analysis.get_orphaned_problems():
            count = len(self.analysis.get_orphaned_problems())
            self.html_parts.append(f'                <tr><td>UNKNOWN</td><td>{count}</td></tr>')

        self.html_parts.append('            </tbody>')
        self.html_parts.append('        </table>')

    def _add_rule_count(self) -> None:
        """Add table of problems by type."""
        self.html_parts.append('        <div class="section-title">Problems by type</div>')
        self.html_parts.append('        <table>')
        self.html_parts.append('            <thead>')
        self.html_parts.append('                <tr><th>Tool</th><th>Rule</th><th>Count</th></tr>')
        self.html_parts.append('            </thead>')
        self.html_parts.append('            <tbody>')

        problem_counts = defaultdict(lambda: defaultdict(lambda: 0))
        for prob in self.analysis.get_problems():
            problem_counts[prob.tool][prob.rule] += 1

        for tool, rules in problem_counts.items():
            first = True
            for rule, count in rules.items():
                tool_display = html.escape(str(tool)) if first else ''
                rule_display = html.escape(str(rule))
                self.html_parts.append(f'                <tr><td>{tool_display}</td><td>{rule_display}</td><td>{count}</td></tr>')
                first = False

        self.html_parts.append('            </tbody>')
        self.html_parts.append('        </table>')

    def _add_file_section(self, filename: str) -> None:
        """Add section for a specific file."""
        display_name = filename[len(self.file_prefix):]
        separator = '─' * 50 + ' ' + display_name + ' ' + '─' * 50
        self.html_parts.append(f'        <div class="separator">{separator}</div>')

        last_printed_line = -1
        problematic_lines = sorted({
            prob.origin.get_file_line()
            for prob in self.analysis.get_problems(filename)
        })

        for line_num in problematic_lines:
            if self.shorten is not None:
                start_line = max(last_printed_line + 1, line_num - self.shorten)
            else:
                start_line = last_printed_line + 1

            if start_line != 0 and start_line != last_printed_line + 1:
                self.html_parts.append('        <div class="ellipsis">...</div>')

            problems = self.analysis.get_problems(filename, line_num)
            self._add_code_block(filename, start_line, line_num + 1, line_num, problems)
            last_printed_line = line_num

    def _add_code_block(
        self,
        filename: str,
        start_line: int,
        end_line: int,
        highlight_line: int,
        problems: list[Problem]
    ) -> None:
        """Add a code block with line numbers."""
        self.html_parts.append('        <div class="code-block">')

        for line_idx in range(start_line, end_line):
            line_content = self.analysis.document.get_file_content(filename, line_idx)
            if line_content and line_content.endswith('\n'):
                line_content = line_content[:-1]

            escaped_content = html.escape(line_content) if line_content else ''
            highlighted_content = self._apply_latex_highlighting(escaped_content)

            if line_idx == highlight_line:
                self.html_parts.append(f'            <div class="code-line highlight">')
            else:
                self.html_parts.append(f'            <div class="code-line">')

            self.html_parts.append(f'                <span class="line-number">{line_idx}</span>')
            self.html_parts.append(f'                <span class="line-content">{highlighted_content}</span>')
            self.html_parts.append('            </div>')

        # Add problems
        for prob in problems:
            msg = html.escape(f">>> [{prob.tool}] {prob.message}")
            self.html_parts.append(f'        <div class="problem">{msg}</div>')

        self.html_parts.append('        </div>')

    def _apply_latex_highlighting(self, content: str) -> str:
        """Apply basic LaTeX syntax highlighting."""
        # This is a simple highlighter - could be enhanced
        import re

        # Highlight comments
        content = re.sub(r'(%.*)', r'<span class="comment">\1</span>', content)

        # Highlight commands
        content = re.sub(
            r'(\\[a-zA-Z@]+)',
            r'<span class="command">\1</span>',
            content
        )

        # Highlight brackets
        content = re.sub(r'([{}[\]])', r'<span class="bracket">\1</span>', content)

        return content

    def _add_orphaned_problems(self) -> None:
        """Add orphaned problems section."""
        problems = self.analysis.get_orphaned_problems()
        if not problems:
            return

        self.html_parts.append('        <div class="separator">─────── Other problems ───────</div>')
        for prob in problems:
            msg = html.escape(f">>> [{prob.tool}] {prob.message}")
            self.html_parts.append(f'        <div class="problem">{msg}</div>')
