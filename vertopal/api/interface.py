"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

import platform
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Optional

import requests

from vertopal import __version__


class Interface:
    """The parent :class:`Interface` class for the API.

    Attributes:
        ENDPOINT (str): The endpoint URL of the Vertopal API.
        ASYNC (str): ASYNC mode strategy constant.
        SYNC (str): SYNC mode strategy constant.
    """

    ENDPOINT: str = "https://api.vertopal.com"
    ASYNC: str = "async"
    SYNC: str = "sync"
    UA_CLI: str = "VertopalCLI"
    UA_LIB: str = "VertopalPythonLib"
    UA_PRODUCT: str = UA_LIB

    @classmethod
    def request( # pylint: disable=too-many-arguments
        cls,
        endpoint: str,
        method: str,
        app: str,
        token: str,
        field_params: Optional[List[str]] = None,
        version: Optional[str] = None,
    ) -> requests.Response:
        """Makes an authenticated HTTP request to the Vertopal API endpoints.

        Args:
            endpoint (str): The endpoint without hostname and API version.
            method (str): The HTTP method of the request.
            app (str): Your App-ID.
            token (str): Your Security-Token.
            field_params (Optional[List[str]], optional): List of field
                parameters which will be parsed into data and files.
                Defaults to `None`.
            version (Optional[str], optional): The API version number.
                Defaults to `None`.

        Returns:
            requests.Response: :class:`Response <Response>` object.
        """

        if endpoint[0] != "/":
            endpoint = f"/{endpoint}"
        if version:
            url = f"{Interface.ENDPOINT}/v{version}{endpoint}"
        else:
            url = f"{Interface.ENDPOINT}{endpoint}"

        if endpoint in ("/upload/file", "/download/url/get"):
            timeout = 300
        else:
            timeout = 30

        field = cls.__parse_field_parameters(field_params, {"%app-id%": app})

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
                    headers=cls._get_headers(token),
                    data=field.data,
                    files=files,
                    timeout=timeout,
                )

        return requests.request(
            method,
            url,
            headers=cls._get_headers(token),
            data=field.data,
            timeout=timeout,
        )

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
            token (str): Your Security-Token.

        Returns:
            Dict[str, str]: The HTTP header needed for API requests.
        """

        return {
            "Authorization": f"Bearer {token}",
            "User-Agent": cls._get_user_agent(),
        }

    @staticmethod
    def __parse_field_parameters(
        params: Optional[List[str]],
        replace: Optional[Dict[str, str]] = None
    ) -> SimpleNamespace:
        """Parse field parameters into a pair of data and file properties.

        Args:
            params (Optional[List[str]]): List of field parameters.
            replace (Optional[Dict[str, str]], optional): A dictionary
                containing keys and values, replacing any key occurrences in the
                parsed data values, to its appointed value. Defaults to `None`.

        Returns:
            SimpleNamespace: A SimpleNamespace instance containing `data` and
                `file` properties, each one a pair of key/value dictionary.
        """

        def _replace(text):
            for replace_from, replace_to in replace.items():
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
                            pval = _replace(pval)
                        if not data:
                            data = {}
                        data[pkey] = pval

        return SimpleNamespace(
            data=data,
            file=file,
        )
