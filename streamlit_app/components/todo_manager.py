"""Todo list manager component."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from models.todo_item import TodoItem
from utils.export import export_todos


def render_todo_manager() -> None:
    """Render the todo list manager with export options."""
    st.header("📋 Todo List")

    if "todos" not in st.session_state or not st.session_state.todos:
        st.info("No items in your todo list yet. Add problems from the viewer above!")
        return

    todos: list[TodoItem] = st.session_state.todos

    # Statistics
    st.subheader("📊 Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Items", len(todos))
    with col2:
        high_priority = sum(1 for t in todos if t.priority == "high")
        st.metric("High Priority", high_priority)
    with col3:
        pending = sum(1 for t in todos if t.status == "pending")
        st.metric("Pending", pending)
    with col4:
        completed = sum(1 for t in todos if t.status == "completed")
        st.metric("Completed", completed)

    # Filter and sort options
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_priority = st.selectbox(
            "Filter by Priority", ["All", "High", "Normal", "Low"], key="filter_priority"
        )

    with col2:
        filter_status = st.selectbox(
            "Filter by Status", ["All", "Pending", "In Progress", "Completed", "Skipped"], key="filter_status"
        )

    with col3:
        sort_by = st.selectbox("Sort by", ["Priority", "File", "Line", "Created"], key="sort_by")

    # Filter todos
    filtered_todos = todos.copy()

    if filter_priority != "All":
        filtered_todos = [t for t in filtered_todos if t.priority.lower() == filter_priority.lower()]

    if filter_status != "All":
        filtered_todos = [t for t in filtered_todos if t.status.replace("_", " ").title() == filter_status]

    # Sort todos
    if sort_by == "Priority":
        priority_order = {"high": 0, "normal": 1, "low": 2}
        filtered_todos.sort(key=lambda t: priority_order.get(t.priority, 3))
    elif sort_by == "File":
        filtered_todos.sort(key=lambda t: (t.file_path, t.line_number))
    elif sort_by == "Line":
        filtered_todos.sort(key=lambda t: t.line_number)
    elif sort_by == "Created":
        filtered_todos.sort(key=lambda t: t.created_at, reverse=True)

    # Display todos
    st.subheader(f"📝 Items ({len(filtered_todos)})")

    for idx, todo in enumerate(filtered_todos):
        _render_todo_item(todo, idx)

    # Export section
    st.divider()
    st.subheader("💾 Export Todo List")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export as JSON", use_container_width=True):
            json_data = export_todos(todos, "json")
            st.download_button(
                label="⬇️ Download JSON",
                data=json_data,
                file_name=f"checkmytex_todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

    with col2:
        if st.button("📊 Export as CSV", use_container_width=True):
            csv_data = export_todos(todos, "csv")
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"checkmytex_todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    with col3:
        if st.button("📝 Export as Markdown", use_container_width=True):
            md_data = export_todos(todos, "markdown")
            st.download_button(
                label="⬇️ Download Markdown",
                data=md_data,
                file_name=f"checkmytex_todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
            )

    # Clear all button
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Clear All Todos", type="secondary"):
            st.session_state.todos = []
            st.rerun()


def _render_todo_item(todo: TodoItem, idx: int) -> None:
    """Render a single todo item with editing capabilities."""
    priority_emoji = {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(todo.priority, "⚪")
    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "skipped": "⏭️",
    }.get(todo.status, "❓")

    with st.expander(
        f"{priority_emoji} {status_emoji} **{todo.file_path}:{todo.line_number}** - {todo.tool}/{todo.rule}",
        expanded=False,
    ):
        # Message
        st.markdown(f"**Message:** {todo.message}")

        # Context
        if todo.context:
            st.code(todo.context, language="latex")

        # Edit controls
        col1, col2, col3 = st.columns(3)

        with col1:
            new_priority = st.selectbox(
                "Priority",
                ["high", "normal", "low"],
                index=["high", "normal", "low"].index(todo.priority),
                key=f"priority_{todo.problem_id}_{idx}",
            )
            if new_priority != todo.priority:
                todo.update_priority(new_priority)

        with col2:
            new_status = st.selectbox(
                "Status",
                ["pending", "in_progress", "completed", "skipped"],
                index=["pending", "in_progress", "completed", "skipped"].index(todo.status),
                key=f"status_{todo.problem_id}_{idx}",
            )
            if new_status != todo.status:
                todo.update_status(new_status)

        with col3:
            if st.button("🗑️ Remove", key=f"remove_{todo.problem_id}_{idx}"):
                st.session_state.todos = [t for t in st.session_state.todos if t.problem_id != todo.problem_id]
                st.rerun()

        # Comment
        new_comment = st.text_area(
            "Personal Note/Comment",
            value=todo.comment,
            key=f"comment_{todo.problem_id}_{idx}",
            help="Add your notes on how to fix this issue",
        )
        if new_comment != todo.comment:
            todo.update_comment(new_comment)

        # Metadata
        st.caption(f"Added: {todo.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if todo.updated_at != todo.created_at:
            st.caption(f"Updated: {todo.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
