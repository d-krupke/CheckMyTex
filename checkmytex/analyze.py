import typing

from checkmytex import DocumentAnalyzer, LatexDocument
from checkmytex.filtering import Filter
from checkmytex.finding import Checker


def analyze(
    path: str,
    checker: typing.Iterable[Checker],
    problem_filter: typing.Iterable[Filter],
    log=print,
):
    doc_checker = DocumentAnalyzer(log=log)
    for c in checker:
        doc_checker.add_checker(c)
    for f in problem_filter:
        doc_checker.add_filter(f)
    doc = LatexDocument(path)
    return doc_checker.analyze(doc)
