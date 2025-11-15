"""TodoItem dataclass for managing problems that need fixing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TodoItem:
    """A todo item representing a problem that needs to be addressed."""

    # Problem identification
    problem_id: str
    tool: str
    rule: str
    message: str

    # Location information
    file_path: str
    line_number: int
    context: str

    # User annotations
    comment: str = ""
    priority: str = "normal"  # low, normal, high
    status: str = "pending"  # pending, in_progress, completed, skipped

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Original problem data (for reference)
    origin_data: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return {
            "id": self.problem_id,
            "tool": self.tool,
            "rule": self.rule,
            "message": self.message,
            "file": self.file_path,
            "line": self.line_number,
            "context": self.context,
            "comment": self.comment,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        lines = [
            f"### {self.file_path}:{self.line_number}",
            f"**Tool:** {self.tool} | **Rule:** {self.rule} | **Priority:** {self.priority}",
            "",
            f"**Message:** {self.message}",
            "",
            "**Context:**",
            f"```",
            self.context,
            f"```",
        ]

        if self.comment:
            lines.extend(["", f"**Note:** {self.comment}"])

        lines.extend(["", "---", ""])
        return "\n".join(lines)

    def update_comment(self, comment: str) -> None:
        """Update the comment and timestamp."""
        self.comment = comment
        self.updated_at = datetime.now()

    def update_priority(self, priority: str) -> None:
        """Update the priority and timestamp."""
        if priority not in ("low", "normal", "high"):
            raise ValueError(f"Invalid priority: {priority}")
        self.priority = priority
        self.updated_at = datetime.now()

    def update_status(self, status: str) -> None:
        """Update the status and timestamp."""
        if status not in ("pending", "in_progress", "completed", "skipped"):
            raise ValueError(f"Invalid status: {status}")
        self.status = status
        self.updated_at = datetime.now()
