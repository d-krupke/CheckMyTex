import typing
import re

from checkmytex.latex_document import LatexDocument
from checkmytex.checker.abstract_checker import Checker
from checkmytex.problem import Problem


class SiUnitx(Checker):
    def __init__(self):
        expr = r"(^|[}])[^{\d]*(?P<number>\d+[,.\d]+)\s*($|[^}\s])"
        self.regex = re.compile(expr)

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        print("Running SiUnitx-check...")
        source = document.get_source()
        for match in self.regex.finditer(source):
            origin = document.get_origin_of_source(match.start("number"),
                                                   match.end("number"))
            message = "It seems like you are using native numbers/units. " \
                      "Prefer using `siunitx` with `\\num{123}` for numbers," \
                      " `\\range{1}{3}` for ranges, and `\\SI{60}{\\second}`" \
                      " for units. The syntax may have changed. Please check" \
                      " the manual of `siunitx`. `siunitx` takes care of" \
                      " proper spacing and uniform units."
            context = document.get_source_context(origin)
            rule = "SIUNITX"
            yield Problem(origin, message, context,
                          long_id=f"{rule}: {context}",
                          rule=rule, tool="SIUNITX")

    def is_available(self) -> bool:
        return True
