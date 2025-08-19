# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Exception handling utilities for Vertopal API responses.
#   Provides a mapping (`ERROR_CODE_MAP`) between API error codes
#   and custom exception classes, and the `ExceptionHandler` class
#   for inspecting JSON responses. The handler uses an internal
#   `_ErrorWrapper` to extract error details, raising mapped
#   exceptions when errors are found, or printing warnings without
#   interrupting program flow. This enables consistent and centralized
#   error-handling across the codebase.

"""
Utilities for mapping API error responses to library exceptions.

This module centralizes logic for inspecting JSON responses from the
Vertopal API and translating server-side error codes into the
library's exception classes. It exposes `ERROR_CODE_MAP` which maps
API error codes to exception types, and the `ExceptionHandler` which
inspects responses and raises the appropriate exception when an
error is detected.
"""

import vertopal.exceptions as vex
from vertopal.utils.data_wrappers import _ErrorWrapper

# Define public names for external usage
__all__ = [
    "ERROR_CODE_MAP",
    "ExceptionHandler",
]


# A mapping of API error codes to custom exception classes.
ERROR_CODE_MAP = {
    "INTERNAL_SERVER_ERROR": vex.InternalServerError,
    "NOT_FOUND": vex.NotFoundError,
    "POST_METHOD_ALLOWED": vex.PostMethodAllowedError,
    "MISSING_AUTHORIZATION_HEADER": vex.MissingAuthorizationHeaderError,
    "INVALID_AUTHORIZATION_HEADER": vex.InvalidAuthorizationHeaderError,
    "INVALID_FIELD": vex.InvalidFieldError,
    "MISSING_REQUIRED_FIELD": vex.MissingRequiredFieldError,
    "WRONG_TYPE_FIELD": vex.WrongTypeFieldError,
    "INVALID_DATA_KEY": vex.InvalidDataKeyError,
    "MISSING_REQUIRED_DATA_KEY": vex.MissingRequiredDataKeyError,
    "WRONG_TYPE_DATA_KEY": vex.WrongTypeDataKeyError,
    "WRONG_VALUE_DATA_KEY": vex.WrongValueDataKeyError,
    "INVALID_CREDENTIAL": vex.InvalidCredentialError,
    "FREE_PLAN_DISALLOWED": vex.FreePlanDisallwedError,
    "INSUFFICIENT_VCREDITS": vex.InsufficentVCreditsError,
    "INVALID_CALLBACK": vex.InvalidCallbackError,
    "UNVERIFIED_DOMAIN_CALLBACK": vex.UnverifiedDomainCallbackError,
    "NO_CONNECTOR_DEPENDENT_TASK": vex.NoConnectorDependentTaskError,
    "NOT_READY_DEPENDENT_TASK": vex.NotReadyDependentTaskError,
    "MISMATCH_VERSION_DEPENDENT_TASK": vex.MismatchVersionDependentTaskError,
    "MISMATCH_DEPENDENT_TASK": vex.MismatchDependentTaskError,
    "FILE_NOT_EXISTS": vex.FileNotExistsError,
    "DOWNLOAD_EXPIRED": vex.DownloadExpiredError,
    "ONLY_DEVELOPMENT_REQUEST": vex.OnlyDevelopmentRequestError,
    "INVALID_PARAMETER": vex.InvalidParameterError,
    "MISSING_REQUIRED_PARAMETER": vex.MissingRequiredParameterError,
    "WRONG_TYPE_PARAMETER": vex.WrongTypeParameterError,
    "WRONG_VALUE_PARAMETER": vex.WrongValueParameterError,
    "ONLY_DEVELOPMENT_FILE": vex.OnlyDevelopmentFileError,
    "NOT_VALID_EXTENSION": vex.NotValidExtensionError,
    "LIMIT_UPLOAD_SIZE": vex.LimitUploadSizeError,
    "EMPTY_FILE": vex.EmptyFileError,
    "WRONG_OUTPUT_FORMAT_STRUCTURE": vex.WrongOutputFormatStructureError,
    "INVALID_OUTPUT_FORMAT": vex.InvalidOutputFormatError,
    "WRONG_INPUT_FORMAT_STRUCTURE": vex.WrongInputFormatStructureError,
    "INVALID_INPUT_FORMAT": vex.InvalidInputFormatError,
    "NO_CONVERTER_INPUT_TO_OUTPUT": vex.NoConverterInputToOutputError,
    "NOT_MATCH_EXTENSION_AND_INPUT": vex.NotMatchExtensionAndInputError,
    "FAILED_CONVERT": vex.FailedConvertError,
}


class ExceptionHandler:
    """
    A handler that examines API responses and raises custom exceptions.
    Uses _ErrorWrapper to extract error details.
    """

    @staticmethod
    def raise_for_response(response: dict) -> None:
        """
        Examines the API response and raises an appropriate exception
        if an error is present.

        This method uses `_ErrorWrapper` to inspect the response
        for known error codes and messages. If a matching error
        is found, it raises a custom exception from `ERROR_CODE_MAP`.
        If no match is found, it defaults to `APIException`.

        If warnings are present instead, they are printed to
        standard output but do not interrupt program flow.

        Args:
            response (dict): The JSON response received from the API.

        Raises:
            APIException or a subclass thereof: Based on the error code
                found in the response.
        """
        wrapper = _ErrorWrapper(response)
        if wrapper.has_error():
            code = wrapper.get_error_code()
            message = wrapper.get_error_message()
            exception_class = ERROR_CODE_MAP.get(code, vex.APIException)
            raise exception_class(f"[{code}] {message}")

        if wrapper.has_warning():
            warnings = wrapper.get_warnings()
            # Process warnings appropriately (e.g., log)
            print("Warning(s) encountered:", warnings)
