from __future__ import annotations

import pytest
from multiboot_usb.grub_config import GrubConfigGenerator
from multiboot_usb.iso_scanner import IsoMetadata


def test_generates_menu_entries():
    meta = IsoMetadata(
        filename="ubuntu-24.04-desktop-amd64.iso",
        distro="ubuntu", version="24.04", arch="amd64",
        boot_type="both", size=5_000_000_000,
        sha256="abc123", menu_label="Ubuntu 24.04"
    )
    gen = GrubConfigGenerator("/dev/sdX3", uuid="TEST-UUID-123")
    cfg = gen.generate([meta])
    assert "Ubuntu 24.04" in cfg
    assert "loopback" in cfg
    assert "iso9660" in cfg
    assert "casper/vmlinuz" in cfg


def test_uefi_only_entry():
    meta = IsoMetadata(
        filename="archlinux-2026.06.01-x86_64.iso",
        distro="arch", version="2026.06.01", arch="amd64",
        boot_type="uefi", size=1_000_000_000,
        sha256="def456", menu_label="Arch 2026.06.01"
    )
    gen = GrubConfigGenerator("/dev/sdX3", uuid="TEST-UUID-123")
    cfg = gen.generate([meta])
    assert "Arch 2026.06.01" in cfg
    assert "arch/boot/x86_64/vmlinuz-linux" in cfg


def test_unknown_distro_uses_defaults():
    meta = IsoMetadata(
        filename="custom-os.iso",
        distro="unknown", version="", arch="unknown",
        boot_type="both", size=100,
        sha256="xyz", menu_label="custom-os.iso"
    )
    gen = GrubConfigGenerator("/dev/sdX3", uuid="TEST")
    cfg = gen.generate([meta])
    assert "isolinux/vmlinuz" in cfg


def test_write_creates_file(tmp_path):
    meta = IsoMetadata(
        filename="test.iso", distro="test", version="1.0", arch="amd64",
        boot_type="both", size=100, sha256="abc", menu_label="Test 1.0"
    )
    gen = GrubConfigGenerator("/dev/sdX3", uuid="TEST")
    output = str(tmp_path / "boot" / "grub" / "grub.cfg")
    gen.write([meta], output)
    assert (tmp_path / "boot" / "grub" / "grub.cfg").exists()
