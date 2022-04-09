import re
import typing

from checkmytex.latex_document import LatexDocument
from checkmytex.checker import Checker
from checkmytex.problem import Problem


class UniformNpHard(Checker):
    """
    There are different styles of writing NP-hard/complete in LaTeX. This module checks
    if the style is mixed.
    """

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        print("Checking for uniform NP-hardness usage...")
        expr = r"((^)|(\s))(?P<np>(\$?[Nn][Pp]\$?)|(\$?\\((math)|(text))cal\{[Nn][Pp]\}\$?))-(([Hh]ard)|([Cc]omplete))"
        variants_np = set()
        for match in re.finditer(expr, document.get_source()):
            variants_np.add(match.group("np").strip())
            if len(variants_np) <= 1:
                continue
            origin = document.get_origin_of_source(match.start(), match.end())
            context = document.get_source_context(origin)
            message = "Non-uniform 'NP'. Maybe use the 'complexity'-package?"
            rule = 'UNIFORM-NP'
            yield Problem(origin, context=context, message=message,
                          long_id=rule + "|" + context, tool="UniformNP", rule=rule,
                          look_up_url="https://ctan.org/pkg/complexity")

    def is_available(self) -> bool:
        return True
