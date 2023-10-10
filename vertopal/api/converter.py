"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

from pathlib import Path
from time import sleep
from types import SimpleNamespace
from typing import Optional, Callable, Union, Tuple, Dict, Any

from requests import exceptions as RequestsExc

from vertopal.api.v1 import API
from vertopal.api import exception


class Converter:
    """Provides different methods to simplify a file conversion.

    Usage:

        >>> from vertopal import Converter
        >>> pdf2docx = Converter(
        ...     "document.pdf",
        ...     app="Your-App-ID",
        ...     token="Your-Security-Token",
        ... )
        >>> pdf2docx.convert("docx")
        >>> pdf2docx.wait()
        >>> if pdf2docx.is_converted():
        ...     pdf2docx.download()
    """

    def __init__(
        self,
        input_file: Union[str, Path],
        app: str,
        token: str
    ) -> None:
        """Converter class initializer.

        Args:
            input_file (str, Path): The input file name or path.
            app (str): Your App-ID.
            token (str): Your Security-Token.
        """

        # validate method parameters
        if not isinstance(input_file, (str, Path)):
            raise TypeError("input_file must be <str> or <Path>.")
        if not isinstance(app, str):
            raise TypeError("app must be <str>.")
        if not isinstance(token, str):
            raise TypeError("token must be <str>.")

        self.__input_file = input_file
        self.__app = app
        self.__token = token
        self.__convert_connector = None
        self.__convert_status = None
        self.__vcredits = None

    def convert(
        self,
        output_format: str,
        input_format: Optional[str] = None
    ) -> None:
        """Start converting the input file to the desired output format.

        Args:
            output_format (str): The output `format[-type]`.
            input_format (str, optional): The input `format[-type]`. If not
                specified, the `format[-type]` of the input file will be 
                considered based on its extension and type. Defaults to `None`.

        Raises:
            EntityStatusNotRunningError: If the entity status is not running.
        
        Returns:
            None
        """

        # validate method parameters
        if not isinstance(output_format, str):
            raise TypeError("output_format must be <str>.")
        if input_format and not isinstance(input_format, (str)):
            raise TypeError("input_format must be <str>")

        filepath = Path(self.__input_file).resolve()
        filename = filepath.name

        upload_response = self._call_task(
            API.upload,
            {
                "filename": filename,
                "filepath": filepath,
                "app": self.__app,
                "token": self.__token,
            },
        )
        upload_connector = upload_response["result"]["output"]["connector"]

        convert_response = self._call_task(
            API.convert,
            {
                "output_format": output_format,
                "app": self.__app,
                "token": self.__token,
                "connector": upload_connector,
                "input_format": input_format,
                "mode": API.ASYNC,
            },
        )
        if convert_response["entity"]["status"] != "running":
            raise exception.EntityStatusNotRunningError
        self.__convert_connector = convert_response["entity"]["id"]

    def wait(self, sleep_pattern: Tuple[int] = (10, 20, 30, 60)) -> None:
        """Wait for the convert to complete.

        Args:
            sleep_pattern (Tuple[int], optional): Sleeps seconds to delay
                between each check for the completion
                of the convert. Defaults to `(10, 20, 30, 60)`.
        
        Returns:
            None
        """

        # vaidate method parameters
        if not isinstance(sleep_pattern, tuple):
            raise TypeError("sleep_pattern must be <tuple>.")
        if not all(tuple(isinstance(i, int) for i in sleep_pattern)):
            raise ValueError("sleep_pattern must be <tuple> of <int>s.")
        if min(sleep_pattern) < 10:
            raise ValueError("sleep_pattern min value must be 10 or greater.")

        sleep_step = 0
        while not self.is_completed():
            sleep(sleep_pattern[sleep_step])
            if sleep_step < len(sleep_pattern) - 1:
                sleep_step += 1

    def is_completed(self) -> bool:
        """Check if the convert task is completed or not.

        Returns:
            bool: `True` if the convert task is completed, otherwise `False`.
        """

        if self._convert_task_status().task == "completed":
            return True
        return False

    def is_converted(self) -> bool:
        """Check if the result of the convert task is successful or not.

        Returns:
            bool: `True` if the convert is successful, otherwise `False`.
        """

        if self.__convert_status == "successful":
            return True
        return False

    def download(self, filename: Optional[str] = None) -> Path:
        """Download the converted file and write it to the disk.

        Args:
            filename (str, optional): Output file name or path
                to write to the disk. If set to `None`, the filename
                received from the API server will be used. Defaults to `None`.

        Raises:
            NetworkConnectionError: If there is a problem in connecting
                to the network.
            OtherError: If an unknown/undefined error occurs.
            HTTPResponseError: If the server returns an HTTP
                response status of 4xx or 5xx.
            OutputWriteError: If there is a problem in writing the downloaded
                output file to the disk.

        Returns:
            Path: The absolute path of the downloaded file.
        """

        # validate method parameters
        if filename and not isinstance(filename, str):
            raise TypeError("filename must be <str>.")

        download_url = self._download_url()
        try:
            response = API.download(
                app=self.__app,
                token=self.__token,
                connector=download_url.connector,
                url=False,
            )
        except RequestsExc.ConnectionError as exc:
            raise exception.NetworkConnectionError from exc
        except Exception as error:
            raise exception.OtherError from error

        # if http response code is 4xx or 5xx
        if (response.status_code % 1000) // 100 in (4, 5):
            raise exception.HTTPResponseError

        if filename:
            output_file = Path(filename)
        else:
            output_file = Path(download_url.filename)
        try:
            with open(output_file, 'wb') as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
        except Exception as error:
            raise exception.OutputWriteError from error

        return output_file.resolve()

    def _download_url(self) -> SimpleNamespace:
        """Send a download request and get the download connector and filename.

        Returns:
            SimpleNamespace: A SimpleNamespace instance with
                `connector` (download connector), and
                `filename` (download filename).
        """

        json = self._call_task(
            API.download,
            {
                "app": self.__app,
                "token": self.__token,
                "connector": self.__convert_connector,
                "url": True,
            },
        )
        return SimpleNamespace(
            connector=json["result"]["output"]["connector"],
            filename=json["result"]["output"]["name"],
        )

    def _convert_task_status(self) -> SimpleNamespace:
        """Run a convert task response request using Vertopal API.

        Returns:
            SimpleNamespace: A SimpleNamespace instance with
                `task` (task status), `vcredits` (used vCredits),
                and `convert` (convert status) properties.
        """

        json = self._call_task(
            API.task_response,
            {
                "app": self.__app,
                "token": self.__token,
                "connector": self.__convert_connector,
            },
        )

        result = json["result"]["output"]["result"]
        if result:
            self.__convert_status = result["output"]["status"]
            self.__vcredits = json["result"]["output"]["entity"]["vcredits"]
        else:
            self.__convert_status = None

        return SimpleNamespace(
            task=json["result"]["output"]["entity"]["status"],
            vcredits=self.__vcredits,
            convert=self.__convert_status,
        )

    def _call_task(
        self,
        func: Callable[[Any], object],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call an API task.

        Args:
            func (Callable[[Any], object]): The API task callable.
            kwargs (Dict[str, Any]): Keyword arguments of the callable `func`.

        Raises:
            InputNotFoundError: If the input file not exists.
            NetworkConnectionError: If there is a problem in connecting
                to the network.
            OtherError: If an unknown/undefined error occurs.
            InvalidJSONResponseError: If the HTTP response is invalid
                and cannot be decoded to JSON.
            HTTPResponseError: If the server returns an HTTP
                response status of 4xx or 5xx.
            APIError: If there is an API-level error code in server response.

        Returns:
            Dict[str, Any]: JSON response of the API cast to Python dictionary.
        """

        try:
            response = func(**kwargs)
        except FileNotFoundError as exc:
            raise exception.InputNotFoundError from exc
        except RequestsExc.ConnectionError as exc:
            raise exception.NetworkConnectionError from exc
        except Exception as error:
            raise exception.OtherError from error

        try:
            json = response.json()
        except RequestsExc.InvalidJSONError as exc:
            raise exception.InvalidJSONResponseError from exc
        except Exception as error:
            raise exception.OtherError from error

        code = None
        if "code" in json:
            code = json["code"]
            message = json["message"] if "message" in json else ""
        if ("result" in json
            and "error" in json["result"]
            and "code" in json["result"]["error"]):
            code = json["result"]["error"]["code"]
            if "message" in json["result"]["error"]:
                message = json["result"]["error"]["message"]
            else:
                message = ""
        if code:
            if code in exception.error_codes:
                raise exception.error_codes[code](message)
            raise exception.APIError
        # if http response code is 4xx or 5xx
        if (response.status_code % 1000) // 100 in (4, 5):
            raise exception.HTTPResponseError

        return json

    @property
    def vcredits(self) -> Union[int, None]:
        """Number of total vCredits spent for the conversion.
        """

        return self.__vcredits
