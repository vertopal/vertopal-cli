# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Core I/O protocol definitions for Vertopal, including abstract
#   base classes and type hints for readable, writable, and
#   seekable binary data sources and sinks.

"""
I/O protocol definitions for readable and writable streams.

These protocols abstract byte-oriented sources and sinks used across
Vertopal package. They enable structural typing for adapters such as
file, pipe, and in-memory readers and writers.
"""

# pylint: disable=unnecessary-ellipsis
# pylint: disable=too-few-public-methods

from typing import (
    BinaryIO,
    ContextManager,
    Optional,
    Protocol,
    runtime_checkable,
)

from vertopal.types import PathType

# Define public names for external usage
__all__ = [
    "Readable",
    "Writable",
]


@runtime_checkable
class Readable(Protocol):
    """
    Represents an object that can be opened for reading 
    as a binary file-like resource.
    """

    def open(self) -> ContextManager[BinaryIO]:
        """
        Returns a context manager that opens the resource
        for binary reading.
        """
        ...

    @property
    def filename(self) -> Optional[str]:
        """Gets the name of the file, if available."""
        ...

    @property
    def content_type(self) -> Optional[str]:
        """Gets the MIME type of the content, if known."""
        ...


@runtime_checkable
class Writable(Protocol):
    """
    Represents an object that can be opened for writing 
    as a binary file-like resource.
    """

    def open(self) -> ContextManager[BinaryIO]:
        """
        Returns a context manager that opens the resource
        for binary writing.
        """
        ...


@runtime_checkable
class PathWritable(Protocol):
    """An object whose writable path can be read and set."""

    @property
    def path(self) -> PathType:
        """Get the writable file system path."""
        ...

    @path.setter
    def path(self, value: PathType) -> None:
        """Set the writable file system path."""
        ...
