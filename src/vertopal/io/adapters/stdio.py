# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Adapters for standard input and output streams, implementing
#   Vertopal's Readable and Writable protocols. Designed for binary
#   pipeline integration without closing the underlying stdio handles.

"""
Standard I/O adapters for Vertopal's Readable/Writable protocol.

This module provides `PipeInput` and `PipeOutput` classes for working
with standard input and output streams as binary I/O endpoints in the
Vertopal pipeline. These adapters do not close the underlying streams.

Example:

    >>> from vertopal.io.adapters.stdio import PipeInput, PipeOutput
    >>> pin = PipeInput()
    >>> with pin.open() as f:
    ...     data = f.read()
    >>> pout = PipeOutput()
    >>> with pout.open() as f:
    ...     f.write(data)
"""

from contextlib import nullcontext
import sys
from typing import Optional

from vertopal.io.protocols import Readable, Writable

# Define public names for external usage
__all__ = [
    "PipeInput",
    "PipeOutput",
]


class PipeInput(Readable):
    """Readable adapter for standard input as a binary stream."""

    def __init__(
        self,
        *,
        filename: Optional[str] = None,
        content_type: Optional[str] = "application/octet-stream",
    ) -> None:
        """
        Initialize a standard input adapter.

        Args:
            filename (Optional[str]): Optional display name; defaults to
                `"stdin"`.
            content_type (Optional[str]): MIME type; defaults to
                `"application/octet-stream"`.
        """
        self._filename = filename or "stdin"
        self._content_type = content_type

    def open(self):
        """
        Return a context manager over `sys.stdin.buffer`.

        The standard input stream is *borrowed* and not closed.
        """
        # Do not close stdin; just borrow it
        return nullcontext(sys.stdin.buffer)

    @property
    def filename(self) -> Optional[str]:
        """Display name for this input (usually `"stdin"`)."""
        return self._filename

    @property
    def content_type(self) -> Optional[str]:
        """MIME type string for this input."""
        return self._content_type


class PipeOutput(Writable):
    """Writable adapter for standard output as a binary stream."""

    def open(self):
        """
        Return a context manager over `sys.stdout.buffer`.

        The standard output stream is *borrowed* and not closed.
        """
        # Do not close stdout; just borrow it
        return nullcontext(sys.stdout.buffer)
