#!/usr/bin/env python

"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
from subprocess import Popen
from zipfile import ZipFile, ZIP_DEFLATED


def main() -> None:
    """Main function for parsing, handling and running command-line arguments.
    
    Use PyInstaller to build single-file CLI executable binaries.

    Returns:
        None
    """

    current_dir = Path(__file__).parent.resolve()

    class Platform:
        """A simple class for getting current system platform name.

        Attributes:
            override (str, optional): Override the return value of
                `Platform.get()` method.
        """

        override: Optional[str] = None

        @classmethod
        def get(cls) -> str:
            """Get the current system platform identifier.

            Returns:
                str: Platform name. E.g. `windows`, `linux`, or `macos`.
            """

            if cls.override:
                return cls.override
            if sys.platform == "win32":
                return "windows"
            elif sys.platform == "darwin":
                return "macos"
            return sys.platform

    def parse() -> object:
        """Use `argparse` to define & parse command-line options and arguments.

        Returns:
            Namespace: A simple `object` containing attributes.
        """

        parser = argparse.ArgumentParser(
            allow_abbrev=False,
            prog="build.py",
            description=("A tiny utility for building Vertopal-CLI binaries "
                         "on different platforms using PyInstaller. "),
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
        """Build Vertopal-CLI binary using PyInstaller command.

        Returns:
            bool: `True` if PyInstaller process exits successfully, 
            otherwise `False`.
        """

        cmd = (
            "pyinstaller",
            "--onefile",
            "-i",
            "NONE",
            "--name",
            "vertopal",
            "vertopal.py",
        )
        with Popen(cmd, cwd=current_dir) as process:
            process.communicate()
        return True if process.returncode == 0 else False

    def archive(delete: bool = False, version: Optional[str] = None) -> None:
        """Archive generated binary (and other files) in `dist/` directory.

        The archive format is ZIP.

        Args:
            delete (bool, optional): Delete files after archiving them. 
                Defaults to `False`.
            version (str, optional): Add version string in archive file name 
                and archive comment meta-data. Defaults to `None`.

        Returns:
            None
        """

        if version:
            version_string = f" \u2014 version {version}"
            archive_name = f"vertopal-cli-{version}-{Platform.get()}.zip"
        else:
            version_string = ""
            archive_name = f"vertopal-cli-{Platform.get()}.zip"

        dist_path = Path(current_dir / "dist")
        archive_path = str(dist_path / archive_name)
        delete_list = []

        with ZipFile(archive_path, "w", ZIP_DEFLATED) as zip_archive:
            for file in dist_path.iterdir():
                if file.is_file() and file.name != archive_name:
                    sys.stdout.write("Archiving {file.name}\n")
                    zip_archive.write(file.resolve(), file.name)
                    if delete:
                        delete_list.append(file)

            zip_archive.comment = (
                b"Vertopal-CLI %s binary"
                b"%s\n"
                b"https://www.vertopal.com\n\n"
                b"https://github.com/vertopal/vertopal-cli"
                % (Platform.get().encode(), version_string.encode())
            )

        if delete and delete_list:
            for file in delete_list:
                file.unlink()

    # Parse command-line options and arguments
    args = parse()

    # Override current platform if it's passed as an argument
    if args.platform:
        Platform.override = args.platform

    # Build and archive binaries using PyInstaller
    if build():
        archive(delete=args.delete_bin, version=args.version)


if __name__ == "__main__":
    main()
