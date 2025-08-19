# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Terminal styling utilities for the Vertopal CLI and library.
#   Defines the `Prism` class, which applies ANSI escape codes
#   to text, parses simple tag-based styles (e.g., "[red]Error[/red]"),
#   and writes styled output to streams. Enables ANSI handling on
#   Windows for compatibility, and provides a compact, consistent API
#   for colored and formatted terminal output across the project.

"""
Terminal styling utilities (Prism).

The Prism class provides convenience helpers to apply ANSI escape
codes to text, parse simple tag-based styling (for example
`[red]text[/red]`), and write styled output to streams. The module
enables ANSI handling on Windows when needed and exposes a compact
API suitable for consistent CLI formatting across the project.
"""

import os
import re
import sys
from typing import Any, ClassVar, Dict, List, Optional, TextIO

# Define public names for external usage
__all__ = [
    "Prism",
]


# Enable ANSI codes for Windows if needed
if sys.platform.startswith("win"):
    os.system("")


class Prism:
    """
    A class for styling terminal text using ANSI escape codes.

    This class provides methods to apply ANSI styling to text strings
    and render styled text with custom tags or predefined styles.

    Attributes:
        ANSI_CODES (ClassVar[Dict[str, str]]): A dictionary
            mapping style names to ANSI escape codes.
        RESET (str): ANSI reset code to revert styling.
        TAG_RE (Pattern): Regular expression for identifying
            custom tags in text.

    Available Colors:
        - black
        - blue
        - cyan
        - gray
        - green
        - magenta
        - red
        - white
        - yellow

    Available Styles:
        - bold (alias: strong, b)
        - italic (alias: i)
        - strikethrough (alias: s)
        - underline (alias: u)

    Example:

        >>> from vertopal.utils.prism import Prism
        >>> print(Prism.get_text("Hello, World!", style="green"))
        >>> Prism.print(
        ...     "Error: Something went wrong!",
        ...     style="red",
        ...     stream=sys.stderr,
        ... )
        >>> Prism.print(
        ...     "[red]Another error with custom style tags![/red]",
        ...     stream=sys.stderr,
        ... )
        >>> Prism.print(
        ...     "Underlined text",
        ...     style="underline",
        ... )
        >>> Prism.print(
        ...     "Strikethrough text",
        ...     style="strikethrough",
        ... )
        >>> Prism.print(
        ...     "Debugging information...",
        ...     style="underline blue",
        ...     stream=sys.stderr,
        ... )
        >>> Prism.print(
        ...     "In the interplay "
        ...     "of [red]red[/red], [green]green[/green], "
        ...     "[cyan]blue[/cyan], and [yellow]yellow[/yellow], "
        ...     "there is [b][white]strength[/white][/b] "
        ...     "and [i][magenta]vibrancy[/magenta][/i]; "
        ...     "yet one [u]must always note[/u], "
        ...     "what was valid yesterday may [s]not be anymore[/s].",
        ... )
    """

    ANSI_CODES: ClassVar[Dict[str, str]] = {
        "black": "\033[30m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "gray": "\033[90m",
        "green": "\033[92m",
        "magenta": "\033[95m",
        "red": "\033[91m",
        "white": "\033[97m",
        "yellow": "\033[93m",
        "bold": "\033[1m",
        "strong": "\033[1m",  # Alias for bold
        "b": "\033[1m",  # Alias for bold
        "italic": "\033[3m",
        "i": "\033[3m", # Alias for italic
        "strikethrough": "\033[9m",
        "s": "\033[9m", # Alias for strikethrough
        "underline": "\033[4m",
        "u": "\033[4m", # Alias for underline
    }

    RESET: str = "\033[0m"

    TAG_RE: re.Pattern = re.compile(r'\[(/?)(\w+)\]')

    @classmethod
    def _get_style(cls, style: str) -> str:
        """
        Retrieve the ANSI code for a given style.

        Args:
            style (str): The name of the style.

        Returns:
            str: The ANSI escape code for the style,
            or the reset code if not found.
        """
        return cls.ANSI_CODES.get(style.lower(), cls.RESET)

    @classmethod
    def _parse_text(cls, text: str) -> str:
        """
        Parses a text string and applies ANSI escape codes
        based on custom tags.

        Args:
            text (str): Input text containing custom tag(s)
                for formatting (e.g., `"[i][red]Vertopal[/red][/i]"`).

        Returns:
            str: A string with ANSI escape codes applied
            for terminal rendering.
        """
        stack: List[str] = [] # To keep track of open tags
        output: str = "" # To build the final output string
        pos: int = 0 # Current position in the string

        for match in cls.TAG_RE.finditer(text):
            # Capture positions of the tag in the text
            start, end = match.span()
            # 'closing' is '/' if it's a closing tag; 'tag' is the tag name
            closing, tag = match.groups()
            # Normalize to lowercase
            tag = tag.lower()

            # Append text before the tag
            output += text[pos:start]
            pos = end

            # If the tag is not defined in our ANSI_CODES, ignore it
            if tag not in cls.ANSI_CODES:
                continue

            if closing:
                # Handling a closing tag:
                # check if it matches the most recent open tag.
                if stack and stack[-1] == tag:
                    stack.pop() # Pop the tag from our stack of open styles
                    output += cls.RESET # Reset formatting
                    # Reapply any formatting that is still open
                    for t in stack:
                        output += cls.ANSI_CODES[t]
                else:
                    # If the tag doesn't match the expected open tag,
                    # we could handle errors here.
                    # For now, we simply ignore unexpected closing tags.
                    pass
            else:
                # Handling an opening tag:
                # push the tag on the stack
                # and output its corresponding ANSI code.
                stack.append(tag)
                output += cls.ANSI_CODES[tag]

        # Append any remaining text after the last tag
        output += text[pos:]
        # Ensure the formatting is reset at the end
        output += cls.RESET
        return output

    @classmethod
    def get_text(cls, text: Any, style: Optional[str] = None) -> str:
        """
        Apply ANSI styles to text and parse embedded tags.

        Args:
            text (Any): The text to style (can be any object
                that converts to string).
            style (Optional[str]): A space-separated string
                of style names. Defaults to `None`.

        Returns:
            str: The styled text with ANSI codes applied.
        """
        output: List[str] = []

        if style:
            for style_token in style.split():
                output.append(cls._get_style(style_token))

        output.append(cls._parse_text(str(text)))
        output.append(cls.RESET)

        return "".join(output)

    @classmethod
    def print(
        cls,
        text: str,
        style: Optional[str] = None,
        stream: TextIO = sys.stdout,
    ) -> None:
        """
        Render styled text with ANSI codes
        and write to an output stream.

        Args:
            text (str): Text with embedded tag(s)
                (e.g., `"[red]Vertopal[/red]"`).
            style (Optional[str]): A space-separated string
                of style names. Defaults to `None`.
            stream (TextIO): Output stream to write to.
                Defaults to `sys.stdout`.
        """
        styled_text = cls.get_text(text, style)
        print(styled_text, file=stream)
