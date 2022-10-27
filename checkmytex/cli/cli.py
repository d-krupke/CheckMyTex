import argparse
import json
import typing

from rich.console import Console

from checkmytex.cli.rich_printer import ProblemHandler, RichPrinter
from checkmytex.document_analyzer import DocumentAnalyzer
from checkmytex.filtering.whitelist import Whitelist
from checkmytex.latex_document.parser import LatexParser
from checkmytex.utils.editor import Editor


def cli(
    engine: DocumentAnalyzer,
    args: argparse.Namespace,
    whitelist: Whitelist,
    latex_parser: typing.Optional[LatexParser] = None,
):
    console = Console(record=True)
    try:
        latex_parser = latex_parser if latex_parser is not None else LatexParser()
        latex_document = latex_parser.parse(args.path[0])
        analyzed_document = engine.analyze(latex_document)
        if args.json:
            with open(args.json, "w") as f:
                json.dump(analyzed_document.serialize(), f)
            return
        if args.html:
            RichPrinter(analyzed_document).to_html(args.html)
        else:
            analyzed_document.set_on_false_positive_cb(lambda p: whitelist.add(p))
            rp = RichPrinter(
                analyzed_document,
                problem_handler=ProblemHandler(analyzed_document, Editor(), console),
                console=console,
            )
            rp.print()
    except KeyError as key_error:
        console.log("Error:", str(key_error))
