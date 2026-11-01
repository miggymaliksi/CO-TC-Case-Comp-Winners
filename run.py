#!/usr/bin/env python3
"""Prepare and start the local demo without asking beginners to activate environments."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import venv
import webbrowser
from local_ai_runtime import start as start_local_ai, stop as stop_local_ai

ROOT = Path(__file__).resolve().parent


def run(command, cwd=ROOT):
    subprocess.run(command, cwd=cwd, check=True)


def main():
    os.chdir(ROOT)
    if sys.version_info < (3, 9):
        raise RuntimeError(
            "Savor needs Python 3.9 or later. Python 3.11+ is recommended."
        )
    env = ROOT / ".venv"
    python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        print("Preparing Savor's local Python environment…", flush=True)
        venv.EnvBuilder(with_pip=True).create(env)
    requirements = ROOT / "backend/requirements.lock"
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker = env / ".savor-requirements.sha256"
    if not marker.exists() or marker.read_text() != digest:
        print("Installing Savor's Python packages…", flush=True)
        run([str(python), "-m", "pip", "install", "-r", str(requirements)])
        marker.write_text(digest)
    frontend = ROOT / "frontend"
    index = frontend / "dist/index.html"
    inputs = list((frontend / "src").glob("*")) + [
        frontend / "package.json",
        frontend / "package-lock.json",
        frontend / "index.html",
        frontend / "vite.config.js",
    ]
    needs_build = not index.exists() or any(
        p.stat().st_mtime > index.stat().st_mtime for p in inputs
    )
    if needs_build:
        npm = shutil.which("npm")
        if not npm:
            raise RuntimeError(
                "Install Node.js (version 22.12+ or 24+) from nodejs.org, restart VS Code, then try again."
            )
        print("Preparing Savor's interface…", flush=True)
        run([npm, "ci", "--no-audit", "--no-fund"], frontend)
        run([npm, "run", "build"], frontend)
    if "--prepare" in sys.argv:
        print("Savor is ready. Run python3 run.py to start.")
        return
    if "--desktop" in sys.argv:
        if sys.platform != "darwin":
            raise RuntimeError("The phone-style desktop demo currently supports Mac.")
        npm = shutil.which("npm")
        node = shutil.which("node")
        if not npm or not node:
            raise RuntimeError("Install Node.js, restart VS Code, then try again.")
        desktop = ROOT / "desktop"
        lock = desktop / "package-lock.json"
        stamp = desktop / "node_modules/.savor-lock.sha256"
        version = hashlib.sha256(lock.read_bytes()).hexdigest()
        if not stamp.exists() or stamp.read_text() != version:
            print("Preparing Savor's Mac window…", flush=True)
            run([npm, "ci", "--no-audit", "--no-fund"], desktop)
            stamp.write_text(version)
        if not (desktop / "node_modules/electron/path.txt").exists():
            run([node, "node_modules/electron/install.js"], desktop)
        run([npm, "start"], desktop)
        return
    config = ROOT / ".env"
    if config.exists():
        for line in config.read_text().splitlines():
            key, sep, value = line.partition("=")
            key = key.strip()
            if sep and key.startswith("SAVOR_"):
                os.environ.setdefault(key, value.strip().strip('"').strip("'"))
    host = os.environ.get("SAVOR_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise RuntimeError(
            "This sample-account build runs on your computer only. Use SAVOR_HOST=127.0.0.1."
        )
    port = int(os.environ.get("SAVOR_PORT", "8000"))
    print(
        f"\nSavor is opening at http://{host}:{port}\nKeep this terminal open. Press Ctrl+C to stop.\n",
        flush=True,
    )
    if "--no-browser" not in sys.argv:
        threading.Timer(2, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    local_process = start_local_ai()
    try:
        run(
            [
                str(python),
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                host,
                "--port",
                str(port),
            ]
        )
    finally:
        stop_local_ai(local_process)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSavor stopped.")
    except (RuntimeError, subprocess.CalledProcessError) as e:
        print(f"\nCould not start Savor: {e}", file=sys.stderr)
        sys.exit(1)
