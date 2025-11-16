"""Tests for TODO/FIXME Checker."""

from checkmytex import DocumentAnalyzer
from checkmytex.finding import TodoChecker
from checkmytex.latex_document.parser import LatexParser
from flachtex import FileFinder


class TestTodoChecker:
    """Test cases for the TODO/FIXME Checker."""

    def test_detects_todo_comment(self):
        """Test that TODO comments are detected."""
        source = r"""
\documentclass{article}
\begin{document}
This is some text.
% TODO: Fix this section
More text here.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = TodoChecker()

        problems = list(checker.check(document))

        assert len(problems) == 1
        assert "TODO" in problems[0].message

    def test_detects_fixme_comment(self):
        """Test that FIXME comments are detected."""
        source = r"""
\documentclass{article}
\begin{document}
Text before.
% FIXME: This needs to be corrected
Text after.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = TodoChecker()

        problems = list(checker.check(document))

        assert len(problems) == 1
        assert "FIXME" in problems[0].message

    def test_detects_xxx_comment(self):
        """Test that XXX comments are detected."""
        source = r"""
\documentclass{article}
\begin{document}
Some text.
% XXX: Important note
More text.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = TodoChecker()

        problems = list(checker.check(document))

        assert len(problems) == 1
        assert "XXX" in problems[0].message

    def test_detects_todo_command(self):
        """Test that \\todo{} commands are detected."""
        source = r"""
\documentclass{article}
\usepackage{todonotes}
\begin{document}
This is some text.
\todo{Remember to add citation here}
More text.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = TodoChecker()

        problems = list(checker.check(document))

        assert len(problems) == 1
        assert "\\todo" in problems[0].message.lower()

    def test_detects_multiple_todos(self):
        """Test detection of multiple TODO markers."""
        source = r"""
\documentclass{article}
\begin{document}
Text.
% TODO: First task
More text.
% FIXME: Second task
% XXX: Third task
\todo{Fourth task}
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = TodoChecker()

        problems = list(checker.check(document))

        # Should find all four TODO markers
        assert len(problems) == 4

    def test_ignores_todo_in_text(self):
        """Test that TODO in regular text (not comment) is not flagged."""
        source = r"""
\documentclass{article}
\begin{document}
We have a TODO list for the project, but this is just text.
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = TodoChecker()

        problems = list(checker.check(document))

        # Should not find TODO in regular text
        assert len(problems) == 0

    def test_case_insensitive(self):
        """Test that TODO detection is case-sensitive (only uppercase)."""
        source = r"""
\documentclass{article}
\begin{document}
% todo: lowercase (should not be detected)
% TODO: uppercase (should be detected)
\end{document}
        """
        parser = LatexParser(FileFinder(".", {"main.tex": source}))
        document = parser.parse("main.tex")
        checker = TodoChecker()

        problems = list(checker.check(document))

        # Should find only the uppercase TODO
        assert len(problems) == 1
        assert "TODO" in problems[0].message

    def test_is_available(self):
        """Test that the checker is always available."""
        checker = TodoChecker()
        assert checker.is_available() is True
