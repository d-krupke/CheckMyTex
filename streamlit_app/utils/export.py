"""Export utilities for todo lists."""

from __future__ import annotations

import csv
import json
from io import StringIO
from typing import List

from models.todo_item import TodoItem


def export_todos_json(todos: List[TodoItem]) -> str:
    """
    Export todos as JSON.

    Args:
        todos: List of TodoItem objects

    Returns:
        JSON string
    """
    data = {
        "todos": [todo.to_dict() for todo in todos],
        "total": len(todos),
        "by_priority": {
            "high": sum(1 for t in todos if t.priority == "high"),
            "normal": sum(1 for t in todos if t.priority == "normal"),
            "low": sum(1 for t in todos if t.priority == "low"),
        },
        "by_status": {
            "pending": sum(1 for t in todos if t.status == "pending"),
            "in_progress": sum(1 for t in todos if t.status == "in_progress"),
            "completed": sum(1 for t in todos if t.status == "completed"),
            "skipped": sum(1 for t in todos if t.status == "skipped"),
        },
    }
    return json.dumps(data, indent=2)


def export_todos_csv(todos: List[TodoItem]) -> str:
    """
    Export todos as CSV.

    Args:
        todos: List of TodoItem objects

    Returns:
        CSV string
    """
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "file",
            "line",
            "tool",
            "rule",
            "priority",
            "status",
            "message",
            "comment",
            "context",
        ],
    )

    writer.writeheader()
    for todo in todos:
        writer.writerow(
            {
                "file": todo.file_path,
                "line": todo.line_number,
                "tool": todo.tool,
                "rule": todo.rule,
                "priority": todo.priority,
                "status": todo.status,
                "message": todo.message,
                "comment": todo.comment,
                "context": todo.context[:100] + "..." if len(todo.context) > 100 else todo.context,
            }
        )

    return output.getvalue()


def export_todos_markdown(todos: List[TodoItem]) -> str:
    """
    Export todos as Markdown.

    Args:
        todos: List of TodoItem objects

    Returns:
        Markdown string
    """
    lines = [
        "# CheckMyTex Todo List",
        "",
        f"**Total Items:** {len(todos)}",
        "",
        "## Summary",
        "",
        "**By Priority:**",
        f"- High: {sum(1 for t in todos if t.priority == 'high')}",
        f"- Normal: {sum(1 for t in todos if t.priority == 'normal')}",
        f"- Low: {sum(1 for t in todos if t.priority == 'low')}",
        "",
        "**By Status:**",
        f"- Pending: {sum(1 for t in todos if t.status == 'pending')}",
        f"- In Progress: {sum(1 for t in todos if t.status == 'in_progress')}",
        f"- Completed: {sum(1 for t in todos if t.status == 'completed')}",
        f"- Skipped: {sum(1 for t in todos if t.status == 'skipped')}",
        "",
        "---",
        "",
        "## Todo Items",
        "",
    ]

    # Group by file
    files = {}
    for todo in todos:
        if todo.file_path not in files:
            files[todo.file_path] = []
        files[todo.file_path].append(todo)

    for file_path, file_todos in sorted(files.items()):
        lines.append(f"## File: `{file_path}`")
        lines.append("")

        for todo in sorted(file_todos, key=lambda t: t.line_number):
            lines.append(todo.to_markdown())

    return "\n".join(lines)


def export_todos(todos: List[TodoItem], format: str = "json") -> str:
    """
    Export todos in the specified format.

    Args:
        todos: List of TodoItem objects
        format: Export format ('json', 'csv', or 'markdown')

    Returns:
        Exported string

    Raises:
        ValueError: If format is not supported
    """
    if format == "json":
        return export_todos_json(todos)
    elif format == "csv":
        return export_todos_csv(todos)
    elif format == "markdown":
        return export_todos_markdown(todos)
    else:
        raise ValueError(f"Unsupported export format: {format}")
