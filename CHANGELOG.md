# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 🌱 [Unreleased]

*Changes currently in progress or planned for future versions will appear here.*

### 🛠 Changed

- Refactored type hints to use built-in generics (`list`, `dict`, and `tuple`) instead of `typing.List`, `typing.Dict`, and `typing.Tuple`.
- Updated README installer instructions to use a unified endpoint for macOS and Linux (`https://run.vertopal.com/cli/unix`).

## [2.0.3] - 2025-09-01

### 🐛 Fixed

- Updated GitHub Actions build matrix to replace `ubuntu-20.04` with `ubuntu-22.04` in preparation for the deprecation and removal of the `ubuntu-20.04` runner image on GitHub Actions (April 1, 2025). This ensures continued availability of Linux builds and avoids scheduled brownout outages.

## [2.0.2] - 2025-09-01

### 🐛 Fixed

- Removed `slots=True` from `@dataclass` declarations to restore compatibility with Python 3.9.

## [2.0.1] - 2025-09-01

### 🐛 Fixed

- Updated GitHub Actions workflow to replace deprecated `actions/upload-artifact@v3` and `actions/download-artifact@v3` with v4 equivalents.
- Adjusted artifact download step to use `pattern` and `merge-multiple` for collecting OS-specific build artifacts in a single directory during release.

## [2.0.0] - 2025-09-01

### 📦 Migration Guide (from 1.x to 2.0.0)

If you are upgrading from Vertopal CLI 1.x, please review and apply the following changes to ensure a smooth transition:

1. **Reconfigure private credentials**
   - The configuration key for the application ID has changed from `api.appid` to `api.app`.
   - You must update your stored credentials; otherwise, the program will raise an `InvalidCredentialError` exception.
   - **New syntax (v2.0.0+):**

     ```bash
     vertopal config api.app "your-app-id" api.token "your-security-token"
     ```

   - **Old syntax (pre‑2.0.0):**

     ```bash
     vertopal config --app "your-app-id" --token "your-security-token"
     ```

2. **Note the new public default credential**
   - Vertopal CLI now ships with a built‑in, non‑authenticated credential (`app: free`, `token: FREE-TOKEN`) so you can start using it immediately after installation.
   - This credential is free but subject to daily rate limits. For production workloads, configure your private credentials as shown above.

For full details, see the **Breaking Changes** and **Added** sections below.

### 🚨 Removed (Breaking Changes)

- Dropped support for Python 3.7 and 3.8 — the package now requires Python 3.9 or later (see [`pyproject.toml`](pyproject.toml)).
- Removed support for legacy import/layout patterns; the project now uses the `src/` package layout as the canonical layout.
- Removed several legacy public symbols previously exported from the package root to provide a smaller, stable public surface (see [`vertopal/__init__.py`](src/vertopal/__init__.py)).
- Removed the top-level re-export of internal API classes. Consumers should import low-level clients directly from their modules (for example `vertopal.api.v1.API`).
- Removed several command-line flags from the `vertopal` command: `--app`, `--token`, `--overwrite`, and `--silent`.
- Configuration key changed — the application ID is now stored under the INI-style key `api.app` in the user configuration file (previously `api.appid`).
  Users upgrading from earlier versions **must** reconfigure their private credentials to continue using them.

  **New syntax (v2.0.0+):**

  ```bash
  vertopal config api.app "your-app-id" api.token "your-security-token"
  ```

  **Old syntax (pre‑2.0.0):**

  ```bash
  vertopal config --app "your-app-id" --token "your-security-token"
  ```

  The old flags are no longer supported. See also the new public default credential in the **Added** section.

### ✨ Added

- Improvements to the `vertopal` CLI (see `vertopal convert --help`):
  - Bulk conversion support: accept files, directories, globs and brace/range patterns (e.g. `{a,b}`, `{1..5}`, `**/*`).
  - Read from `stdin` by using `-` as an input source.
  - Write to `stdout` by passing `--output -`.
  - Accept a file list as input and override output filename or output directory per invocation.
  - Recursive directory traversal and exclude-by-pattern support.
  - Filter inputs by modification date using an ISO 8601 `--modified-since` filter.
- Added credential management to centralize application ID and security token handling (see [`vertopal/api/credential.py`](src/vertopal/api/credential.py)).
- Introduced a new `cli` subpackage and refactored command managers for clearer separation of concerns (see [`vertopal/cli`](src/vertopal/cli/)).
- Reworked the CLI entry point and argument parser for clearer help, subcommands, and argument validation (see [`vertopal/vertopal.py`](src/vertopal/vertopal.py)).
- Added `Readable` and `Writable` I/O protocols and three adapter modules: file, in-memory, and stdio for consistent I/O abstractions (see [`vertopal/io/protocols.py`](src/vertopal/io/protocols.py), and [`vertopal/io/__init__.py`](src/vertopal/io/__init__.py)).
- Added structured API response wrappers and richer helpers to the v1 client to simplify caller code ([vertopal/api/v1.py](src/vertopal/api/v1.py)).
- Added a centralized `settings` module, `enums`, `types`, and `Prism` terminal styling helper for consistency across the codebase (see [`vertopal/settings.py`](src/vertopal/settings.py), [`vertopal/enums.py`](src/vertopal/enums.py), [`vertopal/types.py`](src/vertopal/types.py), and [`vertopal.utils.prism`](src/vertopal/utils/prism.py)).
- Added a public default credential to simplify first-run experience: the CLI ships with a non-authenticated, limited credential (app: `free`, token: `FREE-TOKEN`) so users can try the service without creating an account. This credential is intended for personal testing and evaluation and is subject to daily rate limits; production workloads should configure a private credential in the user config.

### 🛠 Changed

- Moved terminal and CLI internals into the new `cli` subpackage; command registration and adapter responsibilities were reorganized into dedicated manager modules (see [`vertopal/cli`](src/vertopal/cli/)).
- Converted API client methods to return lightweight, structured response wrappers rather than raw dicts/tuples to improve ergonomics and error handling (see [`vertopal/api/v1.py`](src/vertopal/api/v1.py), and [`vertopal/utils/data_wrappers.py`](src/vertopal/utils/data_wrappers.py)).
- Stabilized packaging and metadata to the `src/` layout and modern build metadata (see [`pyproject.toml`](pyproject.toml), and [`setup.py`](setup.py)).
- Moved API exception types into the top-level `vertopal.exceptions` module and simplified exception usage across modules.
- Relocated the build helper into `tools/build.py` for clearer separation of tooling code.
- Reworked the configuration module to use a singleton `Config` and safer load/write semantics (see [`vertopal/utils/config.py`](src/vertopal/utils/config.py)).
- Redesigned `vertopal.api.v1.API` to be an instantiable client object rather than a module-level static; this enables per-instance configuration and better testability.
- Updated the `vertopal config` subcommand: the command's interface and behavior for modifying the user configuration file has been redesigned. It now exposes clearer interactive and non-interactive options, safer write semantics, and explicit flags for common keys (see `vertopal config --help`).

### 🐛 Fixed

- Fixed multiple resource leaks and inconsistent timeout usages in HTTP calls; timeouts are now applied uniformly for requests, uploads, and downloads.

## [1.1.0] - 2024-01-07

### ✨ Added

- Added optional `--beautify` flag to the `vertopal api` command for pretty-printing output.
- Introduced three new API methods:
  - `vertopal.api.v1.API.format_get()`
  - `vertopal.api.v1.API.convert_graph()`
  - `vertopal.api.v1.API.convert_formats()`

### 🐛 Fixed

- Updated package dependencies to use minimum versions for better compatibility.

## [1.0.6] - 2023-12-18

### 🐛 Fixed

- Built Windows binary using *PyInstaller 5.7.0* with a compiled bootloader to prevent false-positive antivirus alerts. ([#1])

## [1.0.5] - 2023-10-25

### ✨ Added

- `vertopal api` command for authenticated HTTP requests to the Vertopal API.

## [1.0.4] - 2023-10-10

### ✨ Added

- `Converter` class for easier file conversion.
- Custom exceptions for better error handling.

### 🛠 Changed

- Product names are now differentiated in User-Agent headers for CLI vs Python package.

### 🐛 Fixed

- Increased connection timeout for upload/download tasks.

## [1.0.3] - 2023-06-03

### ✨ Added

- `--app` and `--token` arguments to override app ID and security token.

### 🐛 Fixed

- Newline added to end of command output.

## [1.0.2] - 2023-03-28

### ✨ Added

- Custom User-Agent header in API requests.

### 🛠 Changed

- Removed trailing whitespace.
- Replaced string concatenation with Python f-strings.
- Set 30-second timeout on API requests.

### 🐛 Fixed

- Improved resource management using `with` statements.

## [1.0.1] - 2023-02-26

### ✨ Added

- `build.py` and a GitHub action to automate the creation and release of standalone binaries using PyInstaller.

### 🐛 Fixed

- Resolved minor issues and improved overall stability.

## Initial Release - 2023-02-10

- Initial release of Vertopal CLI
- Basic command-line interface
- Core conversion functionality
- API client implementation
- Configuration management

[Unreleased]: https://github.com/vertopal/vertopal-cli/compare/v2.0.3...HEAD
[2.0.3]: https://github.com/vertopal/vertopal-cli/releases/tag/v2.0.3
[2.0.2]: https://github.com/vertopal/vertopal-cli/releases/tag/v2.0.2
[2.0.1]: https://github.com/vertopal/vertopal-cli/releases/tag/v2.0.1
[2.0.0]: https://github.com/vertopal/vertopal-cli/releases/tag/v2.0.0
[1.1.0]: https://github.com/vertopal/vertopal-cli/releases/tag/v1.1.0
[1.0.6]: https://github.com/vertopal/vertopal-cli/releases/tag/v1.0.6
[1.0.5]: https://github.com/vertopal/vertopal-cli/releases/tag/v1.0.5
[1.0.4]: https://github.com/vertopal/vertopal-cli/releases/tag/v1.0.4
[1.0.3]: https://github.com/vertopal/vertopal-cli/releases/tag/v1.0.3
[1.0.2]: https://github.com/vertopal/vertopal-cli/releases/tag/v1.0.2
[1.0.1]: https://github.com/vertopal/vertopal-cli/releases/tag/v1.0.1
[#1]: https://github.com/vertopal/vertopal-cli/issues/1
