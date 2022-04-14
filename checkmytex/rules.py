import abc
import typing
import re

from checkmytex.latex_document import LatexDocument
from checkmytex.checker import Problem


class Rule(abc.ABC):
    @abc.abstractmethod
    def prepare(self, document: LatexDocument, whitelist_path: str):
        pass

    @abc.abstractmethod
    def filter(self, problems: typing.Iterable[Problem]) \
            -> typing.Iterable[Problem]:
        pass


class IgnoreIncludegraphics(Rule):
    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument, whitelist_path: str):
        expr = r"\\includegraphics(\[[^\]]*\])?\{(?P<path>[^\}]+)\}"
        for match in re.finditer(expr, document.get_source()):
            r = (match.start("path"), match.end("path"))
            self._ranges.append(r)

    def filter(self, problems: typing.Iterable[Problem]) \
            -> typing.Iterable[Problem]:
        for p in problems:
            b = p.origin.begin.spos
            e = p.origin.end.spos
            if not any(r[0] <= b <= e <= r[1] for r in self._ranges):
                yield p


class IgnoreRefs(Rule):
    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument, whitelist_path: str):
        expr = r"\\(([Cc]?ref)|(fullcite)|(f?ref((ch)|(sec))))\{(?P<ref>[^\}]+)\}"
        for match in re.finditer(expr, document.get_source()):
            r = (match.start("ref"), match.end("ref"))
            self._ranges.append(r)

    def filter(self, problems: typing.Iterable[Problem]) \
            -> typing.Iterable[Problem]:
        for p in problems:
            b = p.origin.begin.spos
            e = p.origin.end.spos
            if not any(r[0] <= b <= e <= r[1] for r in self._ranges):
                yield p


class IgnoreRepeatedWords(Rule):
    def __init__(self, words: typing.List[str]):
        self.words = words
        self.document = None

    def prepare(self, document: LatexDocument, whitelist_path: str):
        self.document = document

    def filter(self, problems: typing.Iterable[Problem]) \
            -> typing.Iterable[Problem]:
        for p in problems:
            if p.rule == "EN_REPEATEDWORDS_PROBLEM":
                text = self.document.get_file_content(p.origin.file)
                t = text[p.origin.begin.pos: p.origin.end.pos]
                if t.strip().lower() in self.words:
                    continue
            yield p
