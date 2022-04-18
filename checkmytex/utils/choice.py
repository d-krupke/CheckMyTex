import typing


class OptionPrompt:
    """
    A simple helper for getting an input from multiple options.
    """

    def __init__(self, front="\033[94m", end=":\033[0m"):
        self._options = {}
        self._front = front
        self._end = end
        self._texts = []
        self._help = {}
        self._help_options = ("h", "help")

    def add_option(
        self,
        key: str,
        text: str,
        func: typing.Callable,
        help_: typing.Optional[str] = None,
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
        for k, h in self._help.items():
            print(f"[{k}] {h}")

    def _is_valid_option(self, option):
        return option in self._options or option in self._help_options

    def _input(self):
        text = ",".join(self._texts)
        return input(f"{self._front}{text}{self._end}")

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
