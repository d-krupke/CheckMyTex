import abc
import os
import re
import typing

from checkmytex.finding import Problem
from checkmytex.latex_document import LatexDocument


class Filter(abc.ABC):
    @abc.abstractmethod
    def prepare(self, document: LatexDocument):
        pass

    @abc.abstractmethod
    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        pass


class IgnoreIncludegraphics(Filter):
    """
    Ignore errors that occur within an \\includegraphics{} command.
    """

    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument):
        expr = r"\\includegraphics(\[[^\]]*\])?\{(?P<path>[^\}]+)\}"
        for match in re.finditer(expr, document.get_source()):
            r = (match.start("path"), match.end("path"))
            self._ranges.append(r)

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for problem in problems:
            begin = problem.origin.begin.spos
            end = problem.origin.end.spos
            if not any(r[0] <= begin <= end <= r[1] for r in self._ranges):
                yield problem


class IgnoreRefs(Filter):
    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument):
        expr = r"\\(([Cc]?ref)|(fullcite)|(f?ref((ch)|(sec))))\{(?P<ref>[^\}]+)\}"
        for match in re.finditer(expr, document.get_source()):
            span = (match.start("ref"), match.end("ref"))
            self._ranges.append(span)

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for problem in problems:
            begin = problem.origin.begin.spos
            end = problem.origin.end.spos
            if not any(r[0] <= begin <= end <= r[1] for r in self._ranges):
                yield problem


class IgnoreRepeatedWords(Filter):
    def __init__(self, words: typing.List[str]):
        self.words = words
        self.document: typing.Optional[LatexDocument] = None

    def prepare(self, document: LatexDocument):
        self.document = document

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        assert self.document, "Prepare has been called."
        for problem in problems:
            if problem.rule == "EN_REPEATEDWORDS_PROBLEM":
                text = self.document.get_file_content(problem.origin.file)
                section = text[problem.origin.begin.pos : problem.origin.end.pos]
                if section.strip().lower() in self.words:
                    continue
            yield problem


class IgnoreSpellingWithMath(Filter):
    def __init__(self):
        self.document = None

    def prepare(self, document: LatexDocument):
        self.document = document

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for problem in problems:
            if problem.rule == "SPELLING":
                begin = problem.origin.begin.spos
                end = problem.origin.end.spos
                source_of_word = self.document.get_source()[begin:end]
                if "\\" in source_of_word or "$" in source_of_word:
                    continue
            yield problem


class MathMode(Filter):
    def __init__(self, rules: typing.Dict[str, typing.Optional[typing.List]]):
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
        begin = problem.origin.begin.spos
        end = problem.origin.end.spos
        if not any(r[0] <= begin <= end <= r[1] for r in self.ranges):
            return False
        return True

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for problem in problems:
            if not self._problem_applies(problem):
                yield problem
