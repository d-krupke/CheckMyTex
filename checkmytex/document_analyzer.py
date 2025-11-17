"""
Module for checking a latex document by applying a set of checker and filter.
"""

import logging
import traceback
import typing

from .analyzed_document import AnalyzedDocument
from .filtering.filter import Filter
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
from .finding.problem import Problem
from .finding.spellcheck import AspellChecker
from .latex_document import LatexDocument


class DocumentAnalyzer:
    """
    Simple class to return the files and its problems of a latex document.
    """

    def __init__(self, log: typing.Callable = print):
        self.log = log
        self.checker: list[Checker] = []
        self.rules: list[Filter] = []

    def setup_default(self) -> None:
        """
        Setup default checker.
        """
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
        """
        Add a filter that is applied on the output of the checkers.
        :param rule: The filter rule
        :return: None
        """
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
        """Find problems using all configured checkers.

        Continues checking with other checkers even if one fails.

        Args:
            latex_document: The document to analyze

        Yields:
            Problems found by checkers

        Note:
            Exceptions from individual checkers are logged but don't stop analysis
        """
        for checker in self.checker:
            try:
                yield from checker.check(latex_document)
            except (RuntimeError, ValueError, TypeError, KeyError) as e:
                # Expected errors from checker logic
                logging.getLogger("CheckMyTex").error(
                    f"Checker {checker} failed with {type(e).__name__}: {e}"
                )
            except Exception as e:
                # Unexpected errors - log full traceback for debugging
                logging.getLogger("CheckMyTex").error(
                    f"Unexpected exception in {checker}: {e}\n{traceback.format_exc()}"
                )
