import unittest

from flachtex import FileFinder

from checkmytex import DocumentAnalyzer
from checkmytex.cli import log
from checkmytex.finding import CheckSpell
from checkmytex.latex_document.latex_document import LatexParser


class CheckerTest(unittest.TestCase):
    def test_1(self):
        source = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsfonts,amsthm}
\usepackage{todonotes}
\usepackage{xspace}

\newcommand{\importantterm}{\emph{ImportantTerm}\xspace}

%%FLACHTEX-SKIP-START
Technicalities (e.g., configuration of Journal-template) that we want to skip.
%%FLACHTEX-SKIP-STOP

\begin{document}

\section{Introduction}

\todo[inline]{This TODO will not be shown because we don't want to analyze it.}

Let us use \importantterm here.

\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        engine = DocumentAnalyzer(log=log)
        engine.add_checker(CheckSpell())
        report = engine.analyze(document)
        print(document.get_text())
        self.assertEqual(len(report.problems), 1)
        start = report.problems[0].origin.begin.pos
        end = report.problems[0].origin.end.pos
        self.assertEqual(start, 176)
        self.assertEqual(end, 189)
        self.assertEqual(source[start:end], "ImportantTerm")

    def test_2(self):
        source = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsfonts,amsthm}
\usepackage{todonotes}
\usepackage{xspace}

\newcommand{\importantterm}[1]{\emph{ImportantTerm}}

%%FLACHTEX-SKIP-START
Technicalities (e.g., configuration of Journal-template) that we want to skip.
%%FLACHTEX-SKIP-STOP

\begin{document}

\section{Introduction}

\todo[inline]{This TODO will not be shown because we don't want to analyze it.}

Let us use \importantterm{}bla here.

\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        engine = DocumentAnalyzer(log=log)
        engine.add_checker(CheckSpell())
        report = engine.analyze(document)
        self.assertEqual(len(report.problems), 1)
        start = report.problems[0].origin.begin.pos
        end = report.problems[0].origin.end.pos
        #print(document.get_text())
        print(source[start:end])
        self.assertEqual(start, 179)
        self.assertEqual(end, 472)
        self.assertEqual(source[start:end], "ImportantTermbla")