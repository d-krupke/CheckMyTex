import re
import typing

from checkmytex.latex_document import LatexDocument

from .abstract_checker import Checker
from .problem import Problem


class Cleveref(Checker):
    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        self.log("Checking for cleveref usage...")
        # \ref instead of smarter \cref
        for match in re.finditer(r"\\ref\{[^\}]+\}", document.get_source()):
            origin = document.get_origin_of_source(match.start(), match.end())
            context = document.get_source_context(origin)
            message = (
                "Prefer using cleveref's \\cref or \\Cref instead of native \\ref."
            )
            rule = "CREF"
            yield Problem(
                origin,
                context=context,
                message=message,
                long_id=rule + "|" + context,
                tool="CleverrefCheck",
                rule=rule,
                look_up_url="https://ctan.org/pkg/cleveref?lang=en",
            )
        # \cref instead of \Cref at beginning of sentence
        expr = r"\.\s*(?P<cref>\\cref\{[^\}]+\})"  # ". \cref{xxx}"
        for match in re.finditer(expr, document.get_source()):
            origin = document.get_origin_of_source(
                match.start("cref"), match.end("cref")
            )
            context = document.get_source_context(origin)
            message = "Use \\Cref instead of \\cref at the beginning of a sentence."
            rule = "CREF-CAPTION"
            yield Problem(
                origin,
                context=context,
                message=message,
                long_id=rule + "|" + context,
                tool="CleverrefCheck",
                rule=rule,
                look_up_url="https://ctan.org/pkg/cleveref?lang=en",
            )

    def is_available(self) -> bool:
        return True
