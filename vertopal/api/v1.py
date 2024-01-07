"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

from typing import Optional

import requests

from vertopal.api.interface import Interface


class API(Interface):
    """Provides methods for sending requests to the Vertopal API-v1 endpoints.

    Attributes:
        ENDPOINT (str): The endpoint URL of the Vertopal API v1.

    Usage:

        >>> import vertopal
        >>> response = vertopal.API.upload(
        ...     filename="document.pdf",
        ...     filepath="/home/vertopal/document.pdf",
        ...     app="my-app-id",
        ...     token="my-security-token",
        ... )
        >>> response
        <Response [200]>
        >>> json_res = response.json()
        >>> json_res["result"]["output"]["connector"]
        'the-connector-of-the-upload-task'
    """

    ENDPOINT: str = "https://api.vertopal.com/v1"

    @classmethod
    def upload(
        cls,
        filename: str,
        filepath: str,
        app: str,
        token: str
    ) -> requests.Response:
        """Send an upload request to the Vertopal API endpoint.

        Args:
            filename (str): Input file name.
            filepath (str): Absolute path of the input file.
            app (str): Your App-ID.
            token (str): Your Security-Token.

        Returns:
            requests.Response: :class:`Response <Response>` object.
        """

        with open(filepath, "rb") as file:
            response = requests.request(
                "POST",
                cls.ENDPOINT + "/upload/file",
                headers=cls._get_headers(token),
                data={
                    'data': '{'
                        f'"app": "{app}"'
                    '}'
                },
                files=[(
                    "file",
                    (filename, file)
                )],
                timeout=300,
            )
        return response

    @classmethod
    def convert( # pylint: disable=too-many-arguments
        cls,
        output_format: str,
        app: str,
        token: str,
        connector: str,
        input_format: Optional[str] = None,
        mode: str = Interface.ASYNC
    ) -> requests.Response:
        """Send a convert request to the Vertopal API endpoint.

        Args:
            output_format (str): The output `format[-type]`, which input file
                will be converted to.
            app (str): Your App-ID.
            token (str): Your Security-Token.
            connector (str): The connector from the previous task (Upload).
            input_format (str, optional): The input `format[-type]`. If not
                specified, the `format[-type]` of the input file will be 
                considered based on its extension and type. Defaults to `None`.
            mode (str, optional): Mode strategy of the task which can be 
                :class:`Interface.SYNC` or :class:`Interface.ASYNC`. 
                Defaults to :class:`Interface.ASYNC`.

        Returns:
            requests.Response: :class:`Response <Response>` object.
        """

        if input_format:
            io_field = f'"input": "{input_format}","output": "{output_format}"'
        else:
            io_field = f'"output": "{output_format}"'
        data = {
            'data': '{'
                f'"app": "{app}",'
                f'"connector": "{connector}",'
                '"include": ["result", "entity"],'
                f'"mode": "{mode}",'
                '"parameters": {'
                    f'{io_field}'
                '}'
            '}'
        }
        response = requests.request(
            "POST",
            cls.ENDPOINT + "/convert/file",
            headers=cls._get_headers(token),
            data=data,
            timeout=30,
        )
        return response

    @classmethod
    def status(cls, app: str, token: str, connector: str) -> requests.Response:
        """Send a convert status request to the Vertopal API endpoint.

        Args:
            app (str): Your App-ID.
            token (str): Your Security-Token.
            connector (str): The connector of a convert task.

        Returns:
            requests.Response: :class:`Response <Response>` object.
        """

        response = requests.request(
            "POST",
            cls.ENDPOINT + "/convert/status",
            headers=cls._get_headers(token),
            data={
                'data': '{'
                    f'"app": "{app}",'
                    f'"connector": "{connector}"'
                '}'
            },
            timeout=30,
        )
        return response

    @classmethod
    def task_response(
        cls,
        app: str,
        token: str,
        connector: str
    ) -> requests.Response:
        """Send a task response request to the Vertopal API endpoint.

        Args:
            app (str): Your App-ID.
            token (str): Your Security-Token.
            connector (str): The connector of a task.

        Returns:
            requests.Response: :class:`Response <Response>` object.
        """

        response = requests.request(
            "POST",
            cls.ENDPOINT + "/task/response",
            headers=cls._get_headers(token),
            data={
                'data': '{'
                    f'"app": "{app}",'
                    f'"connector": "{connector}",'
                    '"include": ["result"]'
                '}'
            },
            timeout=30,
        )
        return response

    @classmethod
    def download(
        cls,
        app: str,
        token: str,
        connector: str,
        url: bool = False
    ) -> requests.Response:
        """Send a download request to the Vertopal API endpoint.

        Args:
            app (str): Your App-ID.
            token (str): Your Security-Token.
            connector (str): The connector from the previous task (Convert).
            url (bool, optional): If `True`, a request for getting download
                url, and if `False` a request for getting file content will be
                send. Defaults to `False`.

        Returns:
            requests.Response: :class:`Response <Response>` object.
        """

        if url:
            endpoint = cls.ENDPOINT + "/download/url"
            timeout = 30
        else:
            endpoint = cls.ENDPOINT + "/download/url/get"
            timeout = 300
        response = requests.request(
            "POST",
            endpoint,
            headers=cls._get_headers(token),
            data={
                'data': '{'
                    f'"app": "{app}",'
                    f'"connector": "{connector}"'
                '}'
            },
            timeout=timeout,
        )
        return response

    @classmethod
    def format_get(
        cls,
        app: str,
        token: str,
        format_: str,
    ) -> requests.Response:
        """Send a format/get request to the Vertopal API endpoint.

        Get the properties of a specific format.

        Args:
            app (str): Your App-ID.
            token (str): Your Security-Token.
            format_ (str): The specific `format[-type]` you want to get
                its properties.

        Returns:
            requests.Response: :class:`Response <Response>` object.
        """

        response = requests.request(
            "POST",
            cls.ENDPOINT + "/format/get",
            headers=cls._get_headers(token),
            data={
                'data': '{'
                    f'"app": "{app}",'
                    '"parameters": {'
                        f'"format": "{format_}"'
                    '}'
                '}'
            },
            timeout=30,
        )
        return response

    @classmethod
    def convert_graph(
        cls,
        app: str,
        token: str,
        input_: str,
        output: str,
    ) -> requests.Response:
        """Send a convert/graph request to the Vertopal API endpoint.

        Get the relation between the input format and the output format
        for file conversion.

        Args:
            app (str): Your App-ID.
            token (str): Your Security-Token.
            input_ (str): The input `format[-type]`.
            output (str): The output `format[-type]`.

        Returns:
            requests.Response: :class:`Response <Response>` object.
        """

        response = requests.request(
            "POST",
            cls.ENDPOINT + "/convert/graph",
            headers=cls._get_headers(token),
            data={
                'data': '{'
                    f'"app": "{app}",'
                    '"parameters": {'
                        f'"input": "{input_}",'
                        f'"output": "{output}"'
                    '}'
                '}'
            },
            timeout=30,
        )
        return response

    @classmethod
    def convert_formats(
        cls,
        app: str,
        token: str,
        sublist: str,
        format_: Optional[str] = None,
    ) -> requests.Response:
        """Send a convert/formats request to the Vertopal API endpoint.

        Get supported input or output formats for file conversion.

        Args:
            app (str): Your App-ID.
            token (str): Your Security-Token.
            sublist (str): Selects supported formats based on whether they are
                inputs or outputs. Valid values are `Interface.INPUTS`
                and `Interface.OUTPUTS`.
            format_ (str, optional): The specific `format[-type]` you want to
                get its supported input or output formats. Defaults to `None`.

        Raises:
            ValueError: If the `sublist` has an invalid value.

        Returns:
            requests.Response: :class:`Response <Response>` object.
        """

        if sublist not in (cls.INPUTS, cls.OUTPUTS):
            raise ValueError('sublist must be either "inputs" or "outputs"')

        if format_:
            data_format = f',"format": "{format_}"'
        else:
            data_format = ""

        response = requests.request(
            "POST",
            cls.ENDPOINT + "/convert/formats",
            headers=cls._get_headers(token),
            data={
                'data': '{'
                    f'"app": "{app}",'
                    '"parameters": {'
                        f'"sublist": "{sublist}"'
                        f'{data_format}'
                    '}'
                '}'
            },
            timeout=30,
        )
        return response
