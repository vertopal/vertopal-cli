# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Common type alias definitions for Vertopal CLI and Python library.
#   Provides the `PathType` union for representing filesystem paths
#   as either strings or os.PathLike objects, ensuring consistent
#   type hints and interface compatibility across modules.

"""
Type aliases for Vertopal CLI and package modules.

This module defines common type aliases used throughout the Vertopal
CLI and Python package, including the `PathType` union for file system
paths. These aliases improve type clarity and compatibility with
standard library and OS interfaces.
"""

from os import PathLike
from typing import Union

# Define public names for external usage
__all__ = [
    "PathType",
]


# Type alias for file system paths.
# Represents either a string path or an object implementing the
# `os.PathLike` protocol (such as `pathlib.Path`).
# Used for parameters and attributes that accept file system paths in
# Vertopal CLI and library modules.
PathType = Union[str, PathLike[str]]
