from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict


def compute_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_iso(iso_path: str, expected_hash: str) -> bool:
    return compute_sha256(iso_path) == expected_hash


def generate_iso_manifest(iso_path: str) -> Dict:
    return {
        "filename": Path(iso_path).name,
        "sha256": compute_sha256(iso_path),
        "size": Path(iso_path).stat().st_size,
        "algorithm": "sha256",
    }


def sign_grub_cfg(config_path: str, key_path: str, cert_path: str) -> bool:
    try:
        subprocess.run([
            "gpg", "--detach-sign", "--armor",
            "--output", f"{config_path}.sig",
            "--default-key", key_path,
            config_path,
        ], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
