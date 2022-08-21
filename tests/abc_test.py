import re
import typing
import unittest

from flachtex import FileFinder

from checkmytex import DocumentAnalyzer, LatexDocument
from checkmytex.cli.rich_printer import RichPrinter
from checkmytex.filtering import (
    IgnoreIncludegraphics,
    IgnoreLikelyAuthorNames,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreSpellingWithMath,
    IgnoreWordsFromBibliography,
    MathMode,
)
from checkmytex.finding import Checker, Problem
from checkmytex.latex_document.parser import LatexParser


class AbcChecker(Checker):
    def __init__(self, check_ranges):
        super().__init__()
        self.check_ranges = check_ranges

    def is_available(self) -> bool:
        return True

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        text = document.get_text()
        source = document.get_source()
        regex = re.compile("ABC")
        for match in regex.finditer(text):
            origin = document.get_simplified_origin_of_text(match.start(), match.end())
            s_origin = origin.get_source_span()
            t_origin = origin.get_text_span()
            f_origin = origin.get_file_span()
            if self.check_ranges:
                assert (
                    text[s_origin[0] : s_origin[1]] == text[match.start() : match.end()]
                )
                assert (
                    text[t_origin[0] : t_origin[1]] == text[match.start() : match.end()]
                )
                assert (
                    text[f_origin[0] : f_origin[1]] == text[match.start() : match.end()]
                )
            yield Problem(
                origin,
                "ABC found.",
                text[match.start() : match.end()],
                str(origin),
                "ABC",
                "ABC",
            )


class AbcTest(unittest.TestCase):
    def test_1(self):
        files = {
            "/main.tex": "This is a test with ABC.\nSecond line. Also here an ABC."
        }
        parser = LatexParser(file_finder=FileFinder("/", files))
        document = parser.parse("/main.tex")
        engine = DocumentAnalyzer()
        engine.add_checker(AbcChecker(check_ranges=True))
        analysis = engine.analyze(document)
        for problem in analysis.problems:
            print(problem.serialize())

    def test_2(self):
        files = {
            "/main.tex": "\\newcommand{ab}[0]{AB}\nThis is a test with ABC.\nSecond line. Also here an ABC.\nHere one with newcommand \\ab{}C."
        }
        parser = LatexParser(file_finder=FileFinder("/", files))
        document = parser.parse("/main.tex")
        engine = DocumentAnalyzer()
        engine.add_checker(AbcChecker(check_ranges=False))
        analysis = engine.analyze(document)
        self.assertEqual(
            document.get_text(),
            "This is a test with ABC.\nSecond line. Also here an ABC.\nHere one with newcommand ABC.",
        )
        self.assertEqual(len(analysis.problems), 3)
        for problem in analysis.problems:
            f_range = problem.origin.get_file_span()
            print(
                problem.serialize(),
                "in file:",
                files["/main.tex"][f_range[0] : f_range[1]],
            )

    def test_3(self):
        files = {
            "/main.tex": "\\newcommand{ab}[0]{AB}\nThis is a test with ABC.\nSecond line. Also here an ABC.\nHere one with newcommand \\ab C."
        }
        parser = LatexParser(file_finder=FileFinder("/", files))
        document = parser.parse("/main.tex")
        engine = DocumentAnalyzer()
        engine.add_checker(AbcChecker(check_ranges=False))
        analysis = engine.analyze(document)
        print(analysis.serialize())
        self.assertEqual(
            document.get_text(),
            "This is a test with ABC.\nSecond line. Also here an ABC.\nHere one with newcommand ABC.",
        )
        self.assertEqual(len(analysis.problems), 3)
        for problem in analysis.problems:
            f_range = problem.origin.get_file_span()
            print(
                problem.serialize(),
                "in file:",
                files["/main.tex"][f_range[0] : f_range[1]],
            )
        RichPrinter(analysis).print()
