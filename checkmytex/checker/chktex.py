import re
import shutil
import typing

from checkmytex.latex_document import LatexDocument
from .abstract_checker import Checker
from .problem import Problem


class ChkTex(Checker):
    """
    A checker module for chktex.
    """
    _format_str = "{input=\"%f\"," \
                  " row=%l," \
                  " col=%c," \
                  " length=%d," \
                  " id=%n," \
                  " type=\"%k\"," \
                  " message=\"%m\"," \
                  " context_before=\"%r\"," \
                  " text=\"%s\"," \
                  " context_after=\"%t\"}\n"

    _regex = r"{input=\"(?P<input>.*)\"," \
             r" row=(?P<row>.*)," \
             r" col=(?P<col>.*)," \
             r" length=(?P<length>.*)," \
             r" id=(?P<id>.*)," \
             r" type=\"(?P<type>.*)\"," \
             r" message=\"(?P<message>.*)\"," \
             r" context_before=\"(?P<context_before>.*)\"," \
             r" text=\"(?P<text>.*)\"," \
             r" context_after=\"(?P<context_after>.*)\"}$"

    def __init__(self):
        self._parser = re.compile(self._regex)

    def _extract_problem(self, match: re.Match, document: LatexDocument) -> Problem:
        # print(parsed)
        row = int(match.group("row"))
        assert row >= 1, "Rows seem to start at 1."
        col = int(match.group("col"))
        assert col >= 1, "Columns seem to start at 1."
        length = int(match.group("length"))
        message = match.group("message")
        message_type = match.group("type")
        context_before = match.group("context_before")
        text = match.group("text")
        context_after = match.group("context_after")
        origin = document.get_origin_of_source((row - 1, col - 1), (row - 1, col + max(len(text), 1) - 1))
        longid = message + "|" + context_before + text + context_after
        return Problem(origin=origin, tool="chktex", long_id=longid,
                       context=context_before + text + context_after,
                       message=f"{message_type}: {message}", rule=f"{message_type}: {message}")

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        self.log("Running chktex...")
        result, err, exitcode = self._run(f"chktex -f '{self._format_str}'", document.get_source())
        results = result.split("\n")
        for result in results:
            parsed = self._parser.fullmatch(result)
            if parsed:
                yield self._extract_problem(parsed, document)

    def is_available(self) -> bool:
        return bool(shutil.which("chktex"))

    def needs_detex(self):
        return False

    def installation_guide(self) -> str:
        return "chktex should come with most latex distributions."
