"""Problem viewer component with clean Streamlit-native design."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import pandas as pd
import streamlit as st
from checkmytex import AnalyzedDocument
from checkmytex.finding import Problem

from models.todo_item import TodoItem


def render_problem_viewer(analyzed_document: AnalyzedDocument) -> None:
    """
    Render the problem viewer with clean Streamlit-native components.

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

    # Overview section
    st.subheader("📊 Overview")

    # Create summary tables
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Problems by File**")
        file_counts = {}
        for filename in analyzed_document.list_files():
            file_counts[filename] = len(analyzed_document.get_problems(filename))

        if file_counts:
            df_files = pd.DataFrame(
                [(file, count) for file, count in sorted(file_counts.items(), key=lambda x: -x[1])],
                columns=["File", "Problems"]
            )
            st.dataframe(df_files, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Problems by Type**")
        problem_counts = defaultdict(int)
        for prob in problems:
            problem_counts[f"{prob.tool}: {prob.rule}"] += 1

        if problem_counts:
            df_types = pd.DataFrame(
                [(type_name, count) for type_name, count in sorted(problem_counts.items(), key=lambda x: -x[1])[:10]],
                columns=["Type", "Count"]
            )
            st.dataframe(df_types, use_container_width=True, hide_index=True)

    st.divider()

    # Filters
    with st.expander("🔧 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            show_skipped = st.checkbox("Show skipped", value=False)
        with col2:
            show_whitelisted = st.checkbox("Show whitelisted", value=False)
        with col3:
            show_in_todos = st.checkbox("Show items in todo list", value=True)

    # Group problems by file and line
    st.subheader("📝 Problems by File")

    for filename in sorted(analyzed_document.list_files()):
        file_problems = analyzed_document.get_problems(filename)

        # Filter problems based on user preferences
        filtered_problems = _filter_problems(
            file_problems, show_skipped, show_whitelisted, show_in_todos
        )

        if not filtered_problems:
            continue

        # Display file header with expandable section
        with st.expander(f"📄 **{filename}** ({len(filtered_problems)} problems)", expanded=True):
            _render_file_problems(filename, filtered_problems, analyzed_document)


def _filter_problems(
    problems: List[Problem],
    show_skipped: bool,
    show_whitelisted: bool,
    show_in_todos: bool
) -> List[Problem]:
    """Filter problems based on user preferences."""
    filtered = []
    for problem in problems:
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

        filtered.append(problem)

    return filtered


def _render_file_problems(
    filename: str,
    problems: List[Problem],
    analyzed_document: AnalyzedDocument
) -> None:
    """Render problems for a single file."""

    # Group by line number
    problems_by_line = defaultdict(list)
    for problem in problems:
        line_num = problem.origin.get_file_line() if problem.origin else 0
        problems_by_line[line_num].append(problem)

    # Render each line group
    for line_num in sorted(problems_by_line.keys()):
        line_problems = problems_by_line[line_num]

        # Show source code context
        st.markdown(f"**Line {line_num}**")

        # Get context lines
        try:
            context_lines = []
            for offset in range(-2, 3):
                line_content = analyzed_document.document.get_file_content(filename, line_num + offset)
                if line_content:
                    prefix = "➤ " if offset == 0 else "  "
                    context_lines.append(f"{prefix}{line_num + offset:4d} | {line_content.rstrip()}")

            if context_lines:
                st.code("\n".join(context_lines), language="latex", line_numbers=False)
        except Exception:
            pass

        # Show each problem on this line
        for idx, problem in enumerate(line_problems):
            _render_problem_card(problem, f"{filename}_{line_num}_{idx}", analyzed_document)

        st.markdown("---")


def _get_severity_color(tool: str, rule: str) -> str:
    """Determine severity color based on tool and rule."""
    tool_lower = tool.lower()
    if "spell" in tool_lower:
        return "🔴"  # Red for spelling
    elif "grammar" in tool_lower or "language" in tool_lower:
        return "🟠"  # Orange for grammar
    elif "chktex" in tool_lower:
        return "🟡"  # Yellow for LaTeX
    elif "style" in tool_lower or "proselint" in tool_lower:
        return "🔵"  # Blue for style
    else:
        return "⚪"  # White for others


def _render_problem_card(
    problem: Problem,
    key_suffix: str,
    analyzed_document: AnalyzedDocument
) -> None:
    """Render a single problem as a card with action buttons."""
    problem_id = problem.short_id

    # Check status
    is_skipped = problem_id in st.session_state.skipped_problems
    is_whitelisted = problem_id in st.session_state.whitelisted_problems
    is_in_todos = any(t.problem_id == problem_id for t in st.session_state.todos)

    # Container for the problem
    with st.container():
        # Header with severity indicator
        severity = _get_severity_color(problem.tool, problem.rule)
        status_badge = ""
        if is_in_todos:
            status_badge = " `📋 In Todo`"
        elif is_skipped:
            status_badge = " `⏭️ Skipped`"
        elif is_whitelisted:
            status_badge = " `✅ Whitelisted`"

        st.markdown(
            f"{severity} **{problem.tool}** · `{problem.rule}`{status_badge}"
        )

        # Message
        st.markdown(problem.message)

        # Action buttons in compact layout
        col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1, 1, 1.5, 1, 1])

        with col1:
            if st.button(
                "📋 Add to Todo",
                key=f"todo_{problem_id}_{key_suffix}",
                disabled=is_in_todos,
                use_container_width=True
            ):
                _add_to_todo(problem)

        with col2:
            if st.button(
                "Skip",
                key=f"skip_{problem_id}_{key_suffix}",
                disabled=is_skipped,
                use_container_width=True
            ):
                st.session_state.skipped_problems.add(problem_id)
                st.rerun()

        with col3:
            if st.button(
                "Whitelist",
                key=f"whitelist_{problem_id}_{key_suffix}",
                disabled=is_whitelisted,
                use_container_width=True
            ):
                st.session_state.whitelisted_problems.add(problem_id)
                analyzed_document.mark_as_false_positive(problem)
                st.rerun()

        with col4:
            if st.button(
                "🚫 Ignore Rule",
                key=f"ignore_{problem_id}_{key_suffix}",
                use_container_width=True
            ):
                ignored_count = analyzed_document.remove_with_rule(problem.rule, problem.tool)
                st.success(f"Ignored {ignored_count} problems")
                st.rerun()

        with col5:
            if problem.look_up_url:
                st.link_button(
                    "🔍 Info",
                    problem.look_up_url,
                    use_container_width=True
                )


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
    st.rerun()
