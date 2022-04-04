import re

from checkmytex.problem import Problem


class Whitelist:
    def __init__(self, path: str = None, on_add=None):
        self._shortkeys = set()
        self._whitelist = {}
        self._on_add = on_add
        self._path = path
        self._rules = set()
        if self._path and os.path.exists(path):
            self.load(path)

    def __contains__(self, item: Problem):
        return item.short_id.strip() in self._shortkeys or item.rule in self._rules

    def load(self, path: str):
        regex = re.compile("^(?P<key>\w+)\s*#?(?P<comment>(.*$)|($))")
        with open(path, "r") as f:
            for line in f.readlines():
                match = regex.fullmatch(line.strip())
                if match:
                    key = match.group("key").strip()
                    comment = match.group("comment").strip()
                    self._whitelist[key] = comment
                    self._shortkeys.add(key)

    def save(self, path):
        with open(path, "w") as f:
            for key, comment in self._whitelist.items():
                f.write(f"{key} # {comment}\n")

    def add_temporary(self, problem: Problem):
        self._shortkeys.add(problem.short_id.strip())

    def add(self, problem: Problem, comment: str = None):
        self._shortkeys.add(problem.short_id.strip())
        self._whitelist[problem.short_id.strip()] = comment if comment else problem.long_id
        if self._on_add:
            self._on_add(problem)
        if self._path:
            self._save_problem(problem, comment)

    def add_rule_temporary(self, rule):
        self._rules.add(rule)

    def _save_problem(self, problem, comment):
        with open(self._path, "a") as f:
            f.write(f"{problem.short_id} # {comment if comment else problem.long_id}\n")