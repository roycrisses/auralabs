"""Tests for body tools — filesystem, sysinfo, process safety."""

import os
import tempfile
from pathlib import Path

import pytest

from aura.body.filesystem import read_file, write_file, list_directory, _is_allowed
from aura.body.process import _is_safe
from aura.body.sysinfo import get_system_info, get_disk_info


# --- Filesystem ---

def test_is_allowed_valid():
    assert _is_allowed(Path(r"D:\automation\test.txt"))
    assert _is_allowed(Path(r"D:\automation\aura\something"))


def test_is_allowed_rejected():
    assert not _is_allowed(Path(r"C:\Windows\System32\cmd.exe"))
    assert not _is_allowed(Path(r"C:\Users\secret.txt"))


def test_read_write_file(tmp_path):
    """Test file read/write within allowed directories."""
    # We test with real allowed path
    test_dir = Path(r"D:\automation\aura\.cache\test")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = str(test_dir / "test_rw.txt")

    result = write_file(test_file, "hello test")
    assert "Written" in result

    content = read_file(test_file)
    assert content == "hello test"

    # Cleanup
    Path(test_file).unlink(missing_ok=True)


def test_list_directory():
    result = list_directory(r"D:\automation\aura")
    assert "aura" in result or "[DIR]" in result


# --- Process safety ---

def test_safe_commands():
    assert _is_safe("echo hello")
    assert _is_safe("dir")
    assert _is_safe("python --version")


def test_blocked_commands():
    assert not _is_safe("rm -rf /")
    assert not _is_safe("format c:")
    assert not _is_safe("shutdown")
    assert not _is_safe("del /s /q c:")


# --- System info ---

def test_get_system_info():
    info = get_system_info()
    assert "os" in info
    assert "ram_total_gb" in info
    assert info["ram_total_gb"] > 0


def test_get_disk_info():
    disks = get_disk_info()
    assert len(disks) > 0
    assert "total_gb" in disks[0]
