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

    def _edit(self, problem):
        f = problem.origin.file
        line = problem.origin.begin.file.position.line
        self.editor.open(file=f, line=line)
        return True

    def _next_file(self, problem):
        self._skip_file = problem.origin.file
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
        if o.begin.text.index is not None and o.end.text.index is not None:
            text = self.analyzed_document.document.get_text()
            begin = max(0, o.begin.text.index - n)
            end = min(len(text), o.end.text.index + n)
            print_detail(
                "Text: " + text[begin : o.begin.text.index],
                text[o.begin.text.index : o.end.text.index],
                text[o.end.text.index : end],
            )
        if None not in (o.begin.source.index, o.end.source.index):
            source = self.analyzed_document.document.get_source()
            begin = max(0, o.begin.source.index - n)
            end = min(len(source), o.end.source.index + n)
            print_detail(
                "Source: " + source[begin : o.begin.source.index],
                source[o.begin.source.index : o.end.source.index],
                source[o.end.source.index : end],
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
                for l in range(origin.begin.source.line, origin.end.source.line + 1):
                    source = (
                        self.analyzed_document.document.sources.flat_source.get_line(l)
                    )
                    print_simple_line(l, source)
            log("Searching in source...")
            for origin in self.analyzed_document.document.find_in_source(pattern):
                print(origin)
                for l in range(origin.begin.source.line, origin.end.source.line + 1):
                    source = (
                        self.analyzed_document.document.sources.flat_source.get_line(l)
                    )
                    print_simple_line(l, source)
        return False

    def __call__(self, problem: Problem):
        if problem.origin.file == self._skip_file:
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
