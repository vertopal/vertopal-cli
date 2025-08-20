# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Implementing the high-level operations supported by the Vertopal
#   public API surface (v1). Methods are deliberately small and
#   primarily compose request payloads then delegate to the
#   `_Interface.send_request` implementation for HTTP transport and
#   response handling. The implementation expects credentials to be
#   available via an optional `Credential` instance or the library
#   configuration.

"""
Vertopal API v1 client utilities.

This module provides the `API` class which implements client-side
helpers for calling Vertopal API version 1 endpoints. The class methods
wrap common server interactions such as uploading files, requesting
conversions, polling task status, fetching results, and streaming
downloads into a small, typed surface that accepts Vertopal I/O
protocol objects (`Readable` and `Writable`) and returns the library's
`vertopal.api.response._CustomResponse` wrapper.

Example:

    >>> from vertopal.api.v1 import API
    >>> from vertopal.io.adapters.file import FileInput
    >>> inp = FileInput("./document.pdf")
    >>> with API() as client:
    ...     resp = client.upload_file(inp)
"""

from typing import Optional

from vertopal.api.credential import Credential
from vertopal.api.interface import _Interface
from vertopal.api.response import _CustomResponse
from vertopal.enums import InterfaceStrategyMode, InterfaceSublistMode
from vertopal.io.protocols import Readable, Writable

# Define public names for external usage
__all__ = [
    "API",
]


class API(_Interface):
    """
    Client helpers for Vertopal API version 1.

    The `API` object provides thin, typed wrappers over the HTTP
    endpoints exposed by Vertopal v1. Methods assemble the JSON payloads
    expected by the server and delegate network I/O to the underlying 
    `vertopal.api.interface._Interface` implementation.

    Example:

        >>> from vertopal.api.v1 import API
        >>> from vertopal.io.adapters.file import FileInput
        >>> inp = FileInput("./document.pdf")
        >>> with API() as client:
        ...     resp = client.upload_file(inp)
    """

    def __init__(self, *, credential: Optional[Credential] = None):
        """
        Create a new API client instance.

        Args:
            credential (Optional[Credential]): A `Credential` instance
                containing application id and token, or `None` to use
                configuration-provided credentials.
        """
        super().__init__(credential=credential)
        self.version = 1

    def upload_file(self, readable: Readable) -> _CustomResponse:
        """
        Upload a file to the Vertopal server.

        Args:
            readable (Readable): The readable to read the file from.

        Returns:
            _CustomResponse: Response wrapper with upload details and
                the server response object available via
                `original_response`.
        """
        filename = readable.filename or "upload.bin"
        content_type = readable.content_type or "application/octet-stream"

        with readable.open() as file:
            response = self.send_request(
                path="/upload/file",
                method="POST",
                data={
                    'data': '{'
                        f'"app": "{self._credential.app}"'
                    '}'
                },
                files=[(
                    "file",
                    (filename, file, content_type)
                )],
                timeout=self.long_timeout,
            )
        return response

    def convert_file(
        self,
        connector: str,
        output_format: str,
        *,
        input_format: Optional[str] = None,
        mode: InterfaceStrategyMode = InterfaceStrategyMode.ASYNC,
    ) -> _CustomResponse:
        """
        Request conversion of an uploaded file.

        Args:
            connector (str): Connector returned by the upload task.
            output_format (str): Target format[-type] for conversion.
            input_format (Optional[str]): Optional input format[-type]
                hint for the conversion engine.
            mode (InterfaceStrategyMode): Strategy mode; synchronous
                (`vertopal.enums.InterfaceStrategyMode.SYNC`)
                or asynchronous
                (`vertopal.enums.InterfaceStrategyMode.ASYNC`)
                processing; defaults to async mode.

        Returns:
            _CustomResponse: Response wrapper containing conversion
                task information.
        """
        if input_format:
            params: str = (
                f'"input": "{input_format}",'
                f'"output": "{output_format}"'
            )
        else:
            params: str = f'"output": "{output_format}"'

        response = self.send_request(
            path="/convert/file",
            method="POST",
            data={
                'data': '{'
                    f'"app": "{self._credential.app}",'
                    f'"connector": "{connector}",'
                    '"include": ["result", "entity"],'
                    f'"mode": "{mode}",'
                    '"parameters": {'
                        f'{params}'
                    '}'
                '}'
            },
            timeout=self.default_timeout,
        )
        return response

    def convert_status(self, connector: str) -> _CustomResponse:
        """
        Retrieve the current status for a conversion task.

        Args:
            connector (str): Connector identifier for the task.

        Returns:
            _CustomResponse: Response with task status details.
        """
        response = self.send_request(
            path="/convert/status",
            method="POST",
            data={
                'data': '{'
                    f'"app": "{self._credential.app}",'
                    f'"connector": "{connector}"'
                '}'
            },
            timeout=self.default_timeout,
        )
        return response

    def task_response(self, connector: str) -> _CustomResponse:
        """
        Fetch the result payload for a completed task.

        Args:
            connector (str): Connector identifier for the task.

        Returns:
            _CustomResponse: Response wrapping the task's result.
        """
        response = self.send_request(
            path="/task/response",
            method="POST",
            data={
                'data': '{'
                    f'"app": "{self._credential.app}",'
                    f'"connector": "{connector}",'
                    '"include": ["result"]'
                '}'
            },
            timeout=self.default_timeout,
        )
        return response

    def download_url(self, connector: str) -> _CustomResponse:
        """
        Obtain a download URL for a converted file.

        Args:
            connector (str): Connector identifier returned by the
                conversion task.

        Returns:
            _CustomResponse: Response containing the download URL
                and related metadata.
        """
        response = self.send_request(
            path="/download/url",
            method="POST",
            data={
                'data': '{'
                    f'"app": "{self._credential.app}",'
                    f'"connector": "{connector}"'
                '}'
            },
            timeout=self.default_timeout,
        )
        return response

    def download_url_get(
        self,
        writable: Writable,
        connector: str,
        *,
        chunk_size: Optional[int] = None,
    ) -> None:
        """
        Stream a converted file to a `Writable` sink.

        Args:
            writable (Writable): Destination sink implementing the
                writable protocol.
            connector (str): Connector identifier for the conversion
                result to download.
            chunk_size (Optional[int]): Number of bytes to request per
                streamed chunk. When `None`, the value is read from
                configuration (`connection_settings.stream_chunk_size`).
        """
        if chunk_size:
            stream_chunk_size: int = chunk_size
        else:
            stream_chunk_size: int = self._config.get(
                "connection_settings",
                "stream_chunk_size",
                cast=int,
            )

        args = {
            "path": "/download/url/get",
            "method": "POST",
            "data":{
                'data': '{'
                    f'"app": "{self._credential.app}",'
                    f'"connector": "{connector}"'
                '}'
            },
            "timeout": self.long_timeout,
            "stream": True,
        }

        with self.send_request(**args) as r:
            with writable.open() as out:
                for chunk in r.iter_content(chunk_size=stream_chunk_size):
                    if chunk:
                        out.write(chunk)

    def format_get(self, format_name: str) -> _CustomResponse:
        """
        Query metadata for a specific file format.

        Args:
            format_name (str): Format[-type] identifier to query.

        Returns:
            _CustomResponse: Server response describing the format.
        """
        response = self.send_request(
            path="/format/get",
            method="POST",
            data={
                'data': '{'
                    f'"app": "{self._credential.app}",'
                    '"parameters": {'
                        f'"format": "{format_name}"'
                    '}'
                '}'
            },
            timeout=self.default_timeout,
        )
        return response

    def convert_graph(
        self,
        input_format: str,
        output_format: str,
    ) -> _CustomResponse:
        """
        Retrieve the conversion graph between two formats.

        Args:
            input_format (str): Source/input format[-type] identifier.
            output_format (str): Target/output format[-type] identifier.

        Returns:
            _CustomResponse: Response describing conversion
                relationships and available paths.
        """
        response = self.send_request(
            path="/convert/graph",
            method="POST",
            data={
                'data': '{'
                    f'"app": "{self._credential.app}",'
                    '"parameters": {'
                        f'"input": "{input_format}",'
                        f'"output": "{output_format}"'
                    '}'
                '}'
            },
            timeout=self.default_timeout,
        )
        return response

    def convert_formats(
        self,
        sublist: InterfaceSublistMode,
        *,
        format_name: Optional[str] = None,
    ) -> _CustomResponse:
        """
        List supported formats for conversion (inputs or outputs).

        Args:
            sublist (InterfaceSublistMode): Either
                `InterfaceSublistMode.INPUTS` or
                `InterfaceSublistMode.OUTPUTS`.
            format_name (Optional[str]): Optional specific format[-type]
                to filter the results for.

        Raises:
            ValueError: If `sublist` is not a valid
                `InterfaceSublistMode` member.

        Returns:
            _CustomResponse: Server response with supported formats.
        """
        if sublist not in InterfaceSublistMode:
            raise ValueError(
                "`sublist` must be either "
                "`InterfaceSublistMode.INPUTS` "
                "or `InterfaceSublistMode.OUTPUTS`."
            )

        if format_name:
            data_format = f',"format": "{format_name}"'
        else:
            data_format = ""

        response = self.send_request(
            path="/convert/formats",
            method="POST",
            data={
                'data': '{'
                    f'"app": "{self._credential.app}",'
                    '"parameters": {'
                        f'"sublist": "{sublist}"'
                        f'{data_format}'
                    '}'
                '}'
            },
            timeout=self.default_timeout,
        )
        return response
