#!/usr/bin/env python3
"""Download distro icons for multiboot-usb GRUB theme.

Requires: curl, imagemagick (convert)
Usage: python3 download_icons.py

Icons sourced from TechIcons (techicons.dev) — official SVG/PNG.
"""
import subprocess
import json
from pathlib import Path

ICONS_DIR = Path(__file__).parent
SIZE = "48"  # px — GRUB gfxmenu supports this

DISTROS = {
    "ubuntu": "ubuntu",
    "arch": "archlinux",
    "debian": "debian",
    "fedora": "fedora",
    "mint": "linux-mint",
    "opensuse": "opensuse",
    "manjaro": "manjaro",
    "centos": "centos",
    "almalinux": "alma-linux",
    "rocky": "rocky-linux",
    "pop": "pop-os",
    "elementary": "elementary",
    "zorin": "zorin-os",
    "kali": "kali-linux",
    "mx": "mx-linux",
    "unknown": "linux",
}

def download_svg(distro_id: str, name: str) -> bool:
    """Download SVG from TechIcons CDN."""
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@v13/icons/{distro_id}.svg"
    dest = ICONS_DIR / f"{name}.svg"
    result = subprocess.run(
        ["curl", "-sL", "-o", str(dest), url],
        capture_output=True, text=True
    )
    if result.returncode == 0 and dest.stat().st_size > 100:
        print(f"  ✓ {name}.svg downloaded")
        return True
    else:
        dest.unlink(missing_ok=True)
        return False

def convert_svg_to_png(name: str) -> bool:
    """Convert SVG to PNG using ImageMagick."""
    svg = ICONS_DIR / f"{name}.svg"
    png = ICONS_DIR / f"{name}.png"
    if not svg.exists():
        return False
    result = subprocess.run([
        "convert", "-background", "none",
        "-resize", f"{SIZE}x{SIZE}",
        str(svg), str(png)
    ], capture_output=True, text=True)
    if result.returncode == 0 and png.exists():
        svg.unlink()  # Remove SVG, keep only PNG
        print(f"  ✓ {name}.png created")
        return True
    return False

def main():
    for name, distro_id in DISTROS.items():
        print(f"[*] {name}...")
        if download_svg(distro_id, name):
            convert_svg_to_png(name)

    # Check what we have
    pngs = list(ICONS_DIR.glob("*.png"))
    print(f"\n[+] {len(pngs)} icons ready:")
    for p in sorted(pngs):
        print(f"    {p.name} ({p.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
