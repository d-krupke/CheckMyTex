"""
Parsing the arguments from CLI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def create_default_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CheckMyTex: A simple tool for checking your LaTeX."
    )

    parser.add_argument("-w", help="Path to whitelist", type=str)
    parser.add_argument("--json", type=str, help="Write result as json to file.")
    parser.add_argument("--print", action="store_true", help="Just print the output")
    parser.add_argument("--html", type=str, help="Create an HTML with the problems.")
    parser.add_argument("path", nargs=1, help="Path to main.tex")
    return parser


def parse_arguments(
    parser: argparse.ArgumentParser | None = None,
) -> argparse.Namespace:
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
        path = Path(args.path[0]).parent
        args.whitelist = str(path / ".whitelist.txt")
    return args
