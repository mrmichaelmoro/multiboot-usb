from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List

from multiboot_usb.iso_scanner import IsoMetadata


class MetadataEditor:
    def __init__(self, boot_partition: str):
        self.boot_dir = Path(boot_partition)
        self.meta_dir = self.boot_dir / "metadata"
        self.isos_dir = self.boot_dir / "boot" / "iso"
        self.isos: List[IsoMetadata] = []

        self.root = tk.Tk()
        self.root.title("multiboot-usb Metadata Editor")
        self.root.geometry("600x380")
        self.root.resizable(True, True)

        self._build_ui()
        self._load_isos()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        ttk.Label(main, text="ISO:").grid(row=0, column=0, sticky="w")
        self.iso_var = tk.StringVar()
        self.iso_combo = ttk.Combobox(main, textvariable=self.iso_var, state="readonly", width=48)
        self.iso_combo.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5)
        self.iso_combo.bind("<<ComboboxSelected>>", self._on_selected)

        row = 1
        self.fields = {}
        for label_text, attr in [
            ("Distro:", "distro"),
            ("Version:", "version"),
            ("Arch:", "arch"),
            ("Boot Type:", "boot_type"),
            ("Custom Label:", "custom_label"),
        ]:
            ttk.Label(main, text=label_text).grid(row=row, column=0, sticky="w", pady=2)
            var = tk.StringVar()
            entry = ttk.Entry(main, textvariable=var, width=48)
            entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=2)
            self.fields[attr] = var
            row += 1

        ttk.Label(main, text="SHA256:").grid(row=row, column=0, sticky="w", pady=2)
        self.sha256_var = tk.StringVar()
        ttk.Entry(main, textvariable=self.sha256_var, state="readonly", width=48).grid(
            row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=2)
        row += 1

        btn = ttk.Frame(main)
        btn.grid(row=row, column=0, columnspan=3, pady=10)
        ttk.Button(btn, text="Save", command=self._save).pack(side="left", padx=5)
        ttk.Button(btn, text="Re-detect", command=self._re_detect).pack(side="left", padx=5)
        ttk.Button(btn, text="Close", command=self.root.destroy).pack(side="left", padx=5)

        main.columnconfigure(1, weight=1)

    def _load_isos(self):
        self.isos = []
        if self.meta_dir.exists():
            for f in sorted(self.meta_dir.glob("*.json")):
                with open(f) as fh:
                    self.isos.append(IsoMetadata.from_dict(json.load(fh)))
        if self.isos:
            self.iso_combo["values"] = [iso.display_name for iso in self.isos]
            self.iso_combo.current(0)
            self._display(0)

    def _on_selected(self, event):
        idx = self.iso_combo.current()
        if idx >= 0:
            self._display(idx)

    def _display(self, idx: int):
        iso = self.isos[idx]
        for attr, var in self.fields.items():
            var.set(getattr(iso, attr, "") or "")
        self.sha256_var.set(iso.sha256)

    def _save(self):
        idx = self.iso_combo.current()
        if idx < 0:
            return
        iso = self.isos[idx]
        for attr, var in self.fields.items():
            setattr(iso, attr, var.get())
        iso.menu_label = iso.display_name
        meta_file = self.meta_dir / f"{iso.filename}.json"
        with open(meta_file, "w") as f:
            json.dump(iso.to_dict(), f, indent=2)
        self._load_isos()
        messagebox.showinfo("Saved", f"{iso.filename} metadata saved.")

    def _re_detect(self):
        idx = self.iso_combo.current()
        if idx < 0:
            return
        iso = self.isos[idx]
        from multiboot_usb.iso_scanner import IsoScanner
        scanner = IsoScanner(str(self.isos_dir))
        fresh = scanner._build_metadata(self.isos_dir / iso.filename)
        iso.distro = fresh.distro
        iso.version = fresh.version
        iso.arch = fresh.arch
        iso.boot_type = fresh.boot_type
        self._display(idx)

    def run(self):
        self.root.mainloop()


def edit_metadata(boot_partition: str):
    MetadataEditor(boot_partition).run()
