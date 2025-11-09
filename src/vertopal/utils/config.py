# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Configuration management for the Vertopal client.
#   Implements a Singleton `Config` class to load, retrieve, update,
#   and persist global settings from an INI‑formatted file, with
#   programmatic defaults defined in `vertopal.settings`. User‑specific
#   values, if present, override these defaults. The configuration
#   file path defaults to the user's home directory, but can be
#   customized at instantiation.

"""
Configuration helper for reading and writing user settings.

This module implements the `Config` singleton which provides a
convenient API to access default and user-specific settings. It
wraps an INI-style configuration file and offers typed `get`, `set`,
and `save` methods as well as a read-only `config_dict` snapshot for
inspection.
"""

import configparser
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Optional, Union

from vertopal import settings
from vertopal.types import PathType

# Define public names for external usage
__all__ = [
    "Config",
]


class Config:
    """
    Public configuration manager for Vertopal

    The configuration file is INI-structured and located in the user's
    home directory by default. Default values for the configuration are
    stored programmatically within the Package (vertopal.settings),
    and are overridden by user-specific values
    if the configuration file exists.

    Resolution priority (highest to lowest):
        1. Explicit Credential passed to API/Converter (outside Config)
        2. In-memory overrides (Config._overrides)
        3. Persistent user config (Config._config, loaded from INI file)
        4. Package defaults (settings.DEFAULT_CONFIG)
        5. Fallback parameter provided to get()

    Public API:
      - `update()`: override values in memory
      - `clear_overrides()`: reset overrides
      - `get()`: read current values

    Internal-use methods (not exported in `__all__`):
      - `set()`, `save()`, `remove()`

    Attributes:
        SAVE_TO_OPENED_FILE (str): A flag to save to the file loaded
            during initialization.
        _SENSITIVE_KEYS: tuple[str, ...] = The keys to mask in string
            representations to avoid accidental disclosure in logs.
        _instance (Config): Holds the Singleton instance of
            the `Config` class.
        _initialized (bool): Tracks whether the Singleton
            has already been initialized.
        _default_config (dict[str, dict[str, Any]]): Stores default
            configuration values.
        _config (dict[str, dict[str, Any]]): Holds user-specific
            configuration values.

    Example:

        >>> from vertopal.utils.config import Config
        >>> config = Config()
        >>> config.get("api", "app")
        'free'
        >>> config.override({"api": {"app": "my-app-id"}})
        >>> config.get("api", "app")
        'my-app-id'
        >>> config.clear_overrides()
        >>> config.get("api", "app")
        'free'

    Notes:
        - The configuration file should follow the INI structure.
        More info: https://en.wikipedia.org/wiki/INI_file#Example
    """
    # Class-level flag(s)
    SAVE_TO_OPENED_FILE = 1

    _SENSITIVE_KEYS: tuple[str, ...] = (
        "token",
        "password",
        "secret",
    )

    _instance = None  # Class-level instance for Singleton
    _initialized = False  # Declare '_initialized' at the class level

    def __new__(
        cls,
        user_config_path: PathType = settings.USER_CONFIG_PATH,
    ):
        if cls._instance is None:
            # If no instance exists, create one
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        user_config_path: PathType = settings.USER_CONFIG_PATH,
    ):
        if Config._initialized:
            # Avoid reinitialization
            return

        self._user_config_path = user_config_path

        # Create a PurePath if user_config_path is string
        if isinstance(user_config_path, str):
            user_config_path = Path(user_config_path)

        # Initialize attributes
        self._default_config = settings.DEFAULT_CONFIG.copy()
        # Loaded from INI file
        self._config: dict[str, dict[str, Any]] = {}
        # Runtime-only overrides
        self._overrides: dict[str, dict[str, Any]] = {}
        self._current_config_path = user_config_path

        # Load user-specific configurations if file exists
        if Path(user_config_path).exists():
            parser = configparser.ConfigParser()
            parser.read(user_config_path, encoding="utf-8")
            for section in parser.sections():
                self._config[section] = dict(parser.items(section))

        # Mark as initialized
        Config._initialized = True

    def get(
        self,
        section: str,
        key: str,
        fallback: Any = None,
        *,
        cast: Optional[Callable[[Any], Any]] = None,
    ) -> Any:
        """
        Fetch a value from the configuration.

        Resolution priority (highest to lowest):
            1. Explicit Credential passed to API/Converter (outside Config)
            2. In-memory overrides (Config._overrides)
            3. Persistent user config (Config._config, loaded from INI file)
            4. Package defaults (settings.DEFAULT_CONFIG)
            5. Fallback parameter provided to get()

        Args:
            section (str): The section in the configuration file.
            key (str): The key within the section.
            fallback (Any, optional): A fallback value
                if the key does not exist.
            cast (Optional[Callable[[Any], Any]], optional): A callable
                to cast the fetched value to a specific type.
                Defaults to `None`.

        Raises:
            ValueError: If casting the value fails.

        Returns:
            Any: The value associated with the key, cast to the
                specified type if provided, or the fallback value
                if not found.
        """
        try:
            value = self._overrides[section][key]
        except KeyError:
            try:
                value = self._config[section][key]
            except KeyError:
                value = self._default_config.get(section, {}).get(key, fallback)

        if cast and value is not None:
            try:
                value = cast(value)
            except ValueError as exc:
                raise ValueError(f"Cannot cast '{value}' to {cast}") from exc

        return value

    def update(self, overrides: dict[str, dict[str, Any]], /) -> None:
        """
        Merge new override values into the in-memory overrides dict.

        Args:
            overrides (dict[str, dict[str, Any]]): Mapping of sections
            to key/value pairs. These values take precedence over both
            user config and defaults, but are not persisted to disk.
        """
        for section, values in overrides.items():
            if section not in self._overrides:
                self._overrides[section] = {}
            self._overrides[section].update(values)

    def clear_overrides(self) -> None:
        """
        Remove all in-memory overrides, restoring config resolution
        to user config and defaults only.
        """
        self._overrides.clear()

    def set(self, section: str, key: str, value: Any) -> None:
        """
        [INTERNAL USE ONLY]

        Update or add a value in the configuration.

        This method is intended for use by Vertopal's internal
        modules and is not part of the public developer API.

        Args:
            section (str): The section in the configuration file.
            key (str): The key within the section.
            value (Any): The value to be set.
        """
        try:
            self._config[section][key] = value
        except KeyError:
            self._config[section] = {}
            self._config[section][key] = value

    def remove(self, section: str, key: Optional[str] = None) -> None:
        """
        [INTERNAL USE ONLY]

        Remove a configuration key or an entire section
        from the configuration.

        If a key is provided, this method deletes the specific key from
        the given section. If the key is None, the entire section
        and all its keys are removed. This flexible approach allows you
        to either remove a single configuration item or clean out
        a section completely.

        This method is intended for use by Vertopal's internal
        modules and is not part of the public developer API.

        Args:
            section (str): The configuration section
                from which to remove data.
            key (Optional[str]): The specific key to remove
                from the section. If `None`,
                the entire section is removed. Defaults to `None`.
        
        Raises:
            KeyError: If the specified section or key does not exist.
        """
        if section not in self._config:
            raise KeyError(
                f"Section '{section}' does not exist in the configuration."
            )

        if key is None:
            # Remove the entire section
            del self._config[section]
        else:
            if key not in self._config[section]:
                raise KeyError(
                    f"Key '{key}' does not exist in section '{section}'."
                )
            del self._config[section][key]
            # Optionally remove the section
            # if it becomes empty after the deletion
            if not self._config[section]:
                del self._config[section]

    def save(
        self,
        path: Union[PathType, int] = SAVE_TO_OPENED_FILE,
    ) -> None:
        """
        [INTERNAL USE ONLY]

        Save the updated configuration to the user-defined file.

        If an integer flag is passed (e.g.,
        `Config.SAVE_TO_OPENED_FILE`), the method saves
        the configuration to the file loaded during initialization.
        If a `Path` or string object is passed, the configuration
        is saved to the specified file path.

        This method is intended for use by Vertopal's internal
        modules and is not part of the public developer API.

    Args:
        user_config_path (Union[PathType, int], optional): The path
            to save the configuration file. It can either be:
            - A `PathType` object representing the file path.
            - A string representing the file path.
            - An integer (e.g., `Config.SAVE_TO_OPENED_FILE`)
              to indicate saving to the file loaded
              during initialization.
            Defaults to `Config.SAVE_TO_OPENED_FILE`.

        Raises:
            PermissionError: If there is a permission error
                writing to the configuration file.

    Usage:

        >>> config = Config("/home/user/config.ini")
        >>> config.save(Config.SAVE_TO_OPENED_FILE)
        >>> # Saves to "/home/user/config.ini"
        >>> 
        >>> config = Config()
        >>> config.save("/home/user/new_config.ini")
        >>> # Saves to "/home/user/new_config.ini"
        """
        if path == Config.SAVE_TO_OPENED_FILE:
            path = self._current_config_path  # Use the opened file path

        parser = configparser.ConfigParser()
        parser.read_dict(self._config)
        with open(path, "w", encoding="utf-8") as configfile:
            parser.write(configfile)

    def __str__(self) -> str:
        """
        Return a human-readable string representation
        of the configuration, masking sensitive values.
        """
        def mask(key: str, value: Any) -> Any:
            if key.lower() in self._SENSITIVE_KEYS and isinstance(value, str):
                return f"{value[:3]}***"
            return value

        config_items = "\n".join(
            f"{section}: {{"
            + ", ".join(
                f"{k}={mask(k, v)}"
                for k, v in items.items()
            )
            + "}"
            for section, items in self._config.items()
        )
        return f"Current Configuration:\n{config_items}"

    def __repr__(self) -> str:
        """
        Return a developer-friendly string representation
        of the Config object, without exposing secrets.
        """
        return (
            f"{type(self).__name__}("
            f"user_config_path={repr(self._user_config_path)}, "
            f"_initialized={self._initialized}, "
            f"overrides={bool(self._overrides)})"
        )

    @property
    def config_dict(self) -> MappingProxyType[str, MappingProxyType[str, Any]]:
        """
        Read-only property to access the current configuration
        as a dictionary.

        This property provides a snapshot of the internal configuration
        settings, organized by sections. It is useful for inspection
        (for example, to check if the configuration file is empty)
        but does not allow external mutation.
        """
        # We use MappingProxyType to enforce read-only access.
        # Instead of wrapping 'self._config' directly,
        # we wrap each section separately.
        # This ensures both the top-level dictionary (sections)
        # and the inner dictionaries (keys within each section)
        # remain fully immutable.
        return MappingProxyType(
            {
                section: MappingProxyType(values)
                for section, values in self._config.items()
            }
        )
