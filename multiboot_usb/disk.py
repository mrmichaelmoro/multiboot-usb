from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class PartitionScheme:
    """GPT layout: EFI + Boot + ISOs."""
    device: str
    efi_size: str = "100M"
    boot_size: str = "500M"

    def partition(self) -> dict:
        subprocess.run(["sgdisk", "-Z", self.device], check=True)
        subprocess.run(["sgdisk", "-a", "2048", "-og", self.device], check=True)

        efi_end = self._parse_size(self.efi_size)
        boot_end = efi_end + self._parse_size(self.boot_size)

        cmds = [
            "mklabel gpt",
            f"mkpart primary fat32 1MiB {efi_end}MiB set 1 esp on",
            f"mkpart primary fat32 {efi_end}MiB {boot_end}MiB name 2 boot",
            f"mkpart primary fat32 {boot_end}MiB 100% name 3 isos",
        ]
        for cmd in cmds:
            subprocess.run(["parted", "--script", self.device, cmd], check=True)

        subprocess.run(["partprobe", self.device], check=True)

        return {
            "efi": f"{self.device}1",
            "boot": f"{self.device}2",
            "isos": f"{self.device}3",
        }

    @staticmethod
    def _parse_size(s: str) -> int:
        s = s.upper()
        if s.endswith("M"):
            return int(s[:-1])
        if s.endswith("G"):
            return int(s[:-1]) * 1024
        return int(s)


def format_partition(device: str, fs_type: str, label: str) -> None:
    if fs_type == "fat32":
        cmd = ["mkfs.fat", "-F", "32", "-n", label, device]
    elif fs_type == "exfat":
        cmd = ["mkfs.exfat", "-n", label, device]
    elif fs_type == "ext4":
        cmd = ["mkfs.ext4", "-L", label, device]
    else:
        raise ValueError(f"Unsupported fs: {fs_type}")
    subprocess.run(cmd, check=True)
