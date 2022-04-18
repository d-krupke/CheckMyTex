from checkmytex.analyzed_document import AnalyzedDocument
from checkmytex.cli.highlighted_output import highlight, print_header


class OverviewPrinter:
    def print(self, document: AnalyzedDocument):
        # Print overview
        print_header("Overview")
        all_problems = document.get_problems()
        print(highlight(f"Found {len(all_problems)} problems in the document."))
        for f in document.list_files():
            problems = document.get_problems(f)
            if len(problems) == 0:
                print(f + ":", "no problems.")
            elif len(problems) == 1:
                print(f + ":", highlight("1 problem."))
            else:
                print(f + ":", highlight(f"{len(problems)} problems."))
