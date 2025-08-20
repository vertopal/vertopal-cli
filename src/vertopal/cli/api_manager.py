# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Provides CLI utilities for invoking the Vertopal HTTP API. Translates
#   argparse Namespace arguments into HTTP requests using the low-level
#   _Interface client, supporting output to file, full response metadata,
#   and beautified JSON output for human consumption.

"""
Utilities for invoking the Vertopal HTTP API from the CLI.

This module translates an argparse `Namespace` into an HTTP request
using the low-level `_Interface` client. It supports writing the
response to a file, printing full response metadata, and beautifying
JSON output for human consumption.
"""

from argparse import Namespace
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

import requests

from vertopal.api.credential import Credential
from vertopal.api.interface import _Interface

# No public names in this file
__all__ = []


class _APIManager:
    """
    Manager for handling Vertopal API commands.

    This adapter accepts an argparse `Namespace` and performs an HTTP
    request via the `_Interface` client, then formats and outputs the
    response according to CLI options.
    """

    def __init__(self, args: Namespace) -> None:
        """
        Initialize the API Manager with parsed command-line arguments.

        Args:
            args (Namespace): Parsed command-line arguments
                from argparse.
        """
        self._args: Namespace = args
        self._credential: Optional[Credential] = None

    def run(self) -> None:
        """
        Execute the API command based on the provided
        command-line arguments.

        The method may write the response to a file, print the full HTTP
        response metadata, or prettify JSON output for stdout.
        """
        # Retrieve credentials from argparse arguments.
        app: Optional[str] = getattr(self._args, "app", None)
        token: Optional[str] = getattr(self._args, "token", None)
        if app and token:
            self._credential = Credential(app, token)

        # Retrieve flags from argparse arguments.
        full_response: bool = getattr(self._args, "full_response", False)
        output: Optional[str] = getattr(self._args, "output", None)
        beautify: bool = getattr(self._args, "beautify", False)

        # Build a dictionary of API parameters expected
        # by the `API.request` method.
        # Adjust the following based on the actual argument names
        # used in your argparse configuration.
        kwargs: Dict[str, Any] = {}
        if hasattr(self._args, "endpoint") and self._args.endpoint:
            kwargs["endpoint"] = self._args.endpoint
        if hasattr(self._args, "method") and self._args.method:
            kwargs["method"] = self._args.method
        if hasattr(self._args, "field"):
            kwargs["field_params"] = self._args.field
        if hasattr(self._args, "version"):
            kwargs["version"] = self._args.version

        # Perform the API request.
        response: requests.Response = self._perform_api_request(**kwargs)

        # If output is specified, write the response stream to the output file.
        if output:
            with open(Path(output).resolve(), "wb") as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
            return

        # If full response is requested, print status and headers.
        if full_response:
            sys.stdout.write(f"Status\t{response.status_code}\n\n")
            sys.stdout.write("Response Headers\n")
            for header_key, header_val in response.headers.items():
                sys.stdout.write(f"{header_key}: {header_val}\n")
            sys.stdout.write("\n")

        # Output the response body.
        if beautify:
            try:
                parsed = json.loads(response.text)
                sys.stdout.write(json.dumps(parsed, indent=2))
            except json.decoder.JSONDecodeError:
                sys.stdout.write("Error beautifying response: Invalid JSON.\n")
        else:
            sys.stdout.write(response.text)
        sys.stdout.write("\n")

    def _perform_api_request(self, **kwargs: Any) -> requests.Response:
        """
        Perform the API HTTP request.

        This method serves as a thin wrapper around the
        `Vertopal.api.interface._Interface.request` method.
        It passes through keyword arguments typically including
        'endpoint', 'method', 'field_params', and 'version'.

        Args:
            **kwargs (Any): Keyword arguments forwarded to
                `_Interface.request`.

        Returns:
            requests.Response: The HTTP response returned from the API.
        """
        client = _Interface(self._credential)
        return client.request(**kwargs)
