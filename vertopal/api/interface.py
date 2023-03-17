"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

from typing import Dict


class Interface:
    """The parent :class:`Interface` class for the API.

    Attributes:
        ASYNC (str): ASYNC mode strategy constant.
        SYNC (str): SYNC mode strategy constant.
    """

    ASYNC: str = "async"
    SYNC: str = "sync"

    @classmethod
    def upload(cls):
        raise NotImplementedError("upload method is not implemented")

    @classmethod
    def convert(cls):
        raise NotImplementedError("convert method is not implemented")

    @classmethod
    def status(cls):
        raise NotImplementedError("status method is not implemented")

    @classmethod
    def task_response(cls):
        raise NotImplementedError("task_response is not implemented")

    @classmethod
    def download(cls):
        raise NotImplementedError("download method is not implemented")

    @staticmethod
    def _get_headers(token: str) -> Dict[str, str]:
        """Concatenate the token provided to build and return an HTTP header.

        Args:
            token (str): Your Security-Token

        Returns:
            Dict[str, str]: The HTTP header needed for API requests.
        """

        return {
            "Authorization": f"Bearer {token}"
        }
