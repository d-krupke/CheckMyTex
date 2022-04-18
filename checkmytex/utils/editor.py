import os
import subprocess


class Editor:
    """
    For opening the editor.
    """

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
        if pattern:
            self.editor_pattern = pattern
        else:
            self.editor_pattern = self._patterns.get(
                self.editor.split("/")[-1], self._default_pattern
            )

    def _number_of_lines(self, f):
        with open(f, "r") as f:
            return len(f.readlines())

    def open(self, file, line) -> int:
        l1 = self._number_of_lines(file)
        offset = self.offsets.get(file, 0) if self.remember_offsets else 0
        cmd = self.editor_pattern.format(e=self.editor, f=file, l=line + 1 + offset)
        subprocess.call(cmd, shell=True)
        l2 = self._number_of_lines(file)
        offset += l2 - l1
        self.offsets[file] = offset
        return offset
