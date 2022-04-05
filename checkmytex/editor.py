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

    def __init__(self, editor=None, pattern=None):
        self.editor = editor if editor else os.environ.get("EDITOR")
        if pattern:
            self.editor_pattern = pattern
        else:
            self.editor_pattern = self._patterns.get(
                self.editor.split("/")[-1],
                self._default_pattern)

    def open(self, file, line) -> int:
        with open(file, "r") as f:
            l1 = len(f.readlines())
        cmd = self.editor_pattern.format(e=self.editor, f=file, l=line + 1)
        subprocess.call(cmd, shell=True)
        with open(file, "r") as f:
            l2 = len(f.readlines())
        return l2 - l1
