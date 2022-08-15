"""
Module for finding raw numbers and units in the LaTeX-document.
SIUnitX is much better in formatting them.
"""

import re
import typing

from checkmytex.latex_document import LatexDocument

from .abstract_checker import Checker
from .problem import Problem


def _looks_like_year(num: str):
    if re.fullmatch("[21][0-9][0-9][0-9]", num):
        return 1900 <= int(num) <= 2030
    return False


class SiUnitx(Checker):
    """
    Displaying numbers and units uniformly and nicely can be difficult.
     SIUnitX is a great latex-package that helps you with it.
    This module is overly sensitive because detecting units is difficult.
     While numbers are not a problem when they are small, units should
      always be encapsulated by \\SI
    """

    def __init__(self):
        super().__init__()
        expr = r"(^|[}])[^{=\d\[]*(?P<number>\d+[,.\d\s]+)\s*($|[^}\s])"
        self.regex = re.compile(expr)

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        self.log("Running SiUnitx-check...")
        source = document.get_source()
        for match in self.regex.finditer(source):
            num = match.group("number").strip()
            if len(num) == 1 or (len(num) == 2 and num[1] in (".", ",")):
                # Don't complain about small numbers.
                continue
            if _looks_like_year(num):  # many false positives.
                continue
            origin = document.get_simplified_origin_of_source(
                match.start("number"), match.end("number")
            )
            message = (
                "Use siunitx to get nice and uniform numbers "
                "(\\num{} at least for >=10 000)"
                " and units (\\SI{}{} for all sizes)."
            )

            context = document.get_source_context(origin)
            rule = "SIUNITX"
            yield Problem(
                origin,
                message,
                context,
                long_id=f"{rule}: {context}",
                rule=rule,
                tool="SIUNITX",
                look_up_url="https://ctan.org/pkg/siunitx?lang=en",
            )

    def is_available(self) -> bool:
        return True
