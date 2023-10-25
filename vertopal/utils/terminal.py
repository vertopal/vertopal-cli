"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

import sys
import argparse
from time import sleep
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Dict, Callable, Any

from requests import exceptions

import vertopal


class Terminal:
    """Provides different methods for handling command-line jobs.

    Attributes:
        silent (bool): If set to `True`, don't write to `stdout` or `stderr`.
        overwrite (bool): If set to `True`, overwrite the output file, if it
            exists on the disk.
        output_dir (str, optional): Directory for saving converted file. 
            If nothing's specified, current working directory will be used. 
            Defaults to `None`.
        ignore_warning (dict): A dictionary to ignore and skip writing specific 
            warning messages to the stdout. Each dictionary key stands for a 
            warning-code, with a value of a list, containing API method names.

    Usage:

        >>> from vertopal.utils.terminal import Terminal
        >>> Terminal.overwrite = True # Overwrite converted file
        >>> Terminal.silent = True # Don't write to stdout & stderr
        >>> Terminal.output_dir = "/home/vertopal/convert_output"
        >>> Terminal.convert(
        ...     input="my_document.docx",
        ...     output_format="txt-markdown",
        ... )
    """

    # Constants
    IGNORE_ALL = "*"
    # Exit Code Constants
    EX_SUCCESSFUL = 0
    EX_OTHER = 1
    EX_INPUT_NOT_FOUND = 2
    EX_UPLOAD_ERROR = 3
    EX_CONVERT_ERROR = 4
    EX_DOWNLOAD_ERROR = 5
    EX_CONNECTION_ERROR = 6
    EX_API_RESPONSE_ERROR = 7
    EX_INVALID_JSON_RESPONSE = 8
    EX_FILE_WRITE_ERROR = 9
    EX_CONVERT_FAILED = 10

    silent: bool = False
    overwrite: bool = False
    output_dir: Optional[str] = None
    ignore_warning: Dict[str, list] = {
        # Ignore all except vertopal.API.download
        "CLI_NEW_VERSION": [
            vertopal.API.upload.__name__,
            vertopal.API.convert.__name__,
            vertopal.API.status.__name__,
            vertopal.API.task_response.__name__,
        ],
    }

    app_id: str = ""
    security_token: str = ""

    @classmethod
    def convert(
        cls,
        input_file: str,
        output_format: str,
        input_format: Optional[str] = None,
    ) -> None:
        """Convert file by running upload, convert, and download tasks.

        Args:
            input_file (str): Input file name, relative or absolute path.
            output_format (str): The output file `format[-type]`.
                E.g. `db-docbook`.
            input_format (Optional[str]): The input file `format[-type]`.
                E.g. `txt` or `txt-markdown`. If not set, the format will be 
                considered based on input extension. Defaults to `None`.

        Returns:
            None
        """

        filepath = Path(input_file).resolve()
        filename = filepath.name
        status = None
        sleep_secs = (10, 20, 30, 60)
        sleep_step = 0

        vertopal.API.set_ua_product_name(vertopal.API.UA_CLI)

        cls._step(f"Uploading {filename}", "1/4")
        upload_connector = cls._upload(filename, filepath)

        cls._step(
            f"Waiting for {output_format.upper()} conversion",
            "2/4"
        )
        convert_connector = cls._convert(
            output_format,
            upload_connector,
            input_format
        )

        cls._step(
            f"Converting {filename} to "
            f"{output_format.upper()} \u2014 please wait...",
            "3/4"
        )
        while status != "completed":
            sleep(sleep_secs[sleep_step])
            if sleep_step < len(sleep_secs) - 1:
                sleep_step += 1
            task_response = cls._task_status(convert_connector)
            status = task_response.task

        cls._info(f"Convert vCredits used: {task_response.vcredits}")

        if task_response.convert == "failed":
            cls._error(
                "Conversion failed. To learn more, visit: "
                "https://www.vertopal.com/en/help/post/27",
                "CONVERT_FAILED",
            )
            cls.exit(cls.EX_CONVERT_FAILED)

        elif task_response.convert == "successful":
            cls._step("Downloading converted file", "4/4")
            download = cls._download(convert_connector)
            cls._download_file(download.connector, download.filename)

        else:
            cls._error("An unexpected error happened")
            cls.exit(cls.EX_OTHER)

    @classmethod
    def api(
        cls,
        full_response: bool,
        output: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Send requests to the Vertopal API and write its response to stdout.

        Args:
            full_response (bool): Include HTTP response status line and
                headers in the output.
        """

        response = vertopal.API.request(**kwargs)

        if output:
            with open(Path(output).resolve(), 'wb') as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
            return

        if full_response:
            sys.stdout.write(f"Status\t{response.status_code}\n\n")
            sys.stdout.write("Response Headers\n")
            for header_key, header_val in response.headers.items():
                sys.stdout.write(f"{header_key}: {header_val}\n")
            sys.stdout.write("\n")

        sys.stdout.write(response.text)
        sys.stdout.write("\n")

    @classmethod
    def check_config(cls) -> None:
        """Show a warning on stdout if AppID and/or Token is not configured.

        Returns:
            None
        """

        if cls.app_id == "" or cls.security_token == "":
            cls._warning("The `App ID` and/or `Security Token` is not set. "
                         "Get them by visiting https://www.vertopal.com")
            cls._print("Use command :: vertopal config --app \"your-app-id\" "
                       "--token \"your-security-token\" :: to set them."
            )

    @classmethod
    def _call_task(
        cls,
        func: Callable[[Any], object],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call an API task in a try-except block and handle its exceptions.

        Args:
            func (Callable[[Any], object]): The API task callable.
            kwargs (Dict[str, Any]): Keyword arguments of the callable `func`.

        Raises:
            FileNotFoundError: If the input file not exists.
            ConnectionError: If cannot reach the API endpoint.
            InvalidJSONError: If error occurs in decoding JSON HTTP response.
            Exception: If there is an error in calling `vertopal.API.download()`
                or if there is an error in API response.

        Returns:
            Dict[str, Any]: JSON response of the API cast to Python dictionary.
        """

        try:
            response = func(**kwargs)
        except FileNotFoundError:
            cls._error("Input file not exists.")
            cls.exit(cls.EX_INPUT_NOT_FOUND)
        except exceptions.ConnectionError:
            cls._error(
                f"Cannot reach API endpoint ({vertopal.API.ENDPOINT}). "
                "Please check your network connection.",
            )
            cls.exit(cls.EX_CONNECTION_ERROR)
        except Exception as error: # pylint: disable=broad-except
            cls._error(repr(error))
            cls.exit(cls.EX_OTHER)
        else:
            try:
                json = response.json()
            except exceptions.InvalidJSONError:
                cls._error(
                    "Cannot decode HTTP response",
                    "INVALID_JSON",
                )
                cls.exit(cls.EX_INVALID_JSON_RESPONSE)
            except Exception as error: # pylint: disable=broad-except
                cls._error(repr(error))
                cls.exit(cls.EX_OTHER)
            # if http response code is 4xx or 5xx
            if (response.status_code % 1000) // 100 in (4, 5):
                cls._error(json["message"], json["code"])
                cls.exit(cls.EX_API_RESPONSE_ERROR)
            else:
                if json["result"]["warning"]:
                    # Iterate over all warning messages
                    for w_code, w_message in json["result"]["warning"].items():
                        # Check if it's ignored in the current function call
                        if (w_code in cls.ignore_warning and
                                (func.__name__ in cls.ignore_warning[w_code] or
                                cls.IGNORE_ALL in cls.ignore_warning[w_code])):
                            continue
                        cls._warning(w_message, w_code)
                if json["result"]["error"]:
                    cls._error(
                        json["result"]["error"]["message"],
                        json["result"]["error"]["code"],
                    )
                    cls.exit(cls.EX_API_RESPONSE_ERROR)
            return json

    @classmethod
    def _upload(cls, filename: str, filepath: str) -> str:
        """Run an upload request using Vertopal API.

        Args:
            filename (str): Input file name.
            filepath (str): Absolute path of the input file.

        Returns:
            str: Upload task connector.
        """

        json = cls._call_task(
            vertopal.API.upload,
            {
                "filename": filename,
                "filepath": filepath,
                "app": cls.app_id,
                "token": cls.security_token,
            },
        )

        return json["result"]["output"]["connector"]

    @classmethod
    def _convert(
        cls,
        output: str,
        connector: str,
        input_format: Optional[str]
    ) -> Optional[str]:
        """Run a convert request using Vertopal API.

        Args:
            output (str): The output file `format[-type]`.
                E.g. `png` or `png-animated`.
            connector (str): The connector from previous task (Upload).
            input_format (Optional[str]): The input file `format[-type]`.

        Returns:
            Optional[str]: Convert task connector or exit the program.
        """

        json = cls._call_task(
            vertopal.API.convert,
            {
                "output_format": output,
                "app": cls.app_id,
                "token": cls.security_token,
                "connector": connector,
                "input_format": input_format,
                "mode": vertopal.API.ASYNC,
            },
        )

        if json["entity"]["status"] == "running":
            return json["entity"]["id"]

        cls._error("Entity status is not running.")
        cls.exit(cls.EX_OTHER)
        return ""

    @classmethod
    def _task_status(cls, connector: str) -> SimpleNamespace:
        """Run a task response request using Vertopal API.

        Args:
            connector (str): Connector of a task. E.g. a convert task.

        Returns:
            SimpleNamespace: A SimpleNamespace instance with 
                `task` (task status), `vcredits` (used vCredits), 
                and `convert` (convert status) properties.
        """

        json = cls._call_task(
            vertopal.API.task_response,
            {
                "app": cls.app_id,
                "token": cls.security_token,
                "connector": connector,
            },
        )

        result = json["result"]["output"]["result"]
        if result:
            convert_status = result["output"]["status"]
        else:
            convert_status = None

        return SimpleNamespace(
            task=json["result"]["output"]["entity"]["status"],
            vcredits=json["result"]["output"]["entity"]["vcredits"],
            convert=convert_status,
        )

    @classmethod
    def _download(cls, connector: str) -> SimpleNamespace:
        """Run a download-url request using Vertopal API.

        Args:
            connector (str): The connector from convert task.

        Returns:
            SimpleNamespace: A SimpleNamespace instance with `connector` and 
                `filename` properties.
        """

        json = cls._call_task(
            vertopal.API.download,
            {
                "app": cls.app_id,
                "token": cls.security_token,
                "connector": connector,
                "url": True,
            },
        )

        return SimpleNamespace(
            connector=json["result"]["output"]["connector"],
            filename=json["result"]["output"]["name"],
        )

    @classmethod
    def _download_file(cls, connector: str, filename: str) -> None:
        """Run a download request and save converted file to disk.

        Args:
            connector (str): The connector from download-url task.
            filename (str): The filename to save the file to the disk.

        Raises:
            ConnectionError: If cannot reach the API endpoint.
            Exception: If there is an error in calling `vertopal.API.download()`
                or if there is an error in API response.

        Returns:
            None
        """

        try:
            response = vertopal.API.download(
                app=cls.app_id,
                token=cls.security_token,
                connector=connector,
                url=False,
            )
        except exceptions.ConnectionError:
            cls._error(f"Cannot reach API endpoint ({vertopal.API.ENDPOINT}). "
                        "Please check your network connection.")
            cls.exit(cls.EX_CONNECTION_ERROR)
        except Exception as error: # pylint: disable=broad-except
            cls._error(repr(error))
            cls.exit(cls.EX_OTHER)
        else:
            # if http response code is 4xx or 5xx
            if (response.status_code % 1000) // 100 in (4, 5):
                cls._error(
                    "Got an unsuccessful HTTP response code",
                    f"HTTP-RES-{response.status_code}"
                )
                cls.exit(cls.EX_API_RESPONSE_ERROR)
            else:
                output = cls._get_output_path(filename)
                try:
                    with open(output, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=128):
                            file.write(chunk)
                except Exception as error: # pylint: disable=broad-except
                    cls._error(repr(error))
                    cls.exit(cls.EX_FILE_WRITE_ERROR)
                else:
                    cls._print_converted(output.name)
                    cls.exit(cls.EX_SUCCESSFUL)

    @classmethod
    def _print(cls, text: str, end: str = "\n") -> None:
        """Write `text` to `stdout`.
        
        Args:
            text (str): The text to write to `stdout`.
            end (str, optional): String appended to the 
                end of the `text`. Defaults to `"\\n"`.
        
        Returns:
            None
        """

        if cls.silent:
            return
        sys.stdout.write(str(text) + end)

    @classmethod
    def _print_converted(cls, filename: str) -> None:
        """Write to the `stdout` declaring the converted file saved to disk.

        Args:
            filename (str): The filename of the saved file.

        Returns:
            None
        """

        if cls.silent:
            return
        line = f"[DONE] Your converted file saved as {str(filename)}\n"
        sys.stdout.write(line)

    @classmethod
    def _step(cls, text: str, step: str) -> None:
        """Write the step of conversion to the `stdout`.

        Args:
            text (str): Description of the step.
            step (str): The step. E.g. `"1"` or `"1/5"`.
        
        Returns:
            None
        """

        if cls.silent:
            return
        sys.stdout.write(f"[{str(step)}] {str(text)}\n")

    @classmethod
    def _error(
        cls,
        text: str,
        errcode: Optional[str] = None,
        end: str = "\n"
    ) -> None:
        """Write an error-line to the `stderr`.

        Args:
            text (str): The error-line description.
            errcode (str, optional): A unique error code. Defaults to `None`.
            end (str, optional): String appended to the 
                end of the `text`. Defaults to `"\\n"`.

        Returns:
            None
        """

        if cls.silent:
            return
        errline = "[ERROR"
        if errcode:
            errline += f" {str(errcode)}] "
        else:
            errline += "] "
        errline += str(text) + end

        sys.stderr.write(errline)

    @classmethod
    def _warning(cls, text: str, wrncode: Optional[str] = None) -> None:
        """Write a warning-line to the `strout`.

        Args:
            text (str): The warning-line description.
            wrncode (str, optional): A unique warning code. Defaults to `None`.

        Returns:
            None
        """

        if cls.silent:
            return
        wrnline = "[WARNING"
        if wrncode:
            wrnline += f" {str(wrncode)}] "
        else:
            wrnline += "] "
        wrnline += str(text) + "\n"

        sys.stdout.write(wrnline)

    @classmethod
    def _info(cls, text: str) -> None:
        """Write an info-line to the `stdout`.

        Args:
            text (str): The info-line description.

        Returns:
            None
        """

        if cls.silent:
            return
        sys.stdout.write("[INFO] " + str(text) + "\n")

    @classmethod
    def _get_output_path(cls, filename: str) -> str:
        """Get file path of the output file.
        
        This class-method can return the proper absolute path of the output file
        based on `Terminal.overwrite` value.

        Args:
            filename (str): Name of the output file

        Returns:
            str: Absolute path of the output file.
        """

        def get_output(filename: str) -> str:
            """Consider `Terminal.output_dir` in getting output absolute path.

            Args:
                filename (str): Name of the output file.

            Returns:
                str: Absolute path of the output file.
            """

            if cls.output_dir:
                return Path(cls.output_dir, filename).resolve()
            return Path(filename).resolve()

        output = get_output(filename)
        if cls.overwrite:
            return output

        stem = output.stem
        counter = 1
        while output.is_file() and output.exists():
            new_name = stem + f"-{counter}" + Path(output).suffix
            output = get_output(new_name)
            counter += 1

        return output

    @classmethod
    def parse(cls) -> object:
        """Use `argparse` to define & parse command-line options and arguments.

        Returns:
            Namespace: A simple `object` containing attributes.
        """

        parser = argparse.ArgumentParser(
            allow_abbrev=False,
            add_help=False,
            prog="vertopal",
            usage="%(prog)s [options] <command> [<args>]",
            epilog="Convert utility by Vertopal - https://www.vertopal.com",
            description=("A small, yet powerful command-line utility for "
                         "converting digital files to a variety of file "
                         "formats using Vertopal public API."),
        )

        subparsers = parser.add_subparsers(
            title="command",
            dest="command",
            prog="vertopal",
            metavar="",
            help=""
        )

        # Create the parser for the <convert> command
        parser_convert = subparsers.add_parser(
            "convert",
            usage="%(prog)s [options] <input> [<args>]",
            help="Convert files on your local machine",
            description="Convert <input> file to 'format[-type]' passed to "
                        "the `--to` argument. If the `--from` argument is not "
                        "set, the 'format[-type]' of the <input> file will be "
                        "considered based on its extension.")
        # Create [<args>] group for the <convert> command
        args_convert = parser_convert.add_argument_group("args")
        # Add <convert> args
        parser_convert.add_argument("input", help="input file name or path")
        args_convert.add_argument(
            "-f", "--from",
            required=False,
            metavar="<format[-type]>",
            dest="input_format",
            help="input file format[-type]"
        )
        args_convert.add_argument(
            "-t", "--to",
            required=True,
            metavar="<format[-type]>",
            dest="output_format",
            help="output file format[-type] (required)"
        )
        args_convert.add_argument(
            "-d", "--output-dir",
            metavar="<directory>",
            help="directory for saving converted file"
        )
        args_convert.add_argument(
            "--app",
            metavar="<app-id>",
            help="override Application ID in global config file"
        )
        args_convert.add_argument(
            "--token",
            metavar="<token>",
            help="override Security Token in global config file"
        )
        args_convert.add_argument(
            "--overwrite",
            action="store_true",
            help="overwrite the converted output file if it exists"
        )
        args_convert.add_argument(
            "--silent",
            action="store_true",
            help="convert without writing to standard output"
        )

        # Create the parser for the <api> command
        parser_api = subparsers.add_parser(
            "api",
            usage="%(prog)s <endpoint> [<args>]",
            help="Send requests to the Vertopal API",
            description="Makes an authenticated HTTP request to the "
                        "Vertopal API and prints the response.",
        )
        # Create [<args>] group for the <api> command
        args_api = parser_api.add_argument_group("args")
        # Add <api> args
        parser_api.add_argument("endpoint", help="the endpoint to the API")
        args_api.add_argument(
            "-F",
            "--field",
            nargs="+",
            type=str,
            default=None,
            metavar="<key=value>",
            help="add a typed parameter in key=value format",
        )
        args_api.add_argument(
            "-v",
            "--version",
            type=str,
            metavar="<number>",
            help="the version number of the API"
        )
        args_api.add_argument(
            "-X",
            "--method",
            type=str.upper,
            choices=(
                "GET",
                "OPTIONS",
                "HEAD",
                "POST",
                "PUT",
                "PATCH",
                "DELETE"
            ),
            metavar="<string>",
            default="POST",
            help="the HTTP method for the request",
        )
        args_api.add_argument(
            "-o",
            "--output",
            metavar="<file>",
            help="write to file instead of stdout",
        )
        args_api.add_argument(
            "-i",
            "--include",
            action="store_true",
            help="include HTTP response status line and headers in the output",
        )
        args_api.add_argument(
            "--app",
            metavar="<app-id>",
            help="the Application ID retrieved from vertopal.com"
        )
        args_api.add_argument(
            "--token",
            metavar="<token>",
            help="the Security Token retrieved from vertopal.com"
        )

        # Create the parser for the <config> command
        parser_config = subparsers.add_parser(
            "config",
            usage="%(prog)s [options] [<args>]",
            help="Configure global config file",
            description="Set vertopal global options.",
        )
        # Create [<args>] group for the <config> command
        args_config = parser_config.add_argument_group("args")
        # Add <config> args
        args_config.add_argument(
            "--app",
            metavar="<app-id>",
            help="submit Application ID retrieved from vertopal.com"
        )
        args_config.add_argument(
            "--token",
            metavar="<token>",
            help="submit Security Token retrieved from vertopal.com"
        )

        # Create [options] and add args
        option = parser.add_argument_group("options")
        option.add_argument("-v", "--version",
            action="version",
            version=f"vertopal version {vertopal.__version__}",
            help="output version information and exit"
        )
        option.add_argument("-h", "--help",
            action="help",
            help="display this help message and exit"
        )

        # By passing the `--help` flag to the args we are sure
        # the help message is shown even if `vertopal` command
        # is called in terminal without any arguments.
        return parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    @staticmethod
    def exit(exitcode: int) -> None:
        """Exit the program with a proper exit code.

        Args:
            exitcode (int): Exit code. Pass constants in `Terminal` 
                start with `EX_...`

        Returns:
            None
        """
        sys.exit(exitcode)
