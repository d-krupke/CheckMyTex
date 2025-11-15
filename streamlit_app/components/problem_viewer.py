"""Problem viewer component with focused one-by-one review mode."""

from __future__ import annotations

from collections import defaultdict
from typing import List

import pandas as pd
import streamlit as st
from checkmytex import AnalyzedDocument
from checkmytex.finding import Problem
from rich.console import Console
from rich.syntax import Syntax

from models.todo_item import TodoItem


def render_problem_viewer(analyzed_document: AnalyzedDocument) -> None:
    """
    Render the problem viewer with overview and focused review mode.

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
    if "review_mode" not in st.session_state:
        st.session_state.review_mode = False
    if "current_problem_index" not in st.session_state:
        st.session_state.current_problem_index = 0

    # Filter problems
    active_problems = _get_active_problems(problems)

    if not active_problems:
        st.info("✅ All problems have been reviewed! You can view skipped/whitelisted items using the filters below.")
        _render_overview(analyzed_document, problems)
        return

    # Show review mode or overview
    if st.session_state.review_mode:
        _render_review_mode(analyzed_document, active_problems)
    else:
        _render_overview_mode(analyzed_document, active_problems, problems)


def _get_active_problems(problems: List[Problem]) -> List[Problem]:
    """Get problems that haven't been skipped or whitelisted."""
    active = []
    for problem in problems:
        problem_id = problem.short_id
        if problem_id not in st.session_state.skipped_problems and \
           problem_id not in st.session_state.whitelisted_problems:
            active.append(problem)
    return active


def _render_overview_mode(analyzed_document: AnalyzedDocument, active_problems: List[Problem], all_problems: List[Problem]):
    """Render the overview mode with statistics and start review button."""

    st.subheader("📊 Overview")

    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Problems", len(all_problems))
    with col2:
        st.metric("To Review", len(active_problems))
    with col3:
        st.metric("In Todo List", len(st.session_state.todos))
    with col4:
        completed = len(st.session_state.skipped_problems) + len(st.session_state.whitelisted_problems)
        st.metric("Completed", completed)

    st.divider()

    # Summary tables
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Problems by File**")
        file_counts = {}
        for filename in analyzed_document.list_files():
            count = sum(1 for p in active_problems if p.origin and p.origin.get_file() == filename)
            if count > 0:
                file_counts[filename] = count

        if file_counts:
            df_files = pd.DataFrame(
                [(file.split('/')[-1], count) for file, count in sorted(file_counts.items(), key=lambda x: -x[1])],
                columns=["File", "Problems"]
            )
            st.dataframe(df_files, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Problems by Type**")
        problem_counts = defaultdict(int)
        for prob in active_problems:
            problem_counts[f"{prob.tool}"] += 1

        if problem_counts:
            df_types = pd.DataFrame(
                [(tool, count) for tool, count in sorted(problem_counts.items(), key=lambda x: -x[1])],
                columns=["Tool", "Count"]
            )
            st.dataframe(df_types, use_container_width=True, hide_index=True)

    st.divider()

    # Start review button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Reviewing Problems", type="primary", use_container_width=True):
            st.session_state.review_mode = True
            st.session_state.current_problem_index = 0
            st.rerun()

    # Show filters for completed items
    with st.expander("🔍 View Completed Items", expanded=False):
        show_skipped = st.checkbox("Show skipped problems", value=False)
        show_whitelisted = st.checkbox("Show whitelisted problems", value=False)

        if show_skipped or show_whitelisted:
            for problem in all_problems:
                problem_id = problem.short_id
                is_skipped = problem_id in st.session_state.skipped_problems
                is_whitelisted = problem_id in st.session_state.whitelisted_problems

                if (is_skipped and show_skipped) or (is_whitelisted and show_whitelisted):
                    status = "⏭️ Skipped" if is_skipped else "✅ Whitelisted"
                    file = problem.origin.get_file() if problem.origin else "Unknown"
                    line = problem.origin.get_file_line() if problem.origin else 0
                    st.caption(f"{status} - {file}:{line} - {problem.tool}: {problem.message}")


def _render_review_mode(analyzed_document: AnalyzedDocument, active_problems: List[Problem]):
    """Render focused one-by-one review mode."""

    idx = st.session_state.current_problem_index

    # Safety check
    if idx >= len(active_problems):
        st.session_state.review_mode = False
        st.session_state.current_problem_index = 0
        st.rerun()
        return

    current_problem = active_problems[idx]

    # Header with progress
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("⬅️ Back to Overview"):
            st.session_state.review_mode = False
            st.rerun()

    with col2:
        st.markdown(f"### Problem {idx + 1} of {len(active_problems)}")
        progress = (idx + 1) / len(active_problems)
        st.progress(progress)

    with col3:
        st.metric("Remaining", len(active_problems) - idx - 1)

    st.divider()

    # Problem details
    _render_focused_problem(current_problem, analyzed_document)

    st.divider()

    # Navigation and actions
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if idx > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.current_problem_index = idx - 1
                st.rerun()

    with col2:
        st.markdown(f"<div style='text-align: center; color: #666;'>Use the action buttons above to handle this problem</div>", unsafe_allow_html=True)

    with col3:
        if idx < len(active_problems) - 1:
            if st.button("Next ➡️", use_container_width=True, type="primary"):
                st.session_state.current_problem_index = idx + 1
                st.rerun()
        else:
            if st.button("✅ Finish", use_container_width=True, type="primary"):
                st.session_state.review_mode = False
                st.balloons()
                st.rerun()


def _render_focused_problem(problem: Problem, analyzed_document: AnalyzedDocument):
    """Render a single problem with full focus and highlighting."""

    problem_id = problem.short_id
    is_in_todos = any(t.problem_id == problem_id for t in st.session_state.todos)

    # Problem header
    severity_color = _get_severity_color(problem.tool)
    st.markdown(f"## {severity_color} {problem.tool}: {problem.rule}")

    # File and line info
    if problem.origin:
        file = problem.origin.get_file()
        line = problem.origin.get_file_line()
        st.caption(f"📄 `{file}` · Line `{line}`")

    # Message
    st.markdown(f"### 💬 {problem.message}")

    # Source code with highlighting
    st.markdown("### 📝 Source Code")

    if problem.origin:
        try:
            filename = problem.origin.get_file()
            line_num = problem.origin.get_file_line()

            # Get more context (±5 lines)
            context_lines = []
            for offset in range(-5, 6):
                try:
                    line_content = analyzed_document.document.get_file_content(filename, line_num + offset)
                    if line_content is not None:
                        context_lines.append((line_num + offset, line_content.rstrip()))
                except:
                    pass

            if context_lines:
                # Create source text with highlighting
                source_text = "\n".join([line[1] for line in context_lines])
                start_line = context_lines[0][0]

                # Use Rich for syntax highlighting
                console = Console(record=True, width=100)
                syntax = Syntax(
                    source_text,
                    "latex",
                    line_numbers=True,
                    start_line=start_line,
                    highlight_lines={line_num},
                    theme="monokai",
                )
                console.print(syntax)

                # Export to HTML
                html_output = console.export_html(inline_styles=True)
                st.components.v1.html(html_output, height=min(400, len(context_lines) * 25 + 100), scrolling=True)
        except Exception as e:
            st.error(f"Could not load source context: {e}")

    # Lookup link if available
    if problem.look_up_url:
        st.markdown(f"[🔍 Learn more about this rule]({problem.look_up_url})")

    st.divider()

    # Action buttons - large and prominent
    st.markdown("### ⚡ Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📋 Add to Todo List", key=f"todo_{problem_id}",
                    disabled=is_in_todos, use_container_width=True, type="primary"):
            _add_to_todo(problem)
            _next_problem()

        if st.button("✅ Whitelist (False Positive)", key=f"whitelist_{problem_id}",
                    use_container_width=True):
            st.session_state.whitelisted_problems.add(problem_id)
            analyzed_document.mark_as_false_positive(problem)
            st.toast("✅ Whitelisted!", icon="✅")
            _next_problem()

    with col2:
        if st.button("⏭️ Skip for Now", key=f"skip_{problem_id}",
                    use_container_width=True):
            st.session_state.skipped_problems.add(problem_id)
            st.toast("⏭️ Skipped", icon="⏭️")
            _next_problem()

        if st.button("🚫 Ignore All of This Rule", key=f"ignore_rule_{problem_id}",
                    use_container_width=True):
            ignored_count = analyzed_document.remove_with_rule(problem.rule, problem.tool)
            for prob in analyzed_document.problems:
                if prob.rule == problem.rule and prob.tool == problem.tool:
                    st.session_state.skipped_problems.add(prob.short_id)
            st.toast(f"🚫 Ignored {ignored_count} problems", icon="🚫")
            _next_problem()

    # Status indicator
    if is_in_todos:
        st.info("📋 This problem is already in your todo list")


def _next_problem():
    """Move to the next problem."""
    st.session_state.current_problem_index += 1
    st.rerun()


def _get_severity_color(tool: str) -> str:
    """Get severity emoji based on tool."""
    tool_lower = tool.lower()
    if "spell" in tool_lower:
        return "🔴"
    elif "grammar" in tool_lower or "language" in tool_lower:
        return "🟠"
    elif "chktex" in tool_lower:
        return "🟡"
    elif "style" in tool_lower or "proselint" in tool_lower:
        return "🔵"
    else:
        return "⚪"


def _render_overview(analyzed_document: AnalyzedDocument, all_problems: List[Problem]):
    """Render just the overview when all problems are handled."""
    st.subheader("📊 Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Problems", len(all_problems))
    with col2:
        st.metric("In Todo List", len(st.session_state.todos))
    with col3:
        completed = len(st.session_state.skipped_problems) + len(st.session_state.whitelisted_problems)
        st.metric("Completed", completed)


def _add_to_todo(problem: Problem) -> None:
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
    st.toast("✅ Added to todo list!", icon="✅")
