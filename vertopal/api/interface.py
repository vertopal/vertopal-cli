"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

import platform
from typing import Dict

from vertopal import __version__


class Interface:
    """The parent :class:`Interface` class for the API.

    Attributes:
        ASYNC (str): ASYNC mode strategy constant.
        SYNC (str): SYNC mode strategy constant.
    """

    ASYNC: str = "async"
    SYNC: str = "sync"
    UA_CLI: str = "VertopalCLI"
    UA_LIB: str = "VertopalPythonLib"
    UA_PRODUCT: str = UA_LIB

    @classmethod
    def set_ua_product_name(cls, product: str) -> None:
        """Set User-Agent product name.

        Args:
            product (str): User-Agent product name.

        Raises:
            ValueError: If the invalid product name is passed.
        """

        if product not in (cls.UA_CLI, cls.UA_LIB):
            raise ValueError("product is not a valid name.")
        cls.UA_PRODUCT = product

    @classmethod
    def _get_user_agent(cls) -> str:
        """Generate User-Agent string for HTTP request header.

        Returns:
            str: User-Agent string.
        """

        product: str = cls.UA_PRODUCT
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

    @classmethod
    def _get_headers(cls, token: str) -> Dict[str, str]:
        """Concatenate the token provided to build and return an HTTP header.

        Args:
            token (str): Your Security-Token

        Returns:
            Dict[str, str]: The HTTP header needed for API requests.
        """

        return {
            "Authorization": f"Bearer {token}",
            "User-Agent": cls._get_user_agent(),
        }
