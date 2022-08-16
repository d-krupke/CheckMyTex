"""
Parsing the arguments from CLI.
"""
import argparse
import os
import sys


def parse_arguments(log):
    """
    Parse CLI arguments.
    :param log: A logging function.
    :return: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="CheckMyTex: A simple tool for checking your LaTeX."
    )

    parser.add_argument("-w", help="Path to whitelist", type=str)
    parser.add_argument("--json", type=str, help="Write result as json to file.")
    parser.add_argument("--print", action="store_true", help="Just print the output")
    parser.add_argument("path", nargs=1, help="Path to main.tex")
    args = parser.parse_args()
    if not args.path:
        parser.print_help()
        sys.exit(1)
    if args.w:
        args.whitelist = args.w
    else:
        path = os.path.dirname(args.path[0])
        args.whitelist = os.path.join(path, ".whitelist.txt")
        log(f"Saving whitelist to {args.whitelist}")
    return args
