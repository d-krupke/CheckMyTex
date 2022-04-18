from checkmytex.cli import InteractiveCli, log, parse_arguments
from checkmytex.document_analyzer import DocumentAnalyzer
from checkmytex.filtering import (
    IgnoreIncludegraphics,
    IgnoreLikelyAuthorNames,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreSpellingWithMath,
    IgnoreWordsFromBibliography,
    Whitelist,
)
from checkmytex.latex_document import LatexDocument


def main():
    args = parse_arguments(log)
    whitelist = Whitelist(args.whitelist)
    log("Parsing LaTeX project...")
    try:
        latex_document = LatexDocument(args.path[0])
        engine = DocumentAnalyzer(log=log)
        engine.setup_default()
        # Add filter
        engine.add_filter(whitelist)
        engine.add_filter(IgnoreIncludegraphics())
        engine.add_filter(IgnoreRefs())
        engine.add_filter(IgnoreRepeatedWords(["problem", "problems"]))
        engine.add_filter(IgnoreLikelyAuthorNames())
        engine.add_filter(IgnoreWordsFromBibliography())
        engine.add_filter(IgnoreSpellingWithMath())
        analyzed_document = engine.analyze(latex_document)

        InteractiveCli(analyzed_document, whitelist, just_print=args.print)
    except KeyError as ke:
        print("Error:", str(ke))


if __name__ == "__main__":
    main()
