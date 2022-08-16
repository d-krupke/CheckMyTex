import webbrowser

from checkmytex.analyzed_document import AnalyzedDocument
from checkmytex.finding import Problem
from checkmytex.utils import Editor, OptionPrompt

from .highlighted_output import log


def print_simple_line(i, l):
    print(f"{i}: {l}")


def print_detail(pre, text, post):
    print(
        pre.replace("\n", " ")
        + "\033[4m"
        + text.replace("\n", "\\n")
        + "\033[0m"
        + post.replace("\n", "\\n")
    )


class InteractiveProblemHandler:
    def __init__(self, document: AnalyzedDocument, editor: Editor):
        self.analyzed_document = document
        self.editor = editor
        self._skip_file = None

    def _skip_all(self, problem):
        self.analyzed_document.remove_similar(problem)
        return True

    def _whitelist_problem(self, problem):
        self.analyzed_document.mark_as_false_positive(problem)
        return True

    def _ignore_all(self, problem):
        self.analyzed_document.remove_with_rule(problem.rule)
        return True

    def _edit(self, problem: Problem):
        f = problem.origin.get_file()
        line = problem.origin.get_file_line()
        self.editor.open(file=f, line=line)
        return True

    def _next_file(self, problem):
        self._skip_file = problem.origin.get_file()
        return True

    def _look_up(self, problem):
        webbrowser.open(problem.look_up_url)
        return False

    def _print_details(self, problem: Problem):
        print("Message:", problem.message)
        print("Tool:", problem.tool)
        print("Rule:", problem.rule)
        print("Context:", problem.context.replace("\n", " "))
        o = problem.origin
        n = 40
        t_span = o.get_text_span()
        if t_span:
            text = self.analyzed_document.document.get_text()
            begin = max(0, t_span[0] - n)
            end = min(len(text), t_span[1] + n)
            print_detail(
                "Text: " + text[begin : t_span[0]],
                text[t_span[0] : t_span[1]],
                text[t_span[1] : end],
            )
        s_span = o.get_source_span()
        if s_span:
            source = self.analyzed_document.document.get_source()
            s_span = o.get_source_span()
            begin = max(0, s_span[0] - n)
            end = min(len(source),s_span[1] + n)
            print_detail(
                "Source: " + source[begin : s_span[0]],
                source[s_span[0] : s_span[1]],
                source[s_span[1] : end],
            )
        print("Position:", problem.origin)
        return False

    def find(self, problem: Problem):
        log("Use this find-utility to compare with other occurrences.")
        pattern = input("Find pattern (regex):")
        if pattern:
            log("Searching in text...")
            for origin in self.analyzed_document.document.find_in_text(pattern):
                print(origin)
                l = origin.get_source_line()
                source = self.analyzed_document.document.get_source(l)
                print_simple_line(l, source)
            log("Searching in source...")
            for origin in self.analyzed_document.document.find_in_source(pattern):
                print(origin)
                l = origin.get_source_line()
                source = self.analyzed_document.document.get_source(l)
                print_simple_line(l, source)
        return False

    def __call__(self, problem: Problem):
        if problem.origin.get_file() == self._skip_file:
            return
        prompt = OptionPrompt()
        prompt.add_option(
            "s", "[s]kip", lambda p: True, help_="Skip to the next problem."
        )
        prompt.add_option(
            "S", "[S]kip all", self._skip_all, help_="Skip all similar problems."
        )
        prompt.add_option(
            "w", "[w]hitelist", self._whitelist_problem, help_="Mark as false positive."
        )
        prompt.add_option(
            "I",
            "[I]gnore all",
            self._ignore_all,
            help_="Skip over all problems of this rule.",
        )
        prompt.add_option(
            "n", "[n]ext file", self._next_file, help_="Skip to next file."
        )
        prompt.add_option("x", None, lambda p: exit(0), help_="Exit.")
        prompt.add_option("exit", None, lambda p: exit(0))
        prompt.add_option("q", None, lambda p: exit(0))
        prompt.add_option(
            "e",
            "[e]dit",
            self._edit,
            help_="Open editor ($EDITOR) to fix this problem.",
        )
        prompt.add_option(
            "f",
            "[f]ind",
            self.find,
            help_="Quickly search the documents text and source.",
        )
        prompt.add_option("?", None, self._print_details, help_="Print details.")
        if problem.look_up_url:
            prompt.add_option("l", "[l]ook up", self._look_up)
        prompt(problem)
