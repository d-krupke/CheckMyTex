import abc
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
        for match in re.finditer(expr, str(document.get_source())):
            r = (match.start("path"), match.end("path"))
            self._ranges.append(r)

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for problem in problems:
            begin = problem.origin.begin.source.index
            end = problem.origin.end.source.index
            if not any(r[0] <= begin <= end <= r[1] for r in self._ranges):
                yield problem


class IgnoreRefs(Filter):
    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument):
        expr = r"\\(([Cc]?ref)|(fullcite)|(f?ref((ch)|(sec))))\{(?P<ref>[^\}]+)\}"
        for match in re.finditer(expr, str(document.get_source())):
            span = (match.start("ref"), match.end("ref"))
            self._ranges.append(span)

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for problem in problems:
            begin = problem.origin.begin.source.index
            end = problem.origin.end.source.index
            if not any(r[0] <= begin <= end <= r[1] for r in self._ranges):
                yield problem


class IgnoreRepeatedWords(Filter):
    def __init__(self, words: list[str] | None = None):
        # Default to common academic words that are often intentionally repeated
        self.words = words if words is not None else ["problem", "problems"]
        self.document: LatexDocument | None = None

    def prepare(self, document: LatexDocument):
        self.document = document

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        if not self.document:
            msg = "prepare() must be called before filter()"
            raise RuntimeError(msg)
        for problem in problems:
            if problem.rule == "EN_REPEATEDWORDS_PROBLEM":
                text = self.document.get_file_content(problem.origin.get_file())
                section = text[
                    problem.origin.begin.file.position.index : problem.origin.end.file.position.index
                ]
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
                begin = problem.origin.begin.source.index
                end = problem.origin.end.source.index
                source_of_word = self.document.get_source()[begin:end]
                if "\\" in source_of_word or "$" in source_of_word:
                    continue
            yield problem
