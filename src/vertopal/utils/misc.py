# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023–2025 Vertopal - https://www.vertopal.com
# Repository: https://github.com/vertopal/vertopal-cli
# Issues: https://github.com/vertopal/vertopal-cli/issues
#
# Description:
#   The helpers include format canonicalization, filename shortening,
#   pluralization and count formatting, brace and bracket pattern expansion
#   for advanced glob-like matching, and inclusion/exclusion checks for
#   file discovery. These utilities centralize common behaviors so other
#   modules can rely on a single consistent implementation.

"""
Small, reusable miscellaneous helpers used across Vertopal.

This module contains a collection of private utility functions for
filename and format handling, pattern expansion, list manipulation,
and input expansion used by the CLI and internal utilities. Functions
are intentionally private (prefixed with `_`) and designed to be
deterministic and side-effect free where possible.
"""

from datetime import datetime
import fnmatch
from pathlib import Path
import re
from typing import Any, List, Optional

# No public names in this file
__all__ = []


def _get_extension(format_string: str) -> str:
    """
    Extracts the extension part of a format string in the 
    `extension[-type]` format.

    The `format_string` consists of an extension followed by an 
    optional type, separated by a hyphen (`-`). This function returns 
    only the extension portion of the string.

    Args:
        format_string (str): A string in the format `extension[-type]`.

    Returns:
        str: The extracted extension portion of the input string.

    Example:

        >>> get_extension("txt")
        'txt'
        >>> get_extension("txt-markdown")
        'txt'
        >>> get_extension("cwk-spreadsheet")
        'cwk'
    """
    return format_string.split('-')[0]


def _get_type(format_string: str) -> Optional[str]:
    """
    Extracts the type part of a format string in the 
    `extension[-type]` format.

    The `format_string` consists of an extension followed by an 
    optional type, separated by a hyphen (`-`). This function returns 
    the type portion of the string if it exists; otherwise, it 
    returns `None`.

    Args:
        format_string (str): A string in the format `extension[-type]`.

    Returns:
        Optional[str]: The type portion of the input string, or `None` 
        if no type is present.

    Example:

        >>> get_type("txt")
        None
        >>> get_type("txt-markdown")
        'markdown'
        >>> get_type("cwk-spreadsheet")
        'spreadsheet'
    """
    parts = format_string.split('-')
    return parts[1] if len(parts) > 1 else None


def _shorten_filename(
    filename: str,
    max_length: int = 20,
    separator: str = "...",
) -> str:
    """
    Shorten a filename that exceeds a given maximum length.

    This function preserves the file extension and key parts of the name
    while adding a customizable separator (e.g., `"..."`)
    to indicate truncation.

    Args:
        filename (str): The original filename to be shortened.
        max_length (int): The maximum allowed length
            for the shortened filename, including the extension.
            Defaults to `15`.
        separator (str): The string to use as a separator
        when truncating the filename. Defaults to `"..."`.

    Returns:
        str: The shortened filename, or the original filename
        if it doesn't exceed the maximum length.

    Example:

        >>> shorten_filename("a-really-long-filename.pdf")
        'a-re...name.pdf'
        >>> shorten_filename("short-name.pdf", separator="---")
        'short-name.pdf'
    """
    # Split filename into name and extension
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
    else:
        name, ext = filename, ""

    if len(filename) <= max_length:
        return filename  # Return original filename if it's within the limit

    # Calculate length for the start and end parts
    separator_length = len(separator)
    split_length = (max_length - len(ext) - separator_length) // 2
    start = name[:split_length]
    end = name[-split_length:]

    # Combine the parts with the extension
    return f"{start}{separator}{end}.{ext}"


def _split_into_lines(text: str, max_length: int = 79) -> List[str]:
    """
    Splits the given text into lines, each with a maximum length
    while preserving word integrity.

    Args:
        text (str): The input string to be split.
        max_length (int, optional): The maximum length of each line.
            Defaults to `79`, which is the recommended maximum
            for docstring lines.

    Returns:
        List[str]: A list of lines where each line does not exceed
        the specified maximum length.

    Example:

        >>> sample_string = (
        ...     "An example text "
        ...     "that needs to be split into lines."
        ... )
        >>> _split_into_lines(sample_string, 20)
        ['An example text that', 'needs to be split', 'into lines.']
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if current_line and len(current_line) + len(word) + 1 > max_length:
            lines.append(current_line)
            current_line = word
        else:
            current_line += (" " if current_line else "") + word

    if current_line:
        lines.append(current_line)

    return lines


def _remove_duplicates_preserve_order(old_list: List[Any]) -> List[Any]:
    """
    Remove duplicate entries from a list while preserving
    the original order.

    This function ensures that only the first occurrence of each item
    in the input list is retained, while subsequent duplicates
    are removed. The order of the input list is preserved
    in the returned list.

    Args:
        old_list (List[Any]): The input list from which duplicates
            should be removed.

    Returns:
        List[Any]: A new list containing unique elements
        from the input list in their original order.

    Example:

        >>> file_paths = [
        ...     "file1.txt",
        ...     "file2.txt",
        ...     "file1.txt",
        ...     "file3.txt"
        ... ]
        >>> remove_duplicates_preserve_order(file_paths)
        ['file1.txt', 'file2.txt', 'file3.txt']
    """
    seen = set()
    new_list_without_duplicates = [
        item for item in old_list if not (item in seen or seen.add(item))
    ]
    return new_list_without_duplicates


def _pluralize(
    count: int,
    singular: str,
    plural: Optional[str] = None,
) -> str:
    """
    Return the appropriate singular or plural form based on count.
    
    Args:
        count (int): The count to determine singular/plural form.
        singular (str): The singular form of the word.
        plural (str, optional): The plural form of the word.
            If not provided, adds 's' to the singular form.
    
    Returns:
        str: The appropriate form based on count.
    
    Example:

        >>> _pluralize(1, "file")
        'file'
        >>> _pluralize(5, "file")
        'files'
        >>> _pluralize(1, "child", "children")
        'child'
        >>> _pluralize(3, "child", "children")
        'children'
    """
    if count == 1:
        return singular
    return plural if plural else singular + "s"


def _format_count_with_plural(
    count: int,
    singular: str,
    plural: Optional[str] = None,
) -> str:
    """
    Format a count with the appropriate singular/plural form.
    
    Args:
        count (int): The count to format.
        singular (str): The singular form of the word.
        plural (str, optional): The plural form of the word.
            If not provided, adds 's' to the singular form.
    
    Returns:
        str: Formatted string with count and appropriate form.
    
    Example:

        >>> _format_count_with_plural(1, "file")
        '1 file'
        >>> _format_count_with_plural(5, "file")
        '5 files'
        >>> _format_count_with_plural(1, "child", "children")
        '1 child'
        >>> _format_count_with_plural(3, "child", "children")
        '3 children'
    """
    return f"{count} {_pluralize(count, singular, plural)}"


def _canonicalize_format(fmt: Optional[str]) -> Optional[str]:
    """
    Normalize a format string to its canonical lowercase form.

    Strips leading/trailing whitespace, removes a leading dot if
    present, and converts the result to lowercase.
    Returns `None` for empty or `None` input.

    Example:

        >>> _canonicalize_format(".PDF")
        'pdf'
        >>> _canonicalize_format("  HTML ")
        'html'
        >>> _canonicalize_format("  SVG:Font ")
        'svg:font'
        >>> _canonicalize_format(None)
        None

    Args:
        fmt: A string representing a file format (e.g., ".pdf", "HTML"),
        or `format:type` combination (e.g., "SVG:Font"), or `None`.

    Returns:
        Optional[str]: A normalized format string (e.g., "pdf", "html"),
        or `None`.
    """
    if fmt is None:
        return None
    fmt = fmt.strip().lower()
    if fmt.startswith("."):
        fmt = fmt[1:]
    return fmt or None


def _expand_braces(pattern: str) -> List[str]:
    """
    Expand brace patterns like {a,b,c} or {1..5}.
    Handles multiple braces in a single pattern.
    
    Args:
        pattern (str): Pattern that may contain brace expansions.
    
    Returns:
        List[str]: List of expanded patterns.
    
    Example:

        >>> _expand_braces("file_{1..3}.txt")
        ['file_1.txt', 'file_2.txt', 'file_3.txt']
        >>> _expand_braces("report_{jan,feb,mar}.pdf")
        ['report_jan.pdf', 'report_feb.pdf', 'report_mar.pdf']
        >>> _expand_braces("simple.txt")
        ['simple.txt']
        >>> _expand_braces("./{a,b}/file-{1..3}.txt")
        [
            './a/file-1.txt',
            './a/file-2.txt',
            './a/file-3.txt',
            './b/file-1.txt',
            './b/file-2.txt',
            './b/file-3.txt'
        ]
    """
    # Find all brace patterns in the string
    brace_pattern = r'\{([^}]+)\}'
    brace_matches = list(re.finditer(brace_pattern, pattern))

    if not brace_matches:
        return [pattern]

    # Start with the original pattern
    results = [pattern]

    # Process each brace expansion
    for match in brace_matches:
        brace_content = match.group(1)
        new_results = []

        for result in results:
            if '..' in brace_content:
                # Handle range expansion {1..5}
                try:
                    start, end = map(int, brace_content.split('..'))
                    replacements = [str(i) for i in range(start, end + 1)]
                except ValueError:
                    # If range expansion fails, treat as literal
                    replacements = [brace_content]
            else:
                # Handle list expansion {a,b,c}
                replacements = [
                    item.strip() for item in brace_content.split(',')
                ]

            # Replace this brace with each option
            for replacement in replacements:
                new_results.append(result.replace(match.group(0), replacement))

        results = new_results

    return results


def _expand_brackets(pattern: str) -> List[str]:
    """
    Expand bracket patterns like [abc] or [0-9].
    Handles multiple brackets in a single pattern.
    """
    bracket_pattern = r'\[([^\]]+)\]'
    bracket_matches = list(re.finditer(bracket_pattern, pattern))
    if not bracket_matches:
        return [pattern]
    results = [pattern]
    for match in bracket_matches:
        bracket_content = match.group(1)
        new_results = []
        for result in results:
            if '-' in bracket_content and len(bracket_content) == 3:
                start, end = bracket_content[0], bracket_content[2]
                if start.isdigit() and end.isdigit():
                    replacements = [
                        str(i) for i in range(int(start), int(end) + 1)
                    ]
                elif start.isalpha() and end.isalpha():
                    replacements = [
                        chr(i) for i in range(ord(start), ord(end) + 1)
                    ]
                else:
                    replacements = [bracket_content]
            else:
                replacements = list(bracket_content)
            for replacement in replacements:
                new_results.append(result.replace(match.group(0), replacement))
        results = new_results
    return results


def _expand_all_patterns(pattern: str) -> List[str]:
    """Expand both brace and bracket patterns in a single pattern."""
    brace_expanded = _expand_braces(pattern)
    all_expanded = []
    for expanded_pattern in brace_expanded:
        bracket_expanded = _expand_brackets(expanded_pattern)
        all_expanded.extend(bracket_expanded)
    return all_expanded


def _should_exclude_file(
    file_path: Path,
    exclude_patterns: Optional[List[str]],
) -> bool:
    """
    Enhanced exclusion with multiple pattern types.
    
    Args:
        file_path (Path): Path to check for exclusion.
        exclude_patterns (Optional[List[str]]): Patterns to exclude.

    Returns:
        bool: `True` if file should be excluded, `False` otherwise.

    Example:

        >>> _should_exclude_file(Path("temp/file.txt"), ["temp/*"])
        True
        >>> _should_exclude_file(Path("docs/file.txt"), ["*.tmp"])
        False
    """
    if not exclude_patterns:
        return False

    for pattern in exclude_patterns:
        # Handle directory patterns
        if pattern.endswith('/') or pattern.endswith('\\'):
            dir_pattern = pattern.rstrip('/\\')
            if str(file_path.parent).endswith(dir_pattern):
                return True

        # Handle glob patterns
        if '*' in pattern or '?' in pattern:
            if fnmatch.fnmatch(str(file_path), pattern):
                return True
            if fnmatch.fnmatch(file_path.name, pattern):
                return True

        # Handle regex patterns (if pattern starts with ^)
        if pattern.startswith('^'):
            try:
                if re.search(pattern, str(file_path)):
                    return True
            except re.error:
                # Invalid regex, treat as literal
                if pattern[1:] in str(file_path):
                    return True

    return False


def _should_include_file(
    file_path: Path,
    exclude_patterns: Optional[List[str]] = None,
    modified_since: Optional[str] = None,
) -> bool:
    """
    Check if a file should be included based on filters.
    
    Args:
        file_path (Path): Path to check.
        exclude_patterns (Optional[List[str]]): Patterns to exclude.
        modified_since (Optional[str]): Date filter (YYYY-MM-DD).
    
    Returns:
        bool: `True` if file should be included, `False` otherwise.
    """
    if not file_path.is_file():
        return False

    # Check exclusion patterns
    if _should_exclude_file(file_path, exclude_patterns):
        return False

    # Check modification date
    if modified_since:
        try:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            filter_date = datetime.strptime(modified_since, "%Y-%m-%d")
            if mod_time < filter_date:
                return False
        except ValueError:
            print(
                f"Error: Invalid date format '{modified_since}'. "
                "Use YYYY-MM-DD."
            )
            return False

    return True


def _enhanced_expand_inputs(
    inputs: List[str],
    recursive: bool = False,
    exclude_patterns: Optional[List[str]] = None,
    modified_since: Optional[str] = None,
) -> List[Path]:
    """
    Enhanced input expansion with better pattern support.
    
    Args:
        inputs (List[str]): List of input patterns.
        recursive (bool): Whether to enable recursive directory search.
        exclude_patterns (Optional[List[str]]): Patterns to exclude.
        modified_since (Optional[str]): Date filter (YYYY-MM-DD).
    
    Returns:
        List[Path]: List of expanded file paths.
    
    Example:

        >>> _enhanced_expand_inputs(["*.pdf", "docs/"])
        [Path('file1.pdf'), Path('file2.pdf'), Path('docs/report.pdf')]
    """
    expanded_files = []

    for input_item in inputs:
        # Handle stdin
        if input_item == '-':
            continue  # Handled separately

        # Expand brace patterns
        expanded_patterns = _expand_all_patterns(input_item)

        for pattern in expanded_patterns:
            # Handle directories
            if Path(pattern).is_dir():
                if recursive:
                    # Recursive search with all files
                    files = Path(pattern).rglob("*")
                else:
                    # Non-recursive search with file extensions
                    files = Path(pattern).glob("*.*")

                for file in files:
                    if _should_include_file(
                        file,
                        exclude_patterns,
                        modified_since,
                    ):
                        expanded_files.append(file)

            # Handle wildcard patterns
            elif '*' in pattern or '?' in pattern:
                if '**' in pattern:
                    # Recursive glob pattern
                    files = Path('.').rglob(pattern.replace('**', '*'))
                else:
                    # Standard glob pattern
                    files = Path('.').glob(pattern)

                for file in files:
                    if _should_include_file(
                        file,
                        exclude_patterns,
                        modified_since
                    ):
                        expanded_files.append(file)

            # Handle single files
            else:
                file_path = Path(pattern)
                if file_path.exists() and _should_include_file(
                    file_path,
                    exclude_patterns,
                    modified_since,
                ):
                    expanded_files.append(file_path)

    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for file_path in expanded_files:
        if file_path not in seen:
            seen.add(file_path)
            unique_files.append(file_path)

    return unique_files
