# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Adapters for reading from and writing to file system paths,
#   implementing Vertopal's Readable, Writable, and PathWritable
#   protocols for binary I/O operations.

"""
File-based stream adapters for Vertopal's I/O protocols.

This module provides adapters that implement Vertopal's readable and
writable I/O protocols backed by file system paths. Use these types when
your source or sink is a local file.

Example:

    Read a file through the Readable protocol:

    >>> from vertopal.io.adapters.file import FileInput
    >>> src = FileInput("input.txt")
    >>> with src.open() as f:
    ...     data = f.read()

    Write to a file through the Writable protocol:

    >>> from vertopal.io.adapters.file import FileOutput
    >>> out = FileOutput("output.txt")
    >>> with out.open() as f:
    ...     _ = f.write(b"hello")
"""

from pathlib import Path
from typing import BinaryIO, cast, ContextManager, Optional

from vertopal.io.protocols import PathWritable, Readable, Writable
from vertopal.types import PathType

# Define public names for external usage
__all__ = [
    "FileInput",
    "FileOutput",
]


class FileInput(Readable):
    """
    Readable adapter for binary input from a file path.

    This adapter opens the given path in binary read mode and exposes
    optional metadata such as a filename (derived from the path if not
    provided) and a content type.

    Example:

        >>> inp = FileInput(
        ...     "invoice.pdf",
        ...     content_type="application/pdf",
        ... )
        >>> inp.filename
        'invoice.pdf'
        >>> with inp.open() as f:
        ...     chunk = f.read(4)
    """

    def __init__(
        self,
        path: PathType,
        *,
        filename: Optional[str] = None,
        content_type: Optional[str] = "application/octet-stream",
    ) -> None:
        """Create a new `FileInput`.

        Args:
            path (PathType): File system path to read from. Accepts a
                string or a `pathlib.Path`-like value.
            filename (Optional[str]): Optional display name exposed via
                the `filename` property. If omitted, the basename of
                `path` is used; if that is empty, `"upload.bin"`
                is used as a fallback.
            content_type (Optional[str]): Optional MIME type for the
                input data. If not provided, defaults to
                `"application/octet-stream"`.
        """
        self._path = path
        self._filename = filename or Path(path).name or "upload.bin"
        self._content_type = content_type

    def open(self) -> ContextManager[BinaryIO]:
        """
        Open the file for binary reading.

        Returns:
            ContextManager[BinaryIO]: A context manager yielding
            a binary file object opened in `"rb"` mode.

        Raises:
            FileNotFoundError: If the path does not exist.
            PermissionError: If the file is not readable.
            IsADirectoryError: If the path refers to a directory.
            OSError: For other I/O related errors.
        """
        return open(self._path, "rb")

    @property
    def filename(self) -> Optional[str]:
        """
        Optional display name for this input.

        Defaults to the basename of `path` if not explicitly set.
        """
        return self._filename

    @property
    def content_type(self) -> Optional[str]:
        """
        Optional MIME type for the input data.

        Defaults to `"application/octet-stream"` if not provided.
        """
        return self._content_type


class FileOutput(Writable, PathWritable):
    """
    Writable adapter for binary output to a file path.

    Opens the target path in binary write or append mode. The `path`
    can be reassigned after construction via the `path` property to
    redirect output.

    Example:

        >>> out = FileOutput("README.md", append=False)
        >>> with out.open() as f:
        ...     _ = f.write(b"# Vertopal Rocks!")
    """

    def __init__(
        self,
        path: PathType,
        buffering: int = -1,
        *,
        append: bool = False,
    ) -> None:
        """Create a new `FileOutput`.

        Args:
            path (PathType): File system path to write to. Accepts a
                string or a `pathlib.Path`-like value.
            buffering (int): Buffering policy forwarded to `open`. `-1`
                uses the platform default, `0` requests unbuffered
                (binary only), and a positive value requests a buffer of
                approximately that size.
            append (bool): If `True`, the underlying file will be opened
                in append mode (`"ab"`); otherwise it will use write
                mode (`"wb"`).
        """
        self._path = path
        self._buffering = buffering
        self._mode = "ab" if append else "wb"

    def open(self) -> ContextManager[BinaryIO]:
        """
        Open the file for binary writing.

        The file is opened in `"ab"` if `append` was set, otherwise in
        `"wb"`. Parent directories are not created automatically.

        Returns:
            ContextManager[BinaryIO]: A context manager yielding
            a binary file object for writing.

        Raises:
            FileNotFoundError: If the path's directory does not exist.
            PermissionError: If the file is not writable.
            IsADirectoryError: If the path refers to a directory.
            OSError: For other I/O related errors.

        Example:

            >>> sink = FileOutput("README.md", buffering=8192)
            >>> with sink.open() as f:
            ...     _ = f.write(b"# Vertopal Rocks!")
        """
        # pylint: disable=consider-using-with
        file = open(self._path, self._mode, buffering=self._buffering)
        return cast(ContextManager[BinaryIO], file)

    @property
    def path(self) -> PathType:
        """
        The current file system path used for output.

        You can reassign this property to redirect subsequent writes.
        """
        return self._path

    @path.setter
    def path(self, value: PathType) -> None:
        """Set the file system path used for output."""
        self._path = value
