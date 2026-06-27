from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class GrubInstaller:
    GRUB_MODULES = [
        "normal", "linux", "loopback", "iso9660", "gzio", "fat",
        "part_gpt", "part_msdos", "efi_gop", "gfxterm", "gfxmenu",
        "png", "boot", "configfile", "search", "search_fs_uuid",
    ]

    def __init__(self, device: str, efi_partition: str, boot_partition: str,
                 mount_point: str, enable_bios: bool = False):
        self.device = device
        self.efi_partition = efi_partition
        self.boot_partition = boot_partition
        self.mount_point = Path(mount_point)
        self.enable_bios = enable_bios
        self.boot_dir = self.mount_point / "boot"
        self.grub_dir = self.boot_dir / "grub"
        self._grub_install = self._find_grub_install()

    @staticmethod
    def _find_grub_install() -> str:
        for name in ["grub-install", "grub2-install"]:
            from shutil import which
            path = which(name)
            if path:
                return path
        raise FileNotFoundError("grub-install not found")

    def install(self) -> None:
        self._prepare_boot_dir()
        self._install_efi()
        if self.enable_bios:
            self._install_bios()
        self._copy_modules()

    def _prepare_boot_dir(self) -> None:
        self.grub_dir.mkdir(parents=True, exist_ok=True)
        (self.boot_dir / "iso").mkdir(exist_ok=True)
        (self.boot_dir / "metadata").mkdir(exist_ok=True)

    def _install_efi(self) -> None:
        subprocess.run([
            self._grub_install,
            "--target=x86_64-efi",
            "--efi-directory", str(self.mount_point),
            "--boot-directory", str(self.boot_dir),
            "--removable",
            "--recheck",
            self.device,
        ], check=True)

    def _install_bios(self) -> None:
        subprocess.run([
            self._grub_install,
            "--target=i386-pc",
            "--boot-directory", str(self.boot_dir),
            "--recheck",
            self.device,
        ], check=True)

    def _copy_modules(self) -> None:
        system_grub = Path("/usr/lib/grub/x86_64-efi")
        if not system_grub.exists():
            system_grub = Path("/usr/lib/grub2/x86_64-efi")
        if not system_grub.exists():
            raise FileNotFoundError("GRUB EFI modules not found")

        target = self.grub_dir / "x86_64-efi"
        target.mkdir(exist_ok=True)

        for mod in system_grub.glob("*.mod"):
            if mod.stem in self.GRUB_MODULES:
                shutil.copy2(mod, target)

        for name in ["grubenv", "fonts", "locale"]:
            src = system_grub.parent / name
            if src.exists():
                dst = self.grub_dir / name
                if src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
