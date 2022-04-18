from checkmytex.analyzed_document import AnalyzedDocument
from checkmytex.cli.file_printer import FilePrinter
from checkmytex.cli.overview import OverviewPrinter
from checkmytex.cli.problem_handler import InteractiveProblemHandler
from checkmytex.filtering.whitelist import Whitelist
from checkmytex.utils.editor import Editor


class InteractiveCli:
    def __init__(
        self,
        analyzed_document: AnalyzedDocument,
        whitelist: Whitelist,
        just_print: bool = False,
    ):
        self.just_print = just_print
        self.editor = Editor()

        analyzed_document.set_on_false_positive_cb(lambda p: whitelist.add(p))
        if self.just_print:
            problem_handler = lambda p: None
        else:
            problem_handler = InteractiveProblemHandler(analyzed_document, self.editor)
        OverviewPrinter().print(analyzed_document)
        fp = FilePrinter(analyzed_document, problem_handler)
        # Go through all files
        for f in analyzed_document.list_files():
            fp.print(f)
