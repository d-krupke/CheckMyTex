"""Tests for Line Length Checker."""

from checkmytex.finding import LineLengthChecker
from checkmytex.latex_document.parser import LatexParser
from flachtex import FileFinder


class TestLineLengthChecker:
    """Test cases for the Line Length Checker."""

    def test_detects_long_lines(self):
        """Test that overly long lines are detected."""
        source = r"""
\documentclass{article}
\begin{document}
This is a short line.
This is a very long line that exceeds the maximum length and should be flagged by the line length checker as a problem that needs to be addressed because it is essentially a full paragraph in a single line which makes version control diffs very hard to read.
Another short line.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = LineLengthChecker(max_length=200)

        problems = list(checker.check(document))

        # Should find exactly one long line
        assert len(problems) == 1
        assert "too long" in problems[0].message.lower()

    def test_ignores_short_lines(self):
        """Test that lines within the limit are not flagged."""
        source = r"""
\documentclass{article}
\begin{document}
This is a short line.
Another short line.
Yet another short line.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = LineLengthChecker(max_length=200)

        problems = list(checker.check(document))

        # Should find no problems
        assert len(problems) == 0

    def test_configurable_max_length(self):
        """Test that max_length is configurable."""
        source = r"""
\documentclass{article}
\begin{document}
This is a line that is longer than 30 characters.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")

        # With max_length=30, should find problems
        checker_30 = LineLengthChecker(max_length=30)
        problems_30 = list(checker_30.check(document))
        assert len(problems_30) > 0

        # With max_length=100, should find no problems
        checker_100 = LineLengthChecker(max_length=100)
        problems_100 = list(checker_100.check(document))
        assert len(problems_100) == 0

    def test_reports_line_number(self):
        """Test that the problem includes the correct line number."""
        source = r"""
\documentclass{article}
\begin{document}
Line 1.
Line 2.
This is line 3 and it is very long so it should be flagged by the checker as exceeding the maximum allowed line length.
Line 4.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = LineLengthChecker(max_length=80)

        problems = list(checker.check(document))

        assert len(problems) == 1
        # The context should include information about which line
        assert "line" in problems[0].message.lower()

    def test_multiple_long_lines(self):
        """Test detection of multiple long lines."""
        source = r"""
\documentclass{article}
\begin{document}
This is the first very long line that exceeds the maximum length and should be flagged by the checker.
Short line.
This is the second very long line that also exceeds the maximum length and should be flagged as well.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = LineLengthChecker(max_length=80)

        problems = list(checker.check(document))

        # Should find two long lines
        assert len(problems) == 2

    def test_is_available(self):
        """Test that the checker is always available."""
        checker = LineLengthChecker()
        assert checker.is_available() is True
