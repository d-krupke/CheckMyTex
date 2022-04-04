import argparse
import typing
import webbrowser

from .document_checker import DocumentChecker
from .editor import Editor
from .latex_document import LatexDocument
from .problem import Problem
from .whitelist import Whitelist


def print_line(line: str, line_number: int, problems: typing.List[Problem]):
    highlighted_line = []
    highlighting = False
    j = 0
    for i, c in enumerate(line):
        if problems and (
                problems[j].origin.begin.row < line_number or problems[
            j].origin.begin.col == i):
            if not highlighting:
                highlighting = True
                highlighted_line.append("\033[91m\033[4m")
        highlighted_line.append(c)
        if problems and problems[j].origin.end.row == line_number and problems[
            j].origin.end.col == i:
            if highlighting:
                highlighting = False
                highlighted_line.append("\033[0m")
                j = min(len(problems) - 1, j + 1)
    if highlighting:
        highlighted_line.append("\033[0m")
    highlighted_line = "".join(highlighted_line).replace("\n", "")
    print(f"\x1b[0;30;47m{line_number}:\x1b[0m", highlighted_line)


def handle_problem(problem: Problem, whitelist: Whitelist, editor: Editor):
    print_problem(problem)
    while True:
        if problem.look_up_url:
            option = input(
                "[s]kip,[S]kip all,[I]gnore rule,[w]hitelist,[e]dit,[l]ook up:")
        else:
            option = input(
                "[s]kip,[S]kip all,[I]gnore rule,[w]hitelist,[e]dit:")
        if option == "w":
            whitelist.add(problem)
            return
        if option == "e":
            editor.open(file=problem.origin.file,
                        line=problem.origin.begin.row)
            return
        if option == "S":
            whitelist.add_temporary(problem)
            return
        if option == "s":
            return
        if problem.look_up_url and option == "l":
            webbrowser.open(problem.look_up_url)
        if option == 'I':
            whitelist.add_rule_temporary(problem.rule)
            return


def print_problem(problem: Problem):
    print(f" >>>  \033[93m{problem.message}\033[0m")


def get_relevant_row_indices(problems: typing.Iterable[Problem]) -> typing.Set[
    int]:
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


def print_file_head(f: str):
    print(f"\x1b[0;30;47m{'=' * len(f)}\x1b[0m")
    print(f"\033[95m{f}\033[0m")
    print(f"\x1b[0;30;47m{'=' * len(f)}\x1b[0m")


class InteractiveCli:
    def __init__(self, main_file: str, whitelist_path: str = None,
                 just_print: bool = False):
        editor = Editor()
        whitelist = Whitelist(whitelist_path)
        latex_document = LatexDocument(main_file)
        for f, problems in DocumentChecker().find_problems(latex_document,
                                                           whitelist):
            print_file_head(f)
            relevant_rows = get_relevant_row_indices(problems)
            last_printed_row = -1
            for i, l in enumerate(
                    latex_document.get_file_content(f).split("\n")):
                if i not in relevant_rows:
                    if last_printed_row == i - 1:
                        print(" ...")
                    continue
                last_printed_row = i
                line_problems = [p for p in problems if
                                 p.origin.begin.row <= i <= p.origin.end.row]
                print_line(l, i, line_problems)
                for p in line_problems:
                    if p.origin.end.row == i and p not in whitelist:
                        if just_print:
                            print_problem(p)
                        else:
                            handle_problem(p, whitelist, editor)


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
    InteractiveCli(args.path[0], whitelist_path=args.w if args.w else None,
                   just_print=args.print)

