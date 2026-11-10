"""Tests for file-list input handling in `_ConversionManager`.

`_read_file_list` is a pure helper (it never touches `self`), so the
tests call it unbound to avoid constructing the networked `Converter`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vertopal.cli.conversion_manager import _ConversionManager


def _read_file_list(path):
    return _ConversionManager._read_file_list(None, path)


def test_read_file_list_missing_file_is_clean_error(tmp_path, capsys):
    assert _read_file_list(str(tmp_path / "no-such-list.txt")) == []
    assert "Error" in capsys.readouterr().out


def test_read_file_list_directory_is_clean_error(tmp_path, capsys):
    assert _read_file_list(str(tmp_path)) == []
    assert "Error" in capsys.readouterr().out


def test_read_file_list_returns_stripped_lines(tmp_path):
    file_list = tmp_path / "files.txt"
    file_list.write_text("a.pdf\n\nb.pdf\n", encoding="utf-8")
    assert _read_file_list(str(file_list)) == ["a.pdf", "b.pdf"]
