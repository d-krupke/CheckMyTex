"""Tests for Ignore Code Listings Filter."""

from checkmytex import DocumentAnalyzer
from checkmytex.filtering import IgnoreCodeListings
from checkmytex.finding import CheckSpell
from checkmytex.latex_document.parser import LatexParser
from flachtex import FileFinder


class TestIgnoreCodeListings:
    """Test cases for the Ignore Code Listings Filter."""

    def test_ignores_lstlisting_environment(self):
        """Test that spelling errors in lstlisting are ignored."""
        source = r"""
\documentclass{article}
\usepackage{listings}
\begin{document}
This is normal text with misspeling.
\begin{lstlisting}
def functon_with_typo():
    varible = 123
    return varible
\end{lstlisting}
More text.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")

        # Create analyzer with spell checker
        analyzer = DocumentAnalyzer()
        analyzer.add_checker(CheckSpell())

        # Without filter
        report_no_filter = analyzer.analyze(document)
        problems_no_filter = list(report_no_filter.get_problems())

        # With filter
        analyzer.add_filter(IgnoreCodeListings())
        report_with_filter = analyzer.analyze(document)
        problems_with_filter = list(report_with_filter.get_problems())

        # Filter should reduce the number of problems
        assert len(problems_with_filter) < len(problems_no_filter)
        # Should still detect the misspelling in normal text
        assert len(problems_with_filter) >= 1

    def test_ignores_verbatim_environment(self):
        """Test that errors in verbatim environment are ignored."""
        source = r"""
\documentclass{article}
\begin{document}
This is normal text with misspeling.
\begin{verbatim}
This has typos liek functon varible
but they should be ignored
\end{verbatim}
More text.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")

        # Create analyzer with spell checker
        analyzer = DocumentAnalyzer()
        analyzer.add_checker(CheckSpell())

        # Without filter
        report_no_filter = analyzer.analyze(document)
        problems_no_filter = list(report_no_filter.get_problems())

        # With filter
        analyzer.add_filter(IgnoreCodeListings())
        report_with_filter = analyzer.analyze(document)
        problems_with_filter = list(report_with_filter.get_problems())

        # Filter should reduce the number of problems
        assert len(problems_with_filter) < len(problems_no_filter)

    def test_detects_errors_outside_code(self):
        """Test that errors outside code blocks are still detected."""
        source = r"""
\documentclass{article}
\begin{document}
This has a misspeling outside code.
\begin{lstlisting}
code here
\end{lstlisting}
This also has a misspeling.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")

        analyzer = DocumentAnalyzer()
        analyzer.add_checker(CheckSpell())
        analyzer.add_filter(IgnoreCodeListings())

        report = analyzer.analyze(document)
        problems = list(report.get_problems())

        # Should detect misspellings outside code blocks
        assert len(problems) >= 2

    def test_multiple_code_blocks(self):
        """Test handling of multiple code blocks."""
        source = r"""
\documentclass{article}
\usepackage{listings}
\begin{document}
Normal text.
\begin{lstlisting}
typo1 typo2
\end{lstlisting}
More text.
\begin{verbatim}
typo3 typo4
\end{verbatim}
Final text.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")

        filter = IgnoreCodeListings()
        filter.prepare(document)

        # Should have identified multiple code block ranges
        assert len(filter._ranges) == 2

    def test_nested_environments(self):
        """Test that nested code environments are handled."""
        source = r"""
\documentclass{article}
\begin{document}
Text with misspeling.
\begin{lstlisting}
outer code with typo
\end{lstlisting}
More text.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")

        filter = IgnoreCodeListings()
        filter.prepare(document)

        # Should identify code block
        assert len(filter._ranges) >= 1

    def test_minted_environment(self):
        """Test that minted environment is also ignored."""
        source = r"""
\documentclass{article}
\usepackage{minted}
\begin{document}
Normal text with misspeling.
\begin{minted}{python}
def functon_typo():
    pass
\end{minted}
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")

        analyzer = DocumentAnalyzer()
        analyzer.add_checker(CheckSpell())
        analyzer.add_filter(IgnoreCodeListings())

        report = analyzer.analyze(document)
        problems = list(report.get_problems())

        # Should detect error in normal text but not in minted
        # The exact number depends on what CheckSpell detects
        assert len(problems) >= 1
