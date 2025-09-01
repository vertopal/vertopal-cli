# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Top-level package initializer for the Vertopal CLI and Python
#   library. Declares package metadata (author, copyright,
#   license, version, description, email, url) and re‑exports core
#   convenience classes for external consumers. Serves as the
#   primary import point for most CLI and library integrations.

"""
Top-level package for the Vertopal CLI and library.

This package exposes the public convenience API for the Vertopal
command-line interface and Python library. The module declares the
package version and re-exports commonly used helpers for external
consumers.

Attributes:
    __author__ (str): Package author.
    __copyright__ (str): Copyright notice.
    __license__ (str): License name.
    __version__ (str): Current package version.
    __description__ (str): Short summary of the package purpose.
    __email__ (str): Contact email for support or inquiries.
    __url__ (str): Project homepage.

Example:

    >>> from vertopal import Converter
    >>> from vertopal import __version__  # Access package version
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

__author__: str = "Vertopal"
__copyright__: str = "Copyright (c) 2023-2025 Vertopal"
__license__: str = "MIT License"
__version__: str = "2.0.3"
__description__: str = (
    "Command-line and Python interface "
    "for converting digital files via Vertopal API"
)
__email__: str = "contact@vertopal.com"
__url__: str = "https://github.com/vertopal/vertopal-cli"

from vertopal.api.converter import Converter

# Define public names for external usage
__all__ = [
    "Converter",
]
