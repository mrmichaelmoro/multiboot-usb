#!/usr/bin/env python3
"""Lightweight web UI for multiboot-usb — served from live ISO on boot."""
from __future__ import annotations

import subprocess
import shutil
import os
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional


DATA_DIR = Path("/tmp/multiboot-usb-data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
ISOS_DIR = DATA_DIR / "isos"
ISOS_DIR.mkdir(exist_ok=True)


def run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def scan_usb() -> list[dict]:
    rc, out, _ = run(["lsblk", "-d", "-o", "NAME,SIZE,TRAN,MODEL", "-n", "-p", "--json"])
    if rc != 0:
        return []
    try:
        data = json.loads(out)
        devices = []
        for b in data.get("blockdevices", []):
            if b.get("tran") == "usb":
                devices.append({
                    "name": b["name"],
                    "size": b.get("size", ""),
                    "model": b.get("model", ""),
                })
        return devices
    except json.JSONDecodeError:
        return []


def get_mount_point(device: str) -> str:
    """Get or create mount point for the boot partition."""
    # Use partition 2 (boot) on the target device
    partition = f"{device}2"
    mount = Path("/tmp/multiboot-usb-mnt")
    mount.mkdir(exist_ok=True)
    run(["mount", partition, str(mount)])
    return str(mount)


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode())

        elif parsed.path == "/api/scan":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            devices = scan_usb()
            self.wfile.write(json.dumps({"devices": devices}).encode())

        elif parsed.path == "/api/isos":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            isos = []
            if ISOS_DIR.exists():
                for f in sorted(ISOS_DIR.glob("*.iso")):
                    isos.append({"name": f.name, "size": f.stat().st_size})
            self.wfile.write(json.dumps({"isos": isos}).encode())

        elif parsed.path == "/api/metadata":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            metadata = []
            meta_dir = DATA_DIR / "metadata"
            if meta_dir.exists():
                for f in sorted(meta_dir.glob("*.json")):
                    with open(f) as fh:
                        metadata.append(json.load(fh))
            self.wfile.write(json.dumps({"metadata": metadata}).encode())

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""
        params = urllib.parse.parse_qs(body.decode()) if body else {}

        if parsed.path == "/api/setup":
            device = params.get("device", [""])[0]
            rc, out, err = run(["multiboot-usb", "setup", device])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": rc == 0, "output": out, "error": err}).encode())

        elif parsed.path == "/api/add-iso":
            iso_path = params.get("iso", [""])[0]
            mount = params.get("mount", [str(ISOS_DIR)])[0]
            if os.path.exists(iso_path):
                dest = Path(mount) / Path(iso_path).name
                shutil.copy2(iso_path, dest)
                rc, out, err = run(["multiboot-usb", "add-iso", mount, str(dest)])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": rc == 0, "output": out, "error": err}).encode())
            else:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "File not found"}).encode())

        elif parsed.path == "/api/refresh":
            mount = params.get("mount", [str(ISOS_DIR)])[0]
            rc, out, err = run(["multiboot-usb", "refresh", mount])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": rc == 0, "output": out, "error": err}).encode())

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def log_message(self, format, *args):
        pass


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>multiboot-usb Config</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }
h1 { text-align: center; margin-bottom: 20px; color: #00d4ff; }
.container { max-width: 700px; margin: 0 auto; }
.card { background: #16213e; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
.card h2 { margin-bottom: 12px; font-size: 1.1em; color: #a0a0ff; }
label { display: block; margin: 6px 0 4px; font-size: 0.9em; }
select, input[type="text"] { width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #333; background: #0f3460; color: #eee; margin-bottom: 10px; }
button { background: #00d4ff; color: #000; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; }
button:hover { background: #00a8cc; }
.btn-danger { background: #e94560; color: #fff; }
.status { margin-top: 10px; padding: 10px; border-radius: 4px; font-size: 0.85em; white-space: pre-wrap; }
.status.ok { background: #0a3d0a; color: #90ee90; }
.status.err { background: #3d0a0a; color: #ffb0b0; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px; text-align: left; border-bottom: 1px solid #333; }
th { color: #a0a0ff; font-size: 0.85em; }
</style>
</head>
<body>
<div class="container">
<h1>multiboot-usb</h1>

<div class="card">
<h2>Target USB Drive</h2>
<p id="no-devices">Scanning for USB devices...</p>
<select id="device-select" style="display:none"></select>
<button onclick="setupDevice()">Setup (Partition + Install)</button>
<div id="setup-status" class="status" style="display:none"></div>
</div>

<div class="card">
<h2>ISO Images</h2>
<table>
<thead><tr><th>File</th><th>Size</th><th>Action</th></tr></thead>
<tbody id="iso-list"></tbody>
</table>
</div>

<div class="card">
<h2>Add ISO</h2>
<input type="text" id="iso-path" placeholder="/path/to/image.iso">
<button onclick="addISO()">Add ISO</button>
<div id="add-status" class="status" style="display:none"></div>
</div>

<div class="card">
<button onclick="refreshMenu()">Refresh Boot Menu</button>
<div id="refresh-status" class="status" style="display:none"></div>
</div>
</div>

<script>
function $(id) { return document.getElementById(id); }
function show(el, cls, msg) { el.style.display = 'block'; el.className = 'status ' + cls; el.textContent = msg; }
function clear(el) { el.style.display = 'none'; }

async function api(path, body) {
  const opts = { method: body ? 'POST' : 'GET' };
  if (body) { opts.headers = {'Content-Type': 'application/x-www-form-urlencoded'}; opts.body = body; }
  const r = await fetch('/api/' + path, opts);
  return r.json();
}

async function scanDevices() {
  const d = await api('scan');
  const sel = $('device-select');
  const none = $('no-devices');
  if (!d.devices.length) {
    none.textContent = 'No USB devices detected.';
    sel.style.display = 'none';
    return;
  }
  none.style.display = 'none';
  sel.style.display = 'block';
  sel.innerHTML = d.devices.map(d => `<option value="${d.name}">${d.name} (${d.size}) — ${d.model || 'Unknown'}</option>`).join('');
}

async function setupDevice() {
  const dev = $('device-select').value;
  if (!dev) return;
  show($('setup-status'), 'err', 'Setting up...');
  const d = await api('setup', 'device=' + encodeURIComponent(dev));
  if (d.ok) show($('setup-status'), 'ok', d.output);
  else show($('setup-status'), 'err, d.error || 'Setup failed');
}

async function loadISOs() {
  const d = await api('isos');
  const list = $('iso-list');
  if (!d.isos.length) { list.innerHTML = '<tr><td colspan="3">No ISOs added yet</td></tr>'; return; }
  list.innerHTML = d.isos.map(i => `<tr><td>${i.name}</td><td>${(i.size / 1024 / 1024).toFixed(1)} MB</td><td><button class="btn-danger" onclick="removeISO('${i.name}')">Remove</button></td></tr>`).join('');
}

async function addISO() {
  const path = $('iso-path').value;
  if (!path) return;
  show($('add-status'), 'err', 'Copying...');
  const d = await api('add-iso', 'iso=' + encodeURIComponent(path));
  if (d.ok) { show($('add-status'), 'ok', 'Added: ' + path); $('iso-path').value = ''; loadISOs(); }
  else show($('add-status'), 'err, d.error || 'Failed');
}

async function refreshMenu() {
  show($('refresh-status'), 'err', 'Refreshing...');
  const d = await api('refresh');
  if (d.ok) show($('refresh-status'), 'ok', d.output);
  else show($('refresh-status'), 'err', d.error || 'Failed');
}

scanDevices();
loadISOs();
</script>
</body>
</html>
"""


def main(port: int = 8080):
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"multiboot-usb web UI running on http://0.0.0.0:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    main(port)
