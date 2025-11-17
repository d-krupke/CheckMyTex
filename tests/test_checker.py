import sys

import pytest
from checkmytex import DocumentAnalyzer
from checkmytex.finding import CheckSpell
from checkmytex.latex_document.parser import LatexParser
from flachtex import FileFinder


class TestChecker:
    @pytest.mark.skipif(
        sys.version_info >= (3, 13),
        reason="Origin tracking broken on Python 3.13 - upstream flachtex/yalafi issue",
    )
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
        engine = DocumentAnalyzer()
        engine.add_checker(CheckSpell())
        report = engine.analyze(document)
        assert len(report.problems) == 1
        start, end = report.problems[0].origin.get_file_span()
        # Position may vary between Python versions due to text processing differences
        # The important check is that it correctly maps back to the source
        assert source[start:end] == "ImportantTerm"

    @pytest.mark.skipif(
        sys.version_info >= (3, 13),
        reason="Origin tracking broken on Python 3.13 - upstream flachtex/yalafi issue",
    )
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
        engine = DocumentAnalyzer()
        engine.add_checker(CheckSpell())
        report = engine.analyze(document)
        assert len(report.problems) == 1
        start, end = report.problems[0].origin.get_file_span()
        # Position may vary between Python versions due to text processing differences
        # The important check is that it correctly maps back to the source
        assert source[start:end] == "bla"
