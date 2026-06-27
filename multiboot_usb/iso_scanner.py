from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class IsoMetadata:
    filename: str
    distro: str
    version: str
    arch: str
    boot_type: str
    size: int
    sha256: str
    menu_label: str
    custom_label: Optional[str] = None

    @property
    def display_name(self) -> str:
        return self.custom_label or self.menu_label

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> IsoMetadata:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class IsoScanner:
    DISTRO_PATTERNS = [
        (r"ubuntu-(\d+\.\d+)", "ubuntu"),
        (r"debian-(\d+\.\d+)", "debian"),
        (r"archlinux-(\d{4}\.\d{2}\.\d{2})", "arch"),
        (r"fedora-(\d+)", "fedora"),
        (r"linuxmint-(\d+\.\d+)", "mint"),
        (r"opensuse-(\d+\.\d+)", "opensuse"),
        (r"manjaro-(\d+\.\d+)", "manjaro"),
        (r"centos-(\d+)", "centos"),
        (r"alma(\d+)", "almalinux"),
        (r"rocky-(\d+)", "rocky"),
        (r"pop_os-(\d+\.\d+)", "pop"),
        (r"elementary-(\d+\.\d+)", "elementary"),
        (r"zorin-(\d+)", "zorin"),
        (r"kali-(\d{4}\.\d+)", "kali"),
        (r"mx-(\d+\.\d+)", "mx"),
    ]

    def __init__(self, iso_directory: str):
        self.iso_dir = Path(iso_directory)

    def scan(self) -> List[IsoMetadata]:
        results = []
        for iso_path in sorted(self.iso_dir.glob("*.iso")):
            results.append(self._build_metadata(iso_path))
        return results

    def _build_metadata(self, iso_path: Path) -> IsoMetadata:
        filename = iso_path.name
        distro, version = self._detect_metadata(filename)
        arch = self._detect_arch(filename)
        sha256 = self._compute_hash(iso_path)
        boot_type = self._detect_boot_type(iso_path)
        label = f"{distro.title()} {version}" if distro != "unknown" else filename

        return IsoMetadata(
            filename=filename,
            distro=distro,
            version=version,
            arch=arch,
            boot_type=boot_type,
            size=iso_path.stat().st_size,
            sha256=sha256,
            menu_label=label,
        )

    def _detect_metadata(self, filename: str) -> tuple[str, str]:
        lower = filename.lower()
        for pattern, distro_name in self.DISTRO_PATTERNS:
            match = re.search(pattern, lower)
            if match:
                return distro_name, match.group(1)
        return "unknown", ""

    def _detect_arch(self, filename: str) -> str:
        lower = filename.lower()
        if "amd64" in lower or "x86_64" in lower or "x64" in lower:
            return "amd64"
        if "i386" in lower or "i686" in lower:
            return "i386"
        if "arm64" in lower or "aarch64" in lower:
            return "arm64"
        return "unknown"

    def _detect_boot_type(self, iso_path: Path) -> str:
        try:
            result = subprocess.run(
                ["file", str(iso_path)],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout.lower()
            if "uefi" in output:
                return "both" if "bootable" in output else "uefi"
            if "bootable" in output:
                return "bios"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return "both"

    @staticmethod
    def _compute_hash(iso_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(iso_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def save_metadata(self, metadata: IsoMetadata, directory: str) -> None:
        meta_dir = Path(directory) / "metadata"
        meta_dir.mkdir(parents=True, exist_ok=True)
        meta_file = meta_dir / f"{metadata.filename}.json"
        with open(meta_file, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

    def load_metadata(self, iso_filename: str, directory: str) -> IsoMetadata:
        meta_file = Path(directory) / "metadata" / f"{iso_filename}.json"
        with open(meta_file) as f:
            data = json.load(f)
        return IsoMetadata.from_dict(data)
