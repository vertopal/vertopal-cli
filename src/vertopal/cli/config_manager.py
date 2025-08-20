# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Command-line wrapper for the _Config singleton, managing user-specific
#   INI-style configuration for Vertopal CLI. Translates argparse Namespace
#   flags into configuration operations and persists changes as needed.

"""
Command-line wrapper around the `_Config` singleton used to manage
user-specific INI-style configuration for the Vertopal CLI.

This module translates argparse `Namespace` flags into calls to
`_Config.get`, `_Config.set`, `_Config.remove` and saves changes when
necessary.
"""

from argparse import Namespace

from vertopal.utils.config import _Config

# No public names in this file
__all__ = []


class _ConfigManager:
    """
    Manager for configuration operations using the `_Config` class.

    This adapter processes command-line arguments from an argparse
    `Namespace` and performs configuration operations such as listing,
    getting, setting, and unsetting configurations. Configuration keys
    must be in the `section.key` format.
    """

    def __init__(self, args: Namespace):
        """
        Initialize the Config Manager with parsed command-line arguments.

        Args:
            args (Namespace): Parsed command-line arguments
                from argparse.
        """
        self._args = args
        self._config = _Config()

    def run(self) -> None:
        """
        Run the configuration manager according to the parsed arguments.

        This will dispatch to listing, getting, setting or unsetting
        operations depending on flags passed by the user.
        """
        # List all configurations
        if self._args.list:
            self._list_configs()
        # Unset (remove) a configuration property
        elif self._args.unset:
            self._unset_config()
        # Either get a configuration or set one or more configurations
        elif self._args.pairs:
            if len(self._args.pairs) == 1:
                self._get_config()
            elif len(self._args.pairs) % 2 == 0:
                self._set_configs()
            else:
                print(
                    "Error: Invalid number of arguments. "
                    "Provide key-value pairs."
                )
        else:
            print(
                "Error: Invalid usage. Use --list, --unset key, or key-value "
                "pairs for setting/getting configurations."
            )

    def _list_configs(self) -> None:
        """Print all stored configuration key/value pairs."""
        if not self._config.config_dict:
            print("No configuration settings found.")
        else:
            for section, item in self._config.config_dict.items():
                for key, value in item.items():
                    print(f"{section}.{key}={value}")

    def _get_config(self) -> None:
        """
        Print the value for a single configuration key specified as
        `section.key`.
        """
        full_key = self._args.pairs[0]
        try:
            section, key = full_key.split(".", 1)
        except ValueError:
            print("Error: Key should be in the format `section.key`")
            return
        value = self._config.get(section, key)
        if value is not None:
            print(value)
        else:
            print(f"No configuration found for key '{full_key}'.")

    def _set_configs(self) -> None:
        """
        Set one or more configuration key-value pairs. Expects an even
        number of arguments where each key is in the `section.key`
        format. Each set operation is persisted immediately.
        """
        for i in range(0, len(self._args.pairs), 2):
            full_key = self._args.pairs[i]
            value = self._args.pairs[i + 1]
            try:
                section, key = full_key.split(".", 1)
            except ValueError:
                print(
                    f"Error: Unable to process key '{full_key}'. "
                    "Must be in format `section.key`."
                )
                continue
            self._config.set(section, key, value)
            self._config.save()
            print(f"Set {full_key} to {value}.")

    def _unset_config(self) -> None:
        """Remove a configuration key provided as `section.key`."""
        if len(self._args.pairs) != 1:
            print(
                "Error: The --unset option requires "
                "exactly one configuration key."
            )
            return
        full_key = self._args.pairs[0]
        try:
            section, key = full_key.split(".", 1)
        except ValueError:
            print("Error: Key should be in the `section.key` format.")
            return
        try:
            self._config.remove(section, key)
            self._config.save()
        except KeyError:
            print(f"No configuration found for key '{full_key}'.")
        except PermissionError:
            print("Permission error writing to configuration file.")
        else:
            print(f"Removed configuration '{full_key}'.")
