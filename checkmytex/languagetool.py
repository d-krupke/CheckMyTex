import json
import shutil
import typing

from .abstract_checker import Checker
from .latex_document import LatexDocument
from .problem import Problem


class Languagetool(Checker):
    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        print("Running Langugagetool...")
        result, err, ex = self._run(
            f"{shutil.which('languagetool')} --json -l en-US "
            f"--disable "
            f"MORFOLOGIK_RULE_EN_US,"
            f"WHITESPACE_RULE,"
            f"COMMA_PARENTHESIS_WHITESPACE",
            input=document.get_text())
        data = json.loads(result)
        for problem in data["matches"]:
            try:
                look_up_url = problem["rule"]["urls"][0]["value"]
            except KeyError:
                look_up_url = None
            origin = document.get_origin_of_text(problem["offset"],
                                                 problem["offset"] +
                                                 problem["length"])
            yield Problem(origin=origin,
                          context=problem["context"]["text"],
                          message=problem["message"],
                          long_id=problem["message"]
                                  + problem["context"]["text"],
                          rule=problem["rule"]["id"],
                          tool="languagetool",
                          look_up_url=look_up_url)

    def is_available(self) -> bool:
        return bool(shutil.which("languagetool"))

    def needs_detex(self):
        return True

    def installation_guide(self) -> str:
        return "You can probably install install languagetool directly" \
               " with your package manager.\n" \
               " e.g. brew install languagetool\n" \
               "      apt-get install languagetool\n" \
               "      pacman -S languagetool\n" \
               "...\n" \
               "Otherwise, you can install it by hand:" \
               " https://github.com/languagetool-org/languagetool"
