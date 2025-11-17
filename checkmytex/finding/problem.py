from __future__ import annotations

import hashlib
from typing import Any

from checkmytex.latex_document import Origin


class Problem:
    """
    A container for a problem.
    """

    def __init__(
        self,
        origin: Origin,
        message: str,
        context: str,
        long_id: str,
        tool: str,
        rule: str,
        look_up_url: str | None = None,
    ):
        self.short_id = str(hashlib.md5((tool + long_id).encode()).hexdigest())
        self.long_id = long_id
        self.tool = tool
        self.origin = origin
        self.message = message
        self.context = context
        self.rule = rule
        self.look_up_url = look_up_url

    def __repr__(self):
        return f"Problem[{self.tool}:{self.short_id}: {self.message} :{self.origin}]"

    def __eq__(self, other):
        return other.short_id == self.short_id

    def __hash__(self):
        return hash(self.short_id)

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.short_id,
            "tool": self.tool,
            "message": self.message,
            "context": self.context,
            "rule": self.rule,
            "origin": self.origin.serialize() if self.origin else None,
            "url": self.look_up_url,
        }
