from __future__ import annotations

import pytest
from multiboot_usb.iso_scanner import IsoScanner, IsoMetadata


def test_detect_metadata():
    scanner = IsoScanner("/tmp")
    distro, version = scanner._detect_metadata("ubuntu-24.04-desktop-amd64.iso")
    assert distro == "ubuntu"
    assert version == "24.04"


def test_detect_arch():
    scanner = IsoScanner("/tmp")
    assert scanner._detect_arch("ubuntu-24.04-desktop-amd64.iso") == "amd64"
    assert scanner._detect_arch("archlinux-2026.06.01-x86_64.iso") == "amd64"


def test_scan_finds_isos(tmp_path):
    (tmp_path / "ubuntu-24.04-desktop-amd64.iso").write_bytes(b"\x00" * 1024)
    (tmp_path / "not_iso.txt").write_bytes(b"hello")
    scanner = IsoScanner(str(tmp_path))
    results = scanner.scan()
    assert len(results) == 1
    assert results[0].distro == "ubuntu"


def test_scan_unknown_distro(tmp_path):
    (tmp_path / "custom-os-v1.0.iso").write_bytes(b"\x00" * 1024)
    scanner = IsoScanner(str(tmp_path))
    results = scanner.scan()
    assert results[0].distro == "unknown"
    assert results[0].menu_label == "custom-os-v1.0.iso"


def test_metadata_roundtrip(tmp_path):
    iso = tmp_path / "test.iso"
    iso.write_bytes(b"test")
    meta = IsoMetadata(
        filename="test.iso", distro="test", version="1.0", arch="amd64",
        boot_type="both", size=4, sha256="abc", menu_label="Test 1.0"
    )
    scanner = IsoScanner(str(tmp_path))
    scanner.save_metadata(meta, str(tmp_path))
    loaded = scanner.load_metadata("test.iso", str(tmp_path))
    assert loaded.distro == "test"
    assert loaded.version == "1.0"


def test_iso_metadata_from_dict():
    data = {
        "filename": "x.iso", "distro": "fedora", "version": "40", "arch": "amd64",
        "boot_type": "both", "size": 100, "sha256": "def", "menu_label": "Fedora 40"
    }
    meta = IsoMetadata.from_dict(data)
    assert meta.distro == "fedora"
    assert meta.display_name == "Fedora 40"


def test_iso_metadata_custom_label():
    meta = IsoMetadata(
        filename="ubuntu.iso", distro="ubuntu", version="24.04", arch="amd64",
        boot_type="both", size=100, sha256="x", menu_label="Ubuntu 24.04",
        custom_label="My Custom Ubuntu"
    )
    assert meta.display_name == "My Custom Ubuntu"
