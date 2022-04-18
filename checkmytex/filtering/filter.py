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
    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument):
        expr = r"\\includegraphics(\[[^\]]*\])?\{(?P<path>[^\}]+)\}"
        for match in re.finditer(expr, document.get_source()):
            r = (match.start("path"), match.end("path"))
            self._ranges.append(r)

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for p in problems:
            b = p.origin.begin.spos
            e = p.origin.end.spos
            if not any(r[0] <= b <= e <= r[1] for r in self._ranges):
                yield p


class IgnoreRefs(Filter):
    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument):
        expr = r"\\(([Cc]?ref)|(fullcite)|(f?ref((ch)|(sec))))\{(?P<ref>[^\}]+)\}"
        for match in re.finditer(expr, document.get_source()):
            r = (match.start("ref"), match.end("ref"))
            self._ranges.append(r)

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for p in problems:
            b = p.origin.begin.spos
            e = p.origin.end.spos
            if not any(r[0] <= b <= e <= r[1] for r in self._ranges):
                yield p


class IgnoreRepeatedWords(Filter):
    def __init__(self, words: typing.List[str]):
        self.words = words
        self.document = None

    def prepare(self, document: LatexDocument):
        self.document = document

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for p in problems:
            if p.rule == "EN_REPEATEDWORDS_PROBLEM":
                text = self.document.get_file_content(p.origin.file)
                t = text[p.origin.begin.pos : p.origin.end.pos]
                if t.strip().lower() in self.words:
                    continue
            yield p


class IgnoreSpellingWithMath(Filter):
    def __init__(self):
        self.document = None

    def prepare(self, document: LatexDocument):
        self.document = document

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for p in problems:
            if p.rule == "SPELLING":
                b = p.origin.begin.spos
                e = p.origin.end.spos
                source_of_word = self.document.get_source()[b:e]
                if "\\" in source_of_word or "$" in source_of_word:
                    continue
            yield p
