"""
A main file to execute CheckMyTex with CLI.
"""

from checkmytex.cli import cli, parse_arguments
from checkmytex.document_analyzer import DocumentAnalyzer
from checkmytex.filtering import (
    IgnoreIncludegraphics,
    IgnoreLikelyAuthorNames,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreSpellingWithMath,
    IgnoreWordsFromBibliography,
    MathMode,
    Whitelist,
)


def main() -> None:
    """
    A main function, such that it can also be called with different entry
    points
    """
    args = parse_arguments()
    engine = DocumentAnalyzer()
    engine.setup_default()
    # Add filter
    whitelist = Whitelist(args.whitelist)
    engine.add_filter(whitelist)
    engine.add_filter(IgnoreIncludegraphics())
    engine.add_filter(IgnoreRefs())
    engine.add_filter(IgnoreRepeatedWords(["problem", "problems"]))
    engine.add_filter(IgnoreLikelyAuthorNames())
    engine.add_filter(IgnoreWordsFromBibliography())
    engine.add_filter(IgnoreSpellingWithMath())
    engine.add_filter(
        MathMode({"SPELLING": None, "languagetool": None, "Proselint": None})
    )
    cli(engine, args=args, whitelist=whitelist)


if __name__ == "__main__":
    main()
