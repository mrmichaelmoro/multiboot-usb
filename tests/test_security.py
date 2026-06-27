from __future__ import annotations

from multiboot_usb.security import compute_sha256, verify_iso, generate_iso_manifest


def test_compute_sha256(tmp_path):
    f = tmp_path / "test.bin"
    f.write_bytes(b"hello world")
    h = compute_sha256(str(f))
    assert len(h) == 64
    assert h == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_verify_iso_valid(tmp_path):
    f = tmp_path / "test.iso"
    f.write_bytes(b"content")
    h = compute_sha256(str(f))
    assert verify_iso(str(f), h) is True


def test_verify_iso_invalid(tmp_path):
    f = tmp_path / "test.iso"
    f.write_bytes(b"content")
    assert verify_iso(str(f), "deadbeef") is False


def test_generate_manifest(tmp_path):
    f = tmp_path / "test.iso"
    f.write_bytes(b"content")
    manifest = generate_iso_manifest(str(f))
    assert manifest["filename"] == "test.iso"
    assert manifest["size"] == 7
    assert manifest["algorithm"] == "sha256"
    assert len(manifest["sha256"]) == 64
