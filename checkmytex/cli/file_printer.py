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
        for i, line_content in enumerate(lines):
            if self._shorten is None:
                yield i, line_content

            def in_range(problem):
                begin = problem.origin.begin.file.position.line - self._shorten
                end = problem.origin.end.file.position.line + self._shorten
                return begin <= i < end

            if any(in_range(p) for p in problems):
                yield i, line_content

    def _print_line(self, file_name, line_number, line):
        problems = self._analyzed_document.get_problems(file_name, line_number)

        def span(p):
            a = (
                p.origin.begin.file.position.line_offset
                if p.origin.begin.file.position.line == line_number
                else 0
            )
            b = (
                p.origin.end.file.position.line_offset
                if p.origin.end.file.position.line == line_number
                else len(line)
            )
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
        line_problems = [
            p for p in line_problems if p.origin.end.file.position.line == i
        ]
        for p in line_problems:
            self._print_problem(p)
            self._problem_handler(p)

    def print(self, file_path: str):
        source = self._analyzed_document.get_file_content(file_path)
        lines = source.split("\n")
        problems = self._analyzed_document.get_problems(file_path)
        # Print Header
        print_header(file_path)
        log(f"{len(problems)} problem{'s' if len(problems) != 1 else ''} found.")
        # Print lines
        last_printed_line = -1
        for i, line in self._enumerate_relevant_lines(lines, problems):
            if i != last_printed_line + 1:
                print("...")
            last_printed_line = i
            self._print_line(file_path, i, line)
            self._handle_line_problems(file_path, i)
        if len(lines) != last_printed_line + 1:
            print("...")
