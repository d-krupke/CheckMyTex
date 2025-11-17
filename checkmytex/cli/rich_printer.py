from __future__ import annotations

import os.path
import typing
import webbrowser
from collections import defaultdict

from rich.console import Console
from rich.markup import escape
from rich.pretty import pprint
from rich.syntax import Syntax
from rich.table import Table

from checkmytex import AnalyzedDocument
from checkmytex.finding import Problem
from checkmytex.utils import Editor, OptionPrompt


class ProblemHandler:
    def __init__(self, document: AnalyzedDocument, editor: Editor, console: Console):
        self.analyzed_document = document
        self.editor = editor
        self.console = console
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
        pprint(problem.serialize())
        return False

    def find(self, _problem: Problem):
        self.console.log("Use this find-utility to compare with other occurrences.")
        pattern = self.console.input("Find pattern (regex):")
        if pattern:
            self.console.log("Searching in text...")
            for origin in self.analyzed_document.document.find_in_text(pattern):
                self.console.log(str(origin))
                self.console.print(
                    escape(
                        f"{origin.get_file()}[{origin.get_file_line()}] {self.analyzed_document.document.get_file_content(origin.get_file(), origin.get_file_line())}"
                    )
                )
            self.console.log("Searching in source...")
            for origin in self.analyzed_document.document.find_in_source(pattern):
                self.console.log(str(origin))
                self.console.print(
                    escape(
                        f"{origin.get_file()}[{origin.get_file_line()}] {self.analyzed_document.document.get_file_content(origin.get_file(), origin.get_file_line())}"
                    )
                )
        return False

    def __call__(self, problem: Problem):
        if problem.origin.get_file() == self._skip_file:
            return
        prompt = OptionPrompt(
            lambda s: self.console.input(escape(s + ":")),
            lambda s: self.console.print(escape(s)),
        )
        prompt.add_option(
            "s", "[s]kip", lambda _: True, help_="Skip to the next problem."
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
        prompt.add_option("x", None, lambda _: exit(0), help_="Exit.")
        prompt.add_option("exit", None, lambda _: exit(0))
        prompt.add_option("q", None, lambda _: exit(0))
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


class RichPrinter:
    def __init__(
        self,
        analysis: AnalyzedDocument,
        shorten: int | None = 5,
        problem_handler: typing.Callable[[Problem], None] | None = None,
        console: Console | None = None,
    ):
        self.problem_handler = problem_handler
        self.analysis = analysis
        self.console = Console(record=True) if console is None else console
        self.shorten = shorten
        self.file_prefix = os.path.commonpath(list(self.analysis.list_files()))

    def print(self):
        self.console.print("CheckMyTex", style="bold italic")
        self.print_file_overview()
        self.print_rule_count()
        for filename in self.analysis.list_files():
            self.print_file(filename)
        self.print_orphaned_problems()

    def to_html(self, path):
        self.print()
        self.console.save_html(path)

    def print_orphaned_problems(self):
        problems = self.analysis.get_orphaned_problems()
        if not problems:
            return
        self.console.rule("Other problems")
        for prob in problems:
            self.print_problem(prob)

    def print_rule_count(self):
        table = Table(title="Problems by type", expand=True)
        table.add_column("Tool", justify="left")
        table.add_column("Rule", justify="left")
        table.add_column("Count", justify="right")
        problem_counts = defaultdict(lambda: defaultdict(lambda: 0))
        for prob in self.analysis.get_problems():
            problem_counts[prob.tool][prob.rule] += 1
        for tool, rules in problem_counts.items():
            first = True
            for rule, count in rules.items():
                if first:
                    table.add_row(escape(str(tool)), escape(str(rule)), str(count))
                    first = False
                else:
                    table.add_row("", escape(str(rule)), str(count))
        self.console.print(table)

    def print_file_overview(self):
        table = Table(title="Problems by file", expand=True)
        table.add_column("File", justify="left")
        table.add_column("Count", justify="right")
        for file in self.analysis.list_files():
            table.add_row(
                escape(str(file[len(self.file_prefix) :])),
                str(len(self.analysis.get_problems(file))),
            )
        if self.analysis.get_orphaned_problems():
            table.add_row("UNKNOWN", str(len(self.analysis.get_orphaned_problems())))
        self.console.print(table)

    def print_file(self, filename: str):
        self.console.print()
        self.console.rule(filename[len(self.file_prefix) :])
        self.console.print()
        last_printed_line = -1
        problematic_lines = list(
            {
                prob.origin.get_file_line()
                for prob in self.analysis.get_problems(filename)
            }
        )
        problematic_lines.sort()
        for line_num in problematic_lines:
            if self.shorten is not None:
                l_ = max(last_printed_line + 1, line_num - self.shorten)
            else:
                l_ = last_printed_line + 1
            if l_ != 0 and l_ != last_printed_line + 1:
                self.console.print("...")
            problems = self.analysis.get_problems(filename, line_num)
            highlights = [
                (
                    prob.origin.get_file_line(),
                    prob.origin.begin.file.position.line_offset,
                    prob.origin.end.file.position.line_offset,
                )
                for prob in problems
            ]
            assert l_ <= line_num
            self.print_source(filename, l_, line_num + 1, highlights)
            last_printed_line = line_num
            for prob in problems:
                self.print_problem(prob)
        if self.shorten is None:
            file_length = len(
                self.analysis.document.get_file_content(filename).split("\n")
            )
            if file_length > last_printed_line + 1:
                self.print_source(filename, last_printed_line + 1, file_length, [])

    def print_source(
        self,
        filename,
        begin,
        end,
        highlights: typing.Iterable[tuple[int, int, int]],
    ):
        text = "".join(
            self.analysis.document.get_file_content(filename, i)
            for i in range(begin, end)
        )
        if not text:
            return
        if text[-1] == "\n":
            text = text[:-1]
        syntax = Syntax(
            text,
            "latex",
            start_line=begin,
            line_numbers=True,
            word_wrap=True,
            tab_size=1,
        )
        for line_no, begin_off, end_off in highlights:
            syntax.stylize_range(
                "white on red",
                (1 + line_no - begin, begin_off),
                (1 + line_no - begin, end_off),
            )
        self.console.print(syntax)

    def print_problem(self, problem: Problem):
        self.console.print(
            escape(f">>> [{problem.tool}] {problem.message}"), style="red on white"
        )
        if self.problem_handler is not None:
            self.problem_handler(problem)
