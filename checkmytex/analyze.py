from __future__ import annotations

import typing

from checkmytex import DocumentAnalyzer
from checkmytex.filtering import Filter
from checkmytex.finding import Checker
from checkmytex.latex_document.parser import LatexParser


def analyze(
    path: str,
    checker: typing.Iterable[Checker],
    problem_filter: typing.Iterable[Filter],
    log: typing.Callable[[str], None] = print,
) -> typing.Any:  # Returns AnalyzedDocument but avoid circular import
    """Analyze a LaTeX document for problems using specified checkers and filters."""
    doc_checker = DocumentAnalyzer(log=log)
    for c in checker:
        doc_checker.add_checker(c)
    for f in problem_filter:
        doc_checker.add_filter(f)
    parser = LatexParser()
    doc = parser.parse(path)
    return doc_checker.analyze(doc)
