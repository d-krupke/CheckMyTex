import webbrowser

from checkmytex.editor import Editor
from checkmytex.highlighted_output import print_problem
from checkmytex.problem import Problem
from checkmytex.whitelist import Whitelist


class OptionPrompt:
    def __init__(self, front="", end=":"):
        self._options = {}
        self._front = front
        self._end = end
        self._texts = []

    def add_option(self, key, text, func):
        self._texts.append(text)
        self._options[key] = func

    def __call__(self, *args, **kwargs):
        option = None
        while option not in self._options:
            option = input(f"{self._front}{','.join(self._texts)}{self._end}")
        return self._options[option](*args, **kwargs)


class ProblemHandlerPrompt:

    def __init__(self, whitelist: Whitelist, editor: Editor):
        self.whitelist = whitelist
        self.editor = editor

    def _skip_all(self, problem):
        self.whitelist.add_temporary(problem)
        return True

    def _whitelist_problem(self, p):
        self.whitelist.add(p)
        return True

    def _ignore_all(self, p):
        self.whitelist.add_rule_temporary(p.rule)
        return True

    def _edit(self, problem):
        f = problem.origin.file
        line = problem.origin.begin.row
        self.editor.open(file=f, line=line)
        return True

    def _next_file(self, problem):
        self.whitelist.skip_file(problem.origin.file)
        return True

    def _look_up(self, problem):
        webbrowser.open(problem.look_up_url)
        return False

    def __call__(self, problem: Problem):
        print_problem(problem)
        prompt = OptionPrompt()
        prompt.add_option("s", "[s]kip", lambda p: True)
        prompt.add_option("S", "[S]kip all", self._skip_all)
        prompt.add_option("w", "[w]hitelist", self._whitelist_problem)
        prompt.add_option("I", "[I]gnore all", self._ignore_all)
        prompt.add_option("n", "[n]ext file", self._next_file)
        prompt.add_option("x", "e[x]it", lambda p: exit(0))
        prompt.add_option("e", "[e]dit", self._edit)
        if problem.look_up_url:
            prompt.add_option("l", "[l]ook up", self._look_up)
        prompt(problem)
