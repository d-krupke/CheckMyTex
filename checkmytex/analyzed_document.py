"""
Provides a container for an analyzed document, i.e., parsed document and found errors.
"""

from __future__ import annotations

import typing
from typing import Any

from checkmytex.finding.problem import Problem
from checkmytex.latex_document import LatexDocument


class AnalyzedDocument:
    """
    An analyzed document. Contains the document and the problems found for it.
    """

    def __init__(
        self, document: LatexDocument, problems: typing.Iterable[Problem]
    ) -> None:
        self.document = document
        self.problems = list(problems)
        self._on_false_positive: typing.Callable[[Problem], None] | None = None

    def set_on_false_positive_cb(
        self, on_false_positive: typing.Callable[[Problem], None]
    ) -> None:
        """
        Set a callback for when a problem is marked as false positive. This allows
        you, e.g., to save this for later iterations.
        """
        self._on_false_positive = on_false_positive

    def mark_as_false_positive(self, problem: Problem) -> None:
        """
        Mark a problem as false positive. All occurrences of this problem will be removed.
        """
        while problem in self.problems:
            self.problems.remove(problem)
        if self._on_false_positive:
            self._on_false_positive(problem)

    def remove_if(self, func: typing.Callable[[Problem], bool]) -> int:
        """
        Remove all problems that fit a corresponding condition.
        Does not mark them as false positives.
        """
        to_remove = [p for p in self.problems if func(p)]
        for problem in to_remove:
            self.problems.remove(problem)
        return len(to_remove)

    def remove_similar(self, problem: Problem) -> int:
        """
        Removes all problems with the same ID.
        """
        return self.remove_if(lambda p: problem.long_id == p.long_id)

    def remove_with_rule(self, rule: str, tool: str | None = None) -> int:
        """
        Remove all problems that have been created by the rule.
        """
        if tool:
            return self.remove_if(lambda p: p.rule == rule and p.tool == tool)
        return self.remove_if(lambda p: p.rule == rule)

    def get_problems(
        self, file: str | None = None, line: int | None = None
    ) -> list[Problem]:
        """
        Returns problems. Can be for a specific file and even line.
        """
        if file:
            problems = [p for p in self.problems if p.origin.get_file() == file]
            if line:
                problems = [p for p in problems if p.origin.get_file_line() == line]
            return problems
        return self.problems

    def get_orphaned_problems(self) -> list[Problem]:
        return [p for p in self.problems if not p.origin]

    def list_files(self) -> typing.Iterable[str]:
        """
        List all files of the document.
        """
        yield from self.document.files()

    def get_file_content(self, file_name: str) -> str:
        """
        Returns the content of a specific file in the document.
        """
        return self.document.get_file_content(file_name)

    def serialize(self) -> dict[str, Any]:
        return {
            "document": self.document.serialize(),
            "problems": [p.serialize() for p in self.problems],
        }
