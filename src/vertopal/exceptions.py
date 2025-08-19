"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""


class APIException(Exception):
    """The parent class of the library exceptions.

    The class hierarchy for the library exceptions is:

    BaseException
     └── Exception
          ├── APIException
          │    ├── OtherError
          │    ├── InputNotFoundError
          │    ├── NetworkConnectionError
          │    ├── APIResponseError
          │    │    ├── InvalidJSONResponseError
          │    │    ├── APIError
          │    │    │    ├── InternalServerError
          │    │    │    ├── NotFoundError
          │    │    │    ├── PostMethodAllowedError
          │    │    │    ├── MissingAuthorizationHeaderError
          │    │    │    ├── InvalidAuthorizationHeaderError
          │    │    │    ├── InvalidFieldError
          │    │    │    ├── MissingRequiredFieldError
          │    │    │    ├── WrongTypeFieldError
          │    │    │    ├── InvalidDataKeyError
          │    │    │    ├── MissingRequiredDataKeyError
          │    │    │    ├── WrongTypeDataKeyError
          │    │    │    ├── WrongValueDataKeyError
          │    │    │    ├── InvalidCredentialError
          │    │    │    ├── FreePlanDisallwedError
          │    │    │    ├── InsufficentVCreditsError
          │    │    │    ├── InvalidCallbackError
          │    │    │    ├── UnverifiedDomainCallbackError
          │    │    │    ├── NoConnectorDependentTaskError
          │    │    │    ├── NotReadyDependentTaskError
          │    │    │    ├── MismatchVersionDependentTaskError
          │    │    │    ├── MismatchDependentTaskError
          │    │    │    ├── FileNotExistsError
          │    │    │    ├── DownloadExpiredError
          │    │    │    ├── OnlyDevelopmentRequestError
          │    │    │    ├── InvalidParameterError
          │    │    │    ├── MissingRequiredParameterError
          │    │    │    ├── WrongTypeParameterError
          │    │    │    ├── WrongValueParameterError
          │    │    │    ├── OnlyDevelopmentFileError
          │    │    │    ├── NotValidExtensionError
          │    │    │    ├── LimitUploadSizeError
          │    │    │    ├── EmptyFileError
          │    │    │    ├── WrongOutputFormatStructureError
          │    │    │    ├── InvalidOutputFormatError
          │    │    │    ├── WrongInputFormatStructureError
          │    │    │    ├── InvalidInputFormatError
          │    │    │    ├── NoConverterInputToOutputError
          │    │    │    ├── NotMatchExtensionAndInputError
          │    │    │    └── FailedConvertError
          │    │    └── HTTPResponseError
          │    ├── APITaskError
          │    │    └── EntityStatusNotRunningError
          │    └── OutputWriteError
          └── Warning
               └── APIWarning
    """

class OtherError(APIException):
    """An unknown error occurred.
    """


class InputNotFoundError(APIException):
    """Input file not found on the disk.
    """


class NetworkConnectionError(APIException):
    """There is a problem in connecting to the network.
    """


class APIResponseError(APIException):
    """The parent class of the HTTP response of the API.
    """


class InvalidJSONResponseError(APIResponseError):
    """The HTTP response is invalid and cannot be decoded to JSON.
    """


class APIError(APIResponseError):
    """The parent class of the different API-level errors.
    """


class InternalServerError(APIError):
    """The server returned an HTTP 500 error. This is a server error.
    Please contact us at vertopal.com if the problem persists.
    """


class NotFoundError(APIError):
    """The API Endpoint is not found.
    """


class PostMethodAllowedError(APIError):
    """Only the HTTP POST method is allowed.
    """


class MissingAuthorizationHeaderError(APIError):
    """The Authorization header is required.
    """


class InvalidAuthorizationHeaderError(APIError):
    """The Authorization header is invalid.
    """


class InvalidFieldError(APIError):
    """The `[NAME]` field is invalid.
    """


class MissingRequiredFieldError(APIError):
    """The `[NAME]` field is required.
    """


class WrongTypeFieldError(APIError):
    """The `[NAME]` field has the wrong type.
    """


class InvalidDataKeyError(APIError):
    """The `[NAME]` key in the data is invalid.
    """


class MissingRequiredDataKeyError(APIError):
    """The `[NAME]` key in the data is required.
    """


class WrongTypeDataKeyError(APIError):
    """The `[NAME]` key in the data has the wrong type.
    """


class WrongValueDataKeyError(APIError):
    """The `[NAME]` key in the data has the wrong value.
    """


class InvalidCredentialError(APIError):
    """The access credential is invalid.
    """


class FreePlanDisallwedError(APIError):
    """To use Vertopal API, activating a premium plan is required.
    """


class InsufficentVCreditsError(APIError):
    """You do not have enough vCredits to run this task.
    """


class InvalidCallbackError(APIError):
    """The callback is invalid.
    """


class UnverifiedDomainCallbackError(APIError):
    """The domain of callback is not verified.
    """


class NoConnectorDependentTaskError(APIError):
    """The Connector is not dependent on any other Task.
    """


class NotReadyDependentTaskError(APIError):
    """The dependent task has not been completed correctly.
    """


class MismatchVersionDependentTaskError(APIError):
    """The dependent task API version is mismatched
    with the current task API version.
    """


class MismatchDependentTaskError(APIError):
    """The dependent task is mismatched with the current task.
    """


class FileNotExistsError(APIError):
    """The `[STATE]` file not exists.
    """


class DownloadExpiredError(APIError):
    """The download of this converted file has expired.
    """


class OnlyDevelopmentRequestError(APIError):
    """Only request of files with the registered hash is allowed
    in the development mode.
    """


class InvalidParameterError(APIError):
    """The `[NAME]` parameter is invalid.
    """


class MissingRequiredParameterError(APIError):
    """The `[NAME]` parameter is required.
    """


class WrongTypeParameterError(APIError):
    """The `[NAME]` parameter has the wrong type.
    """


class WrongValueParameterError(APIError):
    """The `[NAME]` parameter has the wrong value.
    """


class OnlyDevelopmentFileError(APIError):
    """Only file with the registered hash is allowed in the development mode.
    """


class NotValidExtensionError(APIError):
    """File extension `[EXTENSION]` is not valid.
    """


class LimitUploadSizeError(APIError):
    """The max size of the file is `[MAXSIZE]` KB; the current
    is `[FILESIZE]` KB.
    """


class EmptyFileError(APIError):
    """The submitted file is empty.
    """


class WrongOutputFormatStructureError(APIError):
    """The output format has the wrong structure.
    """


class InvalidOutputFormatError(APIError):
    """The `[OUTPUT]` format is not found in the valid output formats.
    """


class WrongInputFormatStructureError(APIError):
    """The input format has the wrong structure.
    """


class InvalidInputFormatError(APIError):
    """The `[INPUT]` format is not found in the valid input formats.
    """


class NoConverterInputToOutputError(APIError):
    """There is no converter for `[INPUT]` format to `[OUTPUT]` format.
    """


class NotMatchExtensionAndInputError(APIError):
    """The file extension (`[FILE_EXTENSION]`) does not match
    the input extension (`[INPUT_EXTENSION]`).
    """


class FailedConvertError(APIError):
    """The conversion has failed.
    """


class HTTPResponseError(APIResponseError):
    """The server returned an HTTP response status of 4xx or 5xx.
    """


class APITaskError(APIException):
    """The parent class of the API-task-level errors.
    """


class EntityStatusNotRunningError(APITaskError):
    """Entity status is not running.
    """


class OutputWriteError(APIException):
    """Writing the output file to the disk failed.
    """


class APIWarning(Warning):
    """API Warning
    """


error_codes = {
    "INTERNAL_SERVER_ERROR": InternalServerError,
    "NOT_FOUND": NotFoundError,
    "POST_METHOD_ALLOWED": PostMethodAllowedError,
    "MISSING_AUTHORIZATION_HEADER": MissingAuthorizationHeaderError,
    "INVALID_AUTHORIZATION_HEADER": InvalidAuthorizationHeaderError,
    "INVALID_FIELD": InvalidFieldError,
    "MISSING_REQUIRED_FIELD": MissingRequiredFieldError,
    "WRONG_TYPE_FIELD": WrongTypeFieldError,
    "INVALID_DATA_KEY": InvalidDataKeyError,
    "MISSING_REQUIRED_DATA_KEY": MissingRequiredDataKeyError,
    "WRONG_TYPE_DATA_KEY": WrongTypeDataKeyError,
    "WRONG_VALUE_DATA_KEY": WrongValueDataKeyError,
    "INVALID_CREDENTIAL": InvalidCredentialError,
    "FREE_PLAN_DISALLOWED": FreePlanDisallwedError,
    "INSUFFICIENT_VCREDITS": InsufficentVCreditsError,
    "INVALID_CALLBACK": InvalidCallbackError,
    "UNVERIFIED_DOMAIN_CALLBACK": UnverifiedDomainCallbackError,
    "NO_CONNECTOR_DEPENDENT_TASK": NoConnectorDependentTaskError,
    "NOT_READY_DEPENDENT_TASK": NotReadyDependentTaskError,
    "MISMATCH_VERSION_DEPENDENT_TASK": MismatchVersionDependentTaskError,
    "MISMATCH_DEPENDENT_TASK": MismatchDependentTaskError,
    "FILE_NOT_EXISTS": FileNotExistsError,
    "DOWNLOAD_EXPIRED": DownloadExpiredError,
    "ONLY_DEVELOPMENT_REQUEST": OnlyDevelopmentRequestError,
    "INVALID_PARAMETER": InvalidParameterError,
    "MISSING_REQUIRED_PARAMETER": MissingRequiredParameterError,
    "WRONG_TYPE_PARAMETER": WrongTypeParameterError,
    "WRONG_VALUE_PARAMETER": WrongValueParameterError,
    "ONLY_DEVELOPMENT_FILE": OnlyDevelopmentFileError,
    "NOT_VALID_EXTENSION": NotValidExtensionError,
    "LIMIT_UPLOAD_SIZE": LimitUploadSizeError,
    "EMPTY_FILE": EmptyFileError,
    "WRONG_OUTPUT_FORMAT_STRUCTURE": WrongOutputFormatStructureError,
    "INVALID_OUTPUT_FORMAT": InvalidOutputFormatError,
    "WRONG_INPUT_FORMAT_STRUCTURE": WrongInputFormatStructureError,
    "INVALID_INPUT_FORMAT": InvalidInputFormatError,
    "NO_CONVERTER_INPUT_TO_OUTPUT": NoConverterInputToOutputError,
    "NOT_MATCH_EXTENSION_AND_INPUT": NotMatchExtensionAndInputError,
    "FAILED_CONVERT": FailedConvertError,
}
