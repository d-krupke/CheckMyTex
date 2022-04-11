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

    def add_option(self, key, text, func, help=None):
        if text:
            self._texts.append(text)
        if help:
            self._help[key] = help
        self._options[key] = func

    def help(self):
        for k, h in self._help.items():
            print(f"[{k}] {h}")

    def _is_valid_option(self, option):
        return option in self._options or option in self._help_options

    def _input(self):
        text = ','.join(self._texts)
        return input(f"{self._front}{text}{self._end}")

    def __call__(self, *args, **kwargs):
        finished = False
        while not finished:
            option = None
            while not self._is_valid_option(option):
                option = self._input()
            if self._help and option in self._help_options:
                self.help()
            else:
                finished = self._options[option](*args, **kwargs)