"""
Checker for detecting TODO, FIXME, XXX comments and \\todo{} commands.

These markers indicate unfinished work and should be resolved before
publishing the final document.
"""

import re
import typing

from checkmytex.latex_document import LatexDocument

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
                    # Try to find the context text (the line before or after the comment)
                    # in the processed source to create a proper origin
                    lines = file_content[:match.start()].split('\n')
                    line_num = len(lines)

                    # Use the full match as context, limited to reasonable length
                    context = match.group(0)
                    if len(context) > 80:
                        context = context[:77] + "..."

                    # Try to find nearby text in the source to create an origin
                    # Look for text in the same or nearby lines
                    file_lines = file_content.split('\n')
                    nearby_text = None
                    for offset in [0, -1, 1, -2, 2]:
                        idx = line_num - 1 + offset
                        if 0 <= idx < len(file_lines):
                            line_text = file_lines[idx].strip()
                            # Skip empty lines and comment lines
                            if line_text and not line_text.startswith('%'):
                                nearby_text = line_text[:50]  # Use first 50 chars
                                break

                    if nearby_text:
                        # Try to find this text in the source
                        # Escape the search pattern since find_in_source uses regex
                        search_pattern = re.escape(nearby_text[:20])
                        source_matches = list(document.find_in_source(search_pattern))
                        if source_matches:
                            # Use the first match to create an origin
                            origin = source_matches[0]
                        else:
                            # Fallback: use beginning of document
                            origin = document.get_simplified_origin_of_source(0, 1)
                    else:
                        # Fallback: use beginning of document
                        origin = document.get_simplified_origin_of_source(0, 1)

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

                    # Try to find nearby text for origin
                    lines = file_content[:match.start()].split('\n')
                    line_num = len(lines)

                    file_lines = file_content.split('\n')
                    nearby_text = None
                    for offset in [0, -1, 1]:
                        idx = line_num - 1 + offset
                        if 0 <= idx < len(file_lines):
                            line_text = file_lines[idx].strip()
                            if line_text and not line_text.startswith('%') and '\\todo' not in line_text:
                                nearby_text = line_text[:50]
                                break

                    if nearby_text:
                        # Escape the search pattern since find_in_source uses regex
                        search_pattern = re.escape(nearby_text[:20])
                        source_matches = list(document.find_in_source(search_pattern))
                        if source_matches:
                            origin = source_matches[0]
                        else:
                            origin = document.get_simplified_origin_of_source(0, 1)
                    else:
                        origin = document.get_simplified_origin_of_source(0, 1)

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
