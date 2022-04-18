import typing

from checkmytex.filtering.filter import Filter
from checkmytex.finding.problem import Problem
from checkmytex.latex_document import LatexDocument

from .analyzed_document import AnalyzedDocument
from .finding import (
    Checker,
    CheckSpell,
    ChkTex,
    Cleveref,
    Languagetool,
    Proselint,
    SiUnitx,
    UniformNpHard,
)
from .finding.spellcheck import AspellChecker


class DocumentAnalyzer:
    """
    Simple class to return the files and its problems of a latex document.
    """

    def __init__(self, log=print):
        self.log = log
        self.checker = []
        self.rules = []

    def setup_default(self):
        self.log("Using default modules.")
        aspell = AspellChecker()
        if aspell.is_available():
            self.add_checker(aspell)
        else:
            self.log("Aspell not available. Using pyspellchecker.")
            self.add_checker(CheckSpell())
        self.add_checker(ChkTex())
        self.add_checker(Languagetool())
        self.add_checker(SiUnitx())
        self.add_checker(Proselint())
        self.add_checker(Cleveref())
        self.add_checker(UniformNpHard())
        for checker in self.checker:
            checker.log = self.log

    def add_checker(self, checker: Checker) -> None:
        """
        Add a checker if it is available.
        :param checker: The checker to be added.
        :return: None
        """
        checker.log = self.log
        if checker.is_available():
            self.checker.append(checker)
        else:
            self.log(str(checker), "is not available.")
            guide = checker.installation_guide()
            if guide:
                self.log(guide)

    def add_filter(self, rule: Filter) -> None:
        self.rules.append(rule)

    def _filter(self, problems: typing.Iterable[Problem]):
        for rule in self.rules:
            problems = rule.filter(problems)
        return problems

    def analyze(self, latex_document: LatexDocument) -> AnalyzedDocument:
        """
        Finds problems of the document. Returns an iterator of file names and
         sorted problems.
        :param latex_document: The latex document to check.
        :param whitelist: The whitelist of problems to ignore.
        :return: Iterator over file name and sorted problems within this file.
        """
        for rule in self.rules:
            rule.prepare(latex_document)
        problems = list(self._filter(self._find_problems(latex_document)))
        problems.sort(key=lambda p: p.origin)
        return AnalyzedDocument(latex_document, problems)

    def _find_problems(self, latex_document: LatexDocument) -> typing.Iterable[Problem]:

        for c in self.checker:
            for p in c.check(latex_document):
                yield p
