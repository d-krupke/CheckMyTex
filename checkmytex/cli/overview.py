"""
Printing a quick overview of all errors.
"""
from checkmytex.analyzed_document import AnalyzedDocument
from checkmytex.cli.highlighted_output import highlight, print_header


def print_overview(document: AnalyzedDocument):
    """
    Print the errors of the document.
    """
    # Print overview
    print_header("Overview")
    all_problems = document.get_problems()
    print(highlight(f"Found {len(all_problems)} problems in the document."))
    for file_path in document.list_files():
        problems = document.get_problems(file_path)
        if len(problems) == 0:
            print(file_path + ":", "no problems.")
        elif len(problems) == 1:
            print(file_path + ":", highlight("1 problem."))
        else:
            print(file_path + ":", highlight(f"{len(problems)} problems."))
