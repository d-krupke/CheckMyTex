"""Problem viewer component using Rich HTML output with Streamlit actions."""

from __future__ import annotations

import io
from typing import List

import streamlit as st
from checkmytex import AnalyzedDocument
from checkmytex.cli.rich_printer import RichPrinter
from checkmytex.finding import Problem
from rich.console import Console

from models.todo_item import TodoItem


def render_problem_viewer(analyzed_document: AnalyzedDocument) -> None:
    """
    Render the problem viewer using Rich HTML with interactive Streamlit buttons.

    Args:
        analyzed_document: The analyzed LaTeX document
    """
    st.header("🔍 Problems Found")

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

    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Problems", len(problems))
    with col2:
        st.metric("In Todo List", len(st.session_state.todos))
    with col3:
        st.metric("Skipped", len(st.session_state.skipped_problems))
    with col4:
        st.metric("Whitelisted", len(st.session_state.whitelisted_problems))

    # Filters
    st.subheader("🔧 Filters")
    col1, col2, col3 = st.columns(3)

    with col1:
        show_skipped = st.checkbox("Show skipped", value=False)
    with col2:
        show_whitelisted = st.checkbox("Show whitelisted", value=False)
    with col3:
        show_in_todos = st.checkbox("Show items in todo list", value=True)

    # Generate Rich HTML overview sections
    console = Console(record=True, width=120)
    printer = RichPrinter(analyzed_document, shorten=5, console=console)

    # Print overview sections
    printer.print_file_overview()
    printer.print_rule_count()

    # Get HTML for overview
    html_output = console.export_html(inline_styles=True)
    st.components.v1.html(html_output, height=400, scrolling=True)

    st.divider()

    # Display problems by file with action buttons
    for filename in analyzed_document.list_files():
        file_problems = analyzed_document.get_problems(filename)

        with st.expander(f"📄 {filename} ({len(file_problems)} problems)", expanded=True):
            # Render source code with Rich
            _render_file_with_actions(filename, file_problems, analyzed_document, show_skipped, show_whitelisted, show_in_todos)

    # Handle orphaned problems
    orphaned = analyzed_document.get_orphaned_problems()
    if orphaned:
        with st.expander(f"⚠️ Other Problems ({len(orphaned)} problems)", expanded=False):
            for idx, problem in enumerate(orphaned):
                _render_problem_with_actions(problem, idx, analyzed_document, show_skipped, show_whitelisted, show_in_todos)


def _render_file_with_actions(
    filename: str,
    problems: List[Problem],
    analyzed_document: AnalyzedDocument,
    show_skipped: bool,
    show_whitelisted: bool,
    show_in_todos: bool,
) -> None:
    """Render a file's problems with Rich formatting and Streamlit actions."""

    # Group problems by line
    problems_by_line = {}
    for problem in problems:
        line_num = problem.origin.get_file_line() if problem.origin else 0
        if line_num not in problems_by_line:
            problems_by_line[line_num] = []
        problems_by_line[line_num].append(problem)

    # Render each line group
    for line_num in sorted(problems_by_line.keys()):
        line_problems = problems_by_line[line_num]

        # Check if any problem should be shown
        should_show_any = False
        for problem in line_problems:
            problem_id = problem.short_id
            is_skipped = problem_id in st.session_state.skipped_problems
            is_whitelisted = problem_id in st.session_state.whitelisted_problems
            is_in_todos = any(t.problem_id == problem_id for t in st.session_state.todos)

            if is_skipped and not show_skipped:
                continue
            if is_whitelisted and not show_whitelisted:
                continue
            if is_in_todos and not show_in_todos:
                continue
            should_show_any = True
            break

        if not should_show_any:
            continue

        # Create a mini console for this section
        console = Console(record=True, width=100)
        printer = RichPrinter(analyzed_document, shorten=2, console=console, problem_handler=None)

        # Print the source code context for this line
        highlights = [
            (
                prob.origin.get_file_line(),
                prob.origin.begin.file.position.line_offset,
                prob.origin.end.file.position.line_offset,
            )
            for prob in line_problems
            if prob.origin
        ]

        begin_line = max(0, line_num - 2)
        end_line = line_num + 1
        printer.print_source(filename, begin_line, end_line, highlights)

        # Display the Rich HTML
        html_output = console.export_html(inline_styles=True)
        st.components.v1.html(html_output, height=150, scrolling=False)

        # Add action buttons for each problem on this line
        for idx, problem in enumerate(line_problems):
            _render_problem_with_actions(problem, idx + line_num * 1000, analyzed_document, show_skipped, show_whitelisted, show_in_todos)

        st.divider()


def _render_problem_with_actions(
    problem: Problem,
    idx: int,
    analyzed_document: AnalyzedDocument,
    show_skipped: bool,
    show_whitelisted: bool,
    show_in_todos: bool,
) -> None:
    """Render a problem message with action buttons."""
    problem_id = problem.short_id

    # Check if we should show this problem
    is_skipped = problem_id in st.session_state.skipped_problems
    is_whitelisted = problem_id in st.session_state.whitelisted_problems
    is_in_todos = any(t.problem_id == problem_id for t in st.session_state.todos)

    if is_skipped and not show_skipped:
        return
    if is_whitelisted and not show_whitelisted:
        return
    if is_in_todos and not show_in_todos:
        return

    # Render problem message using Rich
    console = Console(record=True, width=100)
    printer = RichPrinter(analyzed_document, console=console, problem_handler=None)
    printer.print_problem(problem)

    # Display the Rich HTML
    html_output = console.export_html(inline_styles=True)
    st.components.v1.html(html_output, height=60, scrolling=False)

    # Status badge
    if is_in_todos:
        st.caption("📋 In Todo List")
    elif is_skipped:
        st.caption("⏭️ Skipped")
    elif is_whitelisted:
        st.caption("✅ Whitelisted")

    # Action buttons
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

    with col1:
        if st.button("📋 Add to Todo", key=f"todo_{problem_id}_{idx}", disabled=is_in_todos):
            _add_to_todo(problem, analyzed_document)

    with col2:
        if st.button("⏭️ Skip", key=f"skip_{problem_id}_{idx}", disabled=is_skipped):
            st.session_state.skipped_problems.add(problem_id)
            st.rerun()

    with col3:
        if st.button("✅ Whitelist", key=f"whitelist_{problem_id}_{idx}", disabled=is_whitelisted):
            st.session_state.whitelisted_problems.add(problem_id)
            analyzed_document.mark_as_false_positive(problem)
            st.rerun()

    with col4:
        if st.button("🚫 Ignore Rule", key=f"ignore_{problem_id}_{idx}"):
            ignored_count = analyzed_document.remove_with_rule(problem.rule, problem.tool)
            st.success(f"Ignored {ignored_count} problems with rule {problem.rule}")
            st.rerun()

    with col5:
        if problem.look_up_url:
            st.markdown(f"[🔍 Lookup]({problem.look_up_url})")


def _add_to_todo(problem: Problem, analyzed_document: AnalyzedDocument) -> None:
    """Add a problem to the todo list."""
    problem_id = problem.short_id

    # Create todo item
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
    st.success("✅ Added to todo list!")
    st.rerun()
