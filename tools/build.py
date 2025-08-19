#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Build-and-archive helper for Vertopal CLI binaries.
#   Invokes PyInstaller to produce a single-file executable and
#   packages artifacts from dist/ into a versioned ZIP archive.
#   Supports platform name override for artifact naming and optional
#   post-archive deletion of binaries. Intended to be run from the
#   repository root.

"""
Utilities to build and archive Vertopal CLI binaries.

This module provides a tiny build helper used to create a single-file
CLI binary using PyInstaller and to archive produced artifacts. It is
intended to be run as a standalone script from the project's
repository root.
"""

import argparse
from pathlib import Path
from subprocess import Popen
import sys
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile

# No public names in this file
__all__ = []


def main() -> None:
    """
    Script entry point that parses arguments and runs build tasks.

    This function parses command-line arguments, optionally overrides
    the platform identifier for naming, runs the PyInstaller build,
    and archives the resulting artifacts when the build succeeds.
    """
    repo_dir = Path(__file__).parent.parent.resolve()

    class _Platform:  # pylint: disable=too-few-public-methods
        """Utility for determining the target platform identifier.

        Attributes:
            override (Optional[str]): When set, forces the value
                returned by `Platform.get()`.
        """
        override: Optional[str] = None

        @classmethod
        def get(cls) -> str:
            """
            Return a normalized platform identifier.

            Returns:
                str: Platform name such as `"windows"`, `"macos"`, or a
                    raw `sys.platform` value.
            """
            if cls.override:
                return cls.override
            if sys.platform == "win32":
                return "windows"
            if sys.platform == "darwin":
                return "macos"
            return sys.platform

    def parse() -> argparse.Namespace:
        """
        Define and parse command-line arguments.

        Returns:
            Namespace: Parsed arguments namespace produced by
                `argparse`.
        """
        parser = argparse.ArgumentParser(
            allow_abbrev=False,
            prog="build.py",
            description=(
                "A tiny utility for building Vertopal-CLI binaries "
                "on different platforms using PyInstaller."
            ),
        )
        parser.add_argument(
            "--version",
            metavar="<version>",
            help="Add version string to the archive file name and zip comment"
        )
        parser.add_argument(
            "--platform",
            metavar="<OS>",
            help="Override platform string in archive file name"
        )
        parser.add_argument(
            "--delete-bin",
            action="store_true",
            default=False,
            help="Delete binaries after archive"
        )

        return parser.parse_args()

    def build() -> bool:
        """
        Run PyInstaller to produce a single-file binary.

        Returns:
            bool: `True` when the PyInstaller process exits with code
                0, otherwise `False`.
        """
        cmd = (
            "pyinstaller",
            "--onefile",
            "-i",
            "NONE",
            "--name",
            "vertopal",
            str(repo_dir / "src" / "vertopal" / "vertopal.py"),
        )
        with Popen(cmd, cwd=repo_dir) as process:
            process.communicate()
        return not bool(process.returncode)

    def archive(delete: bool = False, version: Optional[str] = None) -> None:
        """
        Create a ZIP archive of files in the `dist/` directory.

        Args:
            delete (bool): If `True`, delete archived files after
                creating the ZIP. Defaults to `False`.
            version (Optional[str]): Optional version string to include
                in the archive name and ZIP comment.
        """
        if version:
            version_string = f" \u2014 version {version}"
            archive_name = f"vertopal-cli-{version}-{_Platform.get()}.zip"
        else:
            version_string = ""
            archive_name = f"vertopal-cli-{_Platform.get()}.zip"

        dist_path = Path(repo_dir / "dist")
        archive_path = str(dist_path / archive_name)
        delete_list = []

        with ZipFile(archive_path, "w", ZIP_DEFLATED) as zip_archive:
            for file in dist_path.iterdir():
                if file.is_file() and file.name != archive_name:
                    sys.stdout.write(f"Archiving {file.name}\n")
                    zip_archive.write(file.resolve(), file.name)
                    if delete:
                        delete_list.append(file)

            zip_archive.comment = (
                b"Vertopal-CLI %s binary"
                b"%s\n"
                b"https://www.vertopal.com\n\n"
                b"https://github.com/vertopal/vertopal-cli"
                % (_Platform.get().encode(), version_string.encode())
            )

        if delete and delete_list:
            for file in delete_list:
                file.unlink()

    # Parse command-line options and arguments
    args = parse()

    # Override current platform if it's passed as an argument
    if args.platform:
        _Platform.override = args.platform

    # Build and archive binaries using PyInstaller
    if build():
        archive(delete=args.delete_bin, version=args.version)


if __name__ == "__main__":
    main()
