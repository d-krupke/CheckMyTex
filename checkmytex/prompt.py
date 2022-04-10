import webbrowser

from checkmytex.latex_document import LatexDocument
from checkmytex.editor import Editor
from checkmytex.highlighted_output import print_problem, print_line
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
        finished = False
        while not finished:
            option = None
            while option not in self._options:
                option = input(f"{self._front}{','.join(self._texts)}{self._end}")
            finished = self._options[option](*args, **kwargs)


def print_detail(pre, text, post):
    print(
        "\033[94m" + pre.replace('\n', ' ') +
        "\033[4m" + text.replace('\n', ' ') +
        "\033[0m\033[94m" + post.replace('\n', ' ') + "\033[0m")


class ProblemHandlerPrompt:

    def __init__(self, document: LatexDocument, whitelist: Whitelist, editor: Editor):
        self.document = document
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

    def _print_details(self, problem: Problem):
        print("\033[94mMessage:", problem.message)
        print("Tool:", problem.tool)
        print("Rule:", problem.rule)
        print("Context:", problem.context.replace("\n", " "))
        o = problem.origin
        n = 40
        if None not in (o.begin.tpos, o.end.tpos):
            text = self.document.get_text()
            b = max(0, o.begin.tpos - n)
            e = min(len(text), o.end.tpos + n)
            print_detail("Text: " + text[b:o.begin.tpos],
                         text[o.begin.tpos: o.end.tpos], text[o.end.tpos: e])
        if None not in (o.begin.spos, o.end.spos):
            source = self.document.get_source()
            b = max(0, o.begin.spos - n)
            e = min(len(source), o.end.spos + n)
            print_detail("Source: " + source[b:o.begin.spos],
                         source[o.begin.spos: o.end.spos], source[o.end.spos: e])
        print("Position:", problem.origin, "\033[0m")
        return False

    def find(self, problem: Problem):
        print("Use this find-utility to compare with other occurrences.")
        pattern = input("Find pattern (regex):")
        if pattern:
            print("Searching in text...")
            for origin in self.document.find_in_text(pattern):
                print(origin)
                for l in range(origin.begin.row, origin.end.row + 1):
                    source = self.document.get_file_content(origin.file).split("\n")
                    print_line(source[l], l, [])
            print("Searching in source...")
            for origin in self.document.find_in_source(pattern):
                print(origin)
                for l in range(origin.begin.row, origin.end.row + 1):
                    source = self.document.get_file_content(origin.file).split("\n")
                    print_line(source[l], l, [])
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
        prompt.add_option("f", "[f]ind", self.find)
        prompt.add_option("?", "[?]", self._print_details)
        if problem.look_up_url:
            prompt.add_option("l", "[l]ook up", self._look_up)
        prompt(problem)
