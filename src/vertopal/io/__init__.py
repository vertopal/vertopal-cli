# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Package initializer for Vertopal I/O adapters. Exposes unified
#   imports for file-based, in-memory, and stdio-based protocol
#   implementations used across the Vertopal processing pipeline.

"""
Vertopal I/O adapters package initializer.

This package bundles multiple I/O adapter implementations that conform
to the `Readable` and `Writable` protocols. These adapters provide
consistent, file-like binary streams from a variety of sources:

- **FileInput / FileOutput** — Read from or write to filesystem paths.
- **BytesInput / TextInput** — Wrap in-memory bytes or text as streams.
- **PipeInput / PipeOutput** — Use standard input/output as streams.

Importing directly from `vertopal.io` is the preferred way for external
code to access these common adapters.

Example:

    >>> from vertopal.io import TextInput, PipeOutput
    >>> tin = TextInput("Hello World")
    >>> with tin.open() as f_in, PipeOutput().open() as f_out:
    ...     f_out.write(f_in.read())
"""

from vertopal.io.adapters.file import (
    FileInput,
    FileOutput,
)
from vertopal.io.adapters.memory import (
    BytesInput,
    TextInput,
)
from vertopal.io.adapters.stdio import (
    PipeInput,
    PipeOutput,
)

# Define public names for external usage
__all__ = [
    "FileInput",
    "FileOutput",
    "BytesInput",
    "TextInput",
    "PipeInput",
    "PipeOutput",
]
