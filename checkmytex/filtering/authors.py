"""
Provides some filters to lessen reported spelling errors on author names.
"""
import os
import re
import typing

from yalafi.tex2txt import Options, tex2txt

from ..finding import Problem
from ..latex_document import LatexDocument
from .filter import Filter


class IgnoreLikelyAuthorNames(Filter):
    """
    Finds author names use before \\cite and prevents them to be detected
    as spelling error.
    """

    def __init__(self):
        self._name_elements = set()
        self._text = None

    def prepare(self, document: LatexDocument):
        self._text = document.get_text()
        text = re.sub(r"\s+", " ", document.get_text())
        regex = r"(?P<names>(([A-Z][^\s\[]+)(\sand\s)?)+)(\set al\.?)?\s?\[0\]"
        for match in re.finditer(regex, text):
            names = match.group("names")
            for name in names.split(" "):
                self._name_elements.update(name.split("-"))
        self._name_elements.add("et")
        self._name_elements.add("al")

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for p in problems:
            if p.rule == "SPELLING":
                w = self._text[p.origin.begin.tpos : p.origin.end.tpos].strip()
                if w in self._name_elements:
                    continue
            yield p


class IgnoreWordsFromBibliography(Filter):
    """
    Reads the bibtex files and adds words used in title and authors to
    the spelling whitelist.
    """

    def __init__(self, paths=None):
        self._paths = paths if paths else []
        self.word_list = set()

    def _find_bibtex_paths(self, document: LatexDocument):
        regex = r"\\((addbibresource)|(bibliography))\{(?P<path>[^}]+)\}"
        paths = set()
        for match in re.finditer(regex, document.get_source()):
            bib_file = match.group("path")
            in_file = document.get_origin_of_source(
                match.start("path"), match.end("path")
            ).file
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
        for p in self._paths:
            with open(p, "r") as f:
                bibtex += "\n".join(f.readlines())
        return bibtex

    def _extract_words_from_bibtex(self, bibtex: str):
        expr = (
            r"^\s*((author)|(AUTHOR)|(title)|(TITLE))"
            r"\s*=\s*\{(?P<text>[^{}]*(\{[^{}]*\}[^{}]*)*)\}"
        )
        text = ""
        for match in re.finditer(expr, bibtex, re.MULTILINE):
            text += match.group("text") + " "
        text = tex2txt(text, Options())[0]
        for w in re.split(r"[\s.,():\-]+", text):
            if len(w) > 1:
                self.word_list.add(w)

    def prepare(self, document: LatexDocument):
        self._text = document.get_text()
        bibtex = self._collect_bibtexs(document)
        self._extract_words_from_bibtex(bibtex)

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for p in problems:
            if p.rule == "SPELLING":
                w = self._text[p.origin.begin.tpos : p.origin.end.tpos].strip()
                if w in self.word_list:
                    continue
            yield p
