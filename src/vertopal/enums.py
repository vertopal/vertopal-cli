# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Enumerations and terminal control helpers for the Vertopal CLI
#   and library. Provides public enums for interface strategy and
#   format sublist selection, as well as internal enums for progress
#   state tracking. Includes ANSI escape code utilities for cursor
#   positioning, screen manipulation, and rendering control within
#   CLI progress displays.

"""
Enumerations and terminal helpers used by Vertopal CLI.

This module defines enums used across the Vertopal package for
interface strategy selection and format sublist selection. It also
contains small internal helpers for tracking progress unit state and
for producing ANSI escape sequences used by the CLI progress
renderers.
"""

from enum import auto, Enum, unique
import sys
from typing import TextIO

# Define public names for external usage
__all__ = [
    "InterfaceStrategyMode",
    "InterfaceSublistMode",
]


class InterfaceStrategyMode(str, Enum):
    """
    Execution strategy modes for API operations.

    Members:
        ASYNC: Execute operations asynchronously.
        SYNC: Execute operations synchronously.
    """
    ASYNC = "async"
    SYNC = "sync"


class InterfaceSublistMode(str, Enum):
    """
    Sublist selection enum for format queries.

    Members:
        INPUTS: Target input formats.
        OUTPUTS: Target output formats.
    """
    INPUTS = "inputs"
    OUTPUTS = "outputs"


@unique
class _ProgressUnitStateType(Enum):
    """
    Internal enum representing progress task states.

    Values indicate the lifecycle stage of a task displayed by the
    progress renderer.
    """

    PENDING = auto()
    RUNNING = auto()
    ENDED = auto()


class _ANSIEscapeCode(Enum):
    """
    ANSI escape sequences used by the CLI for cursor and screen
    control.

    Each enum member's value is the raw escape sequence or a format
    template that accepts keyword arguments.

    Example:

        >>> from vertopal.enums import _ANSIEscapeCode
        >>> _ANSIEscapeCode.CURSOR_UP_N.write(n=4)  # Move up 4 lines
        >>> _ANSIEscapeCode.CURSOR_INVISIBLE  # Make cursor invisible
    """

    CURSOR_SAVE = "\0337"
    CURSOR_RESTORE = "\0338"
    CURSOR_UP_N = "\033[{n}A"
    CURSOR_DOWN_N = "\033[{n}B"
    CURSOR_RIGHT_N = "\033[{n}C"
    CURSOR_LEFT_N = "\033[{n}D"
    CURSOR_NEXT_LINE_N = "\033[{n}E"
    CURSOR_PREV_LINE_N = "\033[{n}F"
    CURSOR_MOVE_TO_COLUMN_N = "\033[{n}G"
    CURSOR_ERASE_LINE = "\033[K"
    CURSOR_ERASE_TO_END = "\033[0K"
    CURSOR_ERASE_TO_START = "\033[1K"
    CURSOR_ERASE_TO_COMPLETE = "\033[2K"
    CURSOR_INVISIBLE = "\033[?25l"
    CURSOR_VISIBLE = "\033[?25h"

    def format(self, **values) -> str:
        """
        Format the escape sequence using keyword arguments.

        Args:
            **values: Keyword arguments used to substitute values into
                formatted escape templates (for example, `n=3`).

        Returns:
            str: The formatted escape sequence.
        """
        return self.value.format(**values)

    def write(
        self,
        stream: TextIO = sys.stdout,
        *,
        flush: bool = False,
        **values,
    ) -> None:
        """
        Write the ANSI escape sequence to an output stream.

        Args:
            stream (TextIO): Stream to write to. Defaults to `sys.stdout`.
            flush (bool): When `True`, flush the stream after writing.
            **values: Optional formatting values for the escape
                sequence when the member is a template.
        """
        if values:
            sequence: str = self.format(**values)
        else:
            sequence: str = str(self)

        stream.write(sequence)

        # Ensures immediate execution of the escape sequence
        if flush:
            stream.flush()

    def __str__(self) -> str:
        """
        Return the escape sequence as a string.

        Returns:
            str: The raw escape sequence or formatted template value.
        """
        return self.value
