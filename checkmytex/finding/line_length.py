"""
Checker for detecting overly long lines in LaTeX source code.

Long lines make diffs harder to read in version control and reduce code readability.
This checker helps enforce consistent line length limits.
"""

import re
import typing

from checkmytex.latex_document import LatexDocument, Origin
from checkmytex.latex_document.indexed_string import TextPosition
from checkmytex.latex_document.origin import OriginPointer
from checkmytex.latex_document.source import FilePosition

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

    def _create_origin_from_raw_file_line(
        self,
        document: LatexDocument,
        filename: str,
        line_start_pos: int,
        line_end_pos: int,
    ) -> Origin:
        """
        Create an origin from raw file line positions.

        Args:
            document: The LaTeX document
            filename: The file containing the line
            line_start_pos: Start position of the line in raw file
            line_end_pos: End position of the line in raw file

        Returns:
            Origin object pointing to the location
        """
        try:
            # Get the file's indexed text (raw content)
            file_indexed = document.sources.files[filename]

            # Convert positions to TextPosition objects
            begin_text_pos = file_indexed.get_detailed_position(line_start_pos)
            end_text_pos = file_indexed.get_detailed_position(line_end_pos)

            # Create FilePosition objects
            begin_file_pos = FilePosition(filename, begin_text_pos)
            end_file_pos = FilePosition(filename, end_text_pos)

            # Try to find nearby content in processed source for source positions
            line_idx = begin_text_pos.line

            # Search for this line or nearby lines in processed source
            for offset in range(20):
                for direction in [0] if offset == 0 else [1, -1]:
                    check_line = line_idx + (offset * direction)
                    if 0 <= check_line < file_indexed.num_lines():
                        check_content = str(file_indexed.get_line(check_line)).strip()
                        if (
                            check_content
                            and not check_content.startswith("%")
                            and len(check_content) > 10
                        ):
                            # Try to find this in processed source
                            search_pattern = re.escape(
                                check_content[: min(40, len(check_content))]
                            )
                            try:
                                source_matches = list(
                                    document.find_in_source(search_pattern)
                                )
                                for source_match in source_matches:
                                    if source_match.get_file() == filename:
                                        # Use this match's source positions
                                        return Origin(
                                            OriginPointer(
                                                begin_file_pos,
                                                source_match.begin.source,
                                            ),
                                            OriginPointer(
                                                end_file_pos, source_match.end.source
                                            ),
                                        )
                            except Exception:
                                continue

            # Fallback: create with dummy source positions
            dummy_source_pos = TextPosition(0, 0, 0)
            return Origin(
                OriginPointer(begin_file_pos, dummy_source_pos),
                OriginPointer(end_file_pos, dummy_source_pos),
            )

        except Exception as e:
            self.log(f"Warning: Could not create origin: {e}")
            return document.get_simplified_origin_of_source(0, 1)

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        """
        Check document for overly long lines.

        Args:
            document: The LaTeX document to check

        Yields:
            Problem objects for each line that exceeds max_length
        """
        self.log(f"Checking for lines longer than {self.max_length} characters...")

        # Check each file in raw format (to see actual source file lines)
        for filename in document.files():
            file_content = document.get_file_content(filename)
            lines = file_content.split("\n")

            for line_num, line in enumerate(lines, 1):
                line_length = len(line)

                if line_length > self.max_length:
                    try:
                        # Calculate position in file
                        line_start = sum(
                            len(prev_line) + 1 for prev_line in lines[: line_num - 1]
                        )
                        line_end = line_start + line_length

                        # Create origin from raw file position
                        origin = self._create_origin_from_raw_file_line(
                            document, filename, line_start, line_end
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
                        long_id = f"{rule}|{filename}:{line_num}|{context}"

                        yield Problem(
                            origin=origin,
                            message=message,
                            context=context,
                            long_id=long_id,
                            tool="LineLengthChecker",
                            rule=rule,
                            look_up_url=None,
                        )
                    except Exception as e:
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
