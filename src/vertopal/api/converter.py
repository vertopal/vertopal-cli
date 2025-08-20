# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   The implementation composes request payloads and delegates HTTP
#   transport to the API client. It intentionally keeps conversion
#   orchestration local to the client process so calling code can
#   synchronously wait for completion or stream outputs on demand.

"""
Helpers for file conversion using the Vertopal API.

This module provides the `Converter` convenience class and an internal
`_Conversion` helper which orchestrates the typical upload, convert,
poll, and download workflow against the Vertopal v1 API.

The public `Converter` accepts objects that implement the `Readable`
and `Writable` protocols and returns a lightweight `_Conversion`
controller that can be waited on, queried for status, and used to stream
the converted result to a sink.
"""

from dataclasses import dataclass
from time import sleep
from types import SimpleNamespace
from typing import Callable, cast, Optional, Tuple

from vertopal import settings
from vertopal.api.credential import Credential
from vertopal.api.v1 import API
import vertopal.exceptions as vex
from vertopal.enums import InterfaceStrategyMode
from vertopal.io.protocols import PathWritable, Readable, Writable
from vertopal.utils.misc import _canonicalize_format

# Define public names for external usage
__all__ = [
    "Converter",
]


@dataclass(frozen=True, slots=True)
class _InputSpec:
    """Holding specifications of an input file."""
    source: Readable
    format: Optional[str] = None

    def __post_init__(self):
        object.__setattr__(self, "format", _canonicalize_format(self.format))


@dataclass(frozen=True, slots=True)
class _OutputSpec:
    """Holding specifications of an output file."""
    sink: Writable
    format: str

    def __post_init__(self):
        object.__setattr__(self, "format", _canonicalize_format(self.format))


class _Conversion:
    """
    Orchestrates a single file conversion workflow.

    This internal helper handles uploading the input, requesting a
    conversion, polling task status, and exposing helpers to download
    the resulting output. It is returned by `Converter.convert`
    and intended for short-lived use.
    """

    def __init__(
        self,
        client: API,
        readable: Readable,
        writable: Writable,
        *,
        output_format: str,
        input_format: Optional[str] = None,
    ):
        """
        Create and start a conversion operation.

        Args:
            client (API): API client used to perform requests.
            readable (Readable): Source implementing the readable
                protocol for the input data.
            writable (Writable): Destination implementing the writable
                protocol for the converted data.
            output_format (str): Target output format[-type] identifier.
            input_format (Optional[str]): Optional input format[-type]
                hint.
        """
        self.__input = _InputSpec(readable, input_format)
        self.__output = _OutputSpec(writable, output_format)
        self.__client = client
        self.__convert_connector: Optional[str] = None
        self.__convert_status: Optional[str] = None
        self.__credits: Optional[int] = None

        self.__convert()

    def wait(
        self,
        poll_intervals: Tuple[int, ...] = settings.SLEEP_PATTERN,
        sleep_func: Callable[[float], None] = sleep,
    ) -> None:
        """
        Poll the conversion task until it completes.

        Args:
            poll_intervals (Tuple[int, ...]): Sequence of sleep
                durations in seconds used between polls. Defaults to
                `vertopal.settings.SLEEP_PATTERN`.
            sleep_func (Callable[[float], None]): Callable used to
                sleep between polls. Defaults to `sleep` from the
                standard library.
        """
        sleep_step = 0
        while not self.done():
            sleep_func(poll_intervals[sleep_step])
            if sleep_step < len(poll_intervals) - 1:
                sleep_step += 1

    def done(self) -> bool:
        """
        Return `True` when the conversion task has reached completion.

        Returns:
            bool: `True` if the underlying task is completed. Otherwise
            `False`.
        """
        if self.__get_convert_task_status().task == "completed":
            return True
        return False

    def successful(self):
        """
        Return `True` when the conversion result indicates success.

        Returns:
            bool: `True` if the conversion completed successfully.
            Otherwise `False`.
        """
        if self.__convert_status == "successful":
            return True
        return False

    def download(self, *, use_server_filename: bool = False) -> None:
        """
        Download the converted file into the configured sink.

        Args:
            use_server_filename (bool): If `True` and the sink
                implements `PathWritable`, set the sink path to the
                server-provided filename before downloading.
        """
        download_url = self.__download_url()
        server_filename = download_url.filename

        if (
            use_server_filename
            and isinstance(self.__output.sink, PathWritable)
        ):
            self.__output.sink.path = server_filename

        self.__client.download_url_get(
            writable=self.__output.sink,
            connector=download_url.connector,
        )

    def __download_url(self) -> SimpleNamespace:
        response = self.__client.download_url(
            connector=cast(str, self.__convert_connector),
        )

        return SimpleNamespace(
            connector=response.nested.result.output.connector,
            filename=response.nested.result.output.name,
        )

    def __get_convert_task_status(self) -> SimpleNamespace:
        response = self.__client.task_response(
            connector=cast(str, self.__convert_connector),
        )

        result_output = response.nested.result.output
        # If result.output.result is present, update status and credits
        if result_output.result:
            self.__convert_status = result_output.result.output.status
            self.__credits = result_output.entity.vcredits
        else:
            self.__convert_status = None

        return SimpleNamespace(
            task=response.nested.result.output.entity.status,
            credits=self.__credits,
            convert=self.__convert_status,
        )

    def __convert(self) -> None:
        upload_response = self.__client.upload_file(
            readable=self.__input.source,
        )
        upload_connector = upload_response.nested.result.output.connector

        convert_response = self.__client.convert_file(
            connector=upload_connector,
            output_format=cast(str, self.__output.format),
            input_format=self.__input.format,
            mode=InterfaceStrategyMode.ASYNC,
        )
        if convert_response.nested.entity.status != "running":
            raise vex.EntityStatusNotRunningError
        self.__convert_connector = convert_response.nested.entity.id

    @property
    def credits_used(self) -> Optional[int]:
        """
        Return the credits consumed for this conversion, or `None` when
        not yet available.
        """
        if self.__credits is None:
            self.__credits = self.__get_convert_task_status().credits
        return self.__credits


class Converter:
    """
    Convenience facade for performing file conversions.

    The `Converter` class provides a simple entry point to convert files
    by accepting `Readable` and `Writable` protocol objects and
    returning an active `_Conversion` controller.

    Example:

        >>> from vertopal.api.converter import Converter
        >>> from vertopal.io import FileInput, FileOutput
        >>> source = FileInput("./input.md")
        >>> sink = FileOutput("./output.pdf")
        >>> converter = Converter()
        >>> conversion = converter.convert(
        ...     readable=source,
        ...     writable=sink,
        ...     output_format="pdf",
        ... )
        >>> conversion.wait()
        >>> if conversion.successful():
        ...     conversion.download()
        ...     print(conversion.credits_used, "credit(s) used.")
        ... 
        '1 credit(s) used.'
    """

    def __init__(
        self,
        credential: Optional[Credential] = None,
    ):
        """
        Create a new Converter.

        Args:
            credential (Optional[Credential]): A `Credential` instance
                containing application id and token, or `None` to use
                configuration-provided credentials.
        """
        self.__client = API(credential=credential)

    def convert(
        self,
        readable: Readable,
        writable: Writable,
        output_format: str,
        *,
        input_format: Optional[str] = None,
    ) -> _Conversion:
        """
        Start a conversion and return its controller.

        Args:
            readable (Readable): Source implementing the readable
                protocol for the input data.
            writable (Writable): Destination implementing the writable
                protocol for the converted data.
            output_format (str): Target output format[-type] identifier.
            input_format (Optional[str]): Optional input format[-type]
                hint.

        Returns:
            _Conversion: Controller managing the started conversion.
        """
        conversion = _Conversion(
            client=self.__client,
            readable=readable,
            writable=writable,
            output_format=output_format,
            input_format=input_format,
        )
        return conversion

    def close(self) -> None:
        """Close the underlying API client's connection."""
        self.__client.close()
