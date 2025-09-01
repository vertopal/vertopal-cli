# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Manage application credentials (App ID and security token)
#   for authenticating with the Vertopal API.

"""
Vertopal API credential management.

This module defines the `Credential` class, which encapsulates
the Application ID and Security Token required for authenticating
requests to the Vertopal API. It enforces immutability, provides
read-only accessors, equality and hashing for comparisons, and safe
string representations that avoid exposing sensitive information.
"""

from dataclasses import dataclass

# Define public names for external usage
__all__ = [
    "Credential",
]


@dataclass(frozen=True)
class Credential:
    """
    Immutable container for Vertopal API credentials.

    Stores the **Application ID** and **Security Token** needed to
    authenticate API requests.

    Tokens are masked in all human-readable outputs to reduce the risk
    of accidental disclosure in logs or console output.

    Args:
        app (str): Application ID string used for API authentication.
        token (str): Security token string used for API authentication.

    Raises:
        ValueError: If `app` or `token` is empty or not a string.

    Example:

        >>> from vertopal.api.credential import Credential
        >>> cred = Credential("app-id", "token")
        >>> cred.app
        'app-id'
        >>> bool(cred)
        True
        >>> str(cred)        # Masked token
        'app-id:tok***'
        >>> repr(cred)
        'Credential(app-id, ***masked***)'
    """

    app: str
    token: str

    def __post_init__(self) -> None:
        """Validate values after initialization."""
        if not isinstance(self.app, str) or not self.app.strip():
            raise ValueError("Application ID must be a non-empty string")
        if not isinstance(self.token, str) or not self.token.strip():
            raise ValueError("Security token must be a non-empty string")

    def __str__(self) -> str:
        """
        Return a user-friendly masked string representation.

        Format is `<app>:<token_prefix>***`.

        The mask prevents full token exposure in logs.
        """
        masked_token = f"{self.token[:3]}***"
        return f"{self.app}:{masked_token}"

    def __repr__(self) -> str:
        """Return a debug-friendly masked string representation."""
        return f"{type(self).__name__}({self.app}, ***masked***)"

    def __bool__(self) -> bool:
        """Return True if both app and token are set."""
        return bool(self.app and self.token)

    def as_dict(self) -> dict[str, str]:
        """
        Return the credentials as a dictionary.

        Warning:
            The returned dictionary contains the **full** token.
            Handle it with care to avoid leaking sensitive data.
        """
        return {"app": self.app, "token": self.token}
