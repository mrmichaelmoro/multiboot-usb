from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def cmd_setup(args: argparse.Namespace) -> int:
    """Initialize USB drive with multiboot layout."""
    from multiboot_usb.disk import PartitionScheme, format_partition
    from multiboot_usb.grub_installer import GrubInstaller
    from multiboot_usb.iso_scanner import IsoScanner
    from multiboot_usb.grub_config import GrubConfigGenerator

    print(f"[*] Setting up {args.device}...")

    scheme = PartitionScheme(args.device)
    partitions = scheme.partition()
    print(f"    EFI:  {partitions['efi']}")
    print(f"    Boot: {partitions['boot']}")
    print(f"    ISOs: {partitions['isos']}")

    mount = Path("/tmp/multiboot-usb-setup")
    mount.mkdir(exist_ok=True)

    format_partition(partitions["efi"], "fat32", "EFI")
    format_partition(partitions["boot"], "fat32", "BOOT")
    format_partition(partitions["isos"], args.iso_partition_fs, "ISOS")

    subprocess.run(["mount", partitions["boot"], str(mount)], check=True)

    installer = GrubInstaller(
        device=args.device,
        efi_partition=partitions["efi"],
        boot_partition=partitions["boot"],
        mount_point=str(mount),
        enable_bios=args.bios,
    )
    installer.install()
    print("[+] GRUB installed.")

    iso_mount = mount / "iso"
    iso_mount.mkdir(exist_ok=True)
    subprocess.run(["mount", partitions["isos"], str(iso_mount)], check=True)

    scanner = IsoScanner(str(iso_mount))
    isos = scanner.scan()
    for iso in isos:
        scanner.save_metadata(iso, str(mount))
        print(f"[+] Found ISO: {iso.display_name}")

    gen = GrubConfigGenerator(partitions["isos"])
    gen.write(isos, str(mount / "boot" / "grub" / "grub.cfg"))
    print("[+] grub.cfg generated.")

    subprocess.run(["umount", str(iso_mount)], check=True)
    subprocess.run(["umount", str(mount)], check=True)

    print(f"[+] Setup complete!")
    print(f"    Drop ISOs into the ISOS partition and run:")
    print(f"    multiboot-usb refresh <boot_partition_mount>")
    return 0


def cmd_add_iso(args: argparse.Namespace) -> int:
    """Copy ISO to USB and register it."""
    import shutil
    from multiboot_usb.iso_scanner import IsoScanner
    from multiboot_usb.grub_config import GrubConfigGenerator

    iso_path = Path(args.iso_path)
    if not iso_path.exists() or iso_path.suffix != ".iso":
        print(f"Error: {args.iso_path} is not a valid ISO file.")
        return 1

    mount = Path(args.usb_mount)
    iso_dir = mount / "boot" / "iso"

    dest = iso_dir / iso_path.name
    print(f"[*] Copying {iso_path.name}...")
    shutil.copy2(iso_path, dest)

    scanner = IsoScanner(str(iso_dir))
    meta = scanner._build_metadata(dest)
    scanner.save_metadata(meta, str(mount))
    print(f"[+] Added: {meta.display_name}")

    isos = scanner.scan()
    iso_part = _find_partition(args.usb_mount)
    gen = GrubConfigGenerator(iso_part)
    gen.write(isos, str(mount / "boot" / "grub" / "grub.cfg"))
    print("[+] grub.cfg updated.")
    return 0


def cmd_remove_iso(args: argparse.Namespace) -> int:
    """Remove ISO from USB."""
    from multiboot_usb.iso_scanner import IsoScanner
    from multiboot_usb.grub_config import GrubConfigGenerator

    mount = Path(args.usb_mount)
    iso_dir = mount / "boot" / "iso"
    meta_dir = mount / "boot" / "metadata"

    iso_file = iso_dir / args.iso_name
    if iso_file.exists():
        iso_file.unlink()
        meta_file = meta_dir / f"{args.iso_name}.json"
        if meta_file.exists():
            meta_file.unlink()
        print(f"[+] Removed: {args.iso_name}")
    else:
        print(f"[!] ISO not found: {args.iso_name}")
        return 1

    scanner = IsoScanner(str(iso_dir))
    isos = scanner.scan()
    iso_part = _find_partition(args.usb_mount)
    gen = GrubConfigGenerator(iso_part)
    gen.write(isos, str(mount / "boot" / "grub" / "grub.cfg"))
    print("[+] grub.cfg updated.")
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    """Re-scan ISOs and regenerate boot menu."""
    from multiboot_usb.iso_scanner import IsoScanner
    from multiboot_usb.grub_config import GrubConfigGenerator

    mount = Path(args.usb_mount)
    iso_dir = mount / "boot" / "iso"
    scanner = IsoScanner(str(iso_dir))
    isos = scanner.scan()

    for iso in isos:
        scanner.save_metadata(iso, str(mount))
        print(f"[+] {iso.display_name}")

    iso_part = _find_partition(args.usb_mount)
    gen = GrubConfigGenerator(iso_part)
    gen.write(isos, str(mount / "boot" / "grub" / "grub.cfg"))
    print(f"[+] grub.cfg regenerated with {len(isos)} entries.")
    return 0


def cmd_edit_metadata(args: argparse.Namespace) -> int:
    """Launch metadata editor GUI."""
    from multiboot_usb.metadata_gui import edit_metadata
    edit_metadata(args.usb_mount)
    return 0


def _find_partition(mount_point: str) -> str:
    result = subprocess.run(
        ["findmnt", "-n", "-o", "SOURCE", mount_point],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="multiboot-usb",
        description="Create and manage a multi-ISO bootable USB drive"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="Initialize USB drive")
    setup_parser.add_argument("device", help="USB device path (e.g. /dev/sdX)")
    setup_parser.add_argument("--iso-partition-fs", choices=["fat32", "exfat", "ext4"],
                              default="fat32", help="Filesystem for ISO partition")
    setup_parser.add_argument("--bios", action="store_true", help="Enable BIOS fallback")

    add_parser = subparsers.add_parser("add-iso", help="Add ISO to USB")
    add_parser.add_argument("usb_mount", help="Mount point of boot partition")
    add_parser.add_argument("iso_path", help="Path to ISO file")

    remove_parser = subparsers.add_parser("remove-iso", help="Remove ISO from USB")
    remove_parser.add_argument("usb_mount", help="Mount point of boot partition")
    remove_parser.add_argument("iso_name", help="ISO filename to remove")

    refresh_parser = subparsers.add_parser("refresh", help="Re-scan ISOs and regenerate boot menu")
    refresh_parser.add_argument("usb_mount", help="Mount point of boot partition")

    edit_parser = subparsers.add_parser("edit-metadata", help="Edit ISO metadata in GUI")
    edit_parser.add_argument("usb_mount", help="Mount point of boot partition")

    args = parser.parse_args()
    commands = {
        "setup": cmd_setup,
        "add-iso": cmd_add_iso,
        "remove-iso": cmd_remove_iso,
        "refresh": cmd_refresh,
        "edit-metadata": cmd_edit_metadata,
    }
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
