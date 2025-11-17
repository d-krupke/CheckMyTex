"""
Checker for detecting TODO, FIXME, XXX comments and \\todo{} commands.

These markers indicate unfinished work and should be resolved before
publishing the final document.
"""

import re
import typing

from checkmytex.latex_document import LatexDocument, Origin
from checkmytex.latex_document.indexed_string import TextPosition
from checkmytex.latex_document.origin import OriginPointer
from checkmytex.latex_document.source import FilePosition

from .abstract_checker import Checker
from .problem import Problem


class TodoChecker(Checker):
    """
    Checks for TODO, FIXME, XXX comments and \\todo{} commands.

    Helps ensure no draft markers or unfinished work remains in the
    final document before publication.
    """

    def __init__(self, log: typing.Callable = print):
        """
        Initialize the TODO Checker.

        Args:
            log: Logging function (default: print)
        """
        super().__init__(log)

    def _create_origin_from_raw_file_match(
        self, document: LatexDocument, filename: str, match_start: int, match_end: int
    ) -> Origin:
        """
        Create an origin directly from raw file positions.

        Args:
            document: The LaTeX document
            filename: The file containing the match
            match_start: Start position in the raw file content
            match_end: End position in the raw file content

        Returns:
            Origin object pointing to the location
        """
        try:
            # Get the file's indexed text (raw content)
            file_indexed = document.sources.files[filename]

            # Convert positions to TextPosition objects
            begin_text_pos = file_indexed.get_detailed_position(match_start)
            end_text_pos = file_indexed.get_detailed_position(match_end)

            # Create FilePosition objects
            begin_file_pos = FilePosition(filename, begin_text_pos)
            end_file_pos = FilePosition(filename, end_text_pos)

            # We need source positions too for the OriginPointer
            # Since the TODO might not exist in processed source, we'll use
            # a position from nearby processed content

            # Try to find a nearby position in the processed source that corresponds
            # to this file location by searching for content on the same or nearby lines
            line_idx = begin_text_pos.line

            # Search for content on this line or nearby lines that exists in processed source
            for offset in range(50):
                for direction in [0] if offset == 0 else [1, -1]:
                    check_line = line_idx + (offset * direction)
                    if 0 <= check_line < file_indexed.num_lines():
                        line_content = str(file_indexed.get_line(check_line)).strip()
                        if (
                            line_content
                            and not line_content.startswith("%")
                            and len(line_content) > 10
                        ):
                            # Try to find this in processed source
                            search_pattern = re.escape(
                                line_content[: min(40, len(line_content))]
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
            self.log(f"Warning: Could not create origin from raw positions: {e}")
            return document.get_simplified_origin_of_source(0, 1)

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        """
        Check document for TODO markers.

        Args:
            document: The LaTeX document to check

        Yields:
            Problem objects for each TODO marker found
        """
        self.log("Checking for TODO/FIXME/XXX markers...")

        # Patterns for TODO markers
        comment_pattern = r"%\s*(TODO|FIXME|XXX)[\s:](.*?)$"
        todo_cmd_pattern = r"\\todo(\[[^\]]*\])?\{(?P<content>[^}]*)\}"

        # Check each file in raw format
        # (Comments and \todo commands are stripped from processed source)
        for filename in document.files():
            file_content = document.get_file_content(filename)

            # 1. Check for comment-based TODO markers (% TODO: ...)
            for match in re.finditer(comment_pattern, file_content, re.MULTILINE):
                marker_type = match.group(1)
                marker_text = match.group(2).strip()

                try:
                    context = match.group(0)
                    if len(context) > 80:
                        context = context[:77] + "..."

                    # Create origin from the exact raw file match position
                    origin = self._create_origin_from_raw_file_match(
                        document, filename, match.start(), match.end()
                    )

                    message = f"{marker_type} comment found: {marker_text if marker_text else '(no description)'}"

                    rule = f"TODO_MARKER_{marker_type}"
                    # Use origin's file line for the ID
                    long_id = (
                        f"{rule}|{filename}:{origin.get_file_line() + 1}|{context}"
                    )

                    yield Problem(
                        origin=origin,
                        message=message,
                        context=context,
                        long_id=long_id,
                        tool="TodoChecker",
                        rule=rule,
                        look_up_url=None,
                    )
                except Exception as e:
                    self.log(f"Warning: Could not process {marker_type} marker: {e}")
                    continue

            # 2. Check for \todo{} commands
            for match in re.finditer(todo_cmd_pattern, file_content):
                todo_content = match.group("content").strip()

                try:
                    context = match.group(0)
                    if len(context) > 80:
                        context = context[:77] + "..."

                    # Create origin from the exact raw file match position
                    origin = self._create_origin_from_raw_file_match(
                        document, filename, match.start(), match.end()
                    )

                    message = f"\\todo command found: {todo_content if todo_content else '(empty)'}"

                    rule = "TODO_MARKER_CMD"
                    long_id = (
                        f"{rule}|{filename}:{origin.get_file_line() + 1}|{context}"
                    )

                    yield Problem(
                        origin=origin,
                        message=message,
                        context=context,
                        long_id=long_id,
                        tool="TodoChecker",
                        rule=rule,
                        look_up_url="https://ctan.org/pkg/todonotes",
                    )
                except Exception as e:
                    self.log(f"Warning: Could not process \\todo command: {e}")
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
        return "TODO Checker is built-in and requires no installation."
