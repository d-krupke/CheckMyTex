import typing
import re

from checkmytex.latex_document import LatexDocument
from checkmytex.checker.abstract_checker import Checker
from checkmytex.problem import Problem


class SiUnitx(Checker):
    def __init__(self):
        expr = r"(^|[}])[^{=\d\[]*(?P<number>\d+[,.\d\s]+)\s*($|[^}\s])"
        self.regex = re.compile(expr)

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        print("Running SiUnitx-check...")
        source = document.get_source()
        for match in self.regex.finditer(source):
            num = match.group("number").strip()
            if len(num) == 1 or (len(num) == 2 and num[1] in (".", ",")):
                # Don't complain about small numbers.
                continue
            origin = document.get_origin_of_source(match.start("number"),
                                                   match.end("number"))
            message = "Use siunitx to get nice and uniform numbers and units."

            context = document.get_source_context(origin)
            rule = "SIUNITX"
            yield Problem(origin, message, context,
                          long_id=f"{rule}: {context}",
                          rule=rule, tool="SIUNITX",
                          look_up_url="https://ctan.org/pkg/siunitx?lang=en")

    def is_available(self) -> bool:
        return True
