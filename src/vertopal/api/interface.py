# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Internal API interface for managing Vertopal service requests,
#   including request construction, authentication, retries,
#   file uploads, and consistent HTTP session handling. Provides a base
#   wrapper around `requests` with configuration-driven settings and
#   convenience utilities.

"""
Internal API interface for managing Vertopal service requests.

This module defines the internal `_Interface` class which encapsulates
HTTP communication with Vertopal's REST API. Responsibilities include
request construction, authentication, retry/backoff semantics, file
uploads, and consistent HTTP session handling. The implementation
produces `_CustomResponse` wrappers for higher-level clients to use.
"""

from contextlib import ExitStack
from pathlib import Path
import platform
from time import sleep
from types import SimpleNamespace
from typing import Dict, List, Optional

import requests

from vertopal import settings, __version__
from vertopal.api.credential import Credential
from vertopal.api.response import _CustomResponse
import vertopal.exceptions as vex
from vertopal.utils.config import _Config
from vertopal.utils.exception_handler import ExceptionHandler

# No public names in this file
__all__ = []


class _Interface:
    """
    Internal HTTP transport layer for the Vertopal API.

    The `_Interface` class encapsulates low-level HTTP concerns such as
    header construction, retries, JSON validation, file uploads, and
    session lifecycle management. Higher-level API helpers compose
    payloads and call into this class for transport and response
    normalization.
    """

    def __init__(
        self,
        credential: Optional[Credential] = None,
    ):
        """
        Initialize the API interface.

        Args:
            credential (Optional[Credential]): Optional credential
                instance. If not provided, credentials are loaded from
                configuration.
        """
        self._config: _Config = _Config()
        self._user_agent_product = settings.USER_AGENT_PRODUCT_LIB

        if not credential:
            self._credential = Credential(
                app=self._config.get("api", "app"),
                token=self._config.get("api", "token"),
            )
        else:
            self._credential = credential

        self._session = requests.Session()
        self._session.headers.update(self._get_headers())

        self._version: Optional[float] = None

    def send_request(
        self,
        path: str,
        method: str = "POST",
        **kwargs,
    ) -> _CustomResponse:
        """
        Send an HTTP request with retry and JSON validation.

        Args:
            path (str): API endpoint path relative to the base endpoint.
            method (str): HTTP method to use. Defaults to `"POST"`.
            **kwargs: Forwarded to `requests` (for example, `data`,
                `files`, or `timeout`).

        Returns:
            _CustomResponse: Wrapped HTTP response with convenience
            accessors.

        Raises:
            vex.InvalidJSONResponseError: When the response body is
                not valid JSON for endpoints that expect JSON.
            vex.NetworkConnectionError: When all retry attempts fail.
        """
        retries = self._config.get("connection_settings", "retries", cast=int)
        url = f"{self.endpoint}{path}"

        for attempt in range(1, retries + 1):
            try:
                response = self._session.request(method, url, **kwargs)

                # Only validate JSON if not downloading binary content
                if path not in ("/download/url/get", ):
                    ExceptionHandler.raise_for_response(response.json())

                return _CustomResponse(response)

            except requests.exceptions.JSONDecodeError as e:
                raise vex.InvalidJSONResponseError(e)

            except requests.RequestException as e:
                if attempt < retries:
                    # Exponential backoff between retries
                    sleep(2 ** attempt)
                else:
                    raise vex.NetworkConnectionError(
                        f"All {retries} retries failed! Error: {e}"
                    ) from e

        # If somehow the loop completes without returning or raising
        raise vex.NetworkConnectionError("Request failed without exception.")

    def request(
        self,
        endpoint: str,
        method: str,
        field_params: Optional[List[str]] = None,
        version: Optional[str] = None,
    ) -> requests.Response:
        """
        Build and send a single HTTP request using the low-level
        requests API.

        Args:
            endpoint (str): API endpoint path, with or without a
                leading slash.
            method (str): HTTP method to use, for example `"GET"` or
                `"POST"`.
            field_params (Optional[List[str]]): Optional list of
                field assignments in the form `key=value` or
                `key=@/path/to/file` for file uploads.
            version (Optional[str]): Optional API version string to
                include in the constructed path.

        Returns:
            requests.Response: Raw `requests` response object.
        """
        if endpoint[0] != "/":
            endpoint = f"/{endpoint}"
        if version:
            url = f"{self.endpoint}/v{version}{endpoint}"
        else:
            url = f"{self.endpoint}{endpoint}"

        if endpoint in ("/upload/file", "/download/url/get"):
            timeout = self.long_timeout
        else:
            timeout = self.default_timeout

        field = self.__parse_field_parameters(
            field_params,
            {"%app-id%": self._credential.app},
        )

        if field.file:
            with ExitStack() as stack:
                files: List = []
                for key, path in field.file.items():
                    file = Path(path)
                    files.append((
                        key,
                        (
                            file.name,
                            stack.enter_context(open(file.resolve(), "rb")),
                        )
                    ))
                return requests.request(
                    method,
                    url,
                    headers=self._get_headers(),
                    data=field.data,
                    files=files,
                    timeout=timeout,
                )

        return requests.request(
            method,
            url,
            headers=self._get_headers(),
            data=field.data,
            timeout=timeout,
        )

    def _get_user_agent(self) -> str:
        """
        Return a formatted User-Agent string including platform
        details.

        Returns:
            str: Fully formatted User-Agent string.
        """
        product: str = self.user_agent_product
        product_version: str = __version__
        platform_release: str = platform.release()
        platform_machine: str = platform.machine()
        platform_system: str = platform.system()
        # Rename macOS platform
        if platform_system == "Darwin":
            platform_system = "macOs"

        platform_full: str = platform_system

        if platform_release:
            # Shorten release info if contains hyphen
            if "-" in platform_release:
                hyphen_position: int = platform_release.find("-")
                platform_full += " " + platform_release[:hyphen_position]
            else:
                platform_full += " " + platform_release
        if platform_machine:
            if platform_machine == "AMD64":
                if platform_system == "Windows":
                    platform_full += "; Win64"
                platform_full += "; x64"
            else:
                platform_full += "; " + platform_machine

        user_agent: str = f"{product}/{product_version} ({platform_full})"
        return user_agent

    def _get_headers(self) -> Dict[str, str]:
        """
        Build standard headers for API requests.

        Returns:
            Dict[str, str]: Headers containing `Authorization` and
                `User-Agent`.
        """
        return {
            "Authorization": f"Bearer {self._credential.token}",
            "User-Agent": self._get_user_agent(),
        }

    @staticmethod
    def __parse_field_parameters(
        params: Optional[List[str]],
        replace: Optional[Dict[str, str]] = None
    ) -> SimpleNamespace:
        """
        Parse a list of field parameter strings into structured `data`
        and `file` mappings.

        Args:
            params (Optional[List[str]]): List of strings in the form
                `key=value` or `key=@/path/to/file`.
            replace (Optional[Dict[str, str]]): Optional mapping of
                substrings to replace inside values.

        Returns:
            SimpleNamespace: Object with `data` and `file` attributes
                mapping to dictionaries when present.

        Example:

            >>> params = ["key1=value1", "file1=@/path/to/file"]
            >>> replace = {"value1": "new_value1"}
            >>> result = _Interface.__parse_field_parameters(
            ...     params,
            ...     replace,
            ... )
            >>> print(result.data)
            {'key1': 'new_value1'}
            >>> print(result.file)
            {'file1': '/path/to/file'}
        """
        def _replace(text: str, replace_pair: Dict[str, str]) -> str:
            for replace_from, replace_to in replace_pair.items():
                if replace_from and replace_to:
                    return text.replace(replace_from, replace_to)
            return text

        data: Optional[Dict[str, str]] = None
        file: Optional[Dict[str, str]] = None

        if not params:
            return SimpleNamespace(
                data=data,
                file=file,
            )

        for p in params:
            if "=" in p:
                # equal sign position
                eqpos: int = p.index("=")
                # check if the parameter is `file`
                if len(p) > eqpos + 1 and p[eqpos + 1] == "@":
                    pkey, pval = p.split("=@", 1)
                    if pkey and pval:
                        if not file:
                            file = {}
                        file[pkey] = pval
                else:
                    pkey, pval = p.split("=", 1)
                    if pkey and pval:
                        if replace:
                            pval = _replace(pval, replace)
                        if not data:
                            data = {}
                        data[pkey] = pval

        return SimpleNamespace(
            data=data,
            file=file,
        )

    def close(self) -> None:
        """
        Close the underlying HTTP session.

        Note:
            This method is primarily intended for use when the
            instance is not managed with a `with` context manager.
            If using `with`, the session will be closed automatically
            on context exit.
        """
        self._session.close()

    def __enter__(self):
        """
        Enter a runtime context and return this instance.

        Returns:
            _Interface: The current instance for use in a `with` block.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Exit the runtime context and close the session.

        Closes the session regardless of whether an exception occurred.
        """
        self.close()

    @property
    def endpoint(self) -> str:
        """
        Return the full API endpoint URL, including optional versioning.
        """
        endpoint = self._config.get("api", "endpoint")
        if self.version:
            version = f"v{self.version}"
        else:
            version = ""
        return f"{endpoint}/{version}"

    @property
    def default_timeout(self) -> int:
        """Default HTTP timeout in seconds from configuration."""
        return self._config.get("connection_settings", "default_timeout")

    @property
    def long_timeout(self) -> int:
        """
        Extended HTTP timeout in seconds from configuration.

        Used for endpoints where processing or file transfer may take
        longer than the default.
        """
        return self._config.get("connection_settings", "long_timeout")

    @property
    def version(self) -> Optional[float]:
        """Optional API version number."""
        return self._version

    @version.setter
    def version(self, value: Optional[float]) -> None:
        """
        Set the API version number used in the endpoint URL.

        Args:
            value (Optional[float]): Version number as a float, or
                `None` to disable versioning.
        """
        self._version = value

    @property
    def user_agent_product(self) -> str:
        """Product identifier used in the User-Agent string."""
        return self._user_agent_product

    @user_agent_product.setter
    def user_agent_product(self, value: str) -> None:
        """Set the User-Agent product identifier.

        Args:
            value (str): One of the allowed user agent product
                identifiers including
                `vertopal.settings.USER_AGENT_PRODUCT_LIB` or
                `vertopal.settings.USER_AGENT_PRODUCT_CLI`.

        Raises:
            ValueError: If an invalid value is provided.
        """
        valid_user_agents = (
            settings.USER_AGENT_PRODUCT_LIB,
            settings.USER_AGENT_PRODUCT_CLI,
        )
        if value not in valid_user_agents:
            raise ValueError(
                (
                    "Invalid User-Agent value. Possible values are: "
                    f"{', '.join(valid_user_agents)}."
                )
            )
        self._user_agent_product = value
