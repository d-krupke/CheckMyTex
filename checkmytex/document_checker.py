import re
import typing

from .checker import Checker, Languagetool, SiUnitx, ChkTex, CheckSpell, \
    Proselint, Cleveref
from checkmytex.latex_document import LatexDocument
from checkmytex.problem import Problem
from checkmytex.whitelist import Whitelist


class DocumentChecker:
    """
    Simple class to return the files and its problems of a latex document.
    """

    def __init__(self, checker=None):
        self.checker = []
        if checker:
            for c in checker:
                self.add_checker(c)
        else:
            self.add_checker(ChkTex())
            self.add_checker(CheckSpell())
            self.add_checker(Languagetool())
            self.add_checker(SiUnitx())
            self.add_checker(Proselint())
            self.add_checker(Cleveref())

    def add_checker(self, checker: Checker) -> None:
        """
        Add a checker if it is available.
        :param checker: The checker to be added.
        :return: None
        """
        if checker.is_available():
            self.checker.append(checker)
        else:
            print(str(checker), "is not available.")
            guide = checker.installation_guide()
            if guide:
                print(guide)

    def find_problems(self,
                      latex_document: LatexDocument,
                      whitelist: Whitelist = None) \
            -> typing.Iterable[Problem]:
        """
        Finds problems of the document. Returns an iterator of file names and sorted problems.
        :param latex_document: The latex document to check.
        :param whitelist: The whitelist of problems to ignore.
        :return: Iterator over file name and sorted problems within this file.
        """
        whitelist = whitelist if whitelist else Whitelist()
        self._ignore_refs(latex_document, whitelist)
        self._ignore_includegraphics(latex_document, whitelist)
        for c in self.checker:
            for p in c.check(latex_document):
                if p not in whitelist:
                    yield p

    def _ignore_refs(self, latex_document: LatexDocument, whitelist: Whitelist):
        expr = r"\\[Cc]?ref\{(?P<ref>[^\}]+)\}"
        for match in re.finditer(expr, latex_document.get_source()):
            whitelist.skip_range(match.start("ref"), match.end("ref"))

    def _ignore_includegraphics(self, latex_document: LatexDocument, whitelist: Whitelist):
        expr = r"\\includegraphics(\[[^\]]*\])?\{(?P<path>[^\}]+)\}"
        for match in re.finditer(expr, latex_document.get_source()):
            whitelist.skip_range(match.start("path"), match.end("path"))


    def sort_problems_by_file(self, latex_document, problems) \
            -> typing.Iterable[typing.Tuple[str, typing.List[Problem]]]:
        problems_of_files = {f: [] for f in latex_document.files()}
        for p in problems:
            problems_of_files[p.origin.file].append(p)
        for f in latex_document.files():
            problems = [p for p in problems_of_files[f]]
            problems.sort(key=lambda p: (p.origin.begin, p.origin.end))
            yield f, problems
