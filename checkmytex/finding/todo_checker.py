"""
Checker for detecting TODO, FIXME, XXX comments and \\todo{} commands.

These markers indicate unfinished work and should be resolved before
publishing the final document.
"""

import re
import typing

from checkmytex.latex_document import LatexDocument, Origin
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

    def _create_origin_from_file_position(
        self,
        document: LatexDocument,
        filename: str,
        line_num: int,
        context_length: int = 50
    ) -> Origin:
        """
        Create an origin directly from a file line number.

        This creates an origin that points to a specific line in a file,
        and attempts to map it to the corresponding position in the processed source.

        Args:
            document: The LaTeX document
            filename: The file containing the TODO
            line_num: The line number (1-indexed) where the TODO is located
            context_length: Approximate length for the origin range

        Returns:
            Origin object pointing to the location
        """
        # Get the file's indexed text
        file_indexed = document.sources.files[filename]

        # Convert to 0-indexed line number
        line_idx = line_num - 1

        # Get the text position at the start of this line in the file
        file_begin_pos = file_indexed.get_detailed_position((line_idx, 0))

        # Get end position (same line, some characters forward)
        file_end_pos = file_indexed.get_detailed_position((line_idx, min(context_length, 80)))

        # Now we need to find where this file line maps to in the flat source
        # We'll search the flat source for content from this file line
        try:
            # Get the actual content of the line
            line_content = file_indexed.get_line(line_idx)
            line_text = str(line_content).strip()

            # Try to find this line in the processed source
            # Remove comments and try to match actual content
            if line_text and not line_text.startswith('%'):
                # This line has non-comment content, try to find it in source
                search_pattern = re.escape(line_text[:40])
                source_matches = list(document.find_in_source(search_pattern))
                if source_matches:
                    return source_matches[0]

            # If the line itself is a comment or not found, look at nearby lines
            for offset in range(1, 20):
                # Try lines after first (TODOs are often right before relevant content)
                for direction in [1, -1]:
                    nearby_line_idx = line_idx + (offset * direction)
                    if 0 <= nearby_line_idx < file_indexed.num_lines():
                        nearby_content = str(file_indexed.get_line(nearby_line_idx)).strip()
                        if nearby_content and not nearby_content.startswith('%') and len(nearby_content) > 10:
                            # Try to find this content
                            search_pattern = re.escape(nearby_content[:40])
                            source_matches = list(document.find_in_source(search_pattern))
                            if source_matches:
                                return source_matches[0]

            # Last resort: use document start
            return document.get_simplified_origin_of_source(0, 1)

        except Exception as e:
            self.log(f"Warning: Could not create origin for {filename}:{line_num}: {e}")
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

        # Pattern for comment-based TODO markers
        # Matches: % TODO: ..., % FIXME: ..., % XXX: ...
        comment_pattern = r"%\s*(TODO|FIXME|XXX)[\s:](.*?)$"

        # Pattern for \\todo{} commands
        # Matches: \todo{...} and \todo[...]{...}
        todo_cmd_pattern = r"\\todo(\[[^\]]*\])?\{(?P<content>[^}]*)\}"

        # Check each file in the document
        # Comments and \todo commands are often stripped from get_source(),
        # so we need to check the raw file content
        for filename in document.files():
            file_content = document.get_file_content(filename)

            # Check for comment-based TODO markers
            for match in re.finditer(comment_pattern, file_content, re.MULTILINE):
                marker_type = match.group(1)
                marker_text = match.group(2).strip()

                try:
                    # Calculate line number in raw file
                    lines = file_content[:match.start()].split('\n')
                    line_num = len(lines)

                    # Use the full match as context, limited to reasonable length
                    context = match.group(0)
                    if len(context) > 80:
                        context = context[:77] + "..."

                    # Create origin using the helper method
                    origin = self._create_origin_from_file_position(
                        document, filename, line_num
                    )

                    message = f"{marker_type} comment found: {marker_text if marker_text else '(no description)'}"

                    rule = f"TODO_MARKER_{marker_type}"
                    long_id = f"{rule}|{filename}:{line_num}|{context}"

                    yield Problem(
                        origin=origin,
                        message=message,
                        context=context,
                        long_id=long_id,
                        tool="TodoChecker",
                        rule=rule,
                        look_up_url=None
                    )
                except Exception as e:
                    self.log(f"Warning: Could not process {marker_type} marker: {e}")
                    continue

            # Check for \\todo{} commands
            for match in re.finditer(todo_cmd_pattern, file_content):
                todo_content = match.group("content").strip()

                try:
                    # Create readable context
                    context = match.group(0)
                    if len(context) > 80:
                        context = context[:77] + "..."

                    # Calculate line number in raw file
                    lines = file_content[:match.start()].split('\n')
                    line_num = len(lines)

                    # First, try to find the actual \todo command in the processed source
                    # This should work if the \todo is not inside a comment
                    todo_text = match.group(0)
                    search_text = todo_text[:min(50, len(todo_text))]
                    search_pattern = re.escape(search_text)
                    source_matches = list(document.find_in_source(search_pattern))

                    if source_matches:
                        # Found the \todo command itself in the source
                        origin = source_matches[0]
                    else:
                        # The \todo is commented out or not in processed source
                        # Use the helper method to find nearby content
                        origin = self._create_origin_from_file_position(
                            document, filename, line_num
                        )

                    message = f"\\todo command found: {todo_content if todo_content else '(empty)'}"

                    rule = "TODO_MARKER_CMD"
                    long_id = f"{rule}|{filename}:{line_num}|{context}"

                    yield Problem(
                        origin=origin,
                        message=message,
                        context=context,
                        long_id=long_id,
                        tool="TodoChecker",
                        rule=rule,
                        look_up_url="https://ctan.org/pkg/todonotes"
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
