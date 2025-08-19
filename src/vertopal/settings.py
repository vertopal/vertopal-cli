# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Default configuration settings and constants for the Vertopal
#   CLI and Python library.

"""
Configuration defaults and constants for Vertopal CLI and library.

This module centralizes all configurable parameters, including:

- **DEFAULT_CONFIG** — Nested dictionary containing default API credentials,
  endpoints, and connection settings (timeouts, retries, chunk sizes).
- **USER_CONFIG_PATH** — Path to the user-specific configuration file in the home
  directory, allowing overrides of default values.
- **USER_AGENT_PRODUCT_CLI / USER_AGENT_PRODUCT_LIB** — Identifiers used to
  distinguish CLI and library requests in API communications.
- **SLEEP_PATTERN** — Tuple defining progressive polling delays for
  long=running tasks, balancing responsiveness with server load.
- **MAX_CONCURRENT_CONVERSIONS** — Limit on simultaneous file conversions to
  respect API rate limits and maintain service stability.

By centralizing these values, Vertopal ensures consistent behaviour across
all modules and simplifies maintenance when adjusting defaults or enforcing
usage constraints.
"""

from pathlib import Path
from typing import Any, Dict, Tuple

from vertopal.types import PathType


# DEFAULT_CONFIG holds the default configuration settings for the package.
# This dictionary is structured with nested keys, where each top-level key
# represents a section (e.g., "api"), and its values contain
# specific configuration options such as the application ID, token,
# endpoint URL, timeout, and retry count.
DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {

    # API credentials and endpoint configuration
    # ------------------------------------------
    # This section contains the application ID, security token,
    # and base endpoint URL used for communicating with the Vertopal API.
    # You can use the default free credentials provided or replace them
    # with your own credentials obtained from:
    # https://www.vertopal.com/en/account/api/app/new
    "api": {
        # The application ID used for authentication with the Vertopal API.
        "app": "free",

        # The security token used for API authentication.
        "token": "FREE-TOKEN",

        # The base endpoint URL for all API requests.
        # Note: Do not include a version number
        # or a trailing slash in this URL.
        "endpoint": "https://api.vertopal.com",
    },

    # Connection settings for API requests
    # ------------------------------------
    # This section configures various connection parameters,
    # such as retry attempts, timeout durations for API requests,
    # and chunk size for streaming large responses.
    "connection_settings": {
        # The number of retry attempts for failed requests.
        "retries": 5,

        # The default timeout (in seconds) for API requests.
        "default_timeout": 30,

        # The timeout (in seconds) for long-running API requests,
        # such as uploads or downloads.
        "long_timeout": 300,

        # Default chunk size for streaming in bytes.
        "stream_chunk_size": 4096,
    }
}

# USER_CONFIG_PATH is the path to the user-specific configuration file.
# The file is located in the user's home directory by default and stores
# user-defined configurations that may override the default settings.
USER_CONFIG_PATH: PathType = Path.home() / ".vertopal"

# USER_AGENT_PRODUCT_CLI defines the product identifier for CLI-based
# requests to identify the Vertopal Command-Line Interface.
USER_AGENT_PRODUCT_CLI: str = "VertopalCLI"

# USER_AGENT_PRODUCT_LIB defines the product identifier for library-based
# requests to identify the Vertopal Python Library.
USER_AGENT_PRODUCT_LIB: str = "VertopalPythonLib"

# SLEEP_PATTERN defines the default sleep durations (in seconds)
# used for polling the status of long-running tasks. This pattern specifies
# a sequence of intervals that increase progressively to reduce server
# load while maintaining timely updates on the task's status.

# Example:
# - `(10, 20, 30, 60)` means:
#     - Wait 10 seconds after the first attempt,
#     - Wait 20 seconds after the second attempt,
#     - Wait 30 seconds after the third attempt,
#     - Wait 60 seconds after all subsequent attempts.
# This design allows polling with exponential backoff to balance efficiency
# and server resource usage.
SLEEP_PATTERN: Tuple[int, ...] = (10, 10, 15)

# MAX_CONCURRENT_CONVERSIONS defines the maximum number of files that can be
# processed concurrently during bulk conversions in the Vertopal CLI.
#
# This setting ensures efficient parallel processing while adhering to API
# rate limits imposed by the Vertopal service. Users CANNOT increase this
# arbitrarily, as doing so may exceed the API's request quota, leading to
# temporary restrictions on further conversions.
#
# The rate limit is enforced per time window, and exceeding it will result in
# a TOO_MANY_REQUESTS error (HTTP 429). To prevent this, users should monitor
# the X-RATELIMIT response headers and adjust batch sizes accordingly.
#
# For more details on rate limits, refer to the official documentation:
# https://www.vertopal.com/en/developer/api/rate-limit
#
# Example:
# - If set to `2`, two files will be processed simultaneously
#   in bulk conversions.
# - If reduced, conversions will take place sequentially, ensuring compliance
#   with API constraints.
MAX_CONCURRENT_CONVERSIONS: int = 2
