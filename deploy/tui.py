#!/usr/bin/env python3
"""Terminal UI for multiboot-usb configuration on live boot."""
from __future__ import annotations

import subprocess
import shutil
import os
import sys
from pathlib import Path

try:
    from prompt_toolkit import Application as App
    from prompt_toolkit.layout.containers import HSplit, VSplit, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.widgets import Label, Button, TextArea
    from prompt_toolkit.styles import Style
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False


class MultibootUsbTui:
    """Main TUI for configuring multiboot-usb from a live ISO."""

    def __init__(self):
        self.usb_devices = []
        self.selected_device = None
        self.message = ""
        self.message_color = "green"

    def scan_usb_devices(self) -> list[dict]:
        """Scan for available USB drives."""
        devices = []
        result = subprocess.run(
            ["lsblk", "-d", "-o", "NAME,SIZE,TRAN,MODEL", "-n", "-p"],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(None, 3)
            if len(parts) >= 3 and parts[2] == "usb":
                devices.append({
                    "name": parts[0],
                    "size": parts[1],
                    "model": parts[3] if len(parts) > 3 else "",
                })
        self.usb_devices = devices
        return devices

    def setup_device(self, device: str) -> tuple[bool, str]:
        """Run multiboot-usb setup on the selected device."""
        if not os.geteuid() == 0:
            return False, "Root privileges required. Run with sudo."

        if not Path(device).exists():
            return False, f"Device {device} not found."

        try:
            result = subprocess.run(
                ["multiboot-usb", "setup", device],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                return True, f"Successfully set up {device}"
            else:
                return False, f"Setup failed: {result.stderr[:200]}"
        except subprocess.TimeoutExpired:
            return False, "Setup timed out (5 minutes)"
        except FileNotFoundError:
            return False, "multiboot-usb command not found"

    def add_iso(self, mount_point: str, iso_path: str) -> tuple[bool, str]:
        """Add an ISO to the configured USB."""
        try:
            result = subprocess.run(
                ["multiboot-usb", "add-iso", mount_point, iso_path],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return True, f"Added {os.path.basename(iso_path)}"
            return False, f"Failed: {result.stderr[:200]}"
        except Exception as e:
            return False, str(e)

    def refresh_menu(self, mount_point: str) -> tuple[bool, str]:
        """Re-scan ISOs and regenerate boot menu."""
        try:
            result = subprocess.run(
                ["multiboot-usb", "refresh", mount_point],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return True, "Boot menu refreshed"
            return False, f"Refresh failed: {result.stderr[:200]}"
        except Exception as e:
            return False, str(e)

    def simple_menu(self):
        """Fallback simple menu using basic terminal I/O."""
        print("\033[2J\033[H")  # Clear screen
        print("=" * 60)
        print("  multiboot-usb — Live Configuration")
        print("=" * 60)

        while True:
            print("\nScanning USB devices...")
            devices = self.scan_usb_devices()

            if not devices:
                print("\nNo USB drives detected.")
                print("Insert a USB drive and press Enter to rescan.")
                input()
                continue

            print("\nAvailable USB drives:")
            print("-" * 60)
            for i, dev in enumerate(devices, 1):
                model = f" ({dev['model']})" if dev['model'] else ""
                print(f"  {i}. {dev['name']}  {dev['size']}{model}")
            print(f"  0. Exit")

            choice = input("\nSelect device (number): ").strip()
            if choice == "0":
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(devices):
                    self.selected_device = devices[idx]
                    self.device_menu()
                else:
                    print("Invalid selection.")
                    input("Press Enter to continue...")
            except ValueError:
                print("Invalid input.")
                input("Press Enter to continue...")

    def device_menu(self):
        """Menu for a selected device."""
        device = self.selected_device
        print(f"\n{'=' * 60}")
        print(f"  Device: {device['name']} ({device['size']})")
        print(f"{'=' * 60}")

        while True:
            print("\nActions:")
            print("  1. Setup (install multiboot bootloader)")
            print("  2. Add ISO")
            print("  3. Refresh boot menu")
            print("  4. Edit metadata")
            print("  5. Rescan devices")
            print("  0. Back to device list")

            choice = input("\nSelect action: ").strip()

            if choice == "0":
                break
            elif choice == "1":
                ok, msg = self.setup_device(device["name"])
                print(f"\n{'✓' if ok else '✗'} {msg}")
                input("Press Enter to continue...")
            elif choice == "2":
                iso_path = input("Path to ISO file: ").strip()
                if iso_path and os.path.exists(iso_path):
                    # Mount boot partition if needed
                    mount = "/tmp/multiboot-usb-boot"
                    os.makedirs(mount, exist_ok=True)
                    subprocess.run(["mount", f"{device['name']}2", mount], capture_output=True)
                    ok, msg = self.add_iso(mount, iso_path)
                    print(f"\n{'✓' if ok else '✗'} {msg}")
                else:
                    print("ISO file not found.")
                input("Press Enter to continue...")
            elif choice == "3":
                mount = "/tmp/multiboot-usb-boot"
                os.makedirs(mount, exist_ok=True)
                subprocess.run(["mount", f"{device['name']}2", mount], capture_output=True)
                ok, msg = self.refresh_menu(mount)
                print(f"\n{'✓' if ok else '✗'} {msg}")
                input("Press Enter to continue...")
            elif choice == "4":
                mount = "/tmp/multiboot-usb-boot"
                os.makedirs(mount, exist_ok=True)
                subprocess.run(["mount", f"{device['name']}2", mount], capture_output=True)
                subprocess.run(["multiboot-usb", "edit-metadata", mount])
                input("Press Enter to continue...")
            elif choice == "5":
                return


def main():
    tui = MultibootUsbTui()
    tui.simple_menu()


if __name__ == "__main__":
    main()
