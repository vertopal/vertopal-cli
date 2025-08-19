# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Internal HTTP response wrapper extending `requests.Response` with
#   convenience methods for JSON detection, nested property access,
#   and context management. Designed for safe and consistent API
#   response handling across Vertopal's internal services.

"""
Vertopal API response utilities.

This module provides `_CustomResponse`, a thin wrapper around
`requests.Response` that adds:

- JSON content detection via `is_json()`.
- Property-style access to JSON bodies through `nested`, backed by
  `_NestedPropertyWrapper`.
- Context manager passthrough for safe resource handling.
- Access to the original response via `original_response`.

Intended for internal use across Vertopal's API layer to standardize
and simplify HTTP response handling.
"""

from types import TracebackType
from typing import Optional, Type

from requests import Response

from vertopal.utils.data_wrappers import _NestedPropertyWrapper

# No public names in this file
__all__ = []


class _CustomResponse:
    """
    Internal wrapper around `requests.Response` with convenience
    features.

    This class enhances the standard response object with:
    - A quick JSON-content check (`is_json()`).
    - Dot-notation access to JSON payloads (`nested`).
    - Context-manager support that mirrors the underlying response while
      ensuring proper cleanup.
    - Opt-in access to the original response via `original_response`.

    The wrapper delegates unknown attributes and methods to the original
    `requests.Response`, keeping behavior consistent while adding
    utilities.
    """

    def __init__(self, response: Response):
        """
        Initialize the wrapper with a `requests.Response`.

        Args:
            response (Response): The HTTP response instance to wrap.
        """
        self._response = response

    def __getattr__(self, name: str):
        """
        Delegate attribute access to the underlying response.

        Args:
            name (str): Attribute or method name to retrieve.

        Returns:
            The attribute value resolved from the wrapped response.

        Raises:
            AttributeError: If the attribute does not exist on the
                underlying response.
        """
        return getattr(self._response, name)

    def serialize(self, serializer):
        """
        Serialize the JSON content to another format.

        Intended for future support of serializers (e.g., YAML, XML).
        Currently not implemented.

        Args:
            serializer: A serializer object or callable that defines
                a `dump`/`dumps`-like interface.

        Raises:
            NotImplementedError: Always raised until implementation is
                added.
        """
        raise NotImplementedError(
            "The `serialize` method is not implemented yet. "
            "This will be available in a future update."
        )

    def is_json(self) -> bool:
        """
        Return whether the response contains JSON content.

        This checks the `Content-Type` header for `application/json`.

        Returns:
            bool: `True` if the `Content-Type` indicates JSON;
            otherwise `False`.
        """
        content_type: str = self._response.headers.get("Content-Type", "")
        return "application/json" in content_type

    def __enter__(self) -> "_CustomResponse":
        """
        Enter the runtime context related to this object.

        Delegates to the underlying response's `__enter__` if available,
        then returns this wrapper instance.
        """
        enter = getattr(self._response, "__enter__", None)
        if callable(enter):
            enter()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> bool:
        """
        Exit the runtime context and release resources.

        Delegates to the underlying response's `__exit__` if available
        and returns True only if the underlying explicitly suppresses
        the exception. If no context manager is available, the response
        is closed and exceptions are not suppressed.

        Args:
            exc_type (Optional[Type[BaseException]]): Exception class,
                if any.
            exc (Optional[BaseException]): Exception instance, if any.
            tb (Optional[TracebackType]): Traceback, if any.

        Returns:
            bool: `True` to suppress an exception if the underlying
            response explicitly returns `True`; otherwise `False`.
        """
        exit_ = getattr(self._response, "__exit__", None)
        if callable(exit_):
            rv = exit_(exc_type, exc, tb)
            return bool(rv)
        self._response.close()
        return False

    def close(self) -> None:
        """
        Release the connection back to the pool.

        Once called, the underlying `raw` stream must not be accessed.
        Typically not needed when using context managers.
        """
        self._response.close()

    @property
    def nested(self):
        """
        Access JSON-like content using property-style (dot) access.

        Returns:
            _NestedPropertyWrapper: A wrapper enabling attribute-style
            access to JSON fields (e.g., `response.nested.user.name`).

        Raises:
            ValueError: If the response is not JSON (per `is_json()`).
        """
        if not self.is_json():
            raise ValueError(
                "Response content is not JSON and "
                "cannot be accessed as properties."
            )
        return _NestedPropertyWrapper(self.json())

    @property
    def original_response(self) -> Response:
        """
        Return the underlying `requests.Response` instance.

        Useful when direct interaction with the raw response object
        is required (e.g., access to `raw`, `iter_content`, or hooks).

        Returns:
            Response: The wrapped `requests.Response`.
        """
        return self._response
