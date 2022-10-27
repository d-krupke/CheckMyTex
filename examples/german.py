"""
A main file modified to check german tex files. Not as powerful as the
english version.
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
from checkmytex.finding import (
    AspellChecker,
    CheckSpell,
    ChkTex,
    Cleveref,
    Languagetool,
    SiUnitx,
    UniformNpHard,
)


def main():
    """
    A main function, such that it can also be called with different entry
    points
    :return: None
    """
    args = parse_arguments()
    engine = DocumentAnalyzer()
    engine.setup_default()
    # Add filter
    whitelist = Whitelist(args.whitelist)
    aspell = AspellChecker(lang="de_DE")
    if aspell.is_available():
        engine.add_checker(aspell)
    else:
        engine.add_checker(CheckSpell(lang="de"))
    engine.add_checker(ChkTex())
    engine.add_checker(Languagetool(lang="de-DE"))
    engine.add_checker(SiUnitx())
    engine.add_checker(Cleveref())
    engine.add_checker(UniformNpHard())
    # Add filter
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
