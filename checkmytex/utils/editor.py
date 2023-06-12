"""
Provides a class to open editors at specific lines and try to guess the
line number after (sequential) changes in the file.
"""
import logging
import os
import subprocess
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

    _patterns = {
        "nano": "{e} +{l} {f}",
        "vim": "{e} +{l} {f}",
        "gvim": "{e} +{l} {f}",
        "nvim": "{e} +{l} {f}",
    }
    _default_pattern = "{e} {f}"

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
        Open file in editor at line. If file has changed, try to guess
         position.
        :param file: Path to file
        :param line: Line number
        :return: Change in line number.
        """
        if not self.editor:
            _log.error("No editor found. Please set $EDITOR.")
            return 0
        n_lines_before = _number_of_lines(file)
        offset: int = self.offsets.get(file, 0) if self.remember_offsets else 0
        cmd = self.editor_pattern.format(e=self.editor, f=file, l=line + 1 + offset)
        subprocess.call(cmd, shell=True)
        n_lines_after = _number_of_lines(file)
        offset += n_lines_after - n_lines_before
        self.offsets[file] = offset
        return offset
