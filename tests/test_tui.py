from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from deploy.tui import MultibootUsbTui


class TestMultibootUsbTui:
    """Tests for the TUI module."""

    def test_scan_usb_no_devices(self):
        with patch("multiboot_usb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="", returncode=0
            )
            tui = MultibootUsbTui()
            result = tui.scan_usb_devices()
            assert result == []

    def test_scan_usb_finds_devices(self):
        lsblk_output = (
            "NAME SIZE TRAN MODEL\n"
            "/dev/sda 931.5G disk Samsung SSD\n"
            "/dev/sdb 29.7G usb Flash Drive\n"
            "/dev/sdc 14.9G usb USB Stick\n"
        )
        with patch("multiboot_usb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout=lsblk_output, returncode=0
            )
            tui = MultibootUsbTui()
            result = tui.scan_usb_devices()
            assert len(result) == 2
            assert result[0]["name"] == "/dev/sdb"
            assert result[1]["name"] == "/dev/sdc"

    def test_setup_device_not_root(self):
        with patch("os.geteuid", return_value=1000):
            tui = MultibootUsbTui()
            ok, msg = tui.setup_device("/dev/sdb")
            assert ok is False
            assert "root" in msg.lower()

    def test_setup_device_success(self):
        with patch("os.geteuid", return_value=0), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("multiboot_usb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Done", stderr=""
            )
            tui = MultibootUsbTui()
            ok, msg = tui.setup_device("/dev/sdb")
            assert ok is True
            assert "successfully" in msg.lower()

    def test_setup_device_failure(self):
        with patch("os.geteuid", return_value=0), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("multiboot_usb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="Device busy"
            )
            tui = MultibootUsbTui()
            ok, msg = tui.setup_device("/dev/sdb")
            assert ok is False

    def test_add_iso_success(self):
        with patch("multiboot_usb.cli.subprocess.run") as mock_run, \
             patch("os.path.exists", return_value=True), \
             patch("shutil.copy2"):
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Added", stderr=""
            )
            tui = MultibootUsbTui()
            ok, msg = tui.add_iso("/mnt/iso", "/tmp/test.iso")
            assert ok is True

    def test_refresh_menu_success(self):
        with patch("multiboot_usb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Refreshed", stderr=""
            )
            tui = MultibootUsbTui()
            ok, msg = tui.refresh_menu("/mnt/iso")
            assert ok is True
            assert "refreshed" in msg.lower()
