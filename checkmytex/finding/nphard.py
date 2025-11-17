"""
Simple module for finding inconsisting writing style of NP-hard/complete.
Common problem with documents in theoretical computer science.
"""

import re
import typing

from checkmytex.latex_document import LatexDocument

from .abstract_checker import Checker
from .problem import Problem


class UniformNpHard(Checker):
    """
    There are different styles of writing NP-hard/complete in LaTeX. This module checks
    if the style is mixed.
    """

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        self.log("Checking for uniform NP-hardness usage...")
        expr = (
            r"((^)|(\s))"
            r"(?P<np>(\$?\\?[Nn][Pp]\$?)"
            r"|(\$?\\((math)|(text))cal\{[Nn][Pp]\}\$?))"
            r"-(([Hh]ard)|([Cc]omplete))"
        )
        variants_np = set()
        for match in re.finditer(expr, str(document.get_source())):
            cmd = match.group("np").strip()
            if "\\NP" in cmd:  # $\NP$ and \NP can be mixed with no problem
                variants_np.add("\\NP")
                continue  # do not create a warning for usage of \\NP
            variants_np.add(cmd)
            if len(variants_np) <= 1:
                continue

            origin = document.get_simplified_origin_of_source(
                match.start(), match.end()
            )
            context = document.get_source_context(origin)
            message = "Non-uniform 'NP'. Maybe use the 'complexity'-package?"
            rule = "UNIFORM-NP"
            yield Problem(
                origin,
                context=context,
                message=message,
                long_id=rule + "|" + context,
                tool="UniformNP",
                rule=rule,
                look_up_url="https://ctan.org/pkg/complexity",
            )

    def is_available(self) -> bool:
        return True
