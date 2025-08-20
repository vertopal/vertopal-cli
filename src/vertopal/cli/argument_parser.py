# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Defines the argument parser and CLI command wiring for Vertopal CLI.
#   Registers subcommands and delegates execution to command managers.

"""
Argument parser and CLI command wiring for the Vertopal command-line
interface. This module defines the parser, subcommands and the small
adapter functions that delegate work to command managers.
"""

import argparse
from typing import Any

from vertopal import __version__
from vertopal.cli.api_manager import _APIManager
from vertopal.cli.config_manager import _ConfigManager
from vertopal.cli.conversion_manager import _ConversionManager

# No public names in this file
__all__ = []


class _VertopalArgumentParser(argparse.ArgumentParser):
    """
    Custom argument parser for the Vertopal CLI.

    This class provides a modular and organized way to define and parse
    command-line arguments and subcommands for the Vertopal CLI.

    Attributes:
        subparsers (argparse._SubParsersAction): Sub-parser action used
            to register subcommands.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the main argument parser.

        Args:
            *args (Any): Positional arguments passed to
                `argparse.ArgumentParser`.
            **kwargs (Any): Keyword arguments passed to
                `argparse.ArgumentParser`.
        """
        super().__init__(
            *args,
            **kwargs,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self.subparsers = self.add_subparsers(
            title="commands",
            dest="command",
            prog="vertopal",
            metavar="<command>",
            required=True,
            parser_class=argparse.ArgumentParser,
        )
        self._add_optional_arguments()
        self._add_subparser_commands()

    def _add_optional_arguments(self) -> None:
        """
        Register top-level optional arguments such as
        `--version` and `-h`.
        """
        self.add_argument(
            "--version",
            action="version",
            version=f"vertopal version {__version__}",
            help="Output version information and exit",
        )
        self.add_argument(
            "-h", "--help",
            action="help",
            help="Display this help message and exit",
        )

    def _add_subparser_commands(self) -> None:
        """
        Register built-in subcommands for the CLI (`convert`, `api`,
        `config`) and wire them to their respective handler factories.
        """
        self._add_convert_parser()
        self._add_api_parser()
        self._add_config_parser()

    def _add_convert_parser(self) -> None:
        """
        Register arguments for the `convert` subcommand including input
        sources, formats, traversal options and output control.
        """
        convert_parser = self.subparsers.add_parser(
            "convert",
            usage="%(prog)s [options] <input> [<args>]",
            help="convert files or read from stdin",
            description=(
                "Convert files using flexible input options, including stdin "
                "(use `-`), single/multiple files, wildcard patterns, "
                "directories, file lists, brace expansion {a,b,c}, "
                "ranges {1..5}, and recursive patterns **/*."
            ),
        )

        # Create [<args>] group for the <convert> command
        convert_args = convert_parser.add_argument_group("args")

        # Input sources
        convert_parser.add_argument(
            "input",
            nargs="*",
            metavar="<input>",
            help=(
                "input file(s), directories, wildcard patterns, "
                "or '-' for stdin. Supports brace expansion {a,b,c}, "
                "ranges {1..5}, and recursive patterns **/*"
            ),
        )
        convert_args.add_argument(
            "--file-list",
            metavar="<file>",
            help="path to a file containing a list of file paths to convert",
        )

        # Input and output formats
        convert_args.add_argument(
            "-f", "--from",
            required=False,
            metavar="<format[-type]>",
            dest="input_format",
            help="input file format[-type] (required for stdin)",
        )
        convert_args.add_argument(
            "-t", "--to",
            required=True,
            metavar="<format[-type]>",
            dest="output_format",
            help="output file format[-type] (required)",
        )

        # Output sink
        convert_args.add_argument(
            "--output",
            required=False,
            metavar="<output>",
            help="output file name or path, or '-' for stdout",
        )

        # Directory traversal options
        convert_args.add_argument(
            "-r", "--recursive",
            action="store_true",
            help="recursively search through directories for files",
        )
        convert_args.add_argument(
            "--exclude",
            nargs="+",
            metavar="<pattern>",
            help=(
                "exclude files matching the given pattern(s). "
                "Supports glob patterns, directory patterns ending with /, "
                "and regex patterns starting with ^"
            ),
        )
        convert_args.add_argument(
            "--modified-since",
            metavar="<date>",
            help=(
                "filter files modified since the specified date "
                "in ISO 8601 format (YYYY-MM-DD)"
            ),
        )

        # General options
        # convert_args.add_argument(
        #     "--overwrite",
        #     action="store_true",
        #     help="overwrite the output file if it exists",
        # )
        # convert_args.add_argument(
        #     "--silent",
        #     action="store_true",
        #     help="perform conversion without writing to standard output",
        # )

        # Set the default function for execution
        convert_parser.set_defaults(func=self._execute_convert)

    def _add_api_parser(self) -> None:
        """
        Register arguments for the `api` subcommand used to perform
        low-level HTTP requests against the Vertopal API.
        """
        api_parser = self.subparsers.add_parser(
            "api",
            usage="%(prog)s [options] <endpoint> [<args>]",
            help="send requests to the Vertopal API",
            description=(
                "Makes an authenticated HTTP request to the "
                "Vertopal API and prints the response."
            ),
        )

        # Create [<args] group for the <api> command
        api_args = api_parser.add_argument_group("args")

        api_parser.add_argument(
            "endpoint", help="the endpoint to the API"
        )

        api_args.add_argument(
            "-F", "--field",
            nargs="+",
            type=str,
            default=None,
            metavar="<key=value>",
            help="add a typed parameter in `key=value` format",
        )
        api_args.add_argument(
            "-v", "--version",
            type=str,
            metavar="<number>",
            help="the version number of the API",
        )
        api_args.add_argument(
            "-X", "--method",
            type=str.upper,
            choices=("GET", "POST", "PUT", "DELETE"),
            metavar="<string>",
            default="POST",
            help="the HTTP method for the request",
        )
        api_args.add_argument(
            "-o", "--output",
            metavar="<file>",
            help="write to file instread of stdout",
        )
        api_args.add_argument(
            "-i", "--include",
            action="store_true",
            help="include HTTP response status line and headers in the output",
        )
        api_args.add_argument(
            "--beautify",
            action="store_true",
            help="create human readable output (only in stdout)",
        )
        api_args.add_argument(
            "--app",
            metavar="<app-id>",
            help="the Application ID retrieved from vertopal.com"
        )
        api_args.add_argument(
            "--token",
            metavar="<token>",
            help="the Security Token retrieved from vertopal.com"
        )

        # Set the default function for execution
        api_parser.set_defaults(func=self._execute_api)

    def _add_config_parser(self) -> None:
        """
        Register arguments for the `config` subcommand that manages
        the user-specific configuration store.
        """
        config_parser = self.subparsers.add_parser(
            "config",
            usage="%(prog)s [options] [<args>]",
            help="configure user-specific config file",
            description="Set Vertopal user-specific configuration.",
        )

        # Create [<args>] group for the <config> command
        config_args = config_parser.add_argument_group("args")

        config_args.add_argument(
            "--list",
            action="store_true",
            help="list all user-defined configurations",
        )

        config_args.add_argument(
            "--unset",
            action="store_true",
            help="unset (remove) a user-defined configuration key",
        )

        config_args.add_argument(
            "pairs",
            nargs="*",
            help="configuration key-value pairs (section.key value)",
        )

        # Set the default function for execution
        config_parser.set_defaults(func=self._execute_config)

    def _execute_convert(self, args: argparse.Namespace) -> None:
        """
        Execute the `convert` subcommand by delegating to
        `_ConversionManager`.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        conversion_manager = _ConversionManager()
        _ConversionManager.setup_signal_handlers(conversion_manager)
        conversion_manager.convert(args)

    def _execute_api(self, args: argparse.Namespace) -> None:
        """
        Execute the `api` subcommand by delegating to `_APIManager`.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        api_manager = _APIManager(args)
        api_manager.run()

    def _execute_config(self, args: argparse.Namespace) -> None:
        """
        Execute the `config` subcommand by delegating to
        `_ConfigManager`.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        config_manager = _ConfigManager(args)
        config_manager.run()
