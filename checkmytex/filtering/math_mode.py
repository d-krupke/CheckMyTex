"""
The math mode creates text, but it does often not proper english,
leading to many false positives. This module filters out specific problems
in math mode.
"""

import re
import typing

from checkmytex.finding import Problem
from checkmytex.latex_document import LatexDocument

from .filter import Filter


class MathMode(Filter):
    """
    Filter specific problems in math mode.

    Note that the source will be stripped of any comments, allowing us
    to ignore these in our regular expressions.
    """

    def __init__(self, rules: typing.Dict[str, typing.Optional[typing.List]]):
        """
        :param rules: Specify which tools and rules (None for all) should be
        ignored in math mode.
        """
        self.ranges: typing.List[typing.Tuple[int, int]] = []
        self.rules = rules

    def _find_simple_math(self, source):
        regex = re.compile(
            r"(^|[^\$])(?P<math>\$([^\$]|\\\$)*[^\\\$]\$)", re.MULTILINE | re.DOTALL
        )
        for match in regex.finditer(source):
            begin = match.start("math")
            end = match.end("math")
            self.ranges.append((begin, end))

    def _find_line_math(self, source):
        regex = re.compile(r"(\\\[.+?\\\])", re.MULTILINE | re.DOTALL)
        for match in regex.finditer(source):
            begin = match.start()
            end = match.end()
            self.ranges.append((begin, end))

    def _find_environments(self, source, env):
        regex = re.compile(
            r"\\begin\{\s*" + env + r"\s*\}.+?\\end\{\s*" + env + r"\s*\}",
            re.MULTILINE | re.DOTALL,
        )
        for match in regex.finditer(source):
            begin = match.start()
            end = match.end()
            self.ranges.append((begin, end))

    def prepare(self, document: LatexDocument):
        source = document.get_source()
        self._find_simple_math(source)
        self._find_line_math(source)
        self._find_environments(source, "equation")
        self._find_environments(source, "equation\\*")
        self._find_environments(source, "align")
        self._find_environments(source, "align\\*")
        self._find_environments(source, "array")

    def _problem_fits_rule(self, problem):
        for tool, rules in self.rules.items():
            if problem.tool == tool:
                if not rules or problem.rule in rules:
                    return True
        return False

    def _problem_applies(self, problem):
        if not self._problem_fits_rule(problem):
            return False
        begin = problem.origin.begin.source.index
        end = problem.origin.end.source.index
        if not any(r[0] <= begin <= end <= r[1] for r in self.ranges):
            return False
        return True

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for problem in problems:
            if not self._problem_applies(problem):
                yield problem
