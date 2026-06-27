#!/usr/bin/env python3
"""Download distro icons for multiboot-usb GRUB theme.

Sources:
- Devicon (11 icons): MIT-licensed, SVG via jsDelivr CDN
- Wikimedia Commons (5 icons): Various free licenses

Requires: python3 (urllib), ImageMagick (convert)
"""
import urllib.request
import subprocess
import os
from pathlib import Path

ICONS_DIR = Path(__file__).parent / "multiboot_usb" / "grub" / "theme" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# Devicon: name -> (devicon_id, filename)
DEVICON = {
    "ubuntu": ("ubuntu", "ubuntu-plain.svg"),
    "arch": ("archlinux", "archlinux-plain.svg"),
    "debian": ("debian", "debian-plain.svg"),
    "fedora": ("fedora", "fedora-plain.svg"),
    "mint": ("linuxmint", "linuxmint-plain.svg"),
    "opensuse": ("opensuse", "opensuse-plain.svg"),
    "centos": ("centos", "centos-plain.svg"),
    "almalinux": ("almalinux", "almalinux-plain.svg"),
    "rocky": ("rockylinux", "rockylinux-plain.svg"),
    "kali": ("kalilinux", "kalilinux-plain.svg"),
    "unknown": ("linux", "linux-plain.svg"),
}

# Wikimedia: filename -> wikimedia_path
WIKIMEDIA = {
    "manjaro": ("Manjaro-logo.svg", "3/3e/Manjaro-logo.svg"),
    "pop": ("Pop!_OS_Icon.svg", "4/46/Pop%21_OS_Icon.svg"),
    "zorin": ("Zorin_OS.svg", "7/70/Zorin_OS.svg"),
    "mx": ("MX_LINUX_Logo.svg", "2/29/MX_LINUX_Logo.svg"),
    "elementary": ("Elementary_OS_logo.svg", "b/bf/Elementary_OS_logo.svg"),
}


def download_devicon(name: str, devicon_id: str, variant: str) -> bool:
    url = f"https://cdn.jsdelivr.net/gh/devicons/devicon/icons/{devicon_id}/{variant}"
    dest = ICONS_DIR / f"{name}.svg"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read()
        if len(data) < 100 or data[:4] == b"<!do" or data[:4] == b"<htm":
            print(f"  ✗ {name}: not valid SVG (got {len(data)} bytes)")
            return False
        dest.write_bytes(data)
        print(f"  ✓ {name}.svg ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False


def download_wikimedia(name: str, filename: str, path: str) -> bool:
    url = f"https://upload.wikimedia.org/wikipedia/commons/{path}"
    dest = ICONS_DIR / f"{name}.svg"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read()
        if len(data) < 100 or data[:4] == b"<!do" or data[:4] == b"<htm":
            print(f"  ✗ {name}: not valid SVG")
            return False
        dest.write_bytes(data)
        print(f"  ✓ {name}.svg ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False


def convert_svg_to_png(name: str) -> bool:
    svg = ICONS_DIR / f"{name}.svg"
    png = ICONS_DIR / f"{name}.png"
    if not svg.exists():
        return False
    result = subprocess.run([
        "convert", "-background", "none",
        "-resize", "48x48",
        str(svg), str(png)
    ], capture_output=True, text=True)
    if result.returncode == 0 and png.exists():
        svg.unlink()  # Remove SVG, keep only PNG
        print(f"  ✓ {name}.png created")
        return True
    else:
        print(f"  ✗ convert failed for {name}: {result.stderr[:100]}")
        return False


def main():
    print("[*] Downloading Devicon icons...")
    for name, (devicon_id, variant) in DEVICON.items():
        download_devicon(name, devicon_id, variant)

    print("[*] Downloading Wikimedia icons...")
    for name, (filename, path) in WIKIMEDIA.items():
        download_wikimedia(name, filename, path)

    print("[*] Converting SVGs to PNGs...")
    all_names = list(DEVICON.keys()) + list(WIKIMEDIA.keys())
    for name in all_names:
        convert_svg_to_png(name)

    pngs = sorted(ICONS_DIR.glob("*.png"))
    print(f"\n[+] {len(pngs)} icons ready:")
    for p in pngs:
        print(f"    {p.name} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
