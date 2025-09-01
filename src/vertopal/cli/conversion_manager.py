# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Orchestrates high-level file conversions using the Converter API client.
#   Coordinates input expansion, task scheduling, progress reporting, and
#   graceful shutdown. Includes dataclasses for IO descriptors and an
#   internal _ConversionTask for per-file conversion flow.

"""
High-level conversion manager orchestrating file conversions using the
`Converter` API client. This module coordinates input expansion, task
scheduling, and progress reporting to the `_HybridProgress` dashboard.

The implementation contains convenience dataclasses for IO descriptors
and an internal `_ConversionTask` that performs the per-file conversion
flow.
"""

from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
import signal
import threading
from time import sleep
from typing import List, Literal, Optional, Tuple

from vertopal import settings
from vertopal.api.converter import Converter, _Conversion
import vertopal.exceptions as vex
from vertopal.io.adapters.file import FileInput, FileOutput
from vertopal.io.adapters.stdio import PipeInput, PipeOutput
from vertopal.io.protocols import Readable, Writable
from vertopal.types import PathType
from vertopal.utils.dashboard_progress import _create_smart_progress
from vertopal.utils.misc import (
    _enhanced_expand_inputs,
    _get_extension,
    _remove_duplicates_preserve_order,
)

# No public names in this file
__all__ = []


class _ConversionManager:
    """
    High-level manager for orchestrating file conversions using the
    Converter API client.

    Coordinates input expansion, task scheduling, progress reporting,
    and graceful shutdown.
    """
    def __init__(self):
        # This event will signal a shutdown when set.
        self._shutdown_event = threading.Event()
        self._converter = Converter()
        self._progress = None

    @classmethod
    def setup_signal_handlers(cls, instance: "_ConversionManager") -> None:
        """
        Register SIGINT and SIGTERM handlers to trigger graceful
        shutdown on the given instance.

        Args:
            instance (_ConversionManager): Instance to signal for
                shutdown.
        """
        def sigint_handler(_sig, _frame):
            # print("CTRL+C received. Initiating graceful shutdown...")
            instance.initiate_shutdown()
        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)

    def initiate_shutdown(self) -> None:
        """
        Signal shutdown, stop progress display, and close converter
        connection.
        """
        self._shutdown_event.set()
        self._converter.close()

    def convert(self, args: Namespace) -> None:
        """
        Perform file conversion based on parsed command-line arguments.

        Args:
            args (Namespace): Parsed command-line arguments.
        """
        input_files = args.input if args.input else []
        file_list_path = args.file_list
        input_format = args.input_format
        output_format = args.output_format
        output = args.output
        recursive = args.recursive
        exclude_patterns = args.exclude
        modified_since = args.modified_since
        # overwrite = args.overwrite
        # silent = args.silent

        # Validate stdin input
        if "-" in input_files:
            if not input_format:
                print(
                    "Error: "
                    "'--from' is required when reading from stdin ('-')."
                )
                return
            self._convert_from_stdin(
                input_format,
                output_format,
                output=output,
            )
            return

        # Process file list input
        if file_list_path:
            input_files.extend(self._read_file_list(file_list_path))

        # Expand wildcards and directories
        expanded_files = self._expand_inputs(
            input_files, recursive, exclude_patterns, modified_since
        )

        # Eliminate duplicates
        expanded_files = _remove_duplicates_preserve_order(expanded_files)

        # Perform conversions for disk-based files
        self._convert_files(
            expanded_files,
            input_format,
            output_format,
            # overwrite,
            # silent,
        )

    def _convert_from_stdin(
        self,
        input_format: str,
        output_format: str,
        *,
        output: Optional[PathType] = None,
    ) -> None:
        """
        Handle conversion from stdin.

        Args:
            input_format (str): Format of the input data.
            output_format (str): Desired output format.
            output (Optional[PathType]): Output filename or path, or
                '-' for stdout. Defaults to `None`.
        """
        readable: Readable = PipeInput(filename=f"pipe.{input_format}")
        writable: Writable

        if output:
            if output == "-":
                writable = PipeOutput()
            else:
                writable = FileOutput(path=output)
        else:
            writable = FileOutput(path=f"output.{output_format}")

        try:
            converter = Converter()
            conversion = converter.convert(
                readable=readable,
                writable=writable,
                output_format=output_format,
                input_format=input_format,
            )
            conversion.wait()
            if conversion.successful():
                conversion.download()
            else:
                print("Conversion from stdin failed.")
        except vex.APIError as e:
            error_message = str(e)
            print(error_message)

    def _read_file_list(self, file_list_path: str) -> List[str]:
        """
        Read file paths from a file list.

        Args:
            file_list_path (str): Path to the file containing file
                paths.

        Returns:
            List[str]: List of file paths.
        """
        try:
            with open(file_list_path, "r", encoding="utf-8") as file:
                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print(f"Error: File list '{file_list_path}' not found.")
            return []

    def _expand_inputs(
        self,
        inputs: List[str],
        recursive: bool,
        exclude_patterns: Optional[List[str]],
        modified_since: Optional[str],
    ) -> List[str]:
        """
        Expand wildcard patterns and traverse directories based on
        options.

        Args:
            inputs (List[str]): List of input files, directories, or
                patterns.
            recursive (bool): Whether to enable recursive directory
                search.
            exclude_patterns (Optional[List[str]]): Patterns to
                exclude.
            modified_since (Optional[str]): Date filter for
                modification (YYYY-MM-DD).

        Returns:
            List[str]: Expanded list of file paths.
        """
        # Use enhanced input expansion
        expanded_paths = _enhanced_expand_inputs(
            inputs,
            recursive,
            exclude_patterns,
            modified_since,
        )

        # Convert Path objects back to strings for compatibility
        return [str(path) for path in expanded_paths]

    def _convert_files(
        self,
        files: List[str],
        input_format: Optional[str],
        output_format: str,
        # overwrite: bool,
        # silent: bool,
    ) -> None:
        """
        Convert files based on input format and output format.

        Args:
            files (List[str]): List of files to convert.
            input_format (Optional[str]): Source file format[-type].
            output_format (str): Target file format[-type].
        """
        if not files:
            print("No files found.")
            return

        total_tasks: int = len(files)
        max_concurrent: int = settings.MAX_CONCURRENT_CONVERSIONS

        # Create dashboard progress manager
        self._progress = _create_smart_progress(
            total_tasks,
            max_concurrent=max_concurrent,
            filenames=[Path(file_path).name for file_path in files],
        )

        self._progress.start()

        task_futures = []

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            for index, file_path in enumerate(files, start=1):
                output_file = str(
                    Path(file_path).with_suffix(
                        f".{_get_extension(output_format)}"
                    )
                )
                future = executor.submit(
                    self._new_task,
                    index,
                    file_path,
                    input_format,
                    output_file,
                    output_format,
                )
                task_futures.append(future)

            while not all(f.done() for f in task_futures):
                sleep(0.1)

        self._progress.stop()
        self._converter.close()

    def _new_task(
        self,
        task_id: int,
        input_file: str,
        input_format: Optional[str],
        output_file: str,
        output_format: str,
    ) -> None:
        """
        Create and run a new conversion task for a single file.

        Args:
            task_id (int): Task identifier.
            input_file (str): Path to input file.
            input_format (Optional[str]): Input file format.
            output_file (str): Path to output file.
            output_format (str): Output file format.
        """
        task = _ConversionTask(
            task_id=task_id,
            io_files=_IOSpec(
                input_path=input_file,
                input_format=input_format,
                output_path=output_file,
                output_format=output_format,
            ),
            converter=self._converter,
            progress=self._progress,
            shutdown_event=self._shutdown_event,
        )
        task.run()


@dataclass(frozen=True)
class _IOSpec:
    """Holding specifications of an input/output file pair."""
    input_path: PathType
    output_path: PathType
    input_format: Optional[str]
    output_format: str

    @property
    def input_filename(self) -> str:
        """Return the input file name."""
        return Path(self.input_path).name

    @property
    def output_filename(self) -> str:
        """Return the output file name."""
        return Path(self.output_path).name


class _ConversionTask:
    """
    Represents a single file conversion task, handling execution,
    error reporting, and progress updates.
    """

    def __init__(
        self,
        task_id: int,
        io_files: _IOSpec,
        converter: Converter,
        progress,
        shutdown_event: threading.Event,
    ):
        """
        Initialize a conversion task.

        Args:
            task_id (int): Task identifier.
            io_files (_IOSpec): Specification for input/output files.
            converter (Converter): Converter API client.
            progress: Progress dashboard manager.
            shutdown_event (threading.Event): Event to signal
                shutdown.
        """
        self._id = task_id
        self._io_files = io_files
        self._converter = converter
        self._progress = progress
        self._shutdown_event = shutdown_event
        self._current_progress: int = 0

    def run(self):
        """
        Execute the conversion task, handling all major error types
        and reporting to the dashboard.
        """
        try:
            self._run_task()
        except (IOError, OSError) as e:
            self._progress.add_error(self._id, f"File operation error: {e}")
        except vex.NetworkConnectionError as e:
            self._progress.add_error(self._id, f"Network error: {e}")
        except vex.InputNotFoundError as e:
            self._progress.add_error(self._id, str(e))
        except vex.APIError as e:
            error_text = str(e)
            # Pass the full error message to the progress manager;
            # and it will handle any wrapping.
            self._progress.add_error(self._id, error_text)
        # Final fallback for errors
        # pylint: disable=broad-except
        # noqa: B902
        except Exception as e:
            self._progress.add_error(self._id, f"Unexpected error: {e}")

    def _run_task(self):
        """
        Main logic for running the conversion task, including upload,
        queue, conversion, and download steps.
        """
        if self._abort_requested():
            return

        readable: Readable = FileInput(self._io_files.input_path)
        writable: Writable = FileOutput(self._io_files.output_path)

        self._update_progress("Uploading", 5)  # Progression: 5%
        conversion = self._converter.convert(
            readable=readable,
            writable=writable,
            output_format=self._io_files.output_format,
            input_format=self._io_files.input_format,
        )
        self._update_progress("Queued", 5)  # Progression: 10%

        # Sleep and check if shutdown is triggered
        if self._abort_requested(wait=1):
            return

        self._update_progress("Converting...", 5)  # Progression: 15%

        # Wait for the conversion to complete. If a shutdown is triggered,
        # the method will return `True` immediately
        # and we abort the conversion task.
        if self._wait(conversion): # Progression: up to 60%
            return

        if conversion.successful():
            self._update_progress("Downloading", percentage=80)
            conversion.download()

            if self._abort_requested(wait=1):
                return

            self._update_progress("Download complete", 10)  # Progression: 90%

            if self._abort_requested(wait=1):
                return

            # Progression: 100%
            self._update_progress("completed", 10)
        else:
            self._update_progress("Conversion failed", percentage=100)

    def _wait(
        self,
        conversion: _Conversion,
        timeout_pattern: Tuple[int, ...] = settings.SLEEP_PATTERN,
    ) -> bool:
        """
        Block until the internal shutdown event flag is set or
        conversion completes.

        Args:
            conversion (_Conversion): The conversion instance.
            timeout_pattern (Tuple[int, ...]): Sequence of timeout
                durations (in seconds) for retries. Defaults to
                `settings.SLEEP_PATTERN`.

        Returns:
            bool: `True` if shutdown event is set, `False` if conversion
            completes.
        """
        sleep_step = 0

        while not conversion.done():
            # Instead of sleeping unconditionally for a number of seconds,
            # wait on the shutdown event with a timeout.
            if self._shutdown_event.wait(timeout_pattern[sleep_step]):
                self._abort_requested()
                return True

            if sleep_step < len(timeout_pattern) - 1:
                sleep_step += 1

            # Increase progress until conversion completes.
            advance_progress: int = min(self._current_progress + 5, 60)
            self._update_progress("Converting...", advance_progress)

        return False

    def _update_progress(
        self,
        description: str,
        advance: int = 0,
        percentage: Optional[int] = None,
    ):
        """
        Update the progress bar and description for the current task.

        Args:
            description (str): Progress description.
            advance (int): Amount to advance progress (default 0).
            percentage (Optional[int]): Set progress to this percentage
                if provided.
        """
        if percentage is None:
            new_progress: int = self._current_progress + advance
            self._current_progress = min(abs(new_progress), 100)
        else:
            self._current_progress = min(abs(percentage), 100)

        self._progress.update(
            task_id=self._id,
            progress=self._current_progress,
            description=description,
        )

    def _abort_requested(self, wait: Optional[float] = None):
        """
        Check if shutdown event is set, optionally waiting for a given
        time.

        Args:
            wait (Optional[float]): Time in seconds to wait for
                shutdown event.

        Returns:
            bool: `True` if abort requested, `False` otherwise.
        """
        def abort() -> Literal[True]:
            self._update_progress("Aborted")
            return True

        if wait:
            if self._shutdown_event.wait(timeout=wait):
                return abort()
        if self._shutdown_event.is_set():
            return abort()

        return False
