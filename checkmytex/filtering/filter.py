import abc
import os
import typing
import re

from checkmytex.latex_document import LatexDocument
from checkmytex.finding import Problem

from yalafi.tex2txt import Options, tex2txt


class Filter(abc.ABC):
    @abc.abstractmethod
    def prepare(self, document: LatexDocument):
        pass

    @abc.abstractmethod
    def filter(self, problems: typing.Iterable[Problem]) \
            -> typing.Iterable[Problem]:
        pass


class IgnoreIncludegraphics(Filter):
    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument):
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


class IgnoreRefs(Filter):
    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument):
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


class IgnoreRepeatedWords(Filter):
    def __init__(self, words: typing.List[str]):
        self.words = words
        self.document = None

    def prepare(self, document: LatexDocument):
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


class IgnoreLikelyAuthorNames(Filter):
    def __init__(self):
        self._name_elements = set()
        self._text = None

    def prepare(self, document: LatexDocument):
        self._text = document.get_text()
        text = re.sub("\s+", " ", document.get_text())
        regex = r"(?P<names>(([A-Z][^\s\[]+)(\sand\s)?)+)(\set al\.?)?\s?\[0\]"
        for match in re.finditer(regex, text):
            names = match.group("names")
            for n in names.split(" "):
                self._name_elements.update(n.split("-"))

    def filter(self, problems: typing.Iterable[Problem]) \
            -> typing.Iterable[Problem]:
        for p in problems:
            if p.rule == "SPELLING":
                w = self._text[p.origin.begin.tpos:p.origin.end.tpos].strip()
                if w in self._name_elements:
                    continue
            yield p


class IgnoreWordsFromBibliography(Filter):
    def __init__(self):
        self.word_list = set()

    def _find_bibtex_paths(self, document: LatexDocument):
        regex = r"\\((addbibresource)|(bibliography))\{(?P<path>[^}]+)\}"
        paths = set()
        for match in re.finditer(regex, document.get_source()):
            bib_file = match.group("path")
            in_file = document.get_origin_of_source(match.start("path"),
                                                    match.end("path")).file
            p = os.path.join(os.path.dirname(in_file), bib_file)
            if os.path.isfile(p):
                paths.add(p)
            elif os.path.isfile(p + ".bib"):
                paths.add(p + ".bib")
        return paths

    def _collect_bibtexs(self, document: LatexDocument):
        bibtex = ""
        for p in self._find_bibtex_paths(document):
            with open(p, "r") as f:
                bibtex += "\n".join(f.readlines())
        return bibtex

    def _extract_words_from_bibtex(self, bibtex: str):
        expr = r"^\s*((author)|(AUTHOR)|(title)|(TITLE))\s*=\s*\{(?P<text>[^{}]*(\{[^{}]*\}[^{}]*)*)\}"
        text = ""
        for match in re.finditer(expr, bibtex, re.MULTILINE):
            text += match.group('text') + " "
        text = tex2txt(text, Options())[0]
        for w in re.split(r"[\s.,():-]+", text):
            if len(w) > 1:
                self.word_list.add(w)

    def prepare(self, document: LatexDocument):
        self._text = document.get_text()
        bibtex = self._collect_bibtexs(document)
        self._extract_words_from_bibtex(bibtex)

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[
        Problem]:
        for p in problems:
            if p.rule == "SPELLING":
                w = self._text[p.origin.begin.tpos:p.origin.end.tpos].strip()
                if w in self.word_list:
                    continue
            yield p
