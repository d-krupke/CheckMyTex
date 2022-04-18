import os
import re
import typing

from checkmytex.filtering.filter import Filter
from checkmytex.finding.problem import Problem
from checkmytex.latex_document import LatexDocument


class Whitelist(Filter):
    """
    Managing the whitelist, skipped problems, and ignored rules.
    """

    def __init__(self, path: str = None, on_add=None):
        """
        :param path: File to initialize the whitelist from. If you do not want the new problems to be automatically
        appended, use `load` instead.
        :param on_add: Callback [Problem]->None that is called on newly whitelisted problems.
        """
        self._shortkeys = set()
        self._whitelist = {}
        self._on_add = on_add
        self._path = path
        if self._path and os.path.exists(path):
            self.load(path)

    def __contains__(self, item: Problem):
        if not isinstance(item, Problem):
            raise ValueError("Can only check for problems")
        o = item.origin
        return item.short_id.strip() in self._shortkeys

    def load(self, path: str) -> None:
        """
        Load content of a whitelist. Each line contains a whitelisted item in the form `KEY # Comment`
        :param path: Path to the whitelist file.
        :return: None
        """
        regex = re.compile("^(?P<key>\w+)\s*#?(?P<comment>(.*$)|($))")
        with open(path, "r") as f:
            for line in f.readlines():
                match = regex.fullmatch(line.strip())
                if match:
                    key = match.group("key").strip()
                    comment = match.group("comment").strip()
                    self._whitelist[key] = comment
                    self._shortkeys.add(key)

    def save(self, path: str) -> None:
        """
        Save the whitelisted items to a file. All whitelisted items will be written.
        Note that when the whitelist is initialized from a file, all new keys will
        directly be appended.
        :param path: Path to write.
        :return: None
        """
        with open(path, "w") as f:
            for key, comment in self._whitelist.items():
                f.write(f"{key} # {comment}\n")

    def prepare(self, document: LatexDocument):
        pass

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for p in problems:
            if p not in self:
                yield p

    def add(self, problem: Problem, comment: str = None) -> None:
        """
        Adds a problem to the whitelist. If the whitelist is initiated
        from a file, the problem will directly be appended to the file.
        :param problem: The problem to be whitelisted.
        :param comment: Comment describing the problem.
        :return: None
        """
        self._shortkeys.add(problem.short_id.strip())
        key = problem.short_id.strip()
        comment = (
            comment
            if comment
            else f'{problem.tool}: {problem.message} - "{problem.context}"'
        )
        self._whitelist[key] = comment
        if self._on_add:
            self._on_add(problem)
        if self._path:
            self._save_problem(problem, comment)

    def _save_problem(self, problem, comment):
        with open(self._path, "a") as f:
            f.write(f"{problem.short_id} # {comment if comment else problem.long_id}\n")
