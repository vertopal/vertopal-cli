# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   In-memory adapters implementing Vertopal's Readable protocol.
#   Provide binary streams from text or byte data without touching
#   the file system, useful for testing and transient data sources.

"""
In-memory adapters for Vertopal's Readable I/O protocol.

This module defines `BytesInput` and `TextInput`, which wrap string or
byte data in a binary file-like object. These are useful for supplying
data to pipelines without touching the file system.

Example:

    >>> from vertopal.io.adapters.memory import BytesInput, TextInput
    >>> bts = BytesInput(b"ABC")
    >>> with bts.open() as f:
    ...     f.read()
    b'ABC'
    >>> txt = TextInput("Hello")
    >>> with txt.open() as f:
    ...     f.read()
    b'Hello'
"""

from contextlib import nullcontext
import io
from typing import Optional

from vertopal.io.protocols import Readable

# Define public names for external usage
__all__ = [
    "BytesInput",
    "TextInput",
]


class _MemoryInputBase(Readable):
    """
    Base class for in-memory readable adapters.

    Stores optional filename and MIME type metadata common to text
    and byte-based memory inputs.
    """

    def __init__(
        self,
        *,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> None:
        """
        Initialize the memory input metadata.

        Args:
            filename (Optional[str]): Optional display name for this
                input.
            content_type (Optional[str]): Optional MIME type string.
        """
        self._filename = filename
        self._content_type = content_type

    @property
    def filename(self) -> Optional[str]:
        """Optional display name for this input."""
        return self._filename

    @property
    def content_type(self) -> Optional[str]:
        """Optional MIME type string for this input."""
        return self._content_type

    def open(self):
        """
        Return a binary readable stream over the data.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement open().")


class BytesInput(_MemoryInputBase):
    """Readable adapter for raw bytes data."""

    def __init__(
        self,
        data: bytes,
        *,
        filename: Optional[str] = "data.bin",
        content_type: Optional[str] = "application/octet-stream",
    ) -> None:
        """
        Create a new `BytesInput`.

        Args:
            data (bytes): The bytes object to wrap.
            filename (Optional[str]): Optional display name; defaults to
                `"data.bin"`.
            content_type (Optional[str]): MIME type; defaults to
                `"application/octet-stream"`.
        """
        super().__init__(filename=filename, content_type=content_type)
        self._bytes = data

    def open(self):
        """Return a binary stream over the stored bytes."""
        return nullcontext(io.BytesIO(self._bytes))


class TextInput(_MemoryInputBase):
    """
    Readable adapter for UTF-8 (or other encoding) text data.

    Encodes the given string to bytes when constructed.
    """

    def __init__(
        self,
        data: str,
        *,
        encoding: str = "utf-8",
        filename: Optional[str] = "data.txt",
        content_type: Optional[str] = "text/plain; charset=utf-8",
    ) -> None:
        """
        Create a new `TextInput`.

        Args:
            data (str): The text string to wrap.
            encoding (str): Character encoding for the string.
            filename (Optional[str]): Optional display name; defaults to
                `"data.txt"`.
            content_type (Optional[str]): MIME type for the text;
                defaults to UTF-8 plain text
                (`"text/plain; charset=utf-8"`).
        """
        super().__init__(filename=filename, content_type=content_type)
        self._bytes = data.encode(encoding)

    def open(self):
        """Return a binary stream over the encoded text."""
        return nullcontext(io.BytesIO(self._bytes))
