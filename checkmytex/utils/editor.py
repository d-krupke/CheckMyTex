"""
Provides a class to open editors at specific lines and try to guess the
line number after (sequential) changes in the file.
"""

import logging
import os
import shlex
import subprocess
import typing
from pathlib import Path


def _number_of_lines(file_path: str) -> int:
    with Path(file_path).open() as file:
        return len(file.readlines())


_log = logging.getLogger(__name__)


class Editor:
    """
    For opening the editor.
    """

    # Disable warning about too few public methods. We use a class to remember
    # the state.
    # pylint: disable=too-few-public-methods

    _patterns: typing.ClassVar[dict[str, str]] = {
        "nano": "{e} +{l} {f}",
        "vim": "{e} +{l} {f}",
        "gvim": "{e} +{l} {f}",
        "nvim": "{e} +{l} {f}",
    }
    _default_pattern: typing.ClassVar[str] = "{e} {f}"

    def __init__(self, editor=None, pattern=None, remember_offsets=True):
        self.editor = editor if editor else os.environ.get("EDITOR")
        self.offsets = {}
        self.remember_offsets = remember_offsets
        if not self.editor:
            _log.error("No editor found. Please set $EDITOR.")
            return
        if pattern:
            self.editor_pattern = pattern
        else:
            self.editor_pattern = self._patterns.get(
                self.editor.split("/")[-1], self._default_pattern
            )

    def open(self, file: str, line: int) -> int:
        """
        Open file in editor at line. If file has changed, try to guess position.

        Args:
            file: Path to file
            line: Line number

        Returns:
            Change in line number

        Raises:
            subprocess.SubprocessError: If editor command fails
        """
        if not self.editor:
            _log.error("No editor found. Please set $EDITOR.")
            return 0

        n_lines_before = _number_of_lines(file)
        offset: int = self.offsets.get(file, 0) if self.remember_offsets else 0

        # Format the command string
        cmd_str = self.editor_pattern.format(e=self.editor, f=file, l=line + 1 + offset)

        # Use shlex.split to safely parse the command and execute without shell=True
        try:
            cmd_list = shlex.split(cmd_str)
            subprocess.call(cmd_list, shell=False)
        except (subprocess.SubprocessError, OSError, ValueError) as e:
            _log.error(f"Failed to open editor: {e}")
            return 0

        n_lines_after = _number_of_lines(file)
        offset += n_lines_after - n_lines_before
        self.offsets[file] = offset
        return offset
