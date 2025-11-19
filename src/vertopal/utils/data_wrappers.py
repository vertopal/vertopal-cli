# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Internal utility wrappers for handling nested dictionary access,
#   UTC datetime operations, and structured API error/warning parsing.
#   These classes are not part of the public API and are intended for
#   internal use by other Vertopal modules.

"""
Wrappers for API response data and lightweight datetime helpers.

This module contains small, focused wrapper classes used across the
package to provide convenient attribute-style access to nested JSON
responses, to parse and manipulate server-provided UTC timestamps,
and to consistently extract error and warning information from API
responses.
"""

from datetime import datetime, timedelta
from io import UnsupportedOperation
import json
import os
from typing import Any, BinaryIO, Iterator, Optional

# No public names in this file
__all__ = []


class _NestedPropertyWrapper:
    """
    A wrapper for handling nested dictionaries
    with property-style access.

    This class allows intuitive attribute-style access for nested
    dictionary keys, while still preserving the ability to convert back
    to the original dictionary and iterate through keys.

    Attributes:
        _data (dict): The original dictionary being wrapped.

    Example:

        >>> json_data = {"result": {"output": {"status": "success"}}}
        >>> wrapper = NestedPropertyWrapper(json_data)
        >>> print(wrapper.result.output.status)
        'success'

        >>> print("status" in wrapper.result.output)
        True

        >>> print(wrapper.to_dict())
        {'result': {'output': {'status': 'success'}}}
    """

    def __init__(self, data: dict[Any, str]) -> None:
        """
        Initializes the NestedPropertyWrapper instance.

        Args:
            data (dict[Any, str]): The dictionary data to wrap.
        """
        self._data: dict[Any, str] = data

    def to_dict(self) -> dict[Any, str]:
        """
        Converts the wrapper back to the original dictionary.

        Returns:
            dict[Any, str]: The original dictionary data.
        """
        return self._data

    def __getattr__(self, name: str) -> Any:
        """
        Access nested dictionary keys as attributes.

        Args:
            name (str): The key to access.

        Returns:
            Any: The value corresponding to the key, wrapped in
            `NestedPropertyWrapper` if it is another dictionary.

        Raises:
            AttributeError: If the key is not found in the dictionary.
        """
        if name in self._data:
            value = self._data[name]
            if isinstance(value, dict):
                return _NestedPropertyWrapper(value)
            return value
        raise AttributeError(f"'{name}' not found in response")

    def __contains__(self, key: str) -> bool:
        """
        Checks if a specific key exists in the current dictionary.

        Args:
            key (str): The key to check.

        Returns:
            bool: `True` if the key exists, `False` otherwise.
        """
        return key in self._data

    def __iter__(self) -> Iterator[str]:
        """
        Iterates over keys in the current dictionary.

        Returns:
            Iterator[str]: An iterator over the keys in the dictionary.
        """
        return iter(self._data)

    def __bool__(self) -> bool:
        """
        Checks if the wrapped dictionary is empty.
        
        Returns:
            bool: `False` if the dictionary is empty, `True` otherwise.
        """
        return bool(self._data)

    def __str__(self) -> str:
        """
        Returns a user-friendly string representation of the dictionary.

        Returns:
            str: The formatted dictionary as a string.
        """
        return f"{json.dumps(self._data, indent=2)}"

    def __repr__(self) -> str:
        """
        Returns a debug-friendly representation of the class.

        Returns:
            str: A string representation of the `NestedPropertyWrapper`
            instance.
        """
        return f"{type(self).__name__}({repr(self._data)})"


class _DateTimeWrapper:
    """
    A wrapper for handling and manipulating datetime objects,
    specifically server-provided UTC timestamps.

    The class provides functionality for converting UTC timestamps
    to local time zones and calculating durations between two datetime
    instances. It uses only Python's built-in libraries to avoid
    third-party dependencies.

    Attributes:
        _utc_date (datetime): The parsed UTC datetime.

    Example:

        >>> wrapper = DateTimeWrapper("2025-04-03 04:52:47")
        >>> local_time = wrapper.to_local_time(utc_offset_hours=2)
        >>> print(local_time)
        2025-04-03 06:52:47

        >>> other_date = datetime(2025, 4, 2, 18, 30, 0)
        >>> duration = wrapper.get_duration(other_date)
        >>> print(duration)
        10:22:47
    """

    def __init__(self, date_string: str) -> None:
        """
        Initializes the DateTimeWrapper instance by parsing
        a UTC datetime string.

        Args:
            date_string (str): The server-provided UTC datetime string
                in the format "%Y-%m-%d %H:%M:%S".

        Raises:
            ValueError: If the date_string does not match
                the expected format.
        """
        self._utc_date: datetime = datetime.strptime(
            date_string,
            "%Y-%m-%d %H:%M:%S",
        )

    def to_local_time(self, utc_offset_hours: float) -> datetime:
        """
        Converts the UTC datetime to a local time zone
        using a fixed offset.

        Args:
            utc_offset_hours (float): The number of hours
                to offset from UTC.

        Returns:
            datetime: The converted local datetime.
        """
        return self._utc_date + timedelta(hours=utc_offset_hours)

    def get_duration(self, other_date: datetime) -> timedelta:
        """
        Calculates the duration (time difference) between
        the current datetime and another datetime.

        Args:
            other_date (datetime): The other datetime instance
                (should not include time zone information).

        Returns:
            timedelta: The duration between the two datetime instances.

        Raises:
            ValueError: If the other_date includes timezone information.
        """
        if other_date.tzinfo is not None:
            raise ValueError(
                (
                    "The other_date should not include"
                    "timezone information."
                )
            )
        return self._utc_date - other_date


class _ErrorWrapper:
    """
    A wrapper for handling errors in API responses.

    The error and warning information are expected to be structured
    as dictionaries with "code" and "message" keys.

    Supported structures:

      ```
      1. Top-level error:
        {
          "error": {
            "code": "FREE_PLAN_DISALLOWED",
            "message": "Activating a premium plan to use API."
          }
        }
    
      2. Under `result.error`:
        {
          "result": {
              "error": {
                "code": "SOME_CODE",
                "message": "Some error message."
              },
              "warning": {
                "code": "WARNING_CODE",
                "message": "Some warning message."
              },
              "output": {
                "status": "successful"
              }
          }
        }
    
      3. Deeply nested error under `result.output.result.error`:
        {
          "result": {
              "output": {
                  "result": {
                      "error": {
                        "code": "NESTED_ERROR",
                        "message": "Nested error occurred."
                      },
                      "warning": {
                        "code": "NESTED_WARN",
                        "message": "Nested warning message."
                      },
                      "output": { ... }
                  }
              },
              "error": {},
              "warning": {}
          }
        }
      ```
    """
    # Candidate paths for errors
    # (each path should yield a dict with keys `code` and `message`)
    _error_paths = [
        [],
        ["error"],
        ["result", "error"],
        ["result", "output", "result", "error"],
    ]

    # Candidate paths for warnings
    # (each path should yield a dict with keys `code` and `message`)
    _warning_paths = [
        ["warning"],
        ["result", "warning"],
        ["result", "output", "warning"],
        ["result", "output", "result", "warning"],
    ]

    def __init__(self, response: dict) -> None:
        """
        Initializes the _ErrorWrapper instance.

        Args:
            response (dict): The API response data.
        """
        self._response = response

    def _get_by_path(
        self,
        data: dict[str, Any],
        path: list[str],
    ) -> Optional[Any]:
        """
        Traverses the dictionary following the list of keys.
        
        Args:
            data (dict[str, Any]): The dictionary to traverse.
            path (list[str]): A sequence of keys indicating
                the nested structure.
            
        Returns:
            Optional[Any]: The value at the end of the path
            if it exists, otherwise `None`.
        """
        for key in path:
            if isinstance(data, dict):
                value = data.get(key)
                if value is None:
                    return None
                data = value
            else:
                return None
        return data

    def has_error(self) -> bool:
        """
        Checks if any of the candidate error locations contain
        error details.
        
        Returns:
            bool: `True` if an error (with either code or message)
            is found; else `False`.
        """
        for path in self._error_paths:
            error = self._get_by_path(self._response, path)
            if (
                isinstance(error, dict)
                and (error.get("message")
                or error.get("code"))
            ):
                return True
        return False

    def get_error(self) -> dict:
        """
        Retrieves the first error details found from the candidate
        error locations.
        
        Returns:
            dict: An error dictionary with `code` and `message` keys
            if found; else an empty dictionary.
        """
        for path in self._error_paths:
            error = self._get_by_path(self._response, path)
            if (
                isinstance(error, dict)
                and (error.get("message")
                or error.get("code"))
            ):
                return error
        return {}

    def get_error_message(self) -> str:
        """
        Extracts the error message from the error details.

        Returns:
            str: The error message if found,
            otherwise a default message.
        """
        error = self.get_error()
        return error.get("message", "No error message available.")

    def get_error_code(self) -> str:
        """
        Extracts the error code from the error details.

        Returns:
            str: The error code if found, otherwise a default value.
        """
        error = self.get_error()
        return error.get("code", "UNKNOWN_ERROR")

    def has_warning(self) -> bool:
        """
        Checks if any of the candidate warning locations contain
        warning details.
        
        Returns:
            bool: `True` if a warning (with either code or message)
            is found; else `False`.
        """
        for path in self._warning_paths:
            warning = self._get_by_path(self._response, path)
            if (
                isinstance(warning, dict)
                and (warning.get("message")
                or warning.get("code"))
            ):
                return True
        return False

    def get_warnings(self) -> list:
        """
        Retrieves warning details from the candidate locations.
        
        Returns:
            list: A list of warning dictionaries (each containing
            at least `code` and `message`).
        """
        warnings = []
        for path in self._warning_paths:
            warning = self._get_by_path(self._response, path)
            if (
                isinstance(warning, dict)
                and (warning.get("message")
                or warning.get("code"))
            ):
                warnings.append(warning)
        return warnings


class _ChunkedFileWrapper:
    """
    Internal file-like wrapper that enforces a fixed chunk size
    when reading from an underlying binary stream.

    This wrapper is primarily used during streaming uploads to
    control the maximum number of bytes read per call to `.read()`.
    It ensures predictable chunk sizes regardless of the size hint
    provided by the caller.

    Attributes:
        _file (BinaryIO): The underlying binary file-like object.
        _chunk_size (int): The maximum number of bytes to read per call.

    Example:

        >>> import io
        >>> buf = io.BytesIO(b"abcdefghij")
        >>> wrapper = _ChunkedFileWrapper(buf, chunk_size=4)
        >>> wrapper.read()
        b'abcd'
        >>> wrapper.read()
        b'efgh'
        >>> wrapper.read()
        b'ij'
    """

    def __init__(self, file: BinaryIO, chunk_size: int):
        """
        Initialize the wrapper around a binary file-like object.

        Args:
            file (BinaryIO): The underlying file-like object opened in
                binary mode.
            chunk_size (int): The maximum number of bytes to read
                per call.
        """
        self._file = file
        self._chunk_size = chunk_size
        # Always rewind to the start of the file
        try:
            self._file.seek(0)
        except (AttributeError, OSError, UnsupportedOperation):
            # If the underlying object doesn't support seek, ignore
            pass

    def read(self, size: int = -1) -> bytes:
        """
        Read up to `chunk_size` bytes from the underlying file.

        Args:
            size (int, optional): The number of bytes requested by the
                caller.
                - If negative (default), all remaining data is read.
                - If positive and larger than `chunk_size`, the read
                  size is capped at `chunk_size`.
                - Otherwise, reads exactly `size` bytes.

        Returns:
            bytes: The next chunk of data from the file. Returns an
            empty bytes object when the end of file is reached.
        """
        if size < 0:
            # Caller explicitly asked for "all remaining data"
            return self._file.read()
        size = min(size, self._chunk_size)
        return self._file.read(size)

    def __iter__(self):
        """
        Return an iterator over the file stream.

        This enables the wrapper to be used in iteration contexts
        (e.g., `for chunk in wrapper:`), yielding successive chunks
        of data until the end of the file is reached.

        Returns:
            _ChunkedFileWrapper: The wrapper itself, which acts as
                its own iterator.
        """
        return self

    def __next__(self):
        """
        Read and return the next chunk of data from the file.

        Each call retrieves up to `chunk_size` bytes. When the end of
        the file is reached, a `StopIteration` exception is raised to
        signal that iteration is complete.

        Returns:
            bytes: The next chunk of file data.

        Raises:
            StopIteration: If no more data is available in the file.
        """
        chunk = self.read(self._chunk_size)
        if not chunk:
            raise StopIteration
        return chunk

    def __len__(self):
        """
        Return the total size of the underlying file in bytes.

        This method seeks to the end of the file to determine its
        length, then restores the original file pointer position.
        It allows upload clients (such as `requests`) to know the full
        size of the stream before starting the upload.

        Returns:
            int: The total number of bytes in the file.
        """
        current = self._file.tell()
        self._file.seek(0, os.SEEK_END)
        size = self._file.tell()
        self._file.seek(current)
        return size

    def __getattr__(self, name: str):
        """
        Delegate attribute access to the underlying file object.

        This allows the wrapper to behave like the wrapped file,
        exposing methods such as `.close()`, `.seek()`, `.tell()`, etc.

        Args:
            name (str): The attribute name being accessed.

        Returns:
            Any: The attribute from the underlying file object.

        Raises:
            AttributeError: If the attribute does not exist on the file.
        """
        return getattr(self._file, name)
