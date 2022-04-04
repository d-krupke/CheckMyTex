import re
import os

from .problem import Problem


class Whitelist:
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
        self._rules = set()
        if self._path and os.path.exists(path):
            self.load(path)

    def __contains__(self, item: Problem):
        if not isinstance(item, Problem):
            raise ValueError("Can only check for problems")
        return item.short_id.strip() in self._shortkeys or item.rule in self._rules

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

    def add_temporary(self, problem: Problem) -> None:
        """
        Ignore a problem temporarily (without saving).
        :param problem: The problem to be temporarily ignored.
        :return: None
        """
        self._shortkeys.add(problem.short_id.strip())

    def add(self, problem: Problem, comment: str = None) -> None:
        """
        Adds a problem to the whitelist. If the whitelist is initiated
        from a file, the problem will directly be appended to the file.
        :param problem: The problem to be whitelisted.
        :param comment: Comment describing the problem.
        :return: None
        """
        self._shortkeys.add(problem.short_id.strip())
        self._whitelist[problem.short_id.strip()] = comment if comment else problem.long_id
        if self._on_add:
            self._on_add(problem)
        if self._path:
            self._save_problem(problem, comment)

    def add_rule_temporary(self, rule: str) -> None:
        """
        Ignores all problems of a specific rule for the rest of the analysis.
        :param rule: The rule to be ignored (can be found in Problem.rule)
        :return: None
        """
        self._rules.add(rule)

    def _save_problem(self, problem, comment):
        with open(self._path, "a") as f:
            f.write(f"{problem.short_id} # {comment if comment else problem.long_id}\n")
