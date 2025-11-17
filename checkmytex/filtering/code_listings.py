"""Filter to ignore errors within code listing environments."""

import re
import typing

from checkmytex.finding import Problem
from checkmytex.latex_document import LatexDocument

from .filter import Filter


class IgnoreCodeListings(Filter):
    """
    Ignores errors within code listing environments.

    Code snippets (lstlisting, verbatim, minted) should not trigger
    language or spelling checks since they contain programming code
    with different syntax rules.
    """

    def __init__(self):
        """Initialize the filter."""
        self._ranges = []

    def prepare(self, document: LatexDocument):
        """
        Find all code listing environment ranges in the document.

        Args:
            document: The LaTeX document to prepare
        """
        source = str(document.get_source())

        # Pattern for lstlisting environment
        # Matches: \begin{lstlisting}...\end{lstlisting}
        lstlisting_pattern = r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}"

        for match in re.finditer(lstlisting_pattern, source, re.DOTALL):
            self._ranges.append((match.start(), match.end()))

        # Pattern for verbatim environment
        # Matches: \begin{verbatim}...\end{verbatim}
        verbatim_pattern = r"\\begin\{verbatim\}.*?\\end\{verbatim\}"

        for match in re.finditer(verbatim_pattern, source, re.DOTALL):
            self._ranges.append((match.start(), match.end()))

        # Pattern for minted environment
        # Matches: \begin{minted}{language}...\end{minted}
        minted_pattern = r"\\begin\{minted\}.*?\\end\{minted\}"

        for match in re.finditer(minted_pattern, source, re.DOTALL):
            self._ranges.append((match.start(), match.end()))

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        """
        Filter out problems that occur within code listing environments.

        Args:
            problems: Iterable of problems to filter

        Yields:
            Problems that are not within code listing environments
        """
        for problem in problems:
            # Get the problem's position in the source
            begin = problem.origin.begin.source.index
            end = problem.origin.end.source.index

            # Check if this problem is within any code listing range
            in_code_listing = False
            for range_start, range_end in self._ranges:
                # Check if problem overlaps with this code range
                if range_start <= begin <= range_end or range_start <= end <= range_end:
                    in_code_listing = True
                    break

            # Only yield problems that are not in code listings
            if not in_code_listing:
                yield problem
