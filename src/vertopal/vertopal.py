#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Console script entry point for the Vertopal CLI.
#   Parses command-line arguments via the package's custom argument
#   parser and dispatches execution to the appropriate command handler.
#   Can be invoked directly (e.g., PyInstaller-built binary) or via
#   the installed `vertopal` console script. Prints usage information
#   and exits with status code 1 if no valid command is provided.

"""
Console script entry-point for the Vertopal CLI.

This script implements a lightweight CLI wrapper used to parse
command-line arguments and dispatch commands provided by the package's
argument parser. It exposes a `main()` function intended to be used
as a console script entry point or executed directly (for example by
PyInstaller-built binaries).
"""

import sys

from vertopal.cli.argument_parser import _VertopalArgumentParser
from vertopal.utils.misc import _split_into_lines

# No public names in this file
__all__ = []


def main() -> None:
    """
    Main function for parsing, handling and running CLI arguments.

    This function builds the argument parser, parses `sys.argv`, and
    dispatches the selected command. If no command is provided, it
    prints the help text and exits with status code `1`.
    """

    description_text: str = (
        "A small, yet powerful command-line utility "
        "for converting digital files to a variety of file formats "
        "using Vertopal public API."
    )

    parser = _VertopalArgumentParser(
        allow_abbrev=False,
        add_help=False,
        prog="vertopal",
        usage="%(prog)s [options] <command> [<args>]",
        epilog="Convert utility by Vertopal - https://www.vertopal.com",
        description="\n".join(_split_into_lines(description_text)),
    )

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
