import typing

from checkmytex.analyzed_document import AnalyzedDocument
from checkmytex.cli.highlighted_output import (
    ColorCodes,
    add_highlights,
    log,
    print_header,
)
from checkmytex.finding import Problem


class FilePrinter:
    def __init__(
        self,
        analyzed_document: AnalyzedDocument,
        problem_handler,
        shorten: typing.Optional[int] = 3,
    ):
        self._shorten = shorten
        self._problem_handler = problem_handler
        self._analyzed_document = analyzed_document

    def _enumerate_relevant_lines(self, lines, problems):
        for i, l in enumerate(lines):
            if self._shorten is None:
                yield i, l

            def in_range(p):
                b = p.origin.begin.row - self._shorten
                e = p.origin.end.row + self._shorten
                return b <= i < e

            if any(in_range(p) for p in problems):
                yield i, l

    def _print_line(self, file_name, line_number, line):
        problems = self._analyzed_document.get_problems(file_name, line_number)

        def span(p):
            a = p.origin.begin.col if p.origin.begin.row == line_number else 0
            b = p.origin.end.col if p.origin.end.row == line_number else len(line)
            return a, b

        highlighted_line = add_highlights(line, (span(p) for p in problems))
        print(
            f"{ColorCodes.BLACK_ON_WHITE}{line_number}:{ColorCodes.ENDC}",
            highlighted_line,
        )

    def _print_problem(self, p: Problem):
        print(f" >>> {ColorCodes.WARNING}{p.message}{ColorCodes.ENDC} ({p.tool})")

    def _handle_line_problems(self, f, i):
        line_problems = self._analyzed_document.get_problems(f, line=i)
        line_problems = [p for p in line_problems if p.origin.end.row == i]
        for p in line_problems:
            self._print_problem(p)
            self._problem_handler(p)

    def print(self, f: str):
        source = self._analyzed_document.get_file_content(f)
        lines = source.split("\n")
        problems = self._analyzed_document.get_problems(f)
        # Print Header
        print_header(f)
        log(f"{len(problems)} problem{'s' if len(problems) != 1 else ''} found.")
        # Print lines
        last_printed_line = -1
        for i, l in self._enumerate_relevant_lines(lines, problems):
            if i != last_printed_line + 1:
                print("...")
            last_printed_line = i
            self._print_line(f, i, l)
            self._handle_line_problems(f, i)
        if len(lines) != last_printed_line + 1:
            print("...")
