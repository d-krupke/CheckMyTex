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
        self.editor_pattern = pattern if pattern else self._patterns.get(self.editor.split("/")[-1],
                                                                         self._default_pattern)

    def open(self, file, line):
        subprocess.call(self.editor_pattern.format(e=self.editor, f=file, l=line+1), shell=True)
