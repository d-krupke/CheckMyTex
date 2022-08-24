"""
A main file to execute CheckMyTex with CLI.
"""
import json

from checkmytex.cli import InteractiveCli, log, parse_arguments
from checkmytex.cli.rich_printer import ProblemHandler, RichPrinter
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
from checkmytex.latex_document import LatexDocument
from checkmytex.latex_document.parser import LatexParser
from checkmytex.utils import Editor


def main():
    """
    A main function, such that it can also be called with different entry
    points
    :return: None
    """
    args = parse_arguments(log)
    whitelist = Whitelist(args.whitelist)
    log_ = log
    log_("Parsing LaTeX project...")
    try:
        parser = LatexParser()
        latex_document = parser.parse(args.path[0])
        engine = DocumentAnalyzer(log=log_)
        engine.log = log_
        engine.setup_default()
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
        if args.json:
            with open(args.json, "w") as f:
                json.dump(analyzed_document.serialize(), f)
            return
        if args.html:
            RichPrinter(analyzed_document).to_html(args.html)
        else:
            analyzed_document.set_on_false_positive_cb(lambda p: whitelist.add(p))
            rp = RichPrinter(analyzed_document)
            rp.problem_handler = ProblemHandler(analyzed_document, Editor(), rp.console)
            rp.print()
    except KeyError as key_error:
        print("Error:", str(key_error))


if __name__ == "__main__":
    main()
