"""
Checker for detecting overly long lines in LaTeX source code.

Long lines make diffs harder to read in version control and reduce code readability.
This checker helps enforce consistent line length limits.
"""

import typing

from checkmytex.latex_document import LatexDocument

from .abstract_checker import Checker
from .problem import Problem


class LineLengthChecker(Checker):
    """
    Checks for lines that exceed a maximum length threshold.

    Long lines in LaTeX source make version control diffs harder to review
    and reduce overall readability. Most style guides recommend keeping
    lines to 80-100 characters.
    """

    def __init__(self, max_length: int = 200, log: typing.Callable = print):
        """
        Initialize the Line Length Checker.

        Args:
            max_length: Maximum allowed line length in characters (default: 100)
            log: Logging function (default: print)
        """
        super().__init__(log)
        self.max_length = max_length

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        """
        Check document for overly long lines.

        Args:
            document: The LaTeX document to check

        Yields:
            Problem objects for each line that exceeds max_length
        """
        self.log(f"Checking for lines longer than {self.max_length} characters...")

        # Get the complete source code
        source = document.get_source()
        lines = source.split('\n')

        for line_num, line in enumerate(lines, 1):
            line_length = len(line)

            if line_length > self.max_length:
                # Calculate position in source
                # Get the byte offset of the start of this line
                line_start = sum(len(l) + 1 for l in lines[:line_num-1])
                line_end = line_start + line_length

                try:
                    # Get origin for this line
                    origin = document.get_simplified_origin_of_source(
                        line_start, line_end
                    )

                    # Create context string (show part of the line)
                    max_context_len = 50
                    if line_length > max_context_len:
                        context = line[:max_context_len] + "..."
                    else:
                        context = line

                    message = (
                        f"Line is too long ({line_length} characters, "
                        f"max {self.max_length}). Consider breaking it up for "
                        f"better readability and version control."
                    )

                    rule = "LINE_TOO_LONG"
                    long_id = f"{rule}|line{line_num}|{context}"

                    yield Problem(
                        origin=origin,
                        message=message,
                        context=context,
                        long_id=long_id,
                        tool="LineLengthChecker",
                        rule=rule,
                        look_up_url=None
                    )
                except Exception as e:
                    # If we can't get origin (e.g., for certain special lines),
                    # skip this line
                    self.log(f"Warning: Could not process line {line_num}: {e}")
                    continue

    def is_available(self) -> bool:
        """
        Check if the checker is available.

        Returns:
            True (always available, no external dependencies)
        """
        return True

    def installation_guide(self) -> str:
        """
        Get installation guide for this checker.

        Returns:
            Installation guide string
        """
        return "Line Length Checker is built-in and requires no installation."
