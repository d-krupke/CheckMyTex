"""Factory helpers for creating configured DocumentAnalyzer instances."""

from __future__ import annotations

from contextlib import suppress

from checkmytex import DocumentAnalyzer
from checkmytex.filtering import (
    IgnoreCodeListings,
    IgnoreIncludegraphics,
    IgnoreLikelyAuthorNames,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreSpellingWithMath,
    IgnoreWordsFromBibliography,
    MathMode,
)
from checkmytex.finding import (
    AspellChecker,
    CheckSpell,
    ChkTex,
    Cleveref,
    Languagetool,
    LineLengthChecker,
    Proselint,
    SiUnitx,
    TodoChecker,
    UniformNpHard,
)
from config import LANGUAGETOOL_MAX_CHARACTERS, LANGUAGETOOL_TIMEOUT


def create_analyzer(
    enabled_checkers: list[str] | None = None,
    enabled_filters: list[str] | None = None,
) -> DocumentAnalyzer:
    """Create a DocumentAnalyzer with the requested checkers and filters."""
    enabled_checkers = enabled_checkers or []
    enabled_filters = enabled_filters or []

    analyzer = DocumentAnalyzer()

    if "aspell" in enabled_checkers:
        try:
            analyzer.add_checker(AspellChecker())
        except Exception:
            with suppress(Exception):
                analyzer.add_checker(CheckSpell())

    if "languagetool" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(
                Languagetool(
                    max_characters=LANGUAGETOOL_MAX_CHARACTERS,
                    timeout_seconds=LANGUAGETOOL_TIMEOUT,
                )
            )

    if "chktex" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(ChkTex())

    if "siunitx" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(SiUnitx())

    if "nphard" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(UniformNpHard())

    if "cleveref" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(Cleveref())

    if "proselint" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(Proselint())

    if "linelength" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(LineLengthChecker(max_length=200))

    if "todo" in enabled_checkers:
        with suppress(Exception):
            analyzer.add_checker(TodoChecker())

    if "includegraphics" in enabled_filters:
        analyzer.add_filter(IgnoreIncludegraphics())

    if "refs" in enabled_filters:
        analyzer.add_filter(IgnoreRefs())

    if "repeated" in enabled_filters:
        analyzer.add_filter(IgnoreRepeatedWords())

    if "spellingwithmath" in enabled_filters:
        analyzer.add_filter(IgnoreSpellingWithMath())

    if "mathmode" in enabled_filters:
        analyzer.add_filter(MathMode())

    if "authornames" in enabled_filters:
        analyzer.add_filter(IgnoreLikelyAuthorNames())

    if "bibliography" in enabled_filters:
        analyzer.add_filter(IgnoreWordsFromBibliography())

    if "codelistings" in enabled_filters:
        analyzer.add_filter(IgnoreCodeListings())

    return analyzer
