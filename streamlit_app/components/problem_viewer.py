"""Problem viewer component recreating the beautiful CLI experience."""

from __future__ import annotations

from collections import defaultdict
from typing import List

import streamlit as st
from checkmytex import AnalyzedDocument
from checkmytex.finding import Problem
from rich.console import Console
from rich.markup import escape
from rich.syntax import Syntax
from rich.table import Table

from models.todo_item import TodoItem


def render_problem_viewer(analyzed_document: AnalyzedDocument) -> None:
    """
    Render the problem viewer with CLI-like Rich formatting.

    Args:
        analyzed_document: The analyzed LaTeX document
    """
    problems = analyzed_document.problems

    if not problems:
        st.success("🎉 No problems found! Your document looks great!")
        return

    # Initialize session state
    if "todos" not in st.session_state:
        st.session_state.todos = []
    if "skipped_problems" not in st.session_state:
        st.session_state.skipped_problems = set()
    if "whitelisted_problems" not in st.session_state:
        st.session_state.whitelisted_problems = set()
    if "current_problem_index" not in st.session_state:
        st.session_state.current_problem_index = 0

    # Filter active problems
    active_problems = _get_active_problems(problems)

    if not active_problems:
        st.success("✅ All problems reviewed!")
        _show_summary(problems)
        return

    # Show current problem index and navigation
    idx = st.session_state.current_problem_index
    if idx >= len(active_problems):
        idx = 0
        st.session_state.current_problem_index = 0

    current_problem = active_problems[idx]

    # Navigation header
    _render_navigation_header(idx, len(active_problems))

    st.divider()

    # Render the current problem beautifully using Rich
    _render_problem_with_rich(current_problem, analyzed_document)

    st.divider()

    # Action buttons
    _render_action_buttons(current_problem, analyzed_document, idx, len(active_problems))


def _get_active_problems(problems: List[Problem]) -> List[Problem]:
    """Get problems that haven't been skipped or whitelisted."""
    active = []
    for problem in problems:
        problem_id = problem.short_id
        if problem_id not in st.session_state.skipped_problems and \
           problem_id not in st.session_state.whitelisted_problems:
            active.append(problem)
    return active


def _render_navigation_header(idx: int, total: int):
    """Render the navigation header."""
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("⬅️ Previous", disabled=(idx == 0), use_container_width=True):
            st.session_state.current_problem_index = max(0, idx - 1)
            st.rerun()

    with col2:
        progress = (idx + 1) / total if total > 0 else 0
        st.progress(progress, text=f"Problem {idx + 1} of {total}")

    with col3:
        if st.button("Next ➡️", disabled=(idx >= total - 1), use_container_width=True, type="primary"):
            st.session_state.current_problem_index = min(total - 1, idx + 1)
            st.rerun()


def _render_problem_with_rich(problem: Problem, analyzed_document: AnalyzedDocument):
    """Render a problem using Rich for beautiful CLI-like output."""

    # Get file and line info
    if problem.origin:
        filename = problem.origin.get_file()
        line_num = problem.origin.get_file_line()
    else:
        filename = "Unknown"
        line_num = 0

    # Create Rich console - use wider console for better display
    console = Console(record=True, width=120, force_terminal=True, force_interactive=False)

    # Print file header
    console.rule(f"[bold]{filename}[/bold]", style="blue")
    console.print()

    # Print source code with highlighting
    if problem.origin:
        try:
            # Get context (±5 lines)
            context_lines = []
            for offset in range(-5, 6):
                try:
                    line_content = analyzed_document.document.get_file_content(filename, line_num + offset)
                    if line_content is not None:
                        context_lines.append(line_content.rstrip())
                except:
                    pass

            if context_lines:
                source_text = "\n".join(context_lines)
                start_line = max(1, line_num - 5)

                # Get character offsets for highlighting
                highlights = []
                if problem.origin:
                    try:
                        line_offset = problem.origin.begin.file.position.line_offset
                        end_offset = problem.origin.end.file.position.line_offset
                        # Highlight the specific range on the problem line
                        highlights = [(line_num, line_offset, end_offset)]
                    except:
                        pass

                syntax = Syntax(
                    source_text,
                    "latex",
                    line_numbers=True,
                    start_line=start_line,
                    highlight_lines={line_num},
                    theme="monokai",
                    word_wrap=True,
                )

                # Apply character-level highlighting if we have it
                for hl_line, hl_start, hl_end in highlights:
                    try:
                        relative_line = hl_line - start_line + 1
                        syntax.stylize_range("bold red on white", (relative_line, hl_start), (relative_line, hl_end))
                    except:
                        pass

                console.print(syntax)
                console.print()
        except Exception as e:
            console.print(f"[red]Error loading source: {e}[/red]")
            console.print()

    # Print problem details
    console.print(
        f"[white on red]>>> [{escape(problem.tool)}] {escape(problem.message)}[/white on red]"
    )
    console.print()

    # Print metadata table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Tool", escape(problem.tool))
    table.add_row("Rule", escape(problem.rule))
    table.add_row("File", escape(filename))
    table.add_row("Line", str(line_num))

    if problem.look_up_url:
        table.add_row("Info", escape(problem.look_up_url))

    console.print(table)

    # Export to HTML
    html_output = console.export_html(inline_styles=True)

    # Wrap in complete HTML document with dark body to eliminate white box
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            html, body {{
                background-color: #1e1e1e;
                margin: 0;
                padding: 0;
            }}
            .rich-terminal {{
                background-color: #1e1e1e;
                padding: 1.5rem;
                border-radius: 8px;
                font-family: 'Monaco', 'Menlo', 'Courier New', 'Consolas', monospace;
                overflow-x: auto;
            }}
            .rich-terminal pre {{
                background-color: transparent !important;
            }}
        </style>
    </head>
    <body>
        <div class="rich-terminal">
            {html_output}
        </div>
    </body>
    </html>
    """

    st.components.v1.html(full_html, height=700, scrolling=False)


def _render_action_buttons(problem: Problem, analyzed_document: AnalyzedDocument, idx: int, total: int):
    """Render action buttons for the current problem."""
    problem_id = problem.short_id
    is_in_todos = any(t.problem_id == problem_id for t in st.session_state.todos)

    st.markdown("### ⚡ What would you like to do?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "📋 Add to Todo List",
            key=f"todo_{idx}",
            disabled=is_in_todos,
            use_container_width=True,
            type="primary"
        ):
            _add_to_todo(problem)
            _next_problem(idx, total)

        if st.button(
            "✅ Whitelist (False Positive)",
            key=f"whitelist_{idx}",
            use_container_width=True,
            help="Mark this as a false positive - won't show again"
        ):
            st.session_state.whitelisted_problems.add(problem_id)
            analyzed_document.mark_as_false_positive(problem)
            st.toast("✅ Whitelisted!", icon="✅")
            _next_problem(idx, total)

    with col2:
        if st.button(
            "⏭️ Skip for Now",
            key=f"skip_{idx}",
            use_container_width=True,
            help="Skip this problem - you can come back to it later"
        ):
            st.session_state.skipped_problems.add(problem_id)
            st.toast("⏭️ Skipped", icon="⏭️")
            _next_problem(idx, total)

        if st.button(
            "🚫 Ignore All of This Rule",
            key=f"ignore_{idx}",
            use_container_width=True,
            help=f"Ignore all {problem.rule} problems"
        ):
            # Mark all problems with this rule as skipped
            for prob in analyzed_document.problems:
                if prob.rule == problem.rule and prob.tool == problem.tool:
                    st.session_state.skipped_problems.add(prob.short_id)
            st.toast(f"🚫 Ignored all '{problem.rule}' problems", icon="🚫")
            _next_problem(idx, total)

    if is_in_todos:
        st.info("📋 This problem is already in your todo list")

    # Show lookup link prominently if available
    if problem.look_up_url:
        st.markdown(f"[🔍 Learn more about this rule]({problem.look_up_url})")


def _next_problem(current_idx: int, total: int):
    """Move to the next problem."""
    new_idx = current_idx + 1
    if new_idx >= total:
        # All done!
        st.session_state.current_problem_index = 0
        st.balloons()
    else:
        st.session_state.current_problem_index = new_idx
    st.rerun()


def _show_summary(all_problems: List[Problem]):
    """Show summary when all problems are reviewed."""
    console = Console(record=True, width=100, force_terminal=True)

    # Summary table
    table = Table(title="Review Summary", show_header=True)
    table.add_column("Category", style="cyan", justify="left")
    table.add_column("Count", style="magenta", justify="right")

    table.add_row("Total Problems", str(len(all_problems)))
    table.add_row("Added to Todo", str(len(st.session_state.todos)))
    table.add_row("Whitelisted", str(len(st.session_state.whitelisted_problems)))
    table.add_row("Skipped", str(len(st.session_state.skipped_problems)))

    console.print(table)

    # Export and display with dark styling
    html_output = console.export_html(inline_styles=True)

    # Wrap in complete HTML document with dark body
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            html, body {{
                background-color: #1e1e1e;
                margin: 0;
                padding: 0;
            }}
            .rich-terminal {{
                background-color: #1e1e1e;
                padding: 1.5rem;
                border-radius: 8px;
                font-family: 'Monaco', 'Menlo', 'Courier New', 'Consolas', monospace;
            }}
            .rich-terminal pre {{
                background-color: transparent !important;
            }}
        </style>
    </head>
    <body>
        <div class="rich-terminal">
            {html_output}
        </div>
    </body>
    </html>
    """

    st.components.v1.html(full_html, height=300, scrolling=False)


def _add_to_todo(problem: Problem) -> None:
    """Add a problem to the todo list."""
    problem_id = problem.short_id

    todo = TodoItem(
        problem_id=problem_id,
        tool=problem.tool,
        rule=problem.rule,
        message=problem.message,
        file_path=problem.origin.get_file() if problem.origin else "Unknown",
        line_number=problem.origin.get_file_line() if problem.origin else 0,
        context=problem.context,
        comment="",
        priority="normal",
        status="pending",
        origin_data=problem.serialize(),
    )

    st.session_state.todos.append(todo)
    st.toast("✅ Added to todo list!", icon="✅")
