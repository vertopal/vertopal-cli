#!/usr/bin/env python

"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

from vertopal.utils.terminal import Terminal
from vertopal.utils.config import Config


def main() -> None:
    """Main function for parsing, handling and running command-line arguments.

    Returns:
        None
    """

    # Define & Parse command-line options
    args = Terminal.parse()

    if args.command == "convert":

        # Show a warning on stdout if AppID & Security Token is not configured
        Terminal.check_config()

        if args.silent:
            Terminal.silent = True
        if args.overwrite:
            Terminal.overwrite = True
        if args.output_dir:
            Terminal.output_dir = args.output_dir

        input_format = args.input_format
        output_format = args.output_format
        if input_format:
            input_format = input_format.lower()
        if output_format:
            output_format = output_format.lower()

        Terminal.convert(
            input=args.input,
            input_format=input_format,
            output_format=output_format,
        )

    # Write config options to the global user config file
    elif args.command == "config":

        if args.app:
            Config.write("api", "appid", args.app)
        if args.token:
            Config.write("api", "token", args.token)


if __name__ == "__main__":
    main()
