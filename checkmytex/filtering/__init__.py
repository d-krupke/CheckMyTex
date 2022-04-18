"""
A collection of filters to filter issues found by the checker/tools in
 `finding'.
"""
from .authors import IgnoreLikelyAuthorNames, IgnoreWordsFromBibliography
from .filter import (
    Filter,
    IgnoreIncludegraphics,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreSpellingWithMath,
)
from .whitelist import Whitelist
