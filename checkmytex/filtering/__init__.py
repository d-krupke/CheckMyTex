"""
A collection of filters to filter issues found by the checker/tools in
 `finding'.
"""

from .authors import IgnoreLikelyAuthorNames, IgnoreWordsFromBibliography
from .code_listings import IgnoreCodeListings
from .filter import (
    Filter,
    IgnoreIncludegraphics,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreSpellingWithMath,
)
from .math_mode import MathMode
from .whitelist import Whitelist

__all__ = [
    "Filter",
    "IgnoreCodeListings",
    "IgnoreIncludegraphics",
    "IgnoreLikelyAuthorNames",
    "IgnoreRefs",
    "IgnoreRepeatedWords",
    "IgnoreSpellingWithMath",
    "IgnoreWordsFromBibliography",
    "MathMode",
    "Whitelist",
]
