"""
A main file modified to check german tex files. Not as powerful as the
english version.
"""
from checkmytex.cli import InteractiveCli, log, parse_arguments
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
from checkmytex.latex_document import LatexDocument
from checkmytex.latex_document.parser import LatexParser


def main():
    """
    A main function, such that it can also be called with different entry
    points
    :return: None
    """
    args = parse_arguments(log)
    whitelist = Whitelist(args.whitelist)
    log("Parsing LaTeX project...")
    try:
        parser = LatexParser()
        latex_document = parser.parse(args.path[0])
        engine = DocumentAnalyzer(log=log)
        # Add chcker
        aspell = AspellChecker(lang="de_DE")
        if aspell.is_available():
            engine.add_checker(aspell)
        else:
            engine.log("Aspell not available. Using pyspellchecker.")
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

        analyzed_document = engine.analyze(latex_document)

        InteractiveCli(analyzed_document, whitelist, just_print=args.print)
    except KeyError as key_error:
        print("Error:", str(key_error))


if __name__ == "__main__":
    main()
