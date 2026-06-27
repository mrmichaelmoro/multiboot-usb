from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

from multiboot_usb.iso_scanner import IsoMetadata


class GrubConfigGenerator:
    TEMPLATE_HEADER = """# multiboot-usb GRUB configuration
set timeout=10
set default=0
set gfxmode=auto
set gfxpayload=keep

insmod gfxterm
insmod png
insmod part_gpt
insmod iso9660
insmod loopback

if [ -f ${prefix}/themes/terminal/background.png ]; then
    background_image ${prefix}/themes/terminal/background.png
fi

menuentry "Reboot" --class reboot { exit }
menuentry "Shutdown" --class halt { halt }

"""

    TEMPLATE_ENTRY = """menuentry "{label}" --class {distro} {{
    set isofile=/boot/iso/{filename}
    loopback loop $isofile
    linux (loop)/{kernel_path} {kernel_args}
    initrd (loop)/{initrd_path}
    boot
}}

"""

    DISTRO_KERNEL_MAP = {
        "ubuntu": ("casper/vmlinuz", "casper/initrd", "boot=casper quiet splash iso-scan/filename=$isofile --"),
        "debian": ("install.amd/vmlinuz", "install.amd/initrd.gz", "quiet iso-scan/filename=$isofile --"),
        "arch": ("arch/boot/x86_64/vmlinuz-linux", "arch/boot/x86_64/archiso.img", "img_loop=/arch/x86_64.img earlymodules=loop"),
        "fedora": ("isolinux/vmlinuz", "isolinux/initrd.img", "root=live:CDLABEL=LABEL quiet rd.live.image iso-scan/filename=$isofile"),
        "mint": ("casper/vmlinuz", "casper/initrd", "boot=casper quiet splash iso-scan/filename=$isofile --"),
        "opensuse": ("boot/x86_64/loader/linux", "boot/x86_64/loader/initrd", "isofrom_device=/dev/disk/by-uuid/{uuid} isofrom_system=/boot/iso/{filename} quiet"),
        "manjaro": ("boot/vmlinuz-x86_64", "boot/initramfs-x86_64.img", "earlymodules=loop img_loop=/boot/mkiso.img"),
        "pop": ("casper/vmlinuz", "casper/initrd", "boot=casper quiet splash iso-scan/filename=$isofile --"),
    }

    def __init__(self, iso_partition: str, uuid: str = ""):
        self.iso_partition = iso_partition
        self.uuid = uuid or self._get_uuid(iso_partition)

    @staticmethod
    def _get_uuid(partition: str) -> str:
        try:
            result = subprocess.run(
                ["blkid", "-s", "UUID", "-o", "value", partition],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "UNKNOWN"

    def generate(self, isos: List[IsoMetadata]) -> str:
        cfg = self.TEMPLATE_HEADER
        for iso in isos:
            cfg += self._generate_entry(iso)
        return cfg

    def _generate_entry(self, meta: IsoMetadata) -> str:
        distro_key = meta.distro.lower()
        kernel, initrd, args = self.DISTRO_KERNEL_MAP.get(
            distro_key, ("isolinux/vmlinuz", "isolinux/initrd.img", "quiet")
        )
        return self.TEMPLATE_ENTRY.format(
            label=meta.display_name,
            distro=meta.distro,
            filename=meta.filename,
            kernel_path=kernel,
            initrd_path=initrd,
            kernel_args=args.format(uuid=self.uuid, filename=meta.filename),
        )

    def write(self, isos: List[IsoMetadata], output_path: str) -> None:
        cfg = self.generate(isos)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(cfg)
