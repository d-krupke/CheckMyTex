"""
Provides a simple class for CLI option prompt.
"""

import typing


class OptionPrompt:
    """
    A simple helper for getting an input from multiple options.
    """

    def __init__(self, read=input, write=print, front="", end=""):
        self._options = {}
        self._read = read
        self._write = write
        self._front = front
        self._end = end
        self._texts = []
        self._help = {}
        self._help_options = ("h", "help")

    def add_option(
        self,
        key: str,
        text: str | None,
        func: typing.Callable,
        help_: str | None = None,
    ) -> None:
        """
        Adds an option.
        :param key: The key to choose the option, e.g. 'x'.
        :param text: The text to print in the prompt, e.g., 'e[x]it'.
        :param func: The function to call on selection.
        :param help_: The text to show in help.
        :return: No return.
        """
        if text:
            self._texts.append(text)
        if help_:
            self._help[key] = help_
        self._options[key] = func

    def print_help(self):
        """
        Prints help.
        :return: None
        """
        for key, help_text in self._help.items():
            self._write(f"[{key}] {help_text}")

    def _is_valid_option(self, option):
        return option in self._options or option in self._help_options

    def _input(self):
        text = ",".join(self._texts)
        return self._read(f"{self._front}{text}{self._end}")

    def __call__(self, *args, **kwargs):
        finished = False
        while not finished:
            option = None
            while not self._is_valid_option(option):
                option = self._input()
            if self._help and option in self._help_options:
                self.print_help()
            else:
                finished = self._options[option](*args, **kwargs)
