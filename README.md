# multiboot-usb

Lightweight, secure multi-ISO USB bootloader for Linux.

## Features

- **3-partition layout**: EFI boot, modules/themes, ISO storage — all separate
- **UEFI-first** with optional BIOS fallback
- **Auto-discovery**: Drop an ISO on the storage partition, it appears in the boot menu
- **Graphical GRUB menu** with icons (linux/windows/unknown for v1, extensible)
- **Metadata editor** (GUI) for customizing boot entries
- **ISO verification** via SHA256 sidecar files
- **Secure Boot** support (MOK enrollment)
- **Bootable ISO output**: Jenkins builds a bootable live ISO containing the tool

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

## ISO Deployment

The project's deliverable is a bootable live ISO. Jenkins builds it on every commit to main.

```bash
# Build ISO locally (requires Docker)
bash deploy/build-iso.sh

# Test in VM
qemu-system-x86_64 -cdrom multiboot-usb-live.iso -m 512M -boot d

# Write to USB
sudo dd if=multiboot-usb-live.iso of=/dev/sdX bs=4M status=progress conv=fsync
```

The ISO boots into a lightweight live environment with multiboot-usb pre-installed. On boot, a TUI launches for configuring USB drives.

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

## CI/CD

Jenkins pipeline (see `Jenkinsfile`):
1. Checkout
2. Run tests (`pytest tests/ -v`)
3. Build ISO (`bash deploy/build-iso.sh`)
4. Verify ISO (size check)
5. Archive artifact

## Requirements

- Python 3.12+
- `grub-install` (GRUB2)
- `parted`, `sgdisk`, `mkfs.fat`
- Linux host (for setup)
- Docker (for ISO builds)

## License

MIT
