# multiboot-usb

Lightweight, secure multi-ISO USB bootloader for Linux.

## Features

- **3-partition layout**: EFI boot, modules/themes, ISO storage — all separate
- **UEFI-first** with optional BIOS fallback
- **Auto-discovery**: Drop an ISO on the storage partition, it appears in the boot menu
- **Graphical GRUB menu** with distro icons
- **Metadata editor** (GUI) for customizing boot entries
- **ISO verification** via SHA256 sidecar files
- **Secure Boot** support (MOK enrollment)

## Quick Start

```bash
# Install
pip install -e .

# Setup USB drive (WARNING: destroys all data on /dev/sdX)
sudo multiboot-usb setup /dev/sdX

# Add an ISO
sudo multiboot-usb add-iso /mnt/usb/boot ~/Downloads/ubuntu-24.04.iso

# Edit metadata (opens GUI)
multiboot-usb edit-metadata /mnt/usb/boot

# Re-scan for new ISOs
sudo multiboot-usb refresh /mnt/usb/boot
```

## Architecture

```
USB Drive (GPT)
┌──────────────────┬──────────────────┬──────────────────────────┐
│  P1: EFI (FAT32) │ P2: Boot (FAT32) │  P3: ISOs (FAT32/ext4)  │
│  100MB           │ 500MB            │  Remaining space         │
│  ─────────────── │ ──────────────── │  ─────────────────────── │
│  BOOTX64.EFI     │ grub/x86_64-efi/ │  ubuntu-24.04.iso        │
│  grub.cfg        │ grub/themes/     │  archlinux-2026.iso      │
│                  │ grub/iso/        │  ...                     │
│                  │ grub/metadata/   │                          │
└──────────────────┴──────────────────┴──────────────────────────┘
```

## Security Model

1. **Partition isolation**: Bootloader and ISOs on separate partitions
2. **Read-only boot**: P1+P2 can be remounted read-only after setup
3. **ISO verification**: SHA256 hashes stored as `.json` sidecars
4. **Secure Boot**: Optional MOK-based signing chain
5. **No network**: GRUB runs fully offline — no attack surface at boot

## Requirements

- Python 3.12+
- `grub-install` (GRUB2)
- `parted`, `sgdisk`, `mkfs.fat`
- Linux host (for setup)

## License

MIT
