# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   Provides a live terminal dashboard that renders in place while
#   multiple file conversion tasks run concurrently. A background thread
#   handles redraws, while thread-safe methods update task state,
#   report errors, and produce a final static summary when complete.
#   All names in this module are internal (prefixed with an underscore)
#   and not part of the public API.

"""
Terminal dashboard for tracking multiple file conversion tasks.

This module provides a thread-safe, in-place dashboard
(`_HybridProgress`) that renders progress bars, recently completed items
and errors. It is color-aware (uses `Prism`) and uses ANSI escape codes
for cursor control. The dashboard is intended for CLI usage where
multiple concurrent file conversions must be reported to the user in a
compact and attractive way.

Example:

    >>> from vertopal.utils.dashboard_progress import (
    ...     _create_smart_progress,
    ...     _DashboardStyle,
    ... )
    >>> files = ["file-1.txt", "file-2.txt"]
    >>> progress = _create_smart_progress(
    ...     total_units=len(files),
    ...     max_concurrent=2,
    ...     filenames=files,           # optional
    ...     style=_DashboardStyle(),   # optional
    ... )
    >>> progress.start()
    >>> for i, f in enumerate(files, 1):
    ...     progress.update(i, 10, "Queued")
    ...     # ... do work ...
    ...     progress.update(i, 55, "Converting")
    ...     # ... do work ...
    ...     progress.update(i, 100, "Done")
    >>> # To report an error instead of completion:
    >>> # progress.add_error(task_id, "Error message...")
    >>> progress.stop()

Notes:
    - **Terminal assumptions:** Designed for TTYs that support ANSI
      escape codes; the UI relies on cursor movement, line erasure,
      and color sequences.
    - **Safety:** All public-facing methods that mutate state (`update`,
      `add_error`, `safe_print`) acquire an internal lock to prevent
      rendering artifacts.
    - **History limits:** The dashboard shows up to 3 recent completions
      and errors; older items don't affect change detection or layout.
"""

from dataclasses import dataclass
import re
import sys
import threading
import time
from typing import Dict, List, Optional, TextIO

from vertopal.enums import _ANSIEscapeCode, _ProgressUnitStateType
from vertopal.utils.misc import (
    _format_count_with_plural,
    _pluralize,
    _shorten_filename,
)
from vertopal.utils.prism import Prism

# No public names in this file
__all__ = []


@dataclass
class _DashboardStyle:
    """
    Styling configuration for the dashboard based on `Prism`.

    Attributes:
        header_style: Prism style used for the header text.
        stats_style: Prism style used for statistics line.
        label_style: Prism style used for section labels.
        progress_completed_style: Prism style used for
            completed portion of bars.
        progress_remaining_style: Prism style used for
            remaining portion of bars.
        completed_task_style: Prism style used for
            recently completed items.
        bar_width: Width of the overall progress bar.
        task_bar_width: Width of each per-task progress bar.
        dashboard_width: Total width used when rendering the dashboard.
    """

    header_style: str = "bold"
    stats_style: str = "cyan"
    label_style: str = ""
    progress_completed_style: str = "cyan"
    progress_remaining_style: str = "gray"
    completed_task_style: str = ""
    bar_width: int = 25
    task_bar_width: int = 15
    dashboard_width: int = 65


@dataclass
class _TaskInfo:
    """
    Information about a single conversion task.

    Attributes:
        task_id: Numeric identifier for the task.
        filename: Name of the file being converted.
        progress: Progress percentage (0-100).
        description: Short description of current step.
        state: `_ProgressUnitStateType` representing task state.
        start_time: Timestamp when the task started
            (seconds since epoch).
        end_time: Timestamp when the task ended (seconds since epoch).
        error_message: Optional error message when the task failed.
    """

    task_id: int
    filename: str
    progress: int = 0
    description: str = "Pending"
    state: _ProgressUnitStateType = _ProgressUnitStateType.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None

    @property
    def is_completed(self) -> bool:
        """True if the task has ended successfully."""
        return self.state == _ProgressUnitStateType.ENDED

    @property
    def is_running(self) -> bool:
        """True if the task is currently running."""
        return self.state == _ProgressUnitStateType.RUNNING

    @property
    def is_pending(self) -> bool:
        """True if the task is pending and has not started."""
        return self.state == _ProgressUnitStateType.PENDING

    @property
    def has_error(self) -> bool:
        """True if the task has an error message."""
        return self.error_message is not None

    @property
    def duration(self) -> Optional[float]:
        """Returns the duration in seconds if available."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class _HybridProgress:
    """
    Hybrid progress display: a live, in-place dashboard
    for multiple file conversions.

    This class manages a background rendering thread and exposes
    thread-safe update methods for reporting per-task progress, errors
    and final summary. Use `start()` to begin rendering and `stop()`
    to finish and print the final summary.
    """

    def __init__(
        self,
        total_files: int,
        max_concurrent: int = 2,
        filenames: Optional[List[str]] = None,
        style: Optional[_DashboardStyle] = None,
    ):
        """
        Initialize a `_HybridProgress` dashboard.

        Args:
            total_files (int): Total number of files to track.
            max_concurrent (int): Maximum number of concurrently active
                task lines to display. Defaults to `2`.
            filenames (Optional[List[str]]): Optional list of filenames
                to pre-populate tasks with.
            style (Optional[_DashboardStyle]): Optional `_DashboardStyle`
                instance to override presentation settings.
        """
        self.total_files = total_files
        self.max_concurrent = max_concurrent
        self.tasks: Dict[int, _TaskInfo] = {}
        self._completed_count = 0
        self._active_count = 0
        self._pending_count = total_files
        self._error_count = 0
        self.active_tasks: List[_TaskInfo] = []
        self.completed_tasks: List[_TaskInfo] = []
        self.error_tasks: List[_TaskInfo] = []

        # Overall process timing
        self._process_start_time: Optional[float] = None
        self._process_end_time: Optional[float] = None

        # Style configuration
        self.style = style or _DashboardStyle()

        # Display settings
        self.refresh_rate = 0.5  # Update every 500ms
        self.display_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.display_thread = threading.Thread(
            target=self._display_loop,
            daemon=True,
        )
        self.is_first_render = True
        # Tracks how many lines the last dashboard used
        self._last_total_lines = 0

        # Track changes to avoid unnecessary renders
        self._last_render_state = None
        self._needs_render = True

        # Initialize tasks with actual filenames or defaults
        for i in range(1, total_files + 1):
            if filenames and i <= len(filenames):
                filename = filenames[i - 1]
            else:
                filename = f"file-{i}"
            self.tasks[i] = _TaskInfo(task_id=i, filename=filename)

    def update(self, task_id: int, progress: int, description: str) -> None:
        """
        Thread-safe update of a task's progress.

        Args:
            task_id (int): Identifier of the task to update.
            progress (int): Progress percentage (0-100).
            description (str): Short description of the current step.
        """
        with self.display_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]

                # Update task info
                task.progress = progress
                task.description = description

                # Handle state transitions
                if (
                    0 < progress < 100
                    and task.state == _ProgressUnitStateType.PENDING
                ):
                    task.state = _ProgressUnitStateType.RUNNING
                    task.start_time = time.time()

                    # Start overall process timing when first file begins
                    if self._process_start_time is None:
                        self._process_start_time = time.time()

                if (
                    progress >= 100
                    and task.state == _ProgressUnitStateType.RUNNING
                ):
                    task.state = _ProgressUnitStateType.ENDED
                    task.end_time = time.time()
                    task.progress = 100

                    # End overall process timing when last file completes
                    if self._completed_count + 1 == self.total_files:
                        self._process_end_time = time.time()

                # Update counts and lists
                self._update_counts()

                # Mark that a render is needed
                self._needs_render = True

    def add_error(self, task_id: int, error_message: str) -> None:
        """
        Thread-safe mark a task as errored and attach an error message.

        Args:
            task_id (int): Identifier of the task to mark as failed.
            error_message (str): Human-readable error message.
        """
        with self.display_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.error_message = error_message
                task.state = _ProgressUnitStateType.ENDED
                task.end_time = time.time()

                # Update counts and lists
                self._update_counts()

                # Mark that a render is needed
                self._needs_render = True

    def start(self) -> None:
        """
        Start the progress dashboard rendering thread
        and hide the cursor.
        """
        self._hide_cursor()
        self.display_thread.start()

    def stop(self) -> None:
        """
        Stop the dashboard rendering thread, restore the cursor
        and print the final summary.
        """
        self.stop_event.set()
        if self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        self._show_cursor()
        self._render_final_summary()

    def safe_print(self, message: str, file: TextIO = sys.stdout) -> None:
        """
        Print a message above the dashboard without corrupting the
        in-place rendering.

        Args:
            message (str): Message text to print.
            file (TextIO): File-like object to write the message to.
                Defaults to `sys.stdout`.
        """
        with self.display_lock:
            # Total lines for the dashboard (use last rendered count)
            total_lines = self._last_total_lines or 12

            # Move cursor up to clear the dashboard area
            _ANSIEscapeCode.CURSOR_PREV_LINE_N.write(n=total_lines)

            # Clear each line of the dashboard
            for _ in range(total_lines):
                _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
                print()  # Move to next line

            # Move cursor back up
            _ANSIEscapeCode.CURSOR_PREV_LINE_N.write(n=total_lines)
            sys.stdout.flush()

            # Print the message (this will appear above the dashboard)
            print(message, file=file)

            # Re-render the dashboard below the message
            percentage = (
                int((self._completed_count / self.total_files) * 100)
                if self.total_files > 0
                else 0
            )
            progress_bar = self._get_progress_bar(percentage)
            dashboard_width = self.style.dashboard_width
            self._update_dashboard_inplace(
                dashboard_width,
                progress_bar,
                percentage,
            )
            # Update last_total_lines after re-render
            recent_completed = (
                self.completed_tasks[-3:]
                if len(self.completed_tasks) > 3
                else self.completed_tasks
            )
            len_recent_completed = len(recent_completed)

            recent_errors = (
                self.error_tasks[-3:]
                if len(self.error_tasks) > 3
                else self.error_tasks
            )
            len_recent_errors = len(recent_errors)

            base_lines = 9
            total_lines = (
                base_lines + self.max_concurrent
                + (1 + len_recent_completed if len_recent_completed else 1)
            )

            # Add error section if there are errors
            if len_recent_errors:
                total_lines += 2 + len_recent_errors

            self._last_total_lines = total_lines

    def _update_counts(self) -> None:
        """
        Recompute cached counts and task lists
        (active, completed, error).
        """
        # Count completed tasks (excluding error tasks)
        self._completed_count = sum(
            1 for task in self.tasks.values()
            if task.is_completed and not task.has_error
        )
        self._active_count = sum(
            1 for task in self.tasks.values() if task.is_running
        )
        self._error_count = sum(
            1 for task in self.tasks.values() if task.has_error
        )
        self._pending_count = (
            self.total_files
            - self._completed_count
            - self._active_count
            - self._error_count
        )

        # Update active tasks list (only running tasks)
        self.active_tasks = [
            task for task in self.tasks.values() if task.is_running
        ]
        self.active_tasks.sort(key=lambda t: t.task_id)

        # Update completed tasks list (only successful completions)
        self.completed_tasks = [
            task for task in self.tasks.values()
            if task.is_completed and not task.has_error
        ]
        self.completed_tasks.sort(key=lambda t: t.task_id)

        # Update error tasks list
        self.error_tasks = [
            task for task in self.tasks.values() if task.has_error
        ]
        self.error_tasks.sort(key=lambda t: t.task_id)

    def _has_state_changed(self) -> bool:
        """
        Determine whether the visible dashboard state differs
        from the last rendered snapshot.

        Returns:
            bool: `True` if the state has changed and a render is required,
            otherwise `False`.
        """
        current_state = (
            self._completed_count,
            self._active_count,
            self._pending_count,
            self._error_count,
            [
                (t.task_id, t.progress, t.description)
                for t in self.active_tasks
            ],
            [
                (t.task_id, t.duration)
                for t in self.completed_tasks[-3:]
            ],
            [
                (t.task_id, t.error_message)
                for t in self.error_tasks[-3:]
            ],
        )

        if self._last_render_state != current_state:
            self._last_render_state = current_state
            return True
        return False

    def _hide_cursor(self) -> None:
        """Hide the terminal cursor using an ANSI escape sequence."""
        _ANSIEscapeCode.CURSOR_INVISIBLE.write()
        sys.stdout.flush()

    def _show_cursor(self) -> None:
        """Show the terminal cursor using an ANSI escape sequence."""
        _ANSIEscapeCode.CURSOR_VISIBLE.write()
        sys.stdout.flush()

    def _get_progress_bar(
        self,
        percentage: int,
        width: Optional[int] = None,
    ) -> str:
        """
        Generate a colored progress bar string for a given percentage.

        Args:
            percentage (int): Completion percentage in the range 0-100.
            width (Optional[int]): Optional width of the bar
                (overrides configured `bar_width`).

        Returns:
            str: A string containing the colored progress bar.
        """
        if width is None:
            width = self.style.bar_width
        filled = int((percentage / 100) * width)
        filled_part = "━" * filled
        remaining_part = "┈" * (width - filled)
        # Apply colors via Prism
        filled_colored = Prism.get_text(
            filled_part,
            style=self.style.progress_completed_style,
        )
        remaining_colored = Prism.get_text(
            remaining_part,
            style=self.style.progress_remaining_style,
        )
        return filled_colored + remaining_colored

    _ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

    def _pad_visible(
        self,
        text: str,
        width: int,
        align: str = "center",
    ) -> str:
        """
        Pad `text` to a visible `width`, treating ANSI color sequences
        as zero-width.

        Args:
            text (str): Text that may contain ANSI color sequences.
            width (int): Desired visible width.
            align (str): Alignment mode
                (`"center"`, `"left"`, or `"right"`).

        Returns:
            str: The padded string, with original ANSI sequences
            preserved.
        """
        visible_len = len(self._ANSI_RE.sub("", text))
        if visible_len >= width:
            return text
        pad = width - visible_len
        if align == "center":
            left = pad // 2
            right = pad - left
            return " " * left + text + " " * right
        if align == "left":
            return text + " " * pad
        if align == "right":
            return " " * pad + text
        return text + " " * pad

    def _truncate_filename(
        self,
        filename: str,
        max_length: int = 25,
    ) -> str:
        """
        Truncate `filename` to `max_length` characters using `...`
        when needed.

        Args:
            filename (str): The filename to truncate.
            max_length (int): Maximum allowed visible length.
                Defaults to `25`.

        Returns:
            str: The possibly truncated filename.
        """
        return _shorten_filename(filename, max_length, "...")

    def _truncate_description(
        self,
        description: str,
        max_length: int = 13,
    ) -> str:
        """
        Truncate `description` to `max_length` visible characters,
        stripping ANSI sequences for length calculation but preserving
        them in the returned snippet where possible.

        Args:
            description (str): The description text which may contain
                ANSI codes.
            max_length (int): Maximum allowed visible length.
                Defaults to `13`.

        Returns:
            str: The truncated description string.
        """
        # Calculate visible length (without ANSI codes)
        visible_len = len(self._ANSI_RE.sub("", description))

        if visible_len <= max_length:
            return description

        # For simplicity, just truncate the visible text and add "..."
        # This handles the case where ANSI codes make the string
        # longer than expected
        clean_text = self._ANSI_RE.sub("", description)
        return clean_text[:max_length-3] + "..."

    def _format_duration(self, seconds: float) -> str:
        """
        Convert a duration in seconds to a human-friendly string using
        seconds/minutes/hours as appropriate.

        Args:
            seconds (float): Duration in seconds.

        Returns:
            str: A short human-readable string like `"5s"`, `"2m 3s"`,
            or `"1h"`.
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        if seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            if remaining_seconds == 0:
                return f"{minutes}m"
            else:
                return f"{minutes}m {remaining_seconds}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            remaining_seconds = int(seconds % 60)
            if remaining_minutes == 0 and remaining_seconds == 0:
                return f"{hours}h"
            if remaining_seconds == 0:
                return f"{hours}h {remaining_minutes}m"
            return f"{hours}h {remaining_minutes}m {remaining_seconds}s"

    def _render_dashboard(self) -> None:
        """Render (or re-render) the entire dashboard in-place."""
        percentage = (
            int((self._completed_count / self.total_files) * 100)
            if self.total_files > 0
            else 0
        )
        progress_bar = self._get_progress_bar(percentage)

        # Calculate proper spacing for alignment
        dashboard_width = self.style.dashboard_width

        # Determine how many lines the dashboard will occupy dynamically
        recent_completed = (
            self.completed_tasks[-3:]
            if len(self.completed_tasks) > 3
            else self.completed_tasks
        )
        len_recent_completed = len(recent_completed)

        recent_errors = (
            self.error_tasks[-3:]
            if len(self.error_tasks) > 3
            else self.error_tasks
        )
        len_recent_errors = len(recent_errors)

        # Base lines (top, header, 2 separators, stats, progress, labels, bottom)
        # top + header + sep + stats + progress + sep + label + sep + bottom
        base_lines = 9
        # add active task lines
        total_lines_current = base_lines + self.max_concurrent
        if len_recent_completed:
            # "Recently Completed" label + items
            total_lines_current += 1 + len_recent_completed
        else:
            total_lines_current += 1  # "No completed tasks yet..." line

        # Add error section if there are errors
        if len_recent_errors:
            # separator + "Errors:" label + error items
            # separator + "Errors:" label + error items
            total_lines_current += 2 + len_recent_errors

        if not self.is_first_render:
            # Move cursor up to the start of the previous dashboard
            _ANSIEscapeCode.CURSOR_PREV_LINE_N.write(n=self._last_total_lines)

        # Render (or re-render) the dashboard in place
        self._update_dashboard_inplace(
            dashboard_width,
            progress_bar,
            percentage,
        )

        sys.stdout.flush()
        self.is_first_render = False
        # Store the number of lines we just rendered
        # to correctly clear on next update
        self._last_total_lines = total_lines_current

    def _update_dashboard_inplace(
        self,
        dashboard_width: int,
        progress_bar: str,
        percentage: int,
    ) -> None:
        """
        Draw all dashboard rows using `sys.stdout.write` so the output
        can be updated in-place without scrolling.

        Args:
            dashboard_width (int): Total width reserved for the
                dashboard box.
            progress_bar (str): Pre-rendered progress bar string for
                overall progress.
            percentage (int): Overall completion percentage (0-100).
        """
        # Top border
        _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
        sys.stdout.write("┌" + "─" * (dashboard_width - 2) + "┐\n")

        # Header
        _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
        header = "Vertopal CLI - File Conversion Dashboard".center(
            dashboard_width - 2
        )
        header = Prism.get_text(header, style=self.style.header_style)
        sys.stdout.write("│" + header + "│\n")

        # Separator
        _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
        sys.stdout.write("├" + "─" * (dashboard_width - 2) + "┤\n")

        # Statistics line
        _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
        stats_line = (
            f"Total: {self.total_files:2d} │ "
            f"Completed: {self._completed_count:2d} │ "
            f"Active: {self._active_count:2d} │ "
            f"Pending: {self._pending_count:2d} │ "
            f"Failed: {self._error_count:2d}"
        )
        # Check if the line fits, if not make it more compact
        if len(stats_line) > dashboard_width - 2:
            stats_line = (
                f"Total: {self.total_files:2d} │ "
                f"Done: {self._completed_count:2d} │ "
                f"Active: {self._active_count:2d} │ "
                f"Pending: {self._pending_count:2d} │ "
                f"Failed: {self._error_count:2d}"
            )
        stats_colored = Prism.get_text(
            stats_line.center(dashboard_width - 2),
            style=self.style.stats_style,
        )
        sys.stdout.write("│" + stats_colored + "│\n")

        # Progress line
        _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
        progress_line = f"Overall Progress: {progress_bar} {percentage:3d}%"
        progress_padded = self._pad_visible(
            progress_line,
            dashboard_width - 2,
            "center",
        )
        sys.stdout.write("│" + progress_padded + "│\n")

        # Separator
        _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
        sys.stdout.write("├" + "─" * (dashboard_width - 2) + "┤\n")

        # Currently Converting section
        _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
        label_curr = Prism.get_text(
            "Currently Converting:".center(dashboard_width - 2),
            style=self.style.label_style,
        )
        sys.stdout.write("│" + label_curr + "│\n")

        # Show active tasks (up to max_concurrent)
        for i in range(self.max_concurrent):
            _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
            if i < len(self.active_tasks):
                task = self.active_tasks[i]
                filename = self._truncate_filename(task.filename, 20)
                small_bar = self._get_progress_bar(
                    task.progress,
                    width=self.style.task_bar_width,
                )
                description = self._truncate_description(task.description, 13)
                task_line = (
                    f"▸ {filename:<20} {small_bar} "
                    f"{task.progress:3d}% - {description:<13}"
                )
                task_padded = self._pad_visible(
                    task_line,
                    dashboard_width - 2,
                    "left",
                )
                sys.stdout.write("│" + task_padded + "│\n")
            else:
                sys.stdout.write("│" + " " * (dashboard_width - 2) + "│\n")

        # Separator
        _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
        sys.stdout.write("├" + "─" * (dashboard_width - 2) + "┤\n")

        # Show recent completed tasks
        recent_completed = (
            self.completed_tasks[-3:]
            if len(self.completed_tasks) > 3
            else self.completed_tasks
        )
        if recent_completed:
            _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
            label_recent = Prism.get_text(
                "Recently Completed:".center(dashboard_width - 2),
                style=self.style.label_style,
            )
            sys.stdout.write("│" + label_recent + "│\n")
            for task in recent_completed:
                _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
                filename = self._truncate_filename(
                    task.filename,
                    30,  # Increased from 20 to 30
                )
                duration = self._format_duration(task.duration or 0)
                raw_completed_line = (
                    # Added parentheses around duration
                    f"✓ {filename:<30} ({duration})"
                )
                completed_line = Prism.get_text(
                    raw_completed_line,
                    style=self.style.completed_task_style,
                )
                comp_padded = self._pad_visible(
                    completed_line,
                    dashboard_width - 2,
                    "center",
                )
                sys.stdout.write("│" + comp_padded + "│\n")
        else:
            _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
            no_line = Prism.get_text(
                "No completed tasks yet...".center(dashboard_width - 2),
                style=self.style.label_style,
            )
            sys.stdout.write("│" + no_line + "│\n")

        # Show recent error tasks (if any)
        recent_errors = (
            self.error_tasks[-3:]
            if len(self.error_tasks) > 3
            else self.error_tasks
        )
        if recent_errors:
            # Separator
            _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
            sys.stdout.write("├" + "─" * (dashboard_width - 2) + "┤\n")

            # Errors label
            _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
            label_errors = Prism.get_text(
                "Errors:".center(dashboard_width - 2),
                style=self.style.label_style,
            )
            sys.stdout.write("│" + label_errors + "│\n")

                        # Show error tasks
            for task in recent_errors:
                _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
                filename_width = 12  # Space reserved for filename
                filename = self._truncate_filename(
                    task.filename,
                    filename_width,
                )
                prefix = f"✗ {filename:<{filename_width}} - "
                visible_prefix_len = len(self._ANSI_RE.sub("", prefix))

                full_msg = task.error_message or "Unknown error"
                max_visible_width = dashboard_width - 2  # inside borders
                available_space = max_visible_width - visible_prefix_len

                # Truncate message to fit exactly in available space
                if len(full_msg) > available_space:
                    full_msg = full_msg[:available_space - 3] + "..."

                # Create the final line
                raw_error_line = prefix + full_msg

                # No ANSI color codes for error section
                # to avoid length calculation issues
                sys.stdout.write("│" + raw_error_line + "│\n")

        # Bottom border
        _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
        sys.stdout.write("└" + "─" * (dashboard_width - 2) + "┘\n")

    def _render_final_summary(self) -> None:
        """
        Render a final, static summary replacing the in-place dashboard
        when the progress is stopped.
        """
        # Calculate total lines for the dashboard
        total_lines = self._last_total_lines or 12

        # Move cursor up to clear the dashboard area
        _ANSIEscapeCode.CURSOR_PREV_LINE_N.write(n=total_lines)

        # Clear each line of the dashboard
        for _ in range(total_lines):
            _ANSIEscapeCode.CURSOR_ERASE_LINE.write()
            print()  # Move to next line

        # Move cursor back up
        _ANSIEscapeCode.CURSOR_PREV_LINE_N.write(n=total_lines)
        sys.stdout.flush()

        # Calculate proper spacing for alignment
        dashboard_width = self.style.dashboard_width

        print("┌" + "─" * (dashboard_width - 2) + "┐")
        print("│" + "Conversion Complete!".center(dashboard_width - 2) + "│")
        print("├" + "─" * (dashboard_width - 2) + "┤")

        # Handle different scenarios for summary line
        if self._completed_count == 0 and self._error_count == 0:
            summary_line = (
                f"No files were converted "
                f"({_format_count_with_plural(self.total_files, 'file')} "
                "processed)"
            )
        elif self._completed_count == self.total_files:
            summary_line = (
                f"Successfully converted "
                f"{_format_count_with_plural(self._completed_count, 'file')}/"
                f"{self.total_files}"
            )
        elif self._error_count == self.total_files:
            summary_line = (
                f"All {_format_count_with_plural(self.total_files, 'file')} "
                f"failed to convert"
            )
        else:
            summary_line = (
                f"Partially completed: "
                f"{_format_count_with_plural(self._completed_count, 'file')}/"
                f"{self.total_files}"
            )
        print("│" + summary_line.center(dashboard_width - 2) + "│")

        # Add error summary if there are errors
        if self._error_count > 0:
            error_summary = (
                "Failed: "
                f"{_format_count_with_plural(self._error_count, 'file')} "
                f"failed to convert"
            )
            print("│" + error_summary.center(dashboard_width - 2) + "│")

        if (self.completed_tasks
            and self._process_start_time
            and self._process_end_time):
            # Calculate wall clock time for concurrent processing
            total_wall_time = self._process_end_time - self._process_start_time
            avg_wall_time = (
                total_wall_time / len(self.completed_tasks)
                if self.completed_tasks
                else 0
            )

            total_time_str = self._format_duration(total_wall_time)
            avg_time_str = self._format_duration(avg_wall_time)

            time_line = (
                f"Total time: {total_time_str} | "
                f"Average: {avg_time_str} per {_pluralize(1, 'file')}"
            )
            print("│" + time_line.center(dashboard_width - 2) + "│")

        print("└" + "─" * (dashboard_width - 2) + "┘")

    def _display_loop(self) -> None:
        """
        Internal rendering loop that runs in a background thread.
        The loop periodically checks for state changes and triggers
        re-renders.
        """
        while not self.stop_event.is_set():
            with self.display_lock:
                # Always render on first run or when changes are detected
                if self.is_first_render or self._needs_render:
                    if self._has_state_changed() or self.is_first_render:
                        self._render_dashboard()
                        self._needs_render = False

            # Wait for next update
            if self.stop_event.wait(self.refresh_rate):
                break


# Convenience function for easy usage
def _create_smart_progress(
    total_units: int,
    **config_kwargs,
) -> _HybridProgress:
    """
    Create a configured `_HybridProgress` instance.

    Args:
        total_units: Number of units (files) to track.
        config_kwargs: Optional settings (`max_concurrent`, `filenames`,
            `style`).

    Returns:
        _HybridProgress: A configured `_HybridProgress` instance.
    """
    max_concurrent = config_kwargs.get("max_concurrent", 2)
    filenames = config_kwargs.get("filenames", None)
    style: Optional[_DashboardStyle] = config_kwargs.get("style", None)
    return _HybridProgress(
        total_units,
        max_concurrent,
        filenames,
        style,
    )
