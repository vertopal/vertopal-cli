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

        if args.app and args.token:
            Terminal.app_id = args.app
            Terminal.security_token = args.token
        else:
            Terminal.app_id: str = Config.read("api", "appid")
            Terminal.security_token: str = Config.read("api", "token")
            # Show a warning on stdout if client credentials are not configured
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
            input_file=args.input,
            output_format=output_format,
            input_format=input_format,
        )

    # Write config options to the global user config file
    elif args.command == "config":

        if args.app:
            Config.write("api", "appid", args.app)
        if args.token:
            Config.write("api", "token", args.token)

    elif args.command == "api":

        if args.app and args.token:
            app_id = args.app
            security_token = args.token
        else:
            app_id: str = Config.read("api", "appid")
            security_token: str = Config.read("api", "token")

        Terminal.api(
            endpoint=args.endpoint,
            method=args.method,
            app=app_id,
            token=security_token,
            field_params=args.field,
            version=args.version,
            full_response=args.include,
            output=args.output,
        )


if __name__ == "__main__":
    main()
