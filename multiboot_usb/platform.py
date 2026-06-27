from __future__ import annotations

import sys
from pathlib import Path


def is_windows() -> bool:
    return sys.platform == "win32"


def is_linux() -> bool:
    return sys.platform == "linux"


def get_grub_install() -> str:
    if is_windows():
        base = Path(__file__).parent.parent / "tools" / "windows"
        return str(base / "grub-install.exe")
    for name in ["grub-install", "grub2-install"]:
        from shutil import which
        path = which(name)
        if path:
            return path
    raise FileNotFoundError("grub-install not found")


def get_partition_tool() -> str:
    if is_windows():
        return "diskpart"
    return "parted"


def get_sgdisk_tool() -> str:
    if is_windows():
        return "sgdisk.exe"
    return "sgdisk"
