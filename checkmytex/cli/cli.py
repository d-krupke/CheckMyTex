import argparse
import os.path

from checkmytex.analyzed_document import AnalyzedDocument
from checkmytex.cli.file_printer import FilePrinter
from checkmytex.cli.overview import OverviewPrinter
from checkmytex.cli.problem_handler import InteractiveProblemHandler
from checkmytex.document_checker import DocumentChecker
from checkmytex.utils.editor import Editor
from checkmytex.cli.highlighted_output import log
from checkmytex.latex_document import LatexDocument
from checkmytex.whitelist import Whitelist


class InteractiveCli:

    def __init__(self,
                 main_file: str,
                 whitelist_path: str = None,
                 just_print: bool = False):
        self.just_print = just_print
        self.editor = Editor()
        self.whitelist = Whitelist(whitelist_path)
        log("Parsing LaTeX project...")
        self.latex_document = LatexDocument(main_file)
        doc_checker = DocumentChecker(log=log)
        problems = list(doc_checker.find_problems(self.latex_document,
                                                  self.whitelist))
        self.analyzed_document = AnalyzedDocument(self.latex_document, problems,
                                                  lambda p: self.whitelist.add(p))

        problem_handler = InteractiveProblemHandler(self.analyzed_document, self.editor)
        OverviewPrinter().print(self.analyzed_document)
        fp = FilePrinter(self.analyzed_document, problem_handler)
        # Go through all files
        for f in self.analyzed_document.list_files():
            fp.print(f)


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
    InteractiveCli(args.path[0], whitelist_path=whitelist,
                   just_print=args.print)
