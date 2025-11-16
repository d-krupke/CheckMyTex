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
                    # Calculate line number in raw file
                    lines = file_content[:match.start()].split('\n')
                    line_num = len(lines)

                    # Use the full match as context, limited to reasonable length
                    context = match.group(0)
                    if len(context) > 80:
                        context = context[:77] + "..."

                    # Look for substantial non-comment LaTeX content nearby
                    # that we can reliably find in the processed source
                    file_lines = file_content.split('\n')
                    origin = None
                    search_radius = 15  # Look up to 15 lines away

                    # Try multiple nearby lines, with preference for closer lines
                    candidates = []
                    for offset in range(-search_radius, search_radius + 1):
                        idx = line_num - 1 + offset
                        if 0 <= idx < len(file_lines):
                            line_text = file_lines[idx].strip()
                            # Skip empty lines, comment lines, and very short lines
                            if (line_text and
                                not line_text.startswith('%') and
                                len(line_text) > 10):
                                # Prefer lines with LaTeX commands
                                priority = 0
                                if '\\' in line_text:
                                    priority += 2
                                if len(line_text) > 30:
                                    priority += 1
                                candidates.append((abs(offset), priority, line_text))

                    # Sort by priority (higher first), then by distance (closer first)
                    candidates.sort(key=lambda x: (-x[1], x[0]))

                    # Try to find each candidate in the processed source
                    for _, _, line_text in candidates[:10]:  # Try up to 10 candidates
                        # Try different substring lengths for better matching
                        for length in [60, 40, 25, 15]:
                            if len(line_text) >= length:
                                search_text = line_text[:length]
                                # Escape special regex characters
                                search_pattern = re.escape(search_text)
                                try:
                                    source_matches = list(document.find_in_source(search_pattern))
                                    if source_matches:
                                        origin = source_matches[0]
                                        break
                                except Exception:
                                    continue
                        if origin:
                            break

                    # If we still don't have an origin, try to use the document structure
                    # to at least get close to the right section
                    if origin is None:
                        # Look for section headings or other structural elements nearby
                        for offset in range(-20, 20):
                            idx = line_num - 1 + offset
                            if 0 <= idx < len(file_lines):
                                line_text = file_lines[idx]
                                # Look for section commands
                                section_match = re.search(r'\\(section|subsection|subsubsection|chapter|paragraph)\{([^}]+)\}', line_text)
                                if section_match:
                                    section_title = section_match.group(2)[:30]
                                    # Try to find this section in the processed source
                                    search_pattern = re.escape(section_title)
                                    source_matches = list(document.find_in_source(search_pattern))
                                    if source_matches:
                                        origin = source_matches[0]
                                        break

                    # Last resort: use document start
                    if origin is None:
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

                    # Calculate line number in raw file
                    lines = file_content[:match.start()].split('\n')
                    line_num = len(lines)

                    origin = None

                    # First, try to find the actual \todo command in the processed source
                    # This should work if the \todo is not inside a comment
                    todo_text = match.group(0)
                    # Search for a unique portion of the \todo command
                    search_text = todo_text[:min(50, len(todo_text))]
                    search_pattern = re.escape(search_text)
                    source_matches = list(document.find_in_source(search_pattern))
                    if source_matches:
                        origin = source_matches[0]

                    # If that didn't work, look for nearby LaTeX content
                    if origin is None:
                        file_lines = file_content.split('\n')
                        search_radius = 15

                        # Try multiple nearby lines, with preference for closer lines
                        candidates = []
                        for offset in range(-search_radius, search_radius + 1):
                            if offset == 0:  # Skip the line with \todo itself
                                continue
                            idx = line_num - 1 + offset
                            if 0 <= idx < len(file_lines):
                                line_text = file_lines[idx].strip()
                                # Skip empty lines, comment lines, lines with \todo, and very short lines
                                if (line_text and
                                    not line_text.startswith('%') and
                                    '\\todo' not in line_text and
                                    len(line_text) > 10):
                                    # Prefer lines with LaTeX commands
                                    priority = 0
                                    if '\\' in line_text:
                                        priority += 2
                                    if len(line_text) > 30:
                                        priority += 1
                                    candidates.append((abs(offset), priority, line_text))

                        # Sort by priority (higher first), then by distance (closer first)
                        candidates.sort(key=lambda x: (-x[1], x[0]))

                        # Try to find each candidate in the processed source
                        for _, _, line_text in candidates[:10]:  # Try up to 10 candidates
                            # Try different substring lengths for better matching
                            for length in [60, 40, 25, 15]:
                                if len(line_text) >= length:
                                    search_text = line_text[:length]
                                    search_pattern = re.escape(search_text)
                                    try:
                                        source_matches = list(document.find_in_source(search_pattern))
                                        if source_matches:
                                            origin = source_matches[0]
                                            break
                                    except Exception:
                                        continue
                            if origin:
                                break

                    # Try to find section headings if still no origin
                    if origin is None:
                        file_lines = file_content.split('\n')
                        for offset in range(-20, 20):
                            idx = line_num - 1 + offset
                            if 0 <= idx < len(file_lines):
                                line_text = file_lines[idx]
                                section_match = re.search(r'\\(section|subsection|subsubsection|chapter|paragraph)\{([^}]+)\}', line_text)
                                if section_match:
                                    section_title = section_match.group(2)[:30]
                                    search_pattern = re.escape(section_title)
                                    source_matches = list(document.find_in_source(search_pattern))
                                    if source_matches:
                                        origin = source_matches[0]
                                        break

                    # Last resort: use document start
                    if origin is None:
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
