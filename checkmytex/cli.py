import argparse
import os.path
import typing

from .document_checker import DocumentChecker
from checkmytex.utils.editor import Editor
from .highlighted_output import print_line, print_problem, highlight, log, print_header
from .latex_document import LatexDocument
from checkmytex.checker.problem import Problem
from .prompt import ProblemHandlerPrompt
from .whitelist import Whitelist


def get_relevant_row_indices(problems: typing.Iterable[Problem]) \
        -> typing.Set[int]:
    relevant_rows = set()
    for p in problems:
        for i in range(0, 3):
            relevant_rows.add(p.origin.begin.row + i)
            relevant_rows.add(p.origin.end.row + i)
            relevant_rows.add(p.origin.begin.row - i)
            relevant_rows.add(p.origin.end.row - i)
        for i in range(p.origin.begin.row, p.origin.end.row + 1):
            relevant_rows.add(i)
    return relevant_rows


class InteractiveCli:
    def _print_no_problems(self, n):
        if n == 0:
            log("No problems found.")
        elif n == 1:
            log("1 problem found.")
        else:
            log(f"{n} problems found.")

    def _process_file(self, f, problems):
        print_header(f)
        self._print_no_problems(len(problems))
        relevant_rows = get_relevant_row_indices(problems)
        last_printed_row = -1
        for i, l in enumerate(
                self.latex_document.get_file_content(f).split("\n")):
            if i not in relevant_rows:
                if last_printed_row == i - 1:
                    print(" ...")
                continue
            last_printed_row = i
            line_problems = [p for p in problems
                             if p.origin.begin.row <= i <= p.origin.end.row
                             and p not in self.whitelist]
            print_line(l, i, line_problems)
            for p in line_problems:
                if p.origin.end.row == i and p not in self.whitelist:
                    if self.just_print:
                        print_problem(p)
                    else:
                        self.problem_handler(p)

    def __init__(self,
                 main_file: str,
                 whitelist_path: str = None,
                 just_print: bool = False):
        self.just_print = just_print
        self.editor = Editor()
        self.whitelist = Whitelist(whitelist_path)
        log("Parsing LaTeX project...")
        self.latex_document = LatexDocument(main_file)
        self.problem_handler = ProblemHandlerPrompt(self.latex_document,
                                                    self.whitelist,
                                                    self.editor)
        doc_checker = DocumentChecker()
        problems = list(doc_checker.find_problems(self.latex_document,
                                                  self.whitelist))
        problems_of_files = {f: ps for f, ps in
                             doc_checker.sort_problems_by_file(
                                 self.latex_document,
                                 problems)}
        # Print overview
        print_header("Overview")
        print(highlight(f"Found {len(problems)} problems in the document."))
        for f, ps in problems_of_files.items():
            if len(ps) == 0:
                print(f + ":", "no problems.")
            elif len(ps) == 1:
                print(f + ":", highlight("1 problem."))
            else:
                print(f + ":", highlight(f"{len(ps)} problems."))
        # Go through all files
        for f, ps in problems_of_files.items():
            remaining_ps = list(self.whitelist.filter(ps))
            self._process_file(f, remaining_ps)


def main():
    parser = argparse.ArgumentParser(
        description='CheckMyTex: A simple tool for checking your LaTeX.')
    parser.add_argument('-w', help='Path to whitelist', type=str)
    parser.add_argument('--print', action="store_true",
                        help="Just print the output")
    parser.add_argument('path', nargs=1, help="Path to main.tex")
    args = parser.parse_args()
    if not args.path:
        parser.print_help()
        exit(1)
    if args.w:
        whitelist = args.w
    else:
        path = os.path.dirname(args.path[0])
        whitelist = os.path.join(path, ".whitelist.txt")
        log(f"Saving whitelist to {whitelist}")
    InteractiveCli(args.path[0], whitelist_path=whitelist,
                   just_print=args.print)
