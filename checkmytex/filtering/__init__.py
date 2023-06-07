"""
A collection of filters to filter issues found by the checker/tools in
 `finding'.
"""
# flake8: noqa F401
from .authors import IgnoreLikelyAuthorNames, IgnoreWordsFromBibliography
from .filter import (
    Filter,
    IgnoreIncludegraphics,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreSpellingWithMath,
)
from .math_mode import MathMode
from .whitelist import Whitelist
