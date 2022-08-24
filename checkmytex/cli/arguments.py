"""
Parsing the arguments from CLI.
"""
import argparse
import os
import sys
import typing


def create_default_argument_parser():
    parser = argparse.ArgumentParser(
        description="CheckMyTex: A simple tool for checking your LaTeX."
    )

    parser.add_argument("-w", help="Path to whitelist", type=str)
    parser.add_argument("--json", type=str, help="Write result as json to file.")
    parser.add_argument("--print", action="store_true", help="Just print the output")
    parser.add_argument("--html", type=str, help="Create an HTML with the problems.")
    parser.add_argument("path", nargs=1, help="Path to main.tex")
    return parser


def parse_arguments(parser: typing.Optional[argparse.ArgumentParser] = None):
    """
    Parse CLI arguments.
    :param log: A logging function.
    :return: The parsed arguments.
    """
    parser = create_default_argument_parser() if parser is None else parser
    args = parser.parse_args()
    if not args.path:
        parser.print_help()
        sys.exit(1)
    if args.w:
        args.whitelist = args.w
    else:
        path = os.path.dirname(args.path[0])
        args.whitelist = os.path.join(path, ".whitelist.txt")
    return args
