"""
Wrapping chktex (LaTeX linter, part of LaTeX distribution).
https://www.nongnu.org/chktex/
"""

import re
import shutil
import typing

from checkmytex.latex_document import LatexDocument

from .abstract_checker import Checker
from .problem import Problem


def _extract_problem(match: re.Match, document: LatexDocument) -> Problem:
    row = int(match.group("row"))
    if row < 1:
        msg = f"Invalid row number: {row}. Rows should start at 1."
        raise ValueError(msg)
    col = int(match.group("col"))
    if col < 1:
        msg = f"Invalid column number: {col}. Columns should start at 1."
        raise ValueError(msg)
    # length = int(match.group("length"))
    message = match.group("message")
    message_type = match.group("type")
    context_before = match.group("context_before")
    text = match.group("text")
    context_after = match.group("context_after")
    begin = (row - 1, col - 1)
    end = (row - 1, col + max(len(text), 1) - 1)
    origin = document.get_simplified_origin_of_source(begin, end)

    longid = message + "|" + context_before + text + context_after
    return Problem(
        origin=origin,
        tool="chktex",
        long_id=longid,
        context=context_before + text + context_after,
        message=f"{message_type}: {message}",
        rule=f"{message_type}: {message}",
    )


class ChkTex(Checker):
    """
    A checker module for chktex.
    """

    _format_str = (
        '{input="%f",'
        " row=%l,"
        " col=%c,"
        " length=%d,"
        " id=%n,"
        ' type="%k",'
        ' message="%m",'
        ' context_before="%r",'
        ' text="%s",'
        ' context_after="%t"}\n'
    )

    _regex = (
        r"{input=\"(?P<input>.*)\","
        r" row=(?P<row>.*),"
        r" col=(?P<col>.*),"
        r" length=(?P<length>.*),"
        r" id=(?P<id>.*),"
        r" type=\"(?P<type>.*)\","
        r" message=\"(?P<message>.*)\","
        r" context_before=\"(?P<context_before>.*)\","
        r" text=\"(?P<text>.*)\","
        r" context_after=\"(?P<context_after>.*)\"}$"
    )

    def __init__(self):
        super().__init__()
        self._parser = re.compile(self._regex)

    @staticmethod
    def _is_informational_message(stderr: str) -> bool:
        """Check if stderr contains only informational messages, not actual errors."""
        # ChkTeX writes summary statistics and help text to stderr
        # These are not errors and should be filtered out
        informational_patterns = [
            "No errors printed",
            "warnings printed",
            "user suppressed warnings",
            "line suppressed warnings",
            "See the manual",
            "The manual is available",
            "texdoc chktex",
        ]
        return any(pattern in stderr for pattern in informational_patterns)

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        self.log("Running chktex...")
        result, err, _exitcode = self._run(
            f"chktex -q -f '{self._format_str}'", str(document.get_source())
        )
        # Filter out informational messages from stderr
        # ChkTeX writes summary statistics to stderr which are not errors
        if err and not self._is_informational_message(err):
            self.log(f"chktex returned an error: '{err}'")
        results = result.split("\n")
        for result in results:
            parsed = self._parser.fullmatch(result)
            if parsed:
                yield _extract_problem(parsed, document)

    def is_available(self) -> bool:
        return bool(shutil.which("chktex"))

    def needs_detex(self):
        return False

    def installation_guide(self) -> str:
        return "chktex should come with most latex distributions."
