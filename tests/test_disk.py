from __future__ import annotations

import pytest
from unittest.mock import patch
from multiboot_usb.disk import PartitionScheme, format_partition


def test_partition_scheme_creation():
    scheme = PartitionScheme("/dev/sdX")
    assert scheme.device == "/dev/sdX"
    assert scheme.efi_size == "100M"
    assert scheme.boot_size == "500M"


def test_parse_size():
    assert PartitionScheme._parse_size("100M") == 100
    assert PartitionScheme._parse_size("1G") == 1024
    assert PartitionScheme._parse_size("500M") == 500


def test_format_partition_fat32():
    with patch("multiboot_usb.disk.subprocess.run") as mock_run:
        format_partition("/dev/sdX3", "fat32", "ISOS")
        call_args = mock_run.call_args[0][0]
        assert "mkfs.fat" in call_args


def test_format_partition_ext4():
    with patch("multiboot_usb.disk.subprocess.run") as mock_run:
        format_partition("/dev/sdX3", "ext4", "ISOS")
        call_args = mock_run.call_args[0][0]
        assert "mkfs.ext4" in call_args
        assert "-L" in call_args


def test_format_partition_invalid():
    with pytest.raises(ValueError):
        format_partition("/dev/sdX3", "ntfs", "ISOS")
