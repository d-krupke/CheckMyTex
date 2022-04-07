import typing

from .checker import Checker, Languagetool, SiUnitx, ChkTex, CheckSpell
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
            -> typing.Iterable[typing.Tuple[str, typing.List[Problem]]]:
        """
        Finds problems of the document. Returns an iterator of file names and sorted problems.
        :param latex_document: The latex document to check.
        :param whitelist: The whitelist of problems to ignore.
        :return: Iterator over file name and sorted problems within this file.
        """
        whitelist = whitelist if whitelist else Whitelist()
        problems = [p for c in self.checker for p in c.check(latex_document)]
        problems_of_files = {f: [] for f in latex_document.files()}
        for p in problems:
            problems_of_files[p.origin.file].append(p)
        for f in latex_document.files():
            problems = [p for p in problems_of_files[f] if p not in whitelist]
            problems.sort(key=lambda p: (p.origin.begin, p.origin.end))
            yield f, problems
