# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Exceptions are organized so that higher-level code can either
#   respond to specific error types or catch groups of related errors
#   via their common parent classes. Use the most specific exception
#   that makes sense for your error handling logic.

"""
Exception classes used by the Vertopal CLI and library.

This module defines the library's exception hierarchy rooted at
`APIException`. It includes response-related errors, API-level errors,
task-level errors, and utility exceptions such as output write
failures. Consumers may catch broad categories (for example
`APIResponseError`) or handle very specific cases (for example
`InvalidCredentialError`).

Example hierarchy (abridged):

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
        │    │    │    ├── ...
        │    │    │    ├── ...
        │    │    │    ├── ...
        │    │    │    └── FailedConvertError
        │    │    └── HTTPResponseError
        │    ├── APITaskError
        │    │    └── EntityStatusNotRunningError
        │    └── OutputWriteError
        └── Warning
            └── APIWarning
"""


class APIException(Exception):
    """
    Base exception for Vertopal library errors.

    This is the root of the library's exception hierarchy. Catching
    `APIException` will handle any custom exception raised by this
    package.

    Package exception hierarchy:

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
    """An unknown error occurred."""


class InputNotFoundError(APIException):
    """Input file not found on the disk."""


class NetworkConnectionError(APIException):
    """There is a problem in connecting to the network."""


class APIResponseError(APIException):
    """The parent class of the HTTP response of the API."""


class InvalidJSONResponseError(APIResponseError):
    """The HTTP response is invalid and cannot be decoded to JSON."""


class APIError(APIResponseError):
    """The parent class of the different API-level errors."""


class InternalServerError(APIError):
    """
    The server returned an HTTP 500 error. This is a server error.
    Please contact us at vertopal.com if the problem persists.
    """


class NotFoundError(APIError):
    """The API Endpoint is not found."""


class PostMethodAllowedError(APIError):
    """Only the HTTP POST method is allowed."""


class MissingAuthorizationHeaderError(APIError):
    """The Authorization header is required."""


class InvalidAuthorizationHeaderError(APIError):
    """The Authorization header is invalid."""


class InvalidFieldError(APIError):
    """The `[NAME]` field is invalid."""


class MissingRequiredFieldError(APIError):
    """The `[NAME]` field is required."""


class WrongTypeFieldError(APIError):
    """The `[NAME]` field has the wrong type."""


class InvalidDataKeyError(APIError):
    """The `[NAME]` key in the data is invalid."""


class MissingRequiredDataKeyError(APIError):
    """The `[NAME]` key in the data is required."""


class WrongTypeDataKeyError(APIError):
    """The `[NAME]` key in the data has the wrong type."""


class WrongValueDataKeyError(APIError):
    """The `[NAME]` key in the data has the wrong value."""


class InvalidCredentialError(APIError):
    """The access credential is invalid."""


class FreePlanDisallwedError(APIError):
    """To use Vertopal API, activating a premium plan is required."""


class InsufficentVCreditsError(APIError):
    """You do not have enough vCredits to run this task."""


class InvalidCallbackError(APIError):
    """The callback is invalid."""


class UnverifiedDomainCallbackError(APIError):
    """The domain of callback is not verified."""


class NoConnectorDependentTaskError(APIError):
    """The Connector is not dependent on any other Task."""


class NotReadyDependentTaskError(APIError):
    """The dependent task has not been completed correctly."""


class MismatchVersionDependentTaskError(APIError):
    """
    The dependent task API version is mismatched
    with the current task API version.
    """


class MismatchDependentTaskError(APIError):
    """The dependent task is mismatched with the current task."""


class FileNotExistsError(APIError):
    """The `[STATE]` file not exists."""


class DownloadExpiredError(APIError):
    """The download of this converted file has expired."""


class OnlyDevelopmentRequestError(APIError):
    """
    Only request of files with the registered hash
    is allowed in the development mode.
    """


class InvalidParameterError(APIError):
    """The `[NAME]` parameter is invalid."""


class MissingRequiredParameterError(APIError):
    """The `[NAME]` parameter is required."""


class WrongTypeParameterError(APIError):
    """The `[NAME]` parameter has the wrong type."""


class WrongValueParameterError(APIError):
    """The `[NAME]` parameter has the wrong value."""


class OnlyDevelopmentFileError(APIError):
    """
    Only file with the registered hash
    is allowed in the development mode.
    """


class NotValidExtensionError(APIError):
    """File extension `[EXTENSION]` is not valid."""


class LimitUploadSizeError(APIError):
    """
    The max size of the file is `[MAXSIZE]` KB;
    the current is `[FILESIZE]` KB.
    """


class EmptyFileError(APIError):
    """The submitted file is empty."""


class WrongOutputFormatStructureError(APIError):
    """The output format has the wrong structure."""


class InvalidOutputFormatError(APIError):
    """The `[OUTPUT]` format is not found in the valid output formats."""


class WrongInputFormatStructureError(APIError):
    """The input format has the wrong structure."""


class InvalidInputFormatError(APIError):
    """The `[INPUT]` format is not found in the valid input formats."""


class NoConverterInputToOutputError(APIError):
    """There is no converter for `[INPUT]` format to `[OUTPUT]` format."""


class NotMatchExtensionAndInputError(APIError):
    """
    The file extension (`[FILE_EXTENSION]`) does not match
    the input extension (`[INPUT_EXTENSION]`).
    """


class FailedConvertError(APIError):
    """The conversion has failed."""


class HTTPResponseError(APIResponseError):
    """The server returned an HTTP response status of 4xx or 5xx."""


class APITaskError(APIException):
    """The parent class of the API-task-level errors."""


class EntityStatusNotRunningError(APITaskError):
    """Entity status is not running."""


class OutputWriteError(APIException):
    """Writing the output file to the disk failed."""


class APIWarning(Warning):
    """API Warning."""
