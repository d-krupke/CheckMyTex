import argparse
import os.path

from checkmytex.cli.cli import InteractiveCli
from checkmytex.cli.highlighted_output import log
from checkmytex.latex_document import LatexDocument
from checkmytex.document_analyzer import DocumentAnalyzer
from checkmytex.filtering import IgnoreIncludegraphics, IgnoreRefs, \
    IgnoreRepeatedWords, IgnoreLikelyAuthorNames, IgnoreWordsFromBibliography, \
    Whitelist


def main():
    parser = argparse.ArgumentParser(
        description='CheckMyTex: A simple tool for checking your LaTeX.')
    parser.add_argument('-w', help='Path to whitelist', type=str)
    parser.add_argument('--print', action="store_true",
                        help="Just print the output")
    parser.add_argument('path', nargs=1, help="Path to main.tex")
    args = parser.parse_args()
    if not args.path:
        parser.print_help()
        exit(1)
    if args.w:
        whitelist = args.w
    else:
        path = os.path.dirname(args.path[0])
        whitelist = os.path.join(path, ".whitelist.txt")
        log(f"Saving whitelist to {whitelist}")

    whitelist = Whitelist(whitelist)
    log("Parsing LaTeX project...")
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
    analyzed_document = engine.analyze(latex_document)

    InteractiveCli(analyzed_document, whitelist, just_print=args.print)
