import typing

from checkmytex.finding.problem import Problem
from checkmytex.latex_document import LatexDocument


class AnalyzedDocument:
    def __init__(self, document: LatexDocument, problems: typing.Iterable[Problem]):
        self.document = document
        self.problems = list(problems)
        self._on_false_positive: typing.Optional[
            typing.Callable[[Problem], None]
        ] = None

    def set_on_false_positive_cb(
        self, on_false_positive: typing.Callable[[Problem], None]
    ):
        self._on_false_positive = on_false_positive

    def mark_as_false_positive(self, problem: Problem):
        while problem in self.problems:
            self.problems.remove(problem)
        if self._on_false_positive:
            self._on_false_positive(problem)

    def remove_if(self, func: typing.Callable[[Problem], bool]) -> int:
        to_remove = [p for p in self.problems if func(p)]
        for p in to_remove:
            self.problems.remove(p)
        return len(to_remove)

    def remove_similar(self, problem: Problem) -> int:
        return self.remove_if(lambda p: problem.long_id == p.long_id)

    def remove_with_rule(self, rule: str, tool: typing.Optional[str] = None) -> int:
        if tool:
            return self.remove_if(lambda p: p.rule == rule and p.tool == tool)
        else:
            return self.remove_if(lambda p: p.rule == rule)

    def get_problems(
        self, file: typing.Optional[str] = None, line: typing.Optional[int] = None
    ) -> typing.List[Problem]:
        if file:
            problems = [p for p in self.problems if p.origin.file == file]
            if line:
                problems = [
                    p
                    for p in problems
                    if p.origin.begin.row <= line <= p.origin.end.row
                ]
            return problems
        else:
            return self.problems

    def list_files(self) -> typing.Iterable[str]:
        for f in self.document.files():
            yield f

    def get_file_content(self, f) -> str:
        return self.document.get_file_content(f)
