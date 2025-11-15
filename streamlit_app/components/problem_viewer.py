"""Problem viewer component for displaying CheckMyTex problems."""

from __future__ import annotations

from typing import List

import streamlit as st
from checkmytex import AnalyzedDocument
from checkmytex.finding import Problem

from models.todo_item import TodoItem


def _get_priority_emoji(priority: str) -> str:
    """Get emoji for priority level."""
    return {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(priority, "⚪")


def _get_tool_emoji(tool: str) -> str:
    """Get emoji for tool."""
    tool_lower = tool.lower()
    if "spell" in tool_lower:
        return "📝"
    elif "grammar" in tool_lower or "language" in tool_lower:
        return "✍️"
    elif "chktex" in tool_lower:
        return "🔧"
    elif "style" in tool_lower or "proselint" in tool_lower:
        return "🎨"
    else:
        return "⚙️"


def render_problem_viewer(analyzed_document: AnalyzedDocument) -> None:
    """
    Render the problem viewer with interactive action buttons.

    Args:
        analyzed_document: The analyzed LaTeX document
    """
    st.header("🔍 Problems Found")

    problems = analyzed_document.problems

    if not problems:
        st.success("🎉 No problems found! Your document looks great!")
        return

    # Initialize session state for todos if not exists
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

    # Group problems by file
    files = {}
    for problem in problems:
        file_path = problem.origin.get_file() if problem.origin else "Unknown"
        if file_path not in files:
            files[file_path] = []
        files[file_path].append(problem)

    # Display problems by file
    for file_path in sorted(files.keys()):
        file_problems = files[file_path]

        with st.expander(f"📄 {file_path} ({len(file_problems)} problems)", expanded=True):
            for idx, problem in enumerate(file_problems):
                problem_id = problem.short_id

                # Check if we should show this problem
                is_skipped = problem_id in st.session_state.skipped_problems
                is_whitelisted = problem_id in st.session_state.whitelisted_problems
                is_in_todos = any(t.problem_id == problem_id for t in st.session_state.todos)

                if is_skipped and not show_skipped:
                    continue
                if is_whitelisted and not show_whitelisted:
                    continue
                if is_in_todos and not show_in_todos:
                    continue

                # Render problem card
                _render_problem_card(problem, idx, analyzed_document)


def _render_problem_card(problem: Problem, idx: int, analyzed_document: AnalyzedDocument) -> None:
    """Render an individual problem card with action buttons."""
    problem_id = problem.short_id

    # Determine status
    is_skipped = problem_id in st.session_state.skipped_problems
    is_whitelisted = problem_id in st.session_state.whitelisted_problems
    is_in_todos = any(t.problem_id == problem_id for t in st.session_state.todos)

    # Status badge
    status_text = ""
    if is_in_todos:
        status_text = "📋 In Todo List"
    elif is_skipped:
        status_text = "⏭️ Skipped"
    elif is_whitelisted:
        status_text = "✅ Whitelisted"

    # Card container
    with st.container():
        # Header
        col1, col2 = st.columns([4, 1])
        with col1:
            tool_emoji = _get_tool_emoji(problem.tool)
            st.markdown(
                f"**{tool_emoji} {problem.tool}** | Rule: `{problem.rule}` | "
                f"Line: `{problem.origin.get_file_line() if problem.origin else 'N/A'}`"
            )
        with col2:
            if status_text:
                st.markdown(f"*{status_text}*")

        # Message
        st.markdown(f"**Message:** {problem.message}")

        # Context
        if problem.context:
            with st.expander("📝 Context"):
                st.code(problem.context, language="latex")

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

        st.divider()


def _add_to_todo(problem: Problem, analyzed_document: AnalyzedDocument) -> None:
    """Add a problem to the todo list with a comment dialog."""
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
    st.success(f"✅ Added to todo list!")
    st.rerun()
