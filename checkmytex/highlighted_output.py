import typing

from checkmytex.problem import Problem


def highlight(s: str):
    return f"\033[91m\033[4m{s}\x1b[0m"


def add_highlights(line: str,
                   highlights: typing.Iterable[typing.Tuple[int, int]]) -> str:
    highlights = list(highlights)
    if not highlights:
        return line
    highlights.sort()
    hb, he = highlights[0]
    highlighted_line = line[:hb]
    for h in highlights:
        if he >= h[0]:
            he = h[1]
        else:
            highlighted_line += highlight(line[hb:he])
            highlighted_line += line[he:h[0]]
            hb = h[0]
            he = h[1]
    highlighted_line += highlight(line[hb:he] if hb != he else " ")
    highlighted_line += line[he:]
    return highlighted_line


def print_line(line: str, line_number: int,
               problems: typing.Iterable[Problem]):
    def span(p):
        a = p.origin.begin.col if p.origin.begin.row == line_number else 0
        b = p.origin.end.col if p.origin.end.row == line_number else len(line)
        return a, b

    highlighted_line = add_highlights(line, (span(p) for p in problems))
    print(f"\x1b[0;30;47m{line_number}:\x1b[0m", highlighted_line)


def print_problem(problem: Problem):
    print(f" >>>  \033[93m{problem.message}\033[0m")


def print_file_head(f: str):
    print(f"\x1b[0;30;47m{'=' * len(f)}\x1b[0m")
    print(f"\033[95m{f}\033[0m")
    print(f"\x1b[0;30;47m{'=' * len(f)}\x1b[0m")
